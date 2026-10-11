"""Routes des snapshots quotidiens (lecture seule)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from app.api.deps import DbDep, ProviderDep
from app.schemas.snapshot import SnapshotListResponse
from app.services import snapshot_service

router = APIRouter()


@router.get("/snapshots", response_model=SnapshotListResponse, tags=["snapshots"])
async def snapshots(
    session: DbDep,
    provider: ProviderDep,
    repository: str | None = Query(default=None, description="Filtre par dépôt (owner/name)."),
    since: date | None = Query(
        default=None, description="Date de début (inclusive), format YYYY-MM-DD."
    ),
    limit: int = Query(default=100, ge=1, le=500),
) -> SnapshotListResponse:
    """Historique quotidien des compteurs par dépôt, alimenté par le worker."""
    records = snapshot_service.list_snapshots(
        session,
        repository_full_name=repository,
        since=since,
        limit=limit,
    )
    return SnapshotListResponse(
        items=[snapshot_service.to_schema(record) for record in records],
        total=len(records),
        data_source=provider.name,
    )
