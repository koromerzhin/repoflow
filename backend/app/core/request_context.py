"""Contexte de requête : identifiant de corrélation et journal d'accès.

Chaque requête HTTP reçoit un identifiant de corrélation (repris de l'en-tête
``X-Request-ID`` s'il est fourni, sinon généré). Il est propagé via un
``ContextVar`` afin d'apparaître dans les journaux, et renvoyé au client dans
l'en-tête de réponse ``X-Request-ID``.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextvars import ContextVar

from starlette.datastructures import Headers, MutableHeaders

from app.core.logging import get_logger

REQUEST_ID_HEADER = "X-Request-ID"
_MAX_REQUEST_ID_LENGTH = 64
_ALLOWED_REQUEST_ID = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._")

_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    """Retourne l'identifiant de corrélation de la requête courante."""
    return _request_id_var.get()


def _sanitize_request_id(value: str | None) -> str:
    """Nettoie un identifiant fourni par le client, ou en génère un."""
    if value:
        candidate = value.strip()[:_MAX_REQUEST_ID_LENGTH]
        if candidate and all(char in _ALLOWED_REQUEST_ID for char in candidate):
            return candidate
    return uuid.uuid4().hex


class RequestIdFilter(logging.Filter):
    """Injecte l'identifiant de corrélation dans chaque enregistrement de log."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class RequestContextMiddleware:
    """Middleware ASGI : identifiant de corrélation et journal d'accès."""

    def __init__(self, app) -> None:
        self.app = app
        self._logger = get_logger("app.access")

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        request_id = _sanitize_request_id(headers.get(REQUEST_ID_HEADER))
        token = _request_id_var.set(request_id)

        status_holder = {"status": 500}

        async def send_wrapper(message) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        start = time.perf_counter()
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            method = scope.get("method", "-")
            path = scope.get("path", "-")
            status = status_holder["status"]
            self._logger.info(
                "%s %s -> %s (%.1f ms)",
                method,
                path,
                status,
                duration_ms,
            )
            _request_id_var.reset(token)
