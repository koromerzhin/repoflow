"""Routes d'état des automatisations et d'arrêt d'urgence."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.api.deps import DbDep, SettingsDep
from app.core.config import Settings
from app.schemas.automation import AutomationStatus, KillSwitchUpdate
from app.services import system_service

router = APIRouter(prefix="/automation", tags=["automation"])


def _status(session: Session, settings: Settings) -> AutomationStatus:
    return AutomationStatus(
        kill_switch_engaged=system_service.is_kill_switch_engaged(session),
        global_auto_merge_enabled=settings.auto_merge_enabled_globally,
        worker_enabled=settings.worker_enabled,
        worker_interval_seconds=settings.worker_interval_seconds,
    )


@router.get("/status", response_model=AutomationStatus)
async def automation_status(session: DbDep, settings: SettingsDep) -> AutomationStatus:
    """État courant des automatisations et des garde-fous."""
    return _status(session, settings)


@router.post("/kill-switch", response_model=AutomationStatus)
async def set_kill_switch(
    session: DbDep, settings: SettingsDep, payload: KillSwitchUpdate
) -> AutomationStatus:
    """Engage ou désengage l'arrêt d'urgence global.

    Une fois engagé, l'arrêt d'urgence empêche toute fusion automatique,
    quelles que soient les règles configurées.
    """
    system_service.set_kill_switch(session, payload.engaged)
    return _status(session, settings)
