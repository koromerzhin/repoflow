"""Fournisseur GitHub réel.

S'appuie sur :class:`app.integrations.github.client.GitHubClient` pour l'accès
HTTP (authentification côté serveur, pagination, rate limits) et sur le module
``mapping`` pour convertir les données GitHub en enregistrements de domaine.

Aucun token n'est journalisé ni exposé. Aucune action d'écriture n'est
effectuée : ce fournisseur est strictement en lecture seule.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import httpx

from app.core.config import get_settings
from app.core.errors import NotFoundError, ProviderError
from app.core.logging import get_logger
from app.integrations.github.client import GitHubClient
from app.integrations.github.graphql import PULL_REQUESTS_QUERY, pull_requests_page
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
    MergeResultRecord,
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
        token: str | None = None,
        api_url: str = "https://api.github.com",
        *,
        timeout: float = 30.0,
        per_page: int = 100,
        max_pages: int = 10,
        client: GitHubClient | None = None,
        token_provider: Callable[[], Awaitable[str]] | None = None,
        use_graphql: bool = False,
    ) -> None:
        self._max_pages = max_pages
        self._use_graphql = use_graphql
        self._client = client or GitHubClient(
            token,
            api_url,
            timeout=timeout,
            per_page=per_page,
            max_pages=max_pages,
            token_provider=token_provider,
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

        if self._use_graphql:
            return await self._pull_requests_graphql(owner, name, full_name)

        listed = await self._client.get_paginated(f"/repos/{owner}/{name}/pulls", {"state": "open"})

        results: list[PullRequestRecord] = []
        for item in listed:
            number = int(item["number"])
            # L'endpoint de liste n'expose ni mergeable ni les statistiques de
            # diff : on récupère le détail. Le transport GraphQL (config
            # ``use_graphql``) remplace ce chemin par une requête agrégée.
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

    async def _pull_requests_graphql(
        self, owner: str, name: str, full_name: str
    ) -> list[PullRequestRecord]:
        """Pull requests via une requête GraphQL agrégée (1 requête par page).

        Checks CI et revues sont récupérés dans la même requête, ce qui divise
        fortement la consommation de quota par rapport à l'API REST.
        """
        results: list[PullRequestRecord] = []
        cursor: str | None = None
        page = 0
        while True:
            data = await self._client.execute_graphql(
                PULL_REQUESTS_QUERY,
                {"owner": owner, "name": name, "first": 50, "after": cursor},
            )
            items, cursor = pull_requests_page(data)
            for item in items:
                checks = map_combined_checks(item.pop("_check_runs"), item.pop("_statuses"))
                reviews = item.pop("_reviews")
                results.append(
                    map_pull_request(item, full_name, checks, map_review_decision(reviews))
                )
            page += 1
            if not cursor:
                break
            if page >= self._max_pages:
                logger.warning(
                    "Pagination GraphQL interrompue après %s pages (limite configurée).",
                    self._max_pages,
                )
                break
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
        """Issues des dépôts accessibles (hors pull requests).

        Les dépôts sont interrogés en parallèle (concurrence bornée et budget
        par dépôt, comme ``provider.collect``) : un dépôt lent ou en échec
        réseau est ignoré plutôt que de faire échouer toute la liste ; les
        erreurs applicatives (limite de requêtes, authentification) remontent.
        """
        if repository_full_name:
            full_names = [repository_full_name]
        else:
            repositories = await self.list_repositories()
            full_names = [repository.full_name for repository in repositories]

        settings = get_settings()
        semaphore = asyncio.Semaphore(settings.github_max_concurrency)
        timeout = settings.github_collection_timeout

        async def fetch(full_name: str) -> list[IssueRecord]:
            async with semaphore:
                try:
                    return await asyncio.wait_for(
                        self._issues_for(full_name, state=state), timeout=timeout
                    )
                except TimeoutError:
                    logger.warning("Délai dépassé pour les issues de %s ; dépôt ignoré.", full_name)
                    return []
                except ProviderError:
                    raise
                except httpx.HTTPError as exc:
                    logger.warning(
                        "Échec réseau pour les issues de %s ; dépôt ignoré (%s).",
                        full_name,
                        exc,
                    )
                    return []

        results = await asyncio.gather(*(fetch(full_name) for full_name in full_names))
        return [issue for group in results for issue in group]

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

    async def merge_pull_request(
        self,
        repository_full_name: str,
        number: int,
        *,
        merge_method: str = "squash",
    ) -> MergeResultRecord:
        """Fusionne une pull request (action d'écriture).

        Cette méthode n'est appelée que par le worker et uniquement lorsque
        l'automatisation est explicitement activée (règle + global) et que
        l'arrêt d'urgence est désengagé. Elle échoue proprement sinon.
        """
        owner, _, name = repository_full_name.partition("/")
        if not owner or not name:
            raise NotFoundError(
                "Nom de dépôt invalide ; format attendu : « owner/name ».",
                code="invalid_repository",
            )
        payload = await self._client.put(
            f"/repos/{owner}/{name}/pulls/{number}/merge",
            json={"merge_method": merge_method},
        )
        if isinstance(payload, dict) and payload.get("merged"):
            return MergeResultRecord(
                merged=True,
                message=str(payload.get("message") or "Pull request fusionnée."),
                sha=str(payload.get("sha")) if payload.get("sha") else None,
            )
        return MergeResultRecord(
            merged=False,
            message=str((payload or {}).get("message") or "Fusion refusée par GitHub."),
        )
