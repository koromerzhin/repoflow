"""Client HTTP bas niveau pour l'API GitHub.

Responsabilités :

- authentifier côté serveur (le token n'est jamais exposé ni journalisé) ;
- suivre la pagination via l'en-tête ``Link`` ;
- detecter et signaler les limites de requêtes (rate limits) ;
- normaliser les erreurs GitHub.

Ce module ne contient aucune logique métier.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.errors import NotFoundError, ProviderError
from app.core.logging import get_logger
from app.integrations.github.errors import (
    GitHubAuthError,
    GitHubPermissionError,
    GitHubRateLimitError,
)

logger = get_logger(__name__)

_USER_AGENT = "RepoFlow"
_API_VERSION = "2022-11-28"


def parse_next_link(link_header: str | None) -> str | None:
    """Extrait l'URL de la page suivante depuis un en-tête ``Link`` GitHub."""
    if not link_header:
        return None
    for part in link_header.split(","):
        segments = part.split(";")
        url = segments[0].strip().strip("<>")
        for segment in segments[1:]:
            if segment.strip() == 'rel="next"':
                return url
    return None


def _is_rate_limited(response: httpx.Response) -> bool:
    return response.headers.get("x-ratelimit-remaining") == "0"


class GitHubClient:
    """Client HTTP authentifié pour l'API GitHub REST."""

    def __init__(
        self,
        token: str,
        api_url: str,
        *,
        timeout: float = 30.0,
        per_page: int = 100,
        max_pages: int = 10,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._per_page = per_page
        self._max_pages = max_pages
        # Le token est placé dans un en-tête (jamais dans l'URL ni les logs).
        self._client = httpx.AsyncClient(
            base_url=api_url.rstrip("/"),
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": _API_VERSION,
                "User-Agent": _USER_AGENT,
                "Authorization": f"Bearer {token}",
            },
            timeout=timeout,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> GitHubClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    def _raise_for_status(self, response: httpx.Response) -> None:
        status_code = response.status_code
        if status_code < 400:
            return
        if status_code == 401:
            raise GitHubAuthError("Authentification GitHub refusée : token invalide ou expiré.")
        if status_code in (403, 429):
            if _is_rate_limited(response):
                raise self._rate_limit_error(response)
            raise GitHubPermissionError(
                "Accès GitHub refusé : permissions insuffisantes ou ressource protégée."
            )
        if status_code == 404:
            raise NotFoundError("Ressource GitHub introuvable.")
        if status_code >= 500:
            raise ProviderError("Erreur côté GitHub, réessayez plus tard.")
        raise ProviderError(f"Requête GitHub invalide (statut {status_code}).")

    @staticmethod
    def _rate_limit_error(response: httpx.Response) -> GitHubRateLimitError:
        reset_raw = response.headers.get("x-ratelimit-reset")
        reset_at = int(reset_raw) if reset_raw and reset_raw.isdigit() else None
        return GitHubRateLimitError(
            "Limite de requêtes GitHub atteinte. Réessayez après réinitialisation.",
            reset_at=reset_at,
        )

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Effectue une requête GET unique et renvoie le JSON décodé."""
        response = await self._client.get(path, params=params)
        self._raise_for_status(response)
        return response.json()

    async def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Effectue une requête PUT et renvoie le JSON décodé.

        Utilisée uniquement pour les actions d'écriture explicitement
        autorisées (ex. fusion), jamais par défaut.
        """
        response = await self._client.put(path, json=json)
        self._raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()

    async def get_paginated(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        items_key: str | None = None,
    ) -> list[Any]:
        """Récupère toutes les pages d'une ressource.

        ``items_key`` permet d'extraire une liste imbriquée (ex. ``check_runs``).
        Le nombre de pages est borné par ``max_pages``.
        """
        items: list[Any] = []
        page = 1
        while True:
            query = dict(params or {})
            query["per_page"] = self._per_page
            query["page"] = page

            response = await self._client.get(path, params=query)
            self._raise_for_status(response)

            payload = response.json()
            if items_key is not None and isinstance(payload, dict):
                items.extend(payload.get(items_key, []))
            elif isinstance(payload, list):
                items.extend(payload)
            else:
                items.append(payload)

            next_link = parse_next_link(response.headers.get("link"))
            if not next_link:
                break
            if _is_rate_limited(response):
                # La page suivante nécessiterait une requête impossible.
                raise self._rate_limit_error(response)
            page += 1
            if page > self._max_pages:
                logger.warning(
                    "Pagination GitHub interrompue après %s pages (limite configurée).",
                    self._max_pages,
                )
                break
        return items
