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


class GitHubRateLimitStatus(BaseModel):
    """Dernier état connu du quota GitHub (fournisseur github uniquement)."""

    remaining: int | None = Field(description="Requêtes restantes avant réinitialisation.")
    limit: int | None = Field(description="Quota total de la fenêtre courante.")
    reset_at: datetime | None = Field(description="Instant de réinitialisation du quota.")


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
    github_rate_limit: GitHubRateLimitStatus | None = Field(
        default=None,
        description="Quota GitHub observé ; null en mode démonstration.",
    )
