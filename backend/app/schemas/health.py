"""Schémas du point de contrôle de santé."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

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


class LivenessResponse(BaseModel):
    """Réponse de ``GET /api/health/live`` : le processus répond."""

    status: Literal["ok"] = "ok"
    timestamp: datetime


class ReadinessResponse(BaseModel):
    """Réponse de ``GET /api/health/ready`` : dépendances prêtes à servir."""

    status: HealthStatus
    timestamp: datetime
    database: DatabaseStatus
    cache: str = Field(description="Backend de cache actif (memory, redis).")
    provider: str = Field(description="Fournisseur de données actif (demo, github).")
    github_rate_limit: GitHubRateLimitStatus | None = Field(
        default=None,
        description="Dernier quota GitHub observé ; null en mode démonstration.",
    )


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
