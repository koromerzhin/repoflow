"""Authentification par GitHub App : échange clé privée → jeton d'installation.

Une GitHub App authentifie ses requêtes en deux temps :

1. un **JWT** (RS256) signé avec la clé privée de l'application, valable au
   maximum 10 minutes, identifie l'application elle-même ;
2. ce JWT est échangé contre un **jeton d'installation**
   (``POST /app/installations/{id}/access_tokens``) valable une heure et
   porteur des permissions de l'installation (lecture, contenu…).

Le jeton d'installation est mis en cache et renouvelé peu avant son
expiration. Les installations bénéficient d'un quota de 15 000 requêtes/heure
contre 5 000 pour un token personnel.

La clé privée ne quitte jamais le serveur et n'est jamais journalisée.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import time
from datetime import datetime
from typing import Any

import httpx
import jwt

from app.core.errors import NotConfiguredError
from app.core.logging import get_logger
from app.integrations.github.errors import (
    GitHubAuthError,
    GitHubPermissionError,
)

logger = get_logger(__name__)

_JWT_TTL_SECONDS = 600
_JWT_CLOCK_SKEW_SECONDS = 60
_RENEW_MARGIN_SECONDS = 300
_FALLBACK_TTL_SECONDS = 3600

_USER_AGENT = "RepoFlow"
_API_VERSION = "2022-11-28"


def load_private_key(value: str) -> str:
    """Normalise la clé privée fournie (PEM brut, ``\n`` échappés ou base64)."""
    candidate = value.replace("\\n", "\n").strip()
    if candidate.startswith("-----BEGIN"):
        return candidate
    try:
        decoded = base64.b64decode(candidate, validate=True).decode("utf-8").strip()
    except (binascii.Error, UnicodeDecodeError) as cause:
        raise NotConfiguredError(
            "REPOFLOW_GITHUB_APP_PRIVATE_KEY invalide : PEM ou base64 attendu.",
            code="github_app_key_invalid",
        ) from cause
    if not decoded.startswith("-----BEGIN"):
        raise NotConfiguredError(
            "REPOFLOW_GITHUB_APP_PRIVATE_KEY invalide : PEM ou base64 attendu.",
            code="github_app_key_invalid",
        )
    return decoded


class InstallationTokenProvider:
    """Fournit le jeton d'installation courant, renouvelé avant expiration."""

    def __init__(
        self,
        app_id: str,
        private_key: str,
        installation_id: int,
        *,
        api_url: str = "https://api.github.com",
        timeout: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._app_id = app_id
        self._private_key = load_private_key(private_key)
        self._installation_id = installation_id
        self._client = httpx.AsyncClient(
            base_url=api_url.rstrip("/"),
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": _API_VERSION,
                "User-Agent": _USER_AGENT,
            },
            timeout=timeout,
            transport=transport,
        )
        self._lock = asyncio.Lock()
        self._token: str | None = None
        self._expires_epoch = 0.0

    async def get_token(self) -> str:
        """Renvoie le jeton d'installation, en le renouvelant si nécessaire."""
        async with self._lock:
            if self._token is not None and time.time() < self._expires_epoch:
                return self._token
            await self._renew()
            assert self._token is not None
            return self._token

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _renew(self) -> None:
        response = await self._client.post(
            f"/app/installations/{self._installation_id}/access_tokens",
            headers={"Authorization": f"Bearer {self._assertion()}"},
        )
        if response.status_code == 401:
            raise GitHubAuthError(
                "Authentification GitHub App refusée : identifiant d'application "
                "ou clé privée invalide."
            )
        if response.status_code == 404:
            raise GitHubAuthError(
                "Installation GitHub App introuvable : vérifiez "
                "REPOFLOW_GITHUB_APP_INSTALLATION_ID."
            )
        if response.status_code == 403:
            raise GitHubPermissionError(
                "Accès refusé : l'application n'est pas installée sur cette ressource."
            )
        if response.status_code >= 400:
            raise GitHubAuthError(
                f"Échange du jeton d'installation impossible (statut {response.status_code})."
            )
        payload = response.json()
        self._token = str(payload["token"])
        self._expires_epoch = self._expiry_epoch(payload)
        logger.info("Jeton d'installation GitHub App renouvelé.")

    def _assertion(self) -> str:
        now = int(time.time())
        return jwt.encode(
            {
                "iss": self._app_id,
                "iat": now - _JWT_CLOCK_SKEW_SECONDS,
                "exp": now + _JWT_TTL_SECONDS,
            },
            self._private_key,
            algorithm="RS256",
        )

    @staticmethod
    def _expiry_epoch(payload: dict[str, Any]) -> float:
        expires_at = payload.get("expires_at")
        if isinstance(expires_at, str):
            try:
                instant = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                return instant.timestamp() - _RENEW_MARGIN_SECONDS
            except ValueError:
                logger.warning("Expiration du jeton d'installation illisible ; délai par défaut.")
        return time.time() + _FALLBACK_TTL_SECONDS - _RENEW_MARGIN_SECONDS
