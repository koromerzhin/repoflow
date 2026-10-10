"""Durcissement sécurité : en-têtes HTTP et limitation de débit.

En-têtes : posture restrictive sur les réponses API (aucune exécution, pas de
navigation par *frame*). Limitation de débit : fenêtre fixe en mémoire, fondée
sur l'adresse IP du client.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from fastapi.responses import JSONResponse
from starlette.datastructures import MutableHeaders

_DEFAULT_API_CSP = "default-src 'none'; frame-ancestors 'none'"

_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), geolocation=(), microphone=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


class SecurityHeadersMiddleware:
    """Middleware ASGI : ajoute les en-têtes de sécurité sur les réponses."""

    def __init__(
        self,
        app,
        *,
        api_csp: str = _DEFAULT_API_CSP,
        secure_request: Callable[[dict[str, Any]], bool] | None = None,
    ) -> None:
        self.app = app
        self._api_csp = api_csp
        self._secure_request = secure_request

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        is_secure = bool(self._secure_request(scope)) if self._secure_request else False

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in _SECURITY_HEADERS.items():
                    headers[name] = value
                if is_secure:
                    headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
                scope_path = scope.get("path", "")
                if scope_path.startswith("/api"):
                    headers["Content-Security-Policy"] = self._api_csp
            await send(message)

        await self.app(scope, receive, send_wrapper)


class RateLimiter:
    """Limiteur de débit à fenêtre fixe, sans état hors mémoire."""

    def __init__(self, *, requests: int, window_seconds: int) -> None:
        if requests < 1:
            raise ValueError("le nombre de requêtes doit être un entier positif")
        if window_seconds < 1:
            raise ValueError("la fenêtre doit être un entier positif")
        self.requests = requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, tuple[float, int]] = {}

    def allow(self, key: str) -> bool:
        """Autorise la requête si le seuil de la fenêtre n'est pas atteint."""
        now = time.monotonic()
        window_start, count = self._buckets.get(key, (0.0, 0))
        if now - window_start >= self.window_seconds:
            window_start, count = now, 0
        if count >= self.requests:
            self._buckets[key] = (window_start, count)
            return False
        self._buckets[key] = (window_start, count + 1)
        return True

    def remaining(self, key: str) -> int:
        """Retourne le nombre de requêtes encore autorisées dans la fenêtre."""
        now = time.monotonic()
        window_start, count = self._buckets.get(key, (0.0, 0))
        if now - window_start >= self.window_seconds:
            return self.requests
        return max(0, self.requests - count)

    def reset(self) -> None:
        """Vide l'état du limiteur (tests et rotation)."""
        self._buckets.clear()


class RateLimitMiddleware:
    """Middleware ASGI : applique le limiteur de débit par client."""

    def __init__(
        self,
        app,
        *,
        limiter: RateLimiter | None = None,
        enabled: bool = False,
        requests: int = 120,
        window_seconds: int = 60,
    ) -> None:
        self.app = app
        self._limiter = limiter or RateLimiter(requests=requests, window_seconds=window_seconds)
        self._enabled = enabled

    @staticmethod
    def _client_key(scope: dict[str, Any]) -> str:
        client = scope.get("client")
        if client and isinstance(client, (list, tuple)) and client:
            return str(client[0])
        return "unknown"

    async def __call__(self, scope, receive, send) -> None:
        if not self._enabled or scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        key = self._client_key(scope)
        if not self._limiter.allow(key):
            response = JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "rate_limit_exceeded",
                        "message": "Trop de requêtes. Réessayez plus tard.",
                    }
                },
                headers={"Retry-After": str(self._limiter.window_seconds)},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
