"""Route de contrôle de santé."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import ProviderDep, SettingsDep
from app.db.session import get_engine
from app.schemas.health import DatabaseStatus, HealthResponse, HealthStatus

router = APIRouter()


def _database_status() -> DatabaseStatus:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return DatabaseStatus.UNAVAILABLE
    return DatabaseStatus.OK


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
    )
