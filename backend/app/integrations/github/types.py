"""Types de domaine échangés avec les fournisseurs de données.

Ces enregistrements représentent la vue "brute" de GitHub. Les services
métier les transforment ensuite en schémas d'API (calcul de l'état agrégé
des checks, de l'éligibilité de fusion, etc.).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.issue import IssueState
from app.schemas.pull_request import (
    CheckState,
    PullRequestState,
    ReviewDecision,
    ReviewState,
)


class RepositoryRecord(BaseModel):
    """Dépôt tel que fourni par le fournisseur."""

    id: str
    owner: str
    name: str
    full_name: str
    default_branch: str
    private: bool
    open_issues_count: int = Field(ge=0)
    open_pull_requests_count: int = Field(ge=0)
    updated_at: datetime
    html_url: str


class CheckRecord(BaseModel):
    """Check CI brut."""

    name: str
    state: CheckState
    conclusion: str | None = None
    required: bool = False
    details_url: str | None = None


class IssueRecord(BaseModel):
    """Issue brute telle que fournie par le fournisseur."""

    id: str
    number: int = Field(ge=1)
    repository_full_name: str
    title: str
    author: str
    state: IssueState
    is_pull_request: bool = False
    labels: list[str] = Field(default_factory=list)
    assignees: list[str] = Field(default_factory=list)
    milestone: str | None = None
    created_at: datetime
    updated_at: datetime
    html_url: str


class PullRequestRecord(BaseModel):
    """Pull request brute avec ses checks."""

    id: str
    number: int = Field(ge=1)
    repository_full_name: str
    title: str
    author: str
    source_branch: str
    target_branch: str
    state: PullRequestState
    is_draft: bool
    mergeable: bool
    changed_files: int = Field(ge=0)
    additions: int = Field(ge=0)
    deletions: int = Field(ge=0)
    review_decision: ReviewDecision
    checks: list[CheckRecord] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    html_url: str


class PullRequestFileRecord(BaseModel):
    """Fichier modifié par une pull request."""

    filename: str
    status: str
    additions: int = Field(ge=0)
    deletions: int = Field(ge=0)
    changes: int = Field(ge=0)


class PullRequestReviewRecord(BaseModel):
    """Revue déposée sur une pull request."""

    id: str
    author: str
    state: ReviewState
    body: str | None = None
    submitted_at: datetime | None = None


class TimelineEventRecord(BaseModel):
    """Événement de la chronologie d'une pull request."""

    id: str
    event_type: str
    actor: str
    message: str
    created_at: datetime


class PullRequestDetailRecord(PullRequestRecord):
    """Pull request détaillée avec description, fichiers, revues et chronologie."""

    body: str | None = None
    files: list[PullRequestFileRecord] = Field(default_factory=list)
    reviews: list[PullRequestReviewRecord] = Field(default_factory=list)
    timeline: list[TimelineEventRecord] = Field(default_factory=list)


class MergeResultRecord(BaseModel):
    """Résultat d'une tentative de fusion d'une pull request."""

    merged: bool
    message: str
    sha: str | None = None
