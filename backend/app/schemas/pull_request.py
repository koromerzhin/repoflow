"""Schémas liés aux pull requests et aux checks CI."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class CheckState(StrEnum):
    """État d'un check CI.

    ``UNKNOWN`` ne doit jamais être interprété comme un succès.
    """

    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    UNKNOWN = "unknown"


class Check(BaseModel):
    """Résultat d'un check CI rattaché à une pull request."""

    name: str
    state: CheckState
    conclusion: str | None = Field(default=None, description="Conclusion brute du fournisseur.")
    required: bool = False
    details_url: str | None = None


class PullRequestState(StrEnum):
    OPEN = "open"
    DRAFT = "draft"
    CLOSED = "closed"
    MERGED = "merged"


class ReviewDecision(StrEnum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REVIEW_REQUIRED = "review_required"
    NONE = "none"


class MergeBlocker(BaseModel):
    """Motif empêchant la fusion (indicatif, aucune fusion n'est déclenchée)."""

    code: str
    message: str


class MergeEligibility(BaseModel):
    """Évaluation indicative des conditions de fusion.

    Cette évaluation est en lecture seule : aucune fusion n'est exécutée dans
    cette version.
    """

    eligible: bool
    blockers: list[MergeBlocker] = Field(default_factory=list)


class PullRequest(BaseModel):
    """Pull request avec ses checks et son éligibilité de fusion."""

    id: str
    number: int = Field(ge=1)
    repository_full_name: str
    title: str
    author: str
    source_branch: str
    target_branch: str
    state: PullRequestState
    is_draft: bool
    checks: list[Check]
    checks_state: CheckState
    review_decision: ReviewDecision
    mergeable: bool
    changed_files: int = Field(ge=0)
    additions: int = Field(ge=0)
    deletions: int = Field(ge=0)
    merge_eligibility: MergeEligibility
    created_at: datetime
    updated_at: datetime
    html_url: str
    is_demo: bool


class PullRequestListResponse(BaseModel):
    """Réponse de ``GET /api/v1/pull-requests``."""

    items: list[PullRequest]
    total: int = Field(ge=0)
    data_source: str
