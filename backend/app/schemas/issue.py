"""Schémas liés aux issues GitHub."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class IssueState(StrEnum):
    """État d'une issue (les pull requests sont exclues de cet endpoint)."""

    OPEN = "open"
    CLOSED = "closed"


class Issue(BaseModel):
    """Issue GitHub (les pull requests sont filtrées côté fournisseur)."""

    id: str = Field(description="Identifiant interne stable de l'issue.")
    number: int = Field(ge=1)
    repository_full_name: str
    title: str
    author: str
    state: IssueState
    is_pull_request: bool = Field(default=False, description="Toujours faux pour cet endpoint.")
    labels: list[str] = Field(default_factory=list, description="Libellés de l'issue.")
    assignees: list[str] = Field(default_factory=list, description="Logins des assignés.")
    milestone: str | None = Field(default=None, description="Titre du jalon, si défini.")
    created_at: datetime
    updated_at: datetime
    html_url: str
    is_demo: bool = Field(description="Vrai si l'issue provient du mode démonstration.")


class IssueListResponse(BaseModel):
    """Réponse de ``GET /api/v1/issues``."""

    items: list[Issue]
    total: int = Field(ge=0)
    data_source: str
    next_cursor: int | None = Field(
        default=None,
        description="Prochain ``offset`` à passer pour la page suivante, si la liste continue.",
    )
