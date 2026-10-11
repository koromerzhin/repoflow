"""Exceptions applicatives et gestionnaires d'erreurs FastAPI.

Les réponses d'erreur suivent un format stable et ne divulguent jamais de
secrets ni de détails internes sensibles.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.i18n import get_locale, render_message
from app.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Erreur métier de base exposée proprement au client."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "app_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        params: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.params = params
        if code is not None:
            self.code = code


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    """Conflit de ressource (ex. doublon de configuration)."""

    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class ProviderError(AppError):
    """Erreur provenant d'un fournisseur externe (GitHub, démo, ...)."""

    status_code = status.HTTP_502_BAD_GATEWAY
    code = "provider_error"


class NotConfiguredError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "not_configured"


def _error_payload(code: str, message: str) -> dict[str, object]:
    return {"error": {"code": code, "message": message}}


def _validation_details(exc: RequestValidationError) -> list[dict[str, object]]:
    """Détails d'erreur sérialisables (les valeurs ``ctx`` peuvent contenir des exceptions)."""
    details: list[dict[str, object]] = []
    for error in exc.errors():
        item: dict[str, object] = {
            key: error[key] for key in ("loc", "msg", "type") if key in error
        }
        context = error.get("ctx")
        if isinstance(context, dict):
            item["ctx"] = {key: str(value) for key, value in context.items()}
        details.append(item)
    return details


def register_exception_handlers(app: FastAPI) -> None:
    """Enregistre les gestionnaires d'erreurs sur l'application."""

    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        locale = get_locale(request)
        message = render_message(exc.code, locale, exc.params, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(exc.code, message),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        locale = get_locale(request)
        message = render_message("validation_error", locale, None, "La requête est invalide.")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "validation_error",
                    "message": message,
                    "details": _validation_details(exc),
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload("http_error", str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Erreur inattendue", exc_info=exc)
        message = render_message(
            "internal_error",
            get_locale(request),
            None,
            "Une erreur interne est survenue.",
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload("internal_error", message),
        )
