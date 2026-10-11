"""Cache TTL des données du fournisseur : mémoire ou Redis.

Deux backends derrière la même interface, choisis via
``REPOFLOW_CACHE_BACKEND`` :

- ``memory`` (défaut) : dictionnaire en mémoire avec expiration temporelle ;
- ``redis`` : valeurs partagées entre instances (JSON + ``SET … EX``).

Règles communes :

- ``refresh=True`` force le rechargement et remplace l'entrée ;
- ``ttl_seconds`` vaut 0 : le cache est désactivé ;
- les chargements concurrents d'une même clé sont coalescés
  (*single-flight*, par instance) ;
- **une panne Redis n'interrompt jamais l'application** : repli transparent
  sur le cache mémoire avec une nouvelle tentative périodique.

Le choix du backend se fait à chaud (à chaque opération) afin que les tests
puissent injecter un client ; l'URL Redis n'est jamais journalisée.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, TypeVar

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

_ENCODE, _DECODE = 0, 1
#: Codec optionnel : ``(encode) -> str`` et ``(raw: str) -> T``.
Codec = tuple[Callable[[Any], str], Callable[[str], Any]]

_MISS = object()

_entries: dict[tuple[Any, ...], tuple[float, Any]] = {}
_locks: dict[tuple[Any, ...], asyncio.Lock] = {}

_key_prefix = "repoflow:cache:"
_retry_delay_seconds = 30.0
_unavailable_until = 0.0
_client: Any = None
_override_client: Any = None


class RedisLike(Protocol):
    """Sous-ensemble du client Redis utilisé par ce module."""

    async def get(self, key: str) -> str | None: ...

    async def set(self, key: str, value: str, ex: int | None = None) -> Any: ...


def use_redis_client(client: Any | None) -> None:
    """Injecte un client Redis (utilisé par les tests)."""
    global _override_client
    _override_client = client


def default_codec() -> Codec:
    """Codec JSON simple, pour les valeurs directement sérialisables."""
    return (json.dumps, json.loads)


async def get_or_load(
    key: tuple[Any, ...],
    ttl_seconds: int,
    factory: Callable[[], Awaitable[T]],
    *,
    refresh: bool = False,
    codec: Codec | None = None,
) -> T:
    """Retourne la valeur en cache, ou la produit via ``factory``.

    Les appels concurrents pour une même clé partagent un unique chargement.
    ``codec`` définit la (dé)sérialisation pour le backend Redis.
    """
    if ttl_seconds <= 0:
        return await factory()

    lock = _locks.setdefault(key, asyncio.Lock())
    async with lock:
        if not refresh:
            cached = await _read(key, codec)
            if cached is not _MISS:
                return cached  # type: ignore[no-any-return]

        value = await factory()
        await _write(key, value, ttl_seconds, codec)
        return value


def clear() -> None:
    """Vide le cache mémoire et réinitialise l'état Redis (tests)."""
    global _unavailable_until, _client
    _entries.clear()
    _locks.clear()
    _unavailable_until = 0.0
    _client = None


def size() -> int:
    """Nombre d'entrées du cache mémoire (le backend Redis n'est pas compté)."""
    return len(_entries)


def _backend() -> str:
    return get_settings().cache_backend


def _redis_ready() -> bool:
    global _unavailable_until
    if _backend() != "redis":
        return False
    return time.monotonic() >= _unavailable_until


def _mark_unavailable(cause: Exception) -> None:
    global _unavailable_until
    _unavailable_until = time.monotonic() + _retry_delay_seconds
    logger.warning(
        "Cache Redis indisponible (%s) ; repli sur le cache mémoire.",
        type(cause).__name__,
    )


async def _ensure_client() -> Any:
    global _client
    if _override_client is not None:
        return _override_client
    if _client is None:
        try:
            from redis import asyncio as aioredis

            _client = aioredis.from_url(get_settings().cache_redis_url, decode_responses=True)
        except Exception as cause:  # pragma: no cover - import toujours présent
            _mark_unavailable(cause)
            raise
    return _client


def _storage_key(key: tuple[Any, ...]) -> str:
    return _key_prefix + ":".join(str(part) for part in key)


async def get_redis_client() -> Any:
    """Client Redis partagé (cache, limitation de débit).

    Lève si le backend n'est pas ``redis`` ou si la connexion échoue :
    l'appelant doit prévoir son propre repli.
    """
    if _backend() != "redis":
        raise RuntimeError("Le backend Redis n'est pas activé.")
    return await _ensure_client()


async def _read(key: tuple[Any, ...], codec: Codec | None) -> Any:
    if _redis_ready():
        try:
            client = await _ensure_client()
            raw = await client.get(_storage_key(key))
            if raw is not None:
                _, decode = codec or default_codec()
                return decode(raw)
        except Exception as cause:
            _mark_unavailable(cause)
    entry = _entries.get(key)
    if entry is not None and entry[0] > time.monotonic():
        return entry[1]
    return _MISS


async def _write(key: tuple[Any, ...], value: Any, ttl_seconds: int, codec: Codec | None) -> None:
    if _redis_ready():
        try:
            client = await _ensure_client()
            encode, _ = codec or default_codec()
            await client.set(_storage_key(key), encode(value), ex=ttl_seconds)
            return
        except Exception as cause:
            _mark_unavailable(cause)
    _entries[key] = (time.monotonic() + ttl_seconds, value)
