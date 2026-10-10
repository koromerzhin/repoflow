"""Route du journal d'audit."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DbDep
from app.schemas.audit import AuditListResponse
from app.services import audit_service

router = APIRouter(tags=["audit"])


@router.get("/audit", response_model=AuditListResponse)
async def list_audit(
    session: DbDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    event_type: str | None = Query(default=None, description="Filtre par type d'événement."),
    repository: str | None = Query(default=None, description="Filtre par dépôt (owner/name)."),
    before_id: int | None = Query(
        default=None,
        ge=1,
        description="Curseur : entrées strictement antérieures à cet identifiant.",
    ),
) -> AuditListResponse:
    """Journal d'audit des analyses, décisions et tentatives de fusion."""
    events = audit_service.list_events(
        session,
        limit=limit,
        offset=offset,
        event_type=event_type,
        repository_full_name=repository,
        before_id=before_id,
    )
    total = audit_service.count_events(
        session,
        event_type=event_type,
        repository_full_name=repository,
    )
    next_cursor = events[-1].id if len(events) == limit else None
    return AuditListResponse(
        items=[audit_service.to_schema(event) for event in events],
        total=total,
        next_cursor=next_cursor,
    )
