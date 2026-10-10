"""Schémas de l'état des automatisations et de l'arrêt d'urgence."""

from __future__ import annotations

from pydantic import BaseModel


class AutomationStatus(BaseModel):
    """État courant des automatisations (garde-fous inclus)."""

    kill_switch_engaged: bool
    global_auto_merge_enabled: bool
    worker_enabled: bool
    worker_interval_seconds: int


class KillSwitchUpdate(BaseModel):
    """Entrée de modification de l'arrêt d'urgence global."""

    engaged: bool
