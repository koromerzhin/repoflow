"""Route de contrôle de santé."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.deps import ProviderDep, SettingsDep
from app.core.cache import get_redis_client
from app.core.config import Settings
from app.db.session import get_engine
from app.integrations.github import ratelimit
from app.schemas.health import (
    DatabaseStatus,
    GitHubRateLimitStatus,
    HealthResponse,
    HealthStatus,
    LivenessResponse,
    ReadinessResponse,
)

router = APIRouter()


def _database_status() -> DatabaseStatus:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return DatabaseStatus.UNAVAILABLE
    return DatabaseStatus.OK


def _github_rate_limit_status(provider_name: str) -> GitHubRateLimitStatus | None:
    if provider_name != "github":
        return None
    observed = ratelimit.snapshot()
    if observed is None:
        return None
    reset_epoch = observed["reset_at"]
    return GitHubRateLimitStatus(
        resource=str(observed.get("resource") or "core"),
        remaining=observed["remaining"],
        limit=observed["limit"],
        reset_at=(datetime.fromtimestamp(reset_epoch, tz=UTC) if reset_epoch is not None else None),
    )


async def _cache_status(settings: Settings) -> str:
    """Vérifie la disponibilité du backend de cache sans jamais échouer."""
    if settings.cache_backend != "redis":
        return "memory"
    try:
        client = await get_redis_client()
        await client.ping()
    except Exception:
        return "unavailable"
    return "redis"


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health(settings: SettingsDep, provider: ProviderDep) -> HealthResponse:
    """Renvoie l'état de santé du service."""
    db_status = _database_status()
    status = HealthStatus.OK if db_status == DatabaseStatus.OK else HealthStatus.DEGRADED
    return HealthResponse(
        status=status,
        app=settings.app_name,
        version=settings.version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
        data_source=provider.name,
        database=db_status,
        kill_switch_engaged=settings.kill_switch_engaged,
        github_rate_limit=_github_rate_limit_status(provider.name),
    )


@router.get("/health/live", response_model=LivenessResponse, tags=["health"])
async def liveness() -> LivenessResponse:
    """Sonde de vivacité : succès tant que le processus répond."""
    return LivenessResponse(timestamp=datetime.now(UTC))


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ReadinessResponse}},
    tags=["health"],
)
async def readiness(settings: SettingsDep, provider: ProviderDep) -> JSONResponse:
    """Sonde de disponibilité : ``503`` tant qu'une dépendance n'est pas prête."""
    db_status = _database_status()
    cache_status = await _cache_status(settings)
    ready = db_status == DatabaseStatus.OK and cache_status != "unavailable"
    payload = ReadinessResponse(
        status=HealthStatus.OK if ready else HealthStatus.DEGRADED,
        timestamp=datetime.now(UTC),
        database=db_status,
        cache=cache_status,
        provider=provider.name,
        github_rate_limit=_github_rate_limit_status(provider.name),
    )
    return JSONResponse(
        status_code=200 if ready else 503,
        content=payload.model_dump(mode="json"),
    )
