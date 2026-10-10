"""Routes des issues."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query

from app.api.deps import ProviderDep
from app.schemas.issue import IssueListResponse
from app.services.data_service import get_issues

router = APIRouter()

_IssueStateFilter = Literal["open", "closed", "all"]


@router.get("/issues", response_model=IssueListResponse, tags=["issues"])
async def issues(
    provider: ProviderDep,
    repository: str | None = Query(default=None, description="Filtre par dépôt (owner/name)."),
    state: _IssueStateFilter = Query(default="open", description="État des issues à afficher."),
    limit: int = Query(default=100, ge=1, le=500),
    refresh: bool = Query(default=False, description="Ignore le cache et recharge les données."),
) -> IssueListResponse:
    """Liste des issues GitHub, hors pull requests."""
    query_state = None if state == "all" else state
    items = await get_issues(
        provider, repository_full_name=repository, state=query_state, refresh=refresh
    )
    return IssueListResponse(items=items[:limit], total=len(items), data_source=provider.name)
