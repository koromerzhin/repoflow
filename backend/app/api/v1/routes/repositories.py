"""Routes des dépôts."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import ProviderDep
from app.schemas.repository import RepositoryListResponse
from app.services.data_service import get_repositories

router = APIRouter()


@router.get("/repositories", response_model=RepositoryListResponse, tags=["repositories"])
async def repositories(
    provider: ProviderDep,
    limit: int = Query(default=100, ge=1, le=500),
    refresh: bool = Query(default=False, description="Ignore le cache et recharge les données."),
) -> RepositoryListResponse:
    """Liste des dépôts suivis, avec pagination de base."""
    items = await get_repositories(provider, refresh=refresh)
    return RepositoryListResponse(items=items[:limit], total=len(items), data_source=provider.name)
