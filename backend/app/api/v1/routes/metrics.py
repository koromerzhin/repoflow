"""Route d'exposition des métriques d'observation."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.core.metrics import render_metrics

router = APIRouter()


@router.get("/metrics", response_class=PlainTextResponse, tags=["health"])
async def metrics() -> PlainTextResponse:
    """Métriques d'observation au format Prometheus."""
    return PlainTextResponse(
        render_metrics(), media_type="text/plain; version=0.0.4; charset=utf-8"
    )
