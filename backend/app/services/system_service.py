"""Réglages système modifiables à chaud (dont l'arrêt d'urgence)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import SystemSetting

KILL_SWITCH_KEY = "kill_switch_engaged"


def _stored_kill_switch(session: Session) -> bool:
    setting = session.scalar(select(SystemSetting).where(SystemSetting.key == KILL_SWITCH_KEY))
    return setting is not None and setting.value.lower() == "true"


def is_kill_switch_engaged(session: Session) -> bool:
    """Arrêt d'urgence effectif.

    L'arrêt d'urgence est engagé si la variable d'environnement
    ``REPOFLOW_KILL_SWITCH_ENGAGED`` est vraie **ou** s'il a été engagé à
    chaud. Le désengager ne peut jamais neutraliser la variable
    d'environnement : c'est un garde-fou de sécurité.
    """
    return get_settings().kill_switch_engaged or _stored_kill_switch(session)


def set_kill_switch(session: Session, engaged: bool) -> bool:
    """Engage ou désengage l'arrêt d'urgence (override persistant)."""
    setting = session.scalar(select(SystemSetting).where(SystemSetting.key == KILL_SWITCH_KEY))
    value = "true" if engaged else "false"
    if setting is None:
        session.add(SystemSetting(key=KILL_SWITCH_KEY, value=value))
    else:
        setting.value = value
    session.commit()
    return is_kill_switch_engaged(session)
