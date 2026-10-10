"""Rassemblement des routes de l'API v1."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import dashboard, issues, pull_requests, repositories

api_v1_router = APIRouter()
api_v1_router.include_router(dashboard.router)
api_v1_router.include_router(repositories.router)
api_v1_router.include_router(pull_requests.router)
api_v1_router.include_router(issues.router)
