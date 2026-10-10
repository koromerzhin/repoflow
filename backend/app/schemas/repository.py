"""Schémas liés aux dépôts GitHub."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Repository(BaseModel):
    """Dépôt GitHub suivi (données fictives ou réelles)."""

    id: str = Field(description="Identifiant interne stable du dépôt.")
    owner: str
    name: str
    full_name: str = Field(description="Format ``owner/name``.")
    default_branch: str
    private: bool
    open_issues_count: int = Field(ge=0)
    open_pull_requests_count: int = Field(ge=0)
    last_updated: datetime
    html_url: str
    is_demo: bool = Field(description="Vrai si le dépôt provient du mode démonstration.")


class RepositoryListResponse(BaseModel):
    """Réponse de ``GET /api/v1/repositories``."""

    items: list[Repository]
    total: int = Field(ge=0)
    data_source: str
