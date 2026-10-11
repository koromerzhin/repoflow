"""Routes du journal d'audit (consultation et export)."""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from app.api.deps import DbDep
from app.core.i18n import DEFAULT_LOCALE, get_locale
from app.schemas.audit import AuditListResponse
from app.services import audit_service

router = APIRouter(tags=["audit"])

_CSV_COLUMNS = (
    "id",
    "occurred_at",
    "event_type",
    "repository_full_name",
    "pull_request_number",
    "actor",
    "message",
)


@router.get("/audit", response_model=AuditListResponse)
async def list_audit(
    request: Request,
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
    locale = get_locale(request) or DEFAULT_LOCALE
    return AuditListResponse(
        items=[audit_service.to_schema(event, locale) for event in events],
        total=total,
        next_cursor=next_cursor,
    )


@router.get("/audit/export")
async def export_audit(
    request: Request,
    session: DbDep,
    export_format: Literal["csv", "json"] = Query(default="csv", alias="format"),
    event_type: str | None = Query(default=None, description="Filtre par type d'événement."),
    repository: str | None = Query(default=None, description="Filtre par dépôt (owner/name)."),
    limit: int = Query(default=5000, ge=1, le=50000),
) -> Response:
    """Exporte le journal d'audit en CSV ou JSON (mêmes filtres que la liste)."""
    events = audit_service.list_events(
        session,
        limit=limit,
        event_type=event_type,
        repository_full_name=repository,
    )
    locale = get_locale(request) or DEFAULT_LOCALE
    rows = [audit_service.to_schema(event, locale) for event in events]
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    disposition = f'attachment; filename="repoflow-audit-{stamp}.{export_format}"'

    if export_format == "json":
        body = json.dumps(
            [row.model_dump(mode="json") for row in rows],
            ensure_ascii=False,
            indent=2,
        )
        return Response(
            content=body,
            media_type="application/json",
            headers={"Content-Disposition": disposition},
        )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_CSV_COLUMNS)
    for row in rows:
        writer.writerow(
            [
                row.id,
                row.occurred_at.isoformat(),
                row.event_type,
                row.repository_full_name or "",
                row.pull_request_number if row.pull_request_number is not None else "",
                row.actor,
                row.message,
            ]
        )
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": disposition},
    )
