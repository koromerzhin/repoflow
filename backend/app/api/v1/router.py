"""Rassemblement des routes de l'API v1."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import (
    audit,
    automation,
    configs,
    dashboard,
    issues,
    pull_requests,
    repositories,
    snapshots,
)

api_v1_router = APIRouter()
api_v1_router.include_router(dashboard.router)
api_v1_router.include_router(repositories.router)
api_v1_router.include_router(pull_requests.router)
api_v1_router.include_router(issues.router)
api_v1_router.include_router(configs.router)
api_v1_router.include_router(automation.router)
api_v1_router.include_router(audit.router)
api_v1_router.include_router(snapshots.router)
