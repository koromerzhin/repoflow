"""Point d'entrée de l'application FastAPI RepoFlow."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.api.v1.routes.health import router as health_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.db.init_db import create_all


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Cycle de vie : initialisation propre au démarrage."""
    settings = get_settings()
    if settings.auto_create_tables:
        create_all()
    yield


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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(health_router, prefix="/api")
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
