"""Point d'entrée de l'application FastAPI RepoFlow."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.metrics import router as metrics_router
from app.core.config import get_settings
from app.core.errors import NotConfiguredError, register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.metrics import MetricsMiddleware
from app.core.request_context import RequestContextMiddleware
from app.core.security import (
    AuthMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    build_rate_limiter,
)
from app.db.init_db import create_all
from app.integrations.github.factory import get_provider
from app.worker import run_forever


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Cycle de vie : initialisation au démarrage et fermeture à l'arrêt."""
    settings = get_settings()
    if settings.auto_create_tables:
        create_all()

    worker_task: asyncio.Task[None] | None = None
    if settings.worker_enabled:
        worker_task = asyncio.create_task(run_forever(), name="repoflow-worker")

    try:
        yield
    finally:
        if worker_task is not None:
            worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await worker_task
        # Fermeture propre du client HTTP sortant du fournisseur, si présent.
        try:
            provider = get_provider()
        except NotConfiguredError:
            provider = None
        if provider is not None:
            aclose = getattr(provider, "aclose", None)
            if aclose is not None:
                await aclose()


def create_app() -> FastAPI:
    """Fabrique l'application FastAPI."""

    settings = get_settings()
    configure_logging(settings)
    logger = get_logger(__name__)
    logger.info(
        "Démarrage %s v%s (environnement=%s, fournisseur=%s)",
        settings.app_name,
        settings.version,
        settings.environment,
        settings.github_provider,
    )

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Supervision multi-dépôts GitHub : issues, pull requests et checks CI.",
        lifespan=lifespan,
    )

    # Ordre des middlewares : le dernier ajouté est le plus externe.
    # 1. Limitation de débit (le plus interne : peut court-circuiter la requête).
    if settings.rate_limit_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            enabled=True,
            limiter=build_rate_limiter(
                backend=settings.rate_limit_backend,
                requests=settings.rate_limit_requests,
                window_seconds=settings.rate_limit_window_seconds,
            ),
        )
    # 2. En-têtes de sécurité (HSTS réservé aux environnements en HTTPS).
    if settings.security_headers_enabled:
        app.add_middleware(
            SecurityHeadersMiddleware,
            secure_request=lambda _: settings.hsts_enabled or settings.environment == "production",
        )
    # 3. Authentification par jeton porteur (routes de l'API v1).
    if settings.auth_enabled and settings.api_token is not None:
        app.add_middleware(
            AuthMiddleware,
            token=settings.api_token.get_secret_value(),
            protected_prefixes=tuple(settings.auth_protected_prefixes),
        )
    # 4. Métriques d'observation.
    if settings.metrics_enabled:
        app.add_middleware(MetricsMiddleware)
    # 5. Contexte de requête : identifiant de corrélation + journal d'accès.
    app.add_middleware(RequestContextMiddleware)
    # 6. CORS (le plus externe : toute réponse, y compris les erreurs, reçoit
    #    les en-têtes CORS).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(health_router, prefix="/api")
    app.include_router(metrics_router, prefix="/api")
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
