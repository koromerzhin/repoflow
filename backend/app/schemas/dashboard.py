"""Schémas du tableau de bord."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ProviderInfo


class DashboardCounters(BaseModel):
    """Indicateurs synthétiques du tableau de bord."""

    repositories: int = Field(ge=0)
    open_pull_requests: int = Field(ge=0)
    pull_requests_ready_to_merge: int = Field(
        ge=0, description="PR éligibles selon les règles configurées (indicatif)."
    )
    pull_requests_with_failing_checks: int = Field(ge=0)
    pull_requests_pending_checks: int = Field(ge=0)
    open_issues: int = Field(ge=0)


class ActivityItem(BaseModel):
    """Élément d'activité récente affiché sur le tableau de bord."""

    id: str
    event_type: str
    message: str
    repository_full_name: str | None
    occurred_at: datetime


class DashboardResponse(BaseModel):
    """Réponse de ``GET /api/v1/dashboard``."""

    generated_at: datetime
    data_source: str
    provider: ProviderInfo
    counters: DashboardCounters
    recent_activity: list[ActivityItem]
