"""Tests de l'agrégation parallèle des dépôts (`collect`)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import httpx
import pytest

from app.core.config import Settings
from app.integrations.github import provider as provider_module
from app.integrations.github.errors import GitHubRateLimitError
from app.integrations.github.provider import collect
from app.integrations.github.types import PullRequestRecord, RepositoryRecord
from app.schemas.pull_request import PullRequestState, ReviewDecision

_NOW = datetime.now(UTC)


def _repo(full_name: str) -> RepositoryRecord:
    owner, name = full_name.split("/", 1)
    return RepositoryRecord(
        id=f"repo-{name}",
        owner=owner,
        name=name,
        full_name=full_name,
        default_branch="main",
        private=False,
        open_issues_count=0,
        open_pull_requests_count=0,
        updated_at=_NOW,
        html_url=f"https://example.test/{full_name}",
    )


def _pr(full_name: str, number: int) -> PullRequestRecord:
    return PullRequestRecord(
        id=f"{full_name}#{number}",
        number=number,
        repository_full_name=full_name,
        title="Titre",
        author="tester",
        source_branch="feat/x",
        target_branch="main",
        state=PullRequestState.OPEN,
        is_draft=False,
        mergeable=True,
        changed_files=1,
        additions=1,
        deletions=1,
        review_decision=ReviewDecision.REVIEW_REQUIRED,
        checks=[],
        created_at=_NOW,
        updated_at=_NOW,
        html_url=f"https://example.test/{full_name}/pull/{number}",
    )


class FakeProvider:
    """Fournisseur de test : liste de dépôts et PR paramétrables."""

    name = "test"
    is_demo = False
    requires_token = False

    def __init__(
        self,
        repos: list[RepositoryRecord],
        *,
        slow: set[str] | None = None,
        failing: set[str] | None = None,
        provider_errors: set[str] | None = None,
        delay: float = 0.0,
        slow_delay: float = 0.5,
    ) -> None:
        self._repos = repos
        self._slow = slow or set()
        self._failing = failing or set()
        self._provider_errors = provider_errors or set()
        self._delay = delay
        self._slow_delay = slow_delay
        self.active = 0
        self.max_active = 0

    async def list_repositories(self) -> list[RepositoryRecord]:
        return self._repos

    async def list_pull_requests(
        self, repository_full_name: str | None = None
    ) -> list[PullRequestRecord]:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            await asyncio.sleep(self._delay)
            if repository_full_name in self._slow:
                await asyncio.sleep(self._slow_delay)
            if repository_full_name in self._provider_errors:
                raise GitHubRateLimitError("limite atteinte")
            if repository_full_name in self._failing:
                raise httpx.ConnectError("panne réseau simulée")
            if repository_full_name is None:
                return []
            return [
                _pr(repository_full_name, 1),
                _pr(repository_full_name, 2),
            ]
        finally:
            self.active -= 1


def _patch_settings(monkeypatch, **overrides: object) -> None:  # type: ignore[no-untyped-def]
    base = {"github_max_concurrency": 4, "github_collection_timeout": 5.0}
    base.update(overrides)
    monkeypatch.setattr(provider_module, "get_settings", lambda: Settings(**base))


async def test_collect_agrege_tous_les_depots(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _patch_settings(monkeypatch)
    repos = [_repo("acme/a"), _repo("acme/b"), _repo("acme/c")]
    provider = FakeProvider(repos)

    repositories, pull_requests = await collect(provider)

    assert [r.full_name for r in repositories] == ["acme/a", "acme/b", "acme/c"]
    assert len(pull_requests) == 6
    # L'ordre des dépôts est préservé dans l'agrégat.
    assert [pr.repository_full_name for pr in pull_requests[:2]] == ["acme/a", "acme/a"]


async def test_collect_parallelise_avec_concurrence_bornee(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _patch_settings(monkeypatch, github_max_concurrency=2)
    repos = [_repo(f"acme/r{i}") for i in range(6)]
    provider = FakeProvider(repos, delay=0.02)

    await collect(provider)

    assert provider.max_active <= 2


async def test_collect_ignore_un_depot_en_erreur_reseau(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _patch_settings(monkeypatch)
    repos = [_repo("acme/ok"), _repo("acme/ko")]
    provider = FakeProvider(repos, failing={"acme/ko"})

    _, pull_requests = await collect(provider)

    assert {pr.repository_full_name for pr in pull_requests} == {"acme/ok"}


async def test_collect_propage_une_erreur_fournisseur(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _patch_settings(monkeypatch)
    repos = [_repo("acme/ok"), _repo("acme/ko")]
    provider = FakeProvider(repos, provider_errors={"acme/ko"})

    with pytest.raises(GitHubRateLimitError):
        await collect(provider)


async def test_collect_ignore_un_depot_trop_lent(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _patch_settings(monkeypatch, github_collection_timeout=0.05)
    repos = [_repo("acme/fast"), _repo("acme/slow")]
    provider = FakeProvider(repos, slow={"acme/slow"}, slow_delay=0.5)

    _, pull_requests = await collect(provider)

    assert {pr.repository_full_name for pr in pull_requests} == {"acme/fast"}


async def test_collect_ignore_les_depots_archives(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _patch_settings(monkeypatch)
    actif = _repo("acme/actif")
    archive = _repo("acme/archive").model_copy(update={"archived": True})
    provider = FakeProvider([actif, archive])

    repositories, pull_requests = await collect(provider)

    # Le dépôt archivé reste dans le référentiel (compteurs)…
    assert [r.full_name for r in repositories] == ["acme/actif", "acme/archive"]
    # …mais ses PR ne sont pas collectées.
    assert {pr.repository_full_name for pr in pull_requests} == {"acme/actif"}


async def test_collect_sans_depot(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _patch_settings(monkeypatch)
    repositories, pull_requests = await collect(FakeProvider([]))

    assert repositories == []
    assert pull_requests == []
