"""Services liés aux dépôts et aux pull requests."""

from __future__ import annotations

import json
import unicodedata

from pydantic import BaseModel

from app.core.cache import Codec, get_or_load
from app.core.config import get_settings
from app.core.i18n import DEFAULT_LOCALE
from app.integrations.github.provider import Provider, collect
from app.integrations.github.types import (
    IssueRecord,
    PullRequestDetailRecord,
    PullRequestRecord,
    RepositoryRecord,
)
from app.schemas.common import ProviderInfo
from app.schemas.issue import Issue
from app.schemas.pull_request import (
    Check,
    PullRequest,
    PullRequestDetail,
    PullRequestFile,
    PullRequestReview,
    TimelineEvent,
)
from app.schemas.repository import Repository
from app.services.merge_rules import aggregate_checks_state, evaluate_merge_eligibility


def provider_info(provider: Provider) -> ProviderInfo:
    """Description du fournisseur pour les réponses d'API."""
    return ProviderInfo(
        name=provider.name,
        is_demo=provider.is_demo,
        requires_token=provider.requires_token,
    )


def _model_list_codec(model: type[BaseModel]) -> Codec:
    """Codec des listes de records Pydantic pour le backend Redis."""

    def encode(value: list[BaseModel]) -> str:
        return json.dumps([item.model_dump(mode="json") for item in value])

    def decode(raw: str) -> list[BaseModel]:
        return [model.model_validate(item) for item in json.loads(raw)]

    return encode, decode


def _model_codec(model: type[BaseModel]) -> Codec:
    """Codec d'un record Pydantic unique pour le backend Redis."""

    def encode(value: BaseModel) -> str:
        return value.model_dump_json()

    def decode(raw: str) -> BaseModel:
        return model.model_validate_json(raw)

    return encode, decode


def _combined_codec() -> Codec:
    """Codec du tuple ``(dépôts, pull requests)`` pour le backend Redis."""
    repository_codec = _model_list_codec(RepositoryRecord)
    pull_request_codec = _model_list_codec(PullRequestRecord)

    def encode(value: tuple[list[RepositoryRecord], list[PullRequestRecord]]) -> str:
        repositories, pull_requests = value
        return json.dumps(
            {
                "repositories": repository_codec[0](repositories),
                "pull_requests": pull_request_codec[0](pull_requests),
            }
        )

    def decode(raw: str) -> tuple[list[RepositoryRecord], list[PullRequestRecord]]:
        payload = json.loads(raw)
        return (
            repository_codec[1](payload["repositories"]),
            pull_request_codec[1](payload["pull_requests"]),
        )

    return encode, decode


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


def pull_request_to_schema(
    pr: PullRequestRecord, *, is_demo: bool, locale: str = DEFAULT_LOCALE
) -> PullRequest:
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
        merge_eligibility=evaluate_merge_eligibility(pr, locale=locale),
        created_at=pr.created_at,
        updated_at=pr.updated_at,
        html_url=pr.html_url,
        is_demo=is_demo,
    )


async def get_repositories(provider: Provider, *, refresh: bool = False) -> list[Repository]:
    """Dépôts disponibles auprès du fournisseur (mise en cache TTL)."""
    records: list[RepositoryRecord] = await get_or_load(
        (provider.name, "repositories"),
        get_settings().cache_ttl_seconds,
        provider.list_repositories,
        refresh=refresh,
        codec=_model_list_codec(RepositoryRecord),
    )
    return [repository_to_schema(repository, is_demo=provider.is_demo) for repository in records]


async def get_pull_requests(
    provider: Provider,
    repository_full_name: str | None = None,
    *,
    search: str | None = None,
    refresh: bool = False,
    locale: str = DEFAULT_LOCALE,
) -> list[PullRequest]:
    """Pull requests disponibles auprès du fournisseur (mise en cache TTL)."""
    records: list[PullRequestRecord] = await get_or_load(
        (provider.name, "pull_requests", repository_full_name),
        get_settings().cache_ttl_seconds,
        lambda: provider.list_pull_requests(repository_full_name),
        refresh=refresh,
        codec=_model_list_codec(PullRequestRecord),
    )
    return [
        pull_request_to_schema(pr, is_demo=provider.is_demo, locale=locale)
        for pr in records
        if matches_query(
            pr.title,
            pr.author,
            pr.number,
            pr.repository_full_name,
            pr.source_branch,
            pr.target_branch,
            query=search,
        )
    ]


def pull_request_detail_to_schema(
    pr: PullRequestDetailRecord, *, is_demo: bool, locale: str = DEFAULT_LOCALE
) -> PullRequestDetail:
    """Convertit une pull request détaillée du fournisseur en schéma d'API."""
    base = pull_request_to_schema(pr, is_demo=is_demo, locale=locale)
    return PullRequestDetail(
        **base.model_dump(),
        body=pr.body,
        files=[PullRequestFile.model_validate(item.model_dump()) for item in pr.files],
        reviews=[PullRequestReview.model_validate(item.model_dump()) for item in pr.reviews],
        timeline=[TimelineEvent.model_validate(item.model_dump()) for item in pr.timeline],
    )


async def get_pull_request(
    provider: Provider,
    repository_full_name: str,
    number: int,
    *,
    refresh: bool = False,
    locale: str = DEFAULT_LOCALE,
) -> PullRequestDetail:
    """Fiche détaillée d'une pull request (mise en cache TTL)."""
    record: PullRequestDetailRecord = await get_or_load(
        (provider.name, "pull_request", repository_full_name, number),
        get_settings().cache_ttl_seconds,
        lambda: provider.get_pull_request(repository_full_name, number),
        refresh=refresh,
        codec=_model_codec(PullRequestDetailRecord),
    )
    return pull_request_detail_to_schema(record, is_demo=provider.is_demo, locale=locale)


def issue_to_schema(issue: IssueRecord, *, is_demo: bool) -> Issue:
    """Convertit une issue du fournisseur en schéma d'API."""
    return Issue(
        id=issue.id,
        number=issue.number,
        repository_full_name=issue.repository_full_name,
        title=issue.title,
        author=issue.author,
        state=issue.state,
        is_pull_request=issue.is_pull_request,
        body=issue.body,
        labels=list(issue.labels),
        assignees=list(issue.assignees),
        milestone=issue.milestone,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
        html_url=issue.html_url,
        is_demo=is_demo,
    )


def matches_query(*values: object, query: str | None) -> bool:
    """Filtre texte insensible à la casse et aux accents.

    Appliqué après la mise en cache : le cache conserve toujours la liste
    complète du fournisseur.
    """
    normalized = _normalize(query or "")
    if not normalized:
        return True
    haystack = _normalize(" ".join(str(value) for value in values if value is not None))
    return normalized in haystack


def _normalize(value: str) -> str:
    """Normalise pour la recherche : casse et accents neutralisés."""
    decomposed = unicodedata.normalize("NFD", value.strip().lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


async def get_issues(
    provider: Provider,
    repository_full_name: str | None = None,
    state: str | None = None,
    *,
    search: str | None = None,
    refresh: bool = False,
) -> list[Issue]:
    """Issues disponibles auprès du fournisseur (mise en cache TTL)."""
    records: list[IssueRecord] = await get_or_load(
        (provider.name, "issues", repository_full_name, state),
        get_settings().cache_ttl_seconds,
        lambda: provider.list_issues(repository_full_name, state=state),
        refresh=refresh,
        codec=_model_list_codec(IssueRecord),
    )
    return [
        issue_to_schema(issue, is_demo=provider.is_demo)
        for issue in records
        if matches_query(
            issue.title,
            issue.author,
            issue.number,
            issue.repository_full_name,
            *issue.labels,
            *issue.assignees,
            issue.milestone,
            query=search,
        )
    ]


async def get_combined_data(
    provider: Provider, *, refresh: bool = False
) -> tuple[list[RepositoryRecord], list[PullRequestRecord]]:
    """Récupère dépôts et pull requests via le contrat d'intégration.

    Cette fonction existe pour que la couche API reste indépendante de la
    mécanique d'agrégation du fournisseur. Le résultat est mis en cache TTL.
    """
    return await get_or_load(
        (provider.name, "combined"),
        get_settings().cache_ttl_seconds,
        lambda: collect(provider),
        refresh=refresh,
        codec=_combined_codec(),
    )
