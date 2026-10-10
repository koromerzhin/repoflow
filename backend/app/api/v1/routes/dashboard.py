"""Route de tableau de bord."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import ProviderDep
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import build_dashboard

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse, tags=["dashboard"])
async def dashboard(
    provider: ProviderDep,
    refresh: bool = Query(default=False, description="Ignore le cache et recharge les données."),
) -> DashboardResponse:
    """Indicateurs synthétiques et activité récente.

    Les données proviennent du fournisseur configuré (mode démonstration par
    défaut) et sont clairement identifiées comme fictives.
    """
    return await build_dashboard(provider, refresh=refresh)
