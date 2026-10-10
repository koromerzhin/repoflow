"""Route de tableau de bord."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ProviderDep
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import build_dashboard

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse, tags=["dashboard"])
async def dashboard(provider: ProviderDep) -> DashboardResponse:
    """Indicateurs synthétiques et activité récente.

    Les données proviennent du fournisseur configuré (mode démonstration par
    défaut) et sont clairement identifiées comme fictives.
    """
    return await build_dashboard(provider)
