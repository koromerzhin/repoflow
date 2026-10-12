"""Dernier état connu des quotas GitHub, partagé au niveau du processus.

GitHub maintient deux fenêtres distinctes — ``core`` (requêtes REST) et
``graphql`` (points GraphQL), chacune avec ses en-têtes ``X-RateLimit-*``. Le
client HTTP met à jour l'instantané du bucket correspondant après chaque
réponse ; la route de santé expose le bucket **le plus contraint**, celui
qui déclenchera l'épuisement en premier.
"""

from __future__ import annotations

import threading

_lock = threading.Lock()
_snapshots: dict[str, dict[str, int | None]] = {}

_DEFAULT_LIMIT = 5000


def update(
    *, resource: str, remaining: int | None, limit: int | None, reset_at: int | None
) -> None:
    """Enregistre le dernier quota observé pour un bucket (core, graphql)."""
    with _lock:
        _snapshots[resource] = {
            "remaining": remaining,
            "limit": limit,
            "reset_at": reset_at,
        }


def _ratio(entry: dict[str, int | None]) -> float:
    remaining = entry["remaining"]
    if remaining is None:
        return 1.0
    limit = entry["limit"]
    return remaining / limit if limit else remaining / _DEFAULT_LIMIT


def snapshot() -> dict[str, int | str | None] | None:
    """Renvoie le bucket le plus contraint observé (plus faible ratio).

    La clé ``resource`` identifie le bucket (``core`` ou ``graphql``).
    Renvoie ``None`` si aucun quota n'a encore été observé.
    """
    with _lock:
        if not _snapshots:
            return None
        resource, entry = min(_snapshots.items(), key=lambda pair: _ratio(pair[1]))
        return {"resource": resource, **entry}


def reset() -> None:
    """Réinitialise tous les instantanés (utilisé par les tests)."""
    with _lock:
        _snapshots.clear()
