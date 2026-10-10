"""Routes des pull requests."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import ProviderDep
from app.schemas.pull_request import PullRequestListResponse
from app.services.data_service import get_pull_requests

router = APIRouter()


@router.get(
    "/pull-requests",
    response_model=PullRequestListResponse,
    tags=["pull-requests"],
)
async def pull_requests(
    provider: ProviderDep,
    repository: str | None = Query(default=None, description="Filtre par dépôt (owner/name)."),
    limit: int = Query(default=100, ge=1, le=500),
) -> PullRequestListResponse:
    """Liste des pull requests et de leurs checks CI."""
    items = await get_pull_requests(provider, repository_full_name=repository)
    return PullRequestListResponse(items=items[:limit], total=len(items), data_source=provider.name)
