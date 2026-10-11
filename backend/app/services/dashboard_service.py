"""Service de construction du tableau de bord."""

from __future__ import annotations

from datetime import UTC, datetime

from app.integrations.github.provider import Provider
from app.integrations.github.types import PullRequestRecord, RepositoryRecord
from app.schemas.dashboard import ActivityItem, DashboardCounters, DashboardResponse
from app.schemas.pull_request import CheckState, PullRequestState
from app.services.data_service import get_combined_data, provider_info


def pull_request_stats(pull_requests: list[PullRequestRecord]) -> dict[str, int]:
    """Compteurs PR partagés entre le tableau de bord et les snapshots."""
    open_prs = [pr for pr in pull_requests if pr.state == PullRequestState.OPEN]

    def has_state(state: CheckState) -> int:
        return sum(1 for pr in open_prs if any(c.state == state for c in pr.checks))

    ready = sum(
        1
        for pr in open_prs
        if not pr.is_draft
        and pr.mergeable
        and all(c.state == CheckState.SUCCESS for c in pr.checks if c.required)
    )
    return {
        "open_pull_requests": len(open_prs),
        "pull_requests_ready_to_merge": ready,
        "pull_requests_with_failing_checks": has_state(CheckState.FAILURE),
        "pull_requests_pending_checks": has_state(CheckState.PENDING),
    }


def _counters(
    repositories: list[RepositoryRecord], pull_requests: list[PullRequestRecord]
) -> DashboardCounters:
    # Les dépôts archivés restent comptés côté référentiel, mais leurs
    # issues (figées) n'entrent pas dans le compteur d'issues ouvertes.
    return DashboardCounters(
        repositories=len(repositories),
        **pull_request_stats(pull_requests),
        open_issues=sum(
            repository.open_issues_count for repository in repositories if not repository.archived
        ),
    )


def _recent_activity(pull_requests: list[PullRequestRecord]) -> list[ActivityItem]:
    ordered = sorted(pull_requests, key=lambda pr: pr.updated_at, reverse=True)
    items = [
        ActivityItem(
            id=f"pr-{pr.id}-{int(pr.updated_at.timestamp())}",
            event_type="pull_request_update",
            message=(f"PR #{pr.number} « {pr.title} » ({pr.repository_full_name}) mise à jour."),
            repository_full_name=pr.repository_full_name,
            pull_request_number=pr.number,
            occurred_at=pr.updated_at,
        )
        for pr in ordered[:6]
    ]
    return items


async def build_dashboard(provider: Provider, *, refresh: bool = False) -> DashboardResponse:
    """Construit la réponse du tableau de bord à partir du fournisseur."""
    repositories, pull_requests = await get_combined_data(provider, refresh=refresh)
    return DashboardResponse(
        generated_at=datetime.now(UTC),
        data_source=provider.name,
        provider=provider_info(provider),
        counters=_counters(repositories, pull_requests),
        recent_activity=_recent_activity(pull_requests),
    )
