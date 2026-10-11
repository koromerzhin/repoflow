"""Schémas des snapshots quotidiens."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class DailySnapshotRead(BaseModel):
    """Agrégat quotidien d'un dépôt."""

    id: int
    repository_full_name: str
    snapshot_date: date
    data_source: str
    open_pull_requests: int = Field(ge=0)
    pull_requests_ready_to_merge: int = Field(ge=0)
    pull_requests_with_failing_checks: int = Field(ge=0)
    pull_requests_pending_checks: int = Field(ge=0)
    open_issues: int = Field(ge=0)


class SnapshotListResponse(BaseModel):
    """Réponse de ``GET /api/v1/snapshots``."""

    items: list[DailySnapshotRead]
    total: int = Field(ge=0)
    data_source: str
