"""Services liés aux dépôts et aux pull requests."""

from __future__ import annotations

from app.integrations.github.provider import Provider, collect
from app.integrations.github.types import PullRequestRecord, RepositoryRecord
from app.schemas.common import ProviderInfo
from app.schemas.pull_request import Check, PullRequest
from app.schemas.repository import Repository
from app.services.merge_rules import aggregate_checks_state, evaluate_merge_eligibility


def provider_info(provider: Provider) -> ProviderInfo:
    """Description du fournisseur pour les réponses d'API."""
    return ProviderInfo(
        name=provider.name,
        is_demo=provider.is_demo,
        requires_token=provider.requires_token,
    )


def repository_to_schema(repository: RepositoryRecord, *, is_demo: bool) -> Repository:
    """Convertit un dépôt du fournisseur en schéma d'API."""
    return Repository(
        id=repository.id,
        owner=repository.owner,
        name=repository.name,
        full_name=repository.full_name,
        default_branch=repository.default_branch,
        private=repository.private,
        open_issues_count=repository.open_issues_count,
        open_pull_requests_count=repository.open_pull_requests_count,
        last_updated=repository.updated_at,
        html_url=repository.html_url,
        is_demo=is_demo,
    )


def pull_request_to_schema(pr: PullRequestRecord, *, is_demo: bool) -> PullRequest:
    """Convertit une pull request du fournisseur en schéma d'API.

    Le calcul de l'état agrégé des checks et de l'éligibilité est effectué
    par les règles métier (`app.services.merge_rules`).
    """
    return PullRequest(
        id=pr.id,
        number=pr.number,
        repository_full_name=pr.repository_full_name,
        title=pr.title,
        author=pr.author,
        source_branch=pr.source_branch,
        target_branch=pr.target_branch,
        state=pr.state,
        is_draft=pr.is_draft,
        checks=[Check.model_validate(check.model_dump()) for check in pr.checks],
        checks_state=aggregate_checks_state(pr.checks),
        review_decision=pr.review_decision,
        mergeable=pr.mergeable,
        changed_files=pr.changed_files,
        additions=pr.additions,
        deletions=pr.deletions,
        merge_eligibility=evaluate_merge_eligibility(pr),
        created_at=pr.created_at,
        updated_at=pr.updated_at,
        html_url=pr.html_url,
        is_demo=is_demo,
    )


async def get_repositories(provider: Provider) -> list[Repository]:
    """Dépôts disponibles auprès du fournisseur."""
    records = await provider.list_repositories()
    return [repository_to_schema(repository, is_demo=provider.is_demo) for repository in records]


async def get_pull_requests(
    provider: Provider, repository_full_name: str | None = None
) -> list[PullRequest]:
    """Pull requests disponibles auprès du fournisseur."""
    records: list[PullRequestRecord] = await provider.list_pull_requests(repository_full_name)
    return [pull_request_to_schema(pr, is_demo=provider.is_demo) for pr in records]


async def get_combined_data(
    provider: Provider,
) -> tuple[list[RepositoryRecord], list[PullRequestRecord]]:
    """Récupère dépôts et pull requests via le contrat d'intégration.

    Cette fonction existe pour que la couche API reste indépendante de la
    mécanique d'agrégation du fournisseur.
    """
    return await collect(provider)
