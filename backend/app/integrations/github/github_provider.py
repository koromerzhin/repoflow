"""Fournisseur GitHub réel.

S'appuie sur :class:`app.integrations.github.client.GitHubClient` pour l'accès
HTTP (authentification côté serveur, pagination, rate limits) et sur le module
``mapping`` pour convertir les données GitHub en enregistrements de domaine.

Aucun token n'est journalisé ni exposé. Aucune action d'écriture n'est
effectuée : ce fournisseur est strictement en lecture seule.
"""

from __future__ import annotations

from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.integrations.github.client import GitHubClient
from app.integrations.github.mapping import (
    map_combined_checks,
    map_issue,
    map_pull_request,
    map_pull_request_detail,
    map_repository,
    map_review_decision,
)
from app.integrations.github.types import (
    CheckRecord,
    IssueRecord,
    PullRequestDetailRecord,
    PullRequestRecord,
    RepositoryRecord,
)

logger = get_logger(__name__)


class GithubProvider:
    """Fournisseur en lecture seule interrogeant l'API GitHub."""

    name = "github"
    is_demo = False
    requires_token = True

    def __init__(
        self,
        token: str,
        api_url: str = "https://api.github.com",
        *,
        timeout: float = 30.0,
        per_page: int = 100,
        max_pages: int = 10,
        client: GitHubClient | None = None,
    ) -> None:
        self._client = client or GitHubClient(
            token,
            api_url,
            timeout=timeout,
            per_page=per_page,
            max_pages=max_pages,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def list_repositories(self) -> list[RepositoryRecord]:
        """Dépôts accessibles au token (lecture seule)."""
        data = await self._client.get_paginated(
            "/user/repos",
            {
                "sort": "updated",
                "direction": "desc",
                "affiliation": "owner,collaborator,organization_member",
            },
        )
        return [map_repository(item) for item in data]

    async def list_pull_requests(
        self, repository_full_name: str | None = None
    ) -> list[PullRequestRecord]:
        """Pull requests ouvertes, avec checks CI et décision de revue."""
        if repository_full_name:
            full_names = [repository_full_name]
        else:
            repositories = await self.list_repositories()
            full_names = [repository.full_name for repository in repositories]

        pull_requests: list[PullRequestRecord] = []
        for full_name in full_names:
            pull_requests.extend(await self._pull_requests_for(full_name))
        return pull_requests

    async def _pull_requests_for(self, full_name: str) -> list[PullRequestRecord]:
        owner, _, name = full_name.partition("/")
        if not owner or not name:
            logger.warning("Nom de dépôt ignoré car invalide : %s", full_name)
            return []

        listed = await self._client.get_paginated(f"/repos/{owner}/{name}/pulls", {"state": "open"})

        results: list[PullRequestRecord] = []
        for item in listed:
            number = int(item["number"])
            # L'endpoint de liste n'expose ni mergeable ni les statistiques de
            # diff : on récupère le détail. Une optimisation GraphQL pourra
            # réduire le nombre de requêtes ultérieurement.
            detail = await self._client.get(f"/repos/{owner}/{name}/pulls/{number}")
            head_sha = str((detail.get("head") or {}).get("sha") or "")
            checks = await self._checks(owner, name, head_sha)
            reviews = await self._client.get_paginated(
                f"/repos/{owner}/{name}/pulls/{number}/reviews"
            )
            results.append(
                map_pull_request(
                    detail,
                    full_name,
                    checks,
                    map_review_decision(reviews),
                )
            )
        return results

    async def get_pull_request(
        self, repository_full_name: str, number: int
    ) -> PullRequestDetailRecord:
        """Fiche détaillée d'une pull request (fichiers, revues, chronologie)."""
        owner, _, name = repository_full_name.partition("/")
        if not owner or not name:
            raise NotFoundError(
                "Nom de dépôt invalide ; format attendu : « owner/name ».",
                code="invalid_repository",
            )

        detail = await self._client.get(f"/repos/{owner}/{name}/pulls/{number}")
        head_sha = str((detail.get("head") or {}).get("sha") or "")
        checks = await self._checks(owner, name, head_sha)
        reviews = await self._client.get_paginated(f"/repos/{owner}/{name}/pulls/{number}/reviews")
        files = await self._client.get_paginated(f"/repos/{owner}/{name}/pulls/{number}/files")
        timeline = await self._client.get_paginated(
            f"/repos/{owner}/{name}/issues/{number}/timeline"
        )
        return map_pull_request_detail(
            detail, repository_full_name, checks, reviews, files, timeline
        )

    async def list_issues(
        self,
        repository_full_name: str | None = None,
        state: str | None = None,
    ) -> list[IssueRecord]:
        """Issues des dépôts accessibles (hors pull requests)."""
        if repository_full_name:
            full_names = [repository_full_name]
        else:
            repositories = await self.list_repositories()
            full_names = [repository.full_name for repository in repositories]

        issues: list[IssueRecord] = []
        for full_name in full_names:
            issues.extend(await self._issues_for(full_name, state=state))
        return issues

    async def _issues_for(self, full_name: str, *, state: str | None) -> list[IssueRecord]:
        owner, _, name = full_name.partition("/")
        if not owner or not name:
            logger.warning("Nom de dépôt ignoré car invalide : %s", full_name)
            return []

        params: dict[str, str] = {"state": state or "open"}
        data = await self._client.get_paginated(
            f"/repos/{owner}/{name}/issues",
            params,
        )
        return [
            map_issue(item, full_name, is_pull_request="pull_request" in item)
            for item in data
            if "pull_request" not in item
        ]

    async def _checks(self, owner: str, name: str, ref: str) -> list[CheckRecord]:
        if not ref:
            return []
        check_runs = await self._client.get_paginated(
            f"/repos/{owner}/{name}/commits/{ref}/check-runs",
            items_key="check_runs",
        )
        combined_status = await self._client.get(f"/repos/{owner}/{name}/commits/{ref}/status")
        statuses = combined_status.get("statuses", []) if isinstance(combined_status, dict) else []
        return map_combined_checks(check_runs, statuses)
