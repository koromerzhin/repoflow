"""Tests du fournisseur GitHub réel (réponses simulées, aucun réseau)."""

from __future__ import annotations

import httpx
import pytest

from app.integrations.github.client import GitHubClient
from app.integrations.github.errors import GitHubRateLimitError
from app.integrations.github.github_provider import GithubProvider
from app.integrations.github.types import IssueRecord
from app.schemas.pull_request import CheckState, PullRequestState, ReviewDecision


def _repos() -> list[dict]:
    return [
        {
            "id": 1,
            "name": "web-app",
            "full_name": "acme/web-app",
            "owner": {"login": "acme"},
            "default_branch": "main",
            "private": False,
            "open_issues_count": 4,
            "updated_at": "2024-05-02T10:00:00Z",
            "html_url": "https://github.com/acme/web-app",
        },
        {
            "id": 2,
            "name": "api",
            "full_name": "acme/api",
            "owner": {"login": "acme"},
            "default_branch": "main",
            "private": True,
            "open_issues_count": 1,
            "updated_at": "2024-05-01T10:00:00Z",
            "html_url": "https://github.com/acme/api",
        },
    ]


def _pr_summary() -> list[dict]:
    return [{"number": 10}]


def _pr_detail() -> dict:
    return {
        "id": 100,
        "number": 10,
        "title": "Ajouter la limitation de débit",
        "user": {"login": "sami"},
        "head": {"ref": "feat/rate-limit", "sha": "abc123"},
        "base": {"ref": "main"},
        "state": "open",
        "draft": False,
        "mergeable": True,
        "changed_files": 5,
        "additions": 120,
        "deletions": 8,
        "created_at": "2024-05-01T10:00:00Z",
        "updated_at": "2024-05-02T10:00:00Z",
        "html_url": "https://github.com/acme/web-app/pull/10",
    }


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/user/repos":
        return httpx.Response(200, json=_repos())
    if path == "/repos/acme/web-app/pulls":
        return httpx.Response(200, json=_pr_summary())
    if path == "/repos/acme/api/pulls":
        return httpx.Response(200, json=[])
    if path == "/repos/acme/web-app/pulls/10":
        return httpx.Response(200, json=_pr_detail())
    if path == "/repos/acme/web-app/commits/abc123/check-runs":
        return httpx.Response(
            200,
            json={
                "total_count": 1,
                "check_runs": [{"name": "build", "status": "completed", "conclusion": "success"}],
            },
        )
    if path == "/repos/acme/web-app/commits/abc123/status":
        return httpx.Response(
            200, json={"state": "pending", "statuses": [{"context": "deploy", "state": "pending"}]}
        )
    if path == "/repos/acme/web-app/pulls/10/reviews":
        return httpx.Response(
            200,
            json=[
                {
                    "user": {"login": "alice"},
                    "state": "APPROVED",
                    "submitted_at": "2024-05-02T00:00:00Z",
                }
            ],
        )
    if path == "/repos/acme/web-app/issues":
        return httpx.Response(
            200,
            json=[
                {
                    "id": 5,
                    "number": 5,
                    "title": "Bug ouvert",
                    "user": {"login": "dev"},
                    "state": "open",
                },
                {
                    "id": 6,
                    "number": 6,
                    "title": "Tâche fermée",
                    "user": {"login": "dev"},
                    "state": "closed",
                },
                {
                    "id": 7,
                    "number": 7,
                    "title": "PR masquée",
                    "user": {"login": "dev"},
                    "state": "open",
                    "pull_request": {"url": "..."},
                },
            ],
        )
    if path == "/repos/acme/web-app/issues/10/timeline":
        return httpx.Response(
            200,
            json=[
                {
                    "id": 1,
                    "event": "opened",
                    "actor": {"login": "sami"},
                    "created_at": "2024-05-01T10:00:00Z",
                },
                {
                    "id": 2,
                    "event": "commented",
                    "actor": {"login": "alice"},
                    "body": "Merci !",
                    "created_at": "2024-05-02T10:00:00Z",
                },
            ],
        )
    if path == "/repos/acme/web-app/pulls/10/files":
        return httpx.Response(
            200,
            json=[
                {
                    "filename": "src/limit.py",
                    "status": "added",
                    "additions": 100,
                    "deletions": 0,
                    "changes": 100,
                }
            ],
        )
    if path == "/repos/acme/api/issues":
        return httpx.Response(200, json=[])
    if path == "/repos/acme/web-app/pulls/10/merge" and request.method == "PUT":
        return httpx.Response(
            200,
            json={
                "merged": True,
                "sha": "deadbeef",
                "message": "Pull Request successfully merged",
            },
        )
    return httpx.Response(404, json={"message": f"non simulé: {path}"})


@pytest.fixture
def provider() -> GithubProvider:
    client = GitHubClient(
        token="secret-token",
        api_url="https://api.github.com",
        transport=httpx.MockTransport(_handler),
    )
    return GithubProvider(token="secret-token", client=client)


async def test_list_repositories(provider: GithubProvider) -> None:
    repositories = await provider.list_repositories()
    try:
        assert [repo.full_name for repo in repositories] == ["acme/web-app", "acme/api"]
        assert repositories[0].open_issues_count == 4
        assert repositories[1].private is True
    finally:
        await provider.aclose()


async def test_list_pull_requests_toutes_repos(provider: GithubProvider) -> None:
    pull_requests = await provider.list_pull_requests()
    try:
        assert len(pull_requests) == 1
        pr = pull_requests[0]
        assert pr.repository_full_name == "acme/web-app"
        assert pr.state == PullRequestState.OPEN
        assert pr.source_branch == "feat/rate-limit"
        assert pr.target_branch == "main"
        assert pr.changed_files == 5
        assert pr.review_decision == ReviewDecision.APPROVED
        assert {check.name for check in pr.checks} == {"build", "deploy"}
        states = {check.name: check.state for check in pr.checks}
        assert states["build"] == CheckState.SUCCESS
        assert states["deploy"] == CheckState.PENDING
    finally:
        await provider.aclose()


async def test_list_pull_requests_repo_filtre(provider: GithubProvider) -> None:
    pull_requests = await provider.list_pull_requests("acme/web-app")
    try:
        assert len(pull_requests) == 1
        assert pull_requests[0].number == 10
    finally:
        await provider.aclose()


async def test_list_issues_filtre_pull_requests(provider: GithubProvider) -> None:
    issues = await provider.list_issues("acme/web-app")
    try:
        assert len(issues) == 2
        assert all(issue.is_pull_request is False for issue in issues)
        assert issues[0].number == 5
        assert issues[0].state.value == "open"
    finally:
        await provider.aclose()


async def test_list_issues_repo_sans_issue(provider: GithubProvider) -> None:
    issues = await provider.list_issues("acme/api")
    try:
        assert issues == []
    finally:
        await provider.aclose()


async def test_list_issues_tous_les_repos(provider: GithubProvider) -> None:
    issues = await provider.list_issues()
    try:
        assert len(issues) == 2
    finally:
        await provider.aclose()


async def test_list_issues_ignore_un_depot_en_erreur_reseau(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    original = GithubProvider._issues_for

    async def flaky(
        self: GithubProvider, full_name: str, *, state: str | None
    ) -> list[IssueRecord]:
        calls.append(full_name)
        if full_name == "acme/api":
            raise httpx.ConnectError("panne simulée")
        return await original(self, full_name, state=state)

    monkeypatch.setattr(GithubProvider, "_issues_for", flaky)
    client = GitHubClient(
        token="secret-token",
        api_url="https://api.github.com",
        transport=httpx.MockTransport(_handler),
    )
    provider = GithubProvider(token="secret-token", client=client)
    try:
        issues = await provider.list_issues()
        assert {issue.repository_full_name for issue in issues} == {"acme/web-app"}
        assert calls == ["acme/web-app", "acme/api"]
    finally:
        await provider.aclose()


async def test_list_issues_propage_une_erreur_fournisseur(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def limited(
        self: GithubProvider, full_name: str, *, state: str | None
    ) -> list[IssueRecord]:
        if full_name == "acme/api":
            raise GitHubRateLimitError("limite atteinte")
        return []

    monkeypatch.setattr(GithubProvider, "_issues_for", limited)
    client = GitHubClient(
        token="secret-token",
        api_url="https://api.github.com",
        transport=httpx.MockTransport(_handler),
    )
    provider = GithubProvider(token="secret-token", client=client)
    try:
        with pytest.raises(GitHubRateLimitError):
            await provider.list_issues()
    finally:
        await provider.aclose()


async def test_get_pull_request_detail(provider: GithubProvider) -> None:
    detail = await provider.get_pull_request("acme/web-app", 10)
    try:
        assert detail.number == 10
        assert detail.changed_files == 5
        assert detail.review_decision == ReviewDecision.APPROVED
        assert {file.filename for file in detail.files} == {"src/limit.py"}
        assert detail.files[0].additions == 100
        assert len(detail.reviews) == 1
        assert detail.reviews[0].state.value == "approved"
        assert [event.event_type for event in detail.timeline] == ["opened", "commented"]
        assert detail.timeline[1].message == "Merci !"
    finally:
        await provider.aclose()


async def test_get_pull_request_inconnue(provider: GithubProvider) -> None:
    from app.core.errors import NotFoundError

    try:
        with pytest.raises(NotFoundError):
            await provider.get_pull_request("acme/inconnu", 1)
    finally:
        await provider.aclose()


async def test_merge_pull_request(provider: GithubProvider) -> None:
    result = await provider.merge_pull_request("acme/web-app", 10)
    try:
        assert result.merged is True
        assert result.sha == "deadbeef"
    finally:
        await provider.aclose()


async def test_merge_repository_invalide(provider: GithubProvider) -> None:
    from app.core.errors import NotFoundError

    try:
        with pytest.raises(NotFoundError):
            await provider.merge_pull_request("invalide", 10)
    finally:
        await provider.aclose()


async def test_aclose(provider: GithubProvider) -> None:
    await provider.aclose()
