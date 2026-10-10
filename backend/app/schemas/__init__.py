"""Regroupement des schémas Pydantic."""

from app.schemas.common import DataSource, ProviderInfo
from app.schemas.dashboard import ActivityItem, DashboardCounters, DashboardResponse
from app.schemas.health import DatabaseStatus, HealthResponse, HealthStatus
from app.schemas.pull_request import (
    Check,
    CheckState,
    MergeBlocker,
    MergeEligibility,
    PullRequest,
    PullRequestListResponse,
    PullRequestState,
    ReviewDecision,
)
from app.schemas.repository import Repository, RepositoryListResponse

__all__ = [
    "ActivityItem",
    "Check",
    "CheckState",
    "DashboardCounters",
    "DashboardResponse",
    "DataSource",
    "DatabaseStatus",
    "HealthResponse",
    "HealthStatus",
    "MergeBlocker",
    "MergeEligibility",
    "ProviderInfo",
    "PullRequest",
    "PullRequestListResponse",
    "PullRequestState",
    "Repository",
    "RepositoryListResponse",
    "ReviewDecision",
]
