"""Schémas du point de contrôle de santé."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"


class DatabaseStatus(StrEnum):
    OK = "ok"
    UNAVAILABLE = "unavailable"
    NOT_CHECKED = "not_checked"


class HealthResponse(BaseModel):
    """Réponse de ``GET /api/health``."""

    status: HealthStatus = Field(description="État global du service.")
    app: str
    version: str
    environment: str
    timestamp: datetime
    data_source: str = Field(description="Fournisseur de données actif (demo, github).")
    database: DatabaseStatus
    kill_switch_engaged: bool = Field(description="Vrai si l'arrêt d'urgence global est engagé.")
