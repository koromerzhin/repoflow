"""Route de contrôle de santé."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import ProviderDep, SettingsDep
from app.db.session import get_engine
from app.integrations.github import ratelimit
from app.schemas.health import (
    DatabaseStatus,
    GitHubRateLimitStatus,
    HealthResponse,
    HealthStatus,
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
    reset_epoch = observed["reset_at"]
    return GitHubRateLimitStatus(
        remaining=observed["remaining"],
        limit=observed["limit"],
        reset_at=(datetime.fromtimestamp(reset_epoch, tz=UTC) if reset_epoch is not None else None),
    )


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
