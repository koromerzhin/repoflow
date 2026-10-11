"""Dernier état connu du quota GitHub, partagé au niveau du processus.

Le client HTTP met à jour cet instantané après chaque réponse portant les
en-têtes ``X-RateLimit-*``. La route de santé l'expose pour permettre à
l'interface d'afficher la consommation du quota.
"""

from __future__ import annotations

import threading

_lock = threading.Lock()
_snapshot: dict[str, int | None] = {
    "remaining": None,
    "limit": None,
    "reset_at": None,
}


def update(*, remaining: int | None, limit: int | None, reset_at: int | None) -> None:
    """Enregistre le dernier quota observé."""
    with _lock:
        _snapshot["remaining"] = remaining
        _snapshot["limit"] = limit
        _snapshot["reset_at"] = reset_at


def snapshot() -> dict[str, int | None]:
    """Renvoie une copie de l'instantané courant."""
    with _lock:
        return dict(_snapshot)


def reset() -> None:
    """Réinitialise l'instantané (utilisé par les tests)."""
    with _lock:
        _snapshot.update({"remaining": None, "limit": None, "reset_at": None})
