"""Routes des pull requests."""

from __future__ import annotations

from fastapi import APIRouter, Path, Query, Request

from app.api.deps import ProviderDep
from app.core.i18n import get_locale
from app.schemas.pull_request import PullRequestDetail, PullRequestListResponse
from app.services.data_service import get_pull_request, get_pull_requests

router = APIRouter()


@router.get(
    "/pull-requests",
    response_model=PullRequestListResponse,
    tags=["pull-requests"],
)
async def pull_requests(
    request: Request,
    provider: ProviderDep,
    repository: str | None = Query(default=None, description="Filtre par dépôt (owner/name)."),
    limit: int = Query(default=100, ge=1, le=500),
    refresh: bool = Query(default=False, description="Ignore le cache et recharge les données."),
) -> PullRequestListResponse:
    """Liste des pull requests et de leurs checks CI."""
    items = await get_pull_requests(
        provider,
        repository_full_name=repository,
        refresh=refresh,
        locale=get_locale(request),
    )
    return PullRequestListResponse(items=items[:limit], total=len(items), data_source=provider.name)


@router.get(
    "/pull-requests/{number}",
    response_model=PullRequestDetail,
    tags=["pull-requests"],
)
async def pull_request_detail(
    request: Request,
    provider: ProviderDep,
    number: int = Path(ge=1, description="Numéro de la pull request."),
    repository: str = Query(description="Dépôt de la pull request (owner/name)."),
    refresh: bool = Query(default=False, description="Ignore le cache et recharge les données."),
) -> PullRequestDetail:
    """Fiche détaillée d'une pull request : fichiers, revues et chronologie."""
    return await get_pull_request(
        provider,
        repository_full_name=repository,
        number=number,
        refresh=refresh,
        locale=get_locale(request),
    )
