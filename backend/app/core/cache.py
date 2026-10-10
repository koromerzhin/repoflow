"""Cache mémoire à durée de vie (TTL) pour les données du fournisseur.

Le cache évite de solliciter l'API GitHub à chaque requête. Il reste minimal :
un dictionnaire en mémoire avec expiration temporelle.

Il n'est ni persistant ni partagé entre instances : il ne remplace pas un cache
distribué. Les accès concurrents peuvent produire plusieurs chargements (le
dernier gagne), ce qui est acceptable ici.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

T = TypeVar("T")

_entries: dict[tuple[Any, ...], tuple[float, Any]] = {}


async def get_or_load(
    key: tuple[Any, ...],
    ttl_seconds: int,
    factory: Callable[[], Awaitable[T]],
    *,
    refresh: bool = False,
) -> T:
    """Retourne la valeur en cache, ou la produit via ``factory``.

    ``refresh=True`` force le rechargement et remplace l'entrée. Le cache est
    désactivé lorsque ``ttl_seconds`` vaut 0.
    """
    if ttl_seconds <= 0:
        return await factory()

    now = time.monotonic()
    if not refresh:
        entry = _entries.get(key)
        if entry is not None and entry[0] > now:
            return entry[1]  # type: ignore[no-any-return]

    value = await factory()
    _entries[key] = (now + ttl_seconds, value)
    return value


def clear() -> None:
    """Vide entièrement le cache (utilisé par les tests)."""
    _entries.clear()


def size() -> int:
    """Nombre d'entrées actuellement stockées."""
    return len(_entries)
