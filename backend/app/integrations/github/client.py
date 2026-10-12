"""Client HTTP bas niveau pour l'API GitHub.

Responsabilités :

- authentifier côté serveur (le token n'est jamais exposé ni journalisé) ;
- suivre la pagination via l'en-tête ``Link`` ;
- utiliser des requêtes conditionnelles (``ETag``) : les réponses ``304`` ne
  consomment pas la limite de requêtes GitHub ;
- réessayer une fois les limites secondaires (en-tête ``Retry-After``) ;
- detecter et signaler les limites de requêtes (rate limits) ;
- normaliser les erreurs GitHub.

Ce module ne contient aucune logique métier.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.errors import NotFoundError, ProviderError
from app.core.logging import get_logger
from app.core.metrics import record_provider_request
from app.integrations.github import ratelimit
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


@dataclass
class _ConditionalEntry:
    """Réponse mise en cache pour une requête conditionnelle (``ETag``)."""

    etag: str
    body: Any
    next_link: str | None


class GitHubClient:
    """Client HTTP authentifié pour l'API GitHub REST."""

    def __init__(
        self,
        token: str | None,
        api_url: str,
        *,
        timeout: float = 30.0,
        per_page: int = 100,
        max_pages: int = 10,
        max_retry_after: float = 5.0,
        max_conditional_entries: int = 512,
        transport: httpx.AsyncBaseTransport | None = None,
        token_provider: Callable[[], Awaitable[str]] | None = None,
    ) -> None:
        self._per_page = per_page
        self._max_pages = max_pages
        self._max_retry_after = max_retry_after
        self._max_conditional_entries = max_conditional_entries
        self._conditional: dict[str, _ConditionalEntry] = {}
        self._token_provider = token_provider
        # Le token est placé dans un en-tête (jamais dans l'URL ni les logs).
        # Absent lorsque l'authentification passe par un ``token_provider``.
        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": _API_VERSION,
            "User-Agent": _USER_AGENT,
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.AsyncClient(
            base_url=api_url.rstrip("/"),
            headers=headers,
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
            if _is_rate_limited(response) or status_code == 429:
                raise self._rate_limit_error(response)
            raise GitHubPermissionError(
                "Accès GitHub refusé : permissions insuffisantes ou ressource protégée."
            )
        if status_code == 404:
            raise NotFoundError(
                "Ressource GitHub introuvable.",
                code="github_resource_not_found",
            )
        if status_code >= 500:
            raise ProviderError(
                "Erreur côté GitHub, réessayez plus tard.",
                code="github_unavailable",
            )
        raise ProviderError(
            f"Requête GitHub invalide (statut {status_code}).",
            code="github_bad_request",
            params={"status_code": status_code},
        )

    @staticmethod
    def _rate_limit_error(response: httpx.Response) -> GitHubRateLimitError:
        reset_raw = response.headers.get("x-ratelimit-reset")
        reset_at = int(reset_raw) if reset_raw and reset_raw.isdigit() else None
        return GitHubRateLimitError(
            "Limite de requêtes GitHub atteinte. Réessayez après réinitialisation.",
            reset_at=reset_at,
        )

    def _retry_after_seconds(self, response: httpx.Response) -> float | None:
        raw = response.headers.get("retry-after")
        if raw is None or not raw.strip().isdigit():
            return None
        return min(float(raw), self._max_retry_after)

    @staticmethod
    def _record_rate_limit(response: httpx.Response) -> None:
        """Met à jour l'instantané de quota (bucket core ou graphql) exposé par la santé."""
        remaining = response.headers.get("x-ratelimit-remaining")
        if remaining is None or not remaining.isdigit():
            return
        limit = response.headers.get("x-ratelimit-limit")
        reset_raw = response.headers.get("x-ratelimit-reset")
        resource = response.headers.get("x-ratelimit-resource") or "core"
        ratelimit.update(
            resource=resource,
            remaining=int(remaining),
            limit=int(limit) if limit and limit.isdigit() else None,
            reset_at=int(reset_raw) if reset_raw and reset_raw.isdigit() else None,
        )

    def _cache_key(self, path: str, params: dict[str, Any] | None) -> str:
        if not params:
            return path
        query = "&".join(f"{key}={params[key]}" for key in sorted(params))
        return f"{path}?{query}"

    def _store_conditional(
        self,
        key: str,
        etag: str | None,
        body: Any,
        next_link: str | None,
    ) -> None:
        if not etag:
            return
        if len(self._conditional) >= self._max_conditional_entries:
            self._conditional.pop(next(iter(self._conditional)))
        self._conditional[key] = _ConditionalEntry(etag=etag, body=body, next_link=next_link)

    async def _send_with_retry(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        transport: str = "rest",
    ) -> httpx.Response:
        """Envoie la requête et réessaie une fois une limite secondaire.

        Les limites secondaires GitHub (``403``/``429`` avec en-tête
        ``Retry-After``) sont transitoires : une seule nouvelle tentative est
        effectuée après le délai indiqué (plafonné), puis l'erreur éventuelle
        est levée normalement.
        """
        request_headers = dict(headers or {})
        if self._token_provider is not None:
            token = await self._token_provider()
            request_headers["Authorization"] = f"Bearer {token}"
        record_provider_request(transport)
        response = await self._client.request(
            method, path, params=params, json=json, headers=request_headers
        )
        self._record_rate_limit(response)
        delay = self._retry_after_seconds(response)
        if response.status_code in (403, 429) and delay is not None:
            logger.info("Limite secondaire GitHub ; nouvelle tentative dans %.1fs.", delay)
            await asyncio.sleep(delay)
            response = await self._client.request(
                method, path, params=params, json=json, headers=request_headers
            )
        return response

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Effectue une requête GET unique et renvoie le JSON décodé.

        Les requêtes conditionnelles (``If-None-Match``) permettent de réutiliser
        une réponse inchangée sans consommer la limite de requêtes GitHub.
        """
        key = self._cache_key(path, params)
        cached = self._conditional.get(key)
        headers = {"If-None-Match": cached.etag} if cached else None
        response = await self._send_with_retry("GET", path, params=params, headers=headers)

        if response.status_code == 304 and cached is not None:
            return cached.body

        self._raise_for_status(response)
        body = response.json()
        self._store_conditional(key, response.headers.get("etag"), body, None)
        return body

    async def execute_graphql(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Exécute une requête GraphQL et renvoie le champ ``data``.

        Une réponse contenant des ``errors`` GraphQL (avec ou sans ``data``)
        lève ``ProviderError`` : une erreur partielle n'est jamais traitée
        comme un succès.
        """
        response = await self._send_with_retry(
            "POST",
            "/graphql",
            json={"query": query, "variables": variables or {}},
            transport="graphql",
        )
        self._raise_for_status(response)
        payload = response.json()
        errors = payload.get("errors")
        if errors:
            message = errors[0].get("message") if isinstance(errors[0], dict) else str(errors[0])
            raise ProviderError(
                f"Requête GraphQL GitHub refusée : {message}",
                code="github_graphql_error",
            )
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ProviderError(
                "Réponse GraphQL GitHub vide ou invalide.",
                code="github_graphql_error",
            )
        return data

    async def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Effectue une requête PUT et renvoie le JSON décodé.

        Utilisée uniquement pour les actions d'écriture explicitement
        autorisées (ex. fusion), jamais par défaut.
        """
        response = await self._send_with_retry("PUT", path, json=json)
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
        Le nombre de pages est borné par ``max_pages``. Chaque page est requêtée
        de manière conditionnelle (``ETag``) : une page inchangée renvoie
        ``304`` sans consommer la limite de requêtes GitHub.
        """
        items: list[Any] = []
        page = 1
        while True:
            query = dict(params or {})
            query["per_page"] = self._per_page
            query["page"] = page

            key = self._cache_key(path, query)
            cached = self._conditional.get(key)
            headers = {"If-None-Match": cached.etag} if cached else None
            response = await self._send_with_retry("GET", path, params=query, headers=headers)

            if response.status_code == 304 and cached is not None:
                payload = cached.body
                next_link = cached.next_link
            else:
                self._raise_for_status(response)
                payload = response.json()
                next_link = parse_next_link(response.headers.get("link"))
                self._store_conditional(key, response.headers.get("etag"), payload, next_link)
                if _is_rate_limited(response):
                    # La page suivante nécessiterait une requête impossible.
                    raise self._rate_limit_error(response)

            if items_key is not None and isinstance(payload, dict):
                items.extend(payload.get(items_key, []))
            elif isinstance(payload, list):
                items.extend(payload)
            else:
                items.append(payload)

            if not next_link:
                break
            page += 1
            if page > self._max_pages:
                logger.warning(
                    "Pagination GitHub interrompue après %s pages (limite configurée).",
                    self._max_pages,
                )
                break
        return items
