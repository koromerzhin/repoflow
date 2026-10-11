"""Schémas du journal d'audit."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AuditEventRead(BaseModel):
    """Entrée du journal d'audit."""

    id: int
    event_type: str
    repository_full_name: str | None
    pull_request_number: int | None
    actor: str
    message: str
    payload: dict[str, object] | None = None
    occurred_at: datetime


class AuditListResponse(BaseModel):
    """Réponse de ``GET /api/v1/audit``."""

    items: list[AuditEventRead]
    total: int = Field(ge=0)
    next_cursor: int | None = Field(
        default=None,
        description="Identifiant à passer à ``before_id`` pour la page suivante.",
    )
