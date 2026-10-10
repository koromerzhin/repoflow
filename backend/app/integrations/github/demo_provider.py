"""Fournisseur de démonstration : données fictives, clairement identifiées.

Aucune donnée de ce module ne provient de GitHub. Chaque réponse expose
``is_demo=True`` et ``data_source="demo"``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.integrations.github.types import (
    CheckRecord,
    PullRequestRecord,
    RepositoryRecord,
)
from app.schemas.pull_request import CheckState, PullRequestState, ReviewDecision


def _now() -> datetime:
    return datetime.now(UTC)


class DemoProvider:
    """Fournisseur servant des données de démonstration déterministes."""

    name = "demo"
    is_demo = True
    requires_token = False

    def __init__(self) -> None:
        self._data: tuple[list[RepositoryRecord], list[PullRequestRecord]] | None = None

    def _build(self) -> tuple[list[RepositoryRecord], list[PullRequestRecord]]:
        now = _now()
        day = timedelta(days=1)

        repos = [
            RepositoryRecord(
                id="repo-acme-web",
                owner="acme",
                name="web-app",
                full_name="acme/web-app",
                default_branch="main",
                private=False,
                open_issues_count=12,
                open_pull_requests_count=4,
                updated_at=now - timedelta(hours=2),
                html_url="https://github.com/acme/web-app",
            ),
            RepositoryRecord(
                id="repo-acme-api",
                owner="acme",
                name="api-gateway",
                full_name="acme/api-gateway",
                default_branch="main",
                private=False,
                open_issues_count=3,
                open_pull_requests_count=2,
                updated_at=now - timedelta(hours=5),
                html_url="https://github.com/acme/api-gateway",
            ),
            RepositoryRecord(
                id="repo-acme-sdk",
                owner="acme",
                name="client-sdk",
                full_name="acme/client-sdk",
                default_branch="trunk",
                private=True,
                open_issues_count=8,
                open_pull_requests_count=1,
                updated_at=now - timedelta(days=1),
                html_url="https://github.com/acme/client-sdk",
            ),
        ]

        prs = [
            PullRequestRecord(
                id="pr-acme-web-142",
                number=142,
                repository_full_name="acme/web-app",
                title="Améliorer l'affichage du tableau de bord sur mobile",
                author="camille.m",
                source_branch="feat/mobile-dashboard",
                target_branch="main",
                state=PullRequestState.OPEN,
                is_draft=False,
                mergeable=True,
                changed_files=14,
                additions=342,
                deletions=87,
                review_decision=ReviewDecision.APPROVED,
                checks=[
                    CheckRecord(
                        name="build",
                        state=CheckState.SUCCESS,
                        conclusion="success",
                        required=True,
                    ),
                    CheckRecord(
                        name="lint",
                        state=CheckState.SUCCESS,
                        conclusion="success",
                        required=True,
                    ),
                    CheckRecord(
                        name="unit-tests",
                        state=CheckState.SUCCESS,
                        conclusion="success",
                        required=True,
                    ),
                ],
                created_at=now - 3 * day,
                updated_at=now - timedelta(hours=1),
                html_url="https://github.com/acme/web-app/pull/142",
            ),
            PullRequestRecord(
                id="pr-acme-web-138",
                number=138,
                repository_full_name="acme/web-app",
                title="Corriger la fuite mémoire du composant de recherche",
                author="jules.r",
                source_branch="fix/memory-leak-search",
                target_branch="main",
                state=PullRequestState.OPEN,
                is_draft=False,
                mergeable=True,
                changed_files=6,
                additions=45,
                deletions=22,
                review_decision=ReviewDecision.CHANGES_REQUESTED,
                checks=[
                    CheckRecord(
                        name="build",
                        state=CheckState.SUCCESS,
                        conclusion="success",
                        required=True,
                    ),
                    CheckRecord(
                        name="unit-tests",
                        state=CheckState.FAILURE,
                        conclusion="failure",
                        required=True,
                    ),
                ],
                created_at=now - 5 * day,
                updated_at=now - timedelta(hours=4),
                html_url="https://github.com/acme/web-app/pull/138",
            ),
            PullRequestRecord(
                id="pr-acme-web-130",
                number=130,
                repository_full_name="acme/web-app",
                title="Refonte du module d'authentification",
                author="lea.b",
                source_branch="feat/auth-redesign",
                target_branch="main",
                state=PullRequestState.DRAFT,
                is_draft=True,
                mergeable=True,
                changed_files=23,
                additions=980,
                deletions=410,
                review_decision=ReviewDecision.NONE,
                checks=[
                    CheckRecord(
                        name="build",
                        state=CheckState.PENDING,
                        conclusion=None,
                        required=True,
                    ),
                ],
                created_at=now - day,
                updated_at=now - timedelta(minutes=20),
                html_url="https://github.com/acme/web-app/pull/130",
            ),
            PullRequestRecord(
                id="pr-acme-api-77",
                number=77,
                repository_full_name="acme/api-gateway",
                title="Ajouter la limite de débit par clé d'API",
                author="sami.h",
                source_branch="feat/rate-limit-api-keys",
                target_branch="main",
                state=PullRequestState.OPEN,
                is_draft=False,
                mergeable=True,
                changed_files=9,
                additions=210,
                deletions=15,
                review_decision=ReviewDecision.APPROVED,
                checks=[
                    CheckRecord(
                        name="build",
                        state=CheckState.SUCCESS,
                        conclusion="success",
                        required=True,
                    ),
                    CheckRecord(
                        name="integration-tests",
                        state=CheckState.UNKNOWN,
                        conclusion=None,
                        required=True,
                    ),
                ],
                created_at=now - 2 * day,
                updated_at=now - timedelta(hours=3),
                html_url="https://github.com/acme/api-gateway/pull/77",
            ),
            PullRequestRecord(
                id="pr-acme-api-74",
                number=74,
                repository_full_name="acme/api-gateway",
                title="Mettre à jour la documentation OpenAPI",
                author="camille.m",
                source_branch="docs/openapi-update",
                target_branch="main",
                state=PullRequestState.OPEN,
                is_draft=False,
                mergeable=True,
                changed_files=3,
                additions=120,
                deletions=60,
                review_decision=ReviewDecision.REVIEW_REQUIRED,
                checks=[
                    CheckRecord(
                        name="lint",
                        state=CheckState.SUCCESS,
                        conclusion="success",
                        required=True,
                    ),
                    CheckRecord(
                        name="docs-build",
                        state=CheckState.PENDING,
                        conclusion=None,
                        required=True,
                    ),
                ],
                created_at=now - day,
                updated_at=now - timedelta(hours=6),
                html_url="https://github.com/acme/api-gateway/pull/74",
            ),
            PullRequestRecord(
                id="pr-acme-sdk-31",
                number=31,
                repository_full_name="acme/client-sdk",
                title="Exposer les erreurs typées du SDK",
                author="jules.r",
                source_branch="feat/typed-errors",
                target_branch="trunk",
                state=PullRequestState.OPEN,
                is_draft=False,
                mergeable=False,
                changed_files=11,
                additions=180,
                deletions=40,
                review_decision=ReviewDecision.NONE,
                checks=[
                    CheckRecord(
                        name="build",
                        state=CheckState.SUCCESS,
                        conclusion="success",
                        required=True,
                    ),
                    CheckRecord(
                        name="e2e",
                        state=CheckState.FAILURE,
                        conclusion="failure",
                        required=True,
                    ),
                ],
                created_at=now - 4 * day,
                updated_at=now - timedelta(hours=2),
                html_url="https://github.com/acme/client-sdk/pull/31",
            ),
            PullRequestRecord(
                id="pr-acme-web-120",
                number=120,
                repository_full_name="acme/web-app",
                title="Gérer les utilitaires de date en interne",
                author="lea.b",
                source_branch="chore/date-utils",
                target_branch="main",
                state=PullRequestState.MERGED,
                is_draft=False,
                mergeable=True,
                changed_files=5,
                additions=88,
                deletions=12,
                review_decision=ReviewDecision.APPROVED,
                checks=[
                    CheckRecord(
                        name="build",
                        state=CheckState.SUCCESS,
                        conclusion="success",
                        required=True,
                    ),
                ],
                created_at=now - 10 * day,
                updated_at=now - 9 * day,
                html_url="https://github.com/acme/web-app/pull/120",
            ),
        ]

        return repos, prs

    def _ensure_built(self) -> None:
        if self._data is None:
            self._data = self._build()

    async def list_repositories(self) -> list[RepositoryRecord]:
        self._ensure_built()
        assert self._data is not None
        return self._data[0]

    async def list_pull_requests(
        self, repository_full_name: str | None = None
    ) -> list[PullRequestRecord]:
        self._ensure_built()
        assert self._data is not None
        prs = self._data[1]
        if repository_full_name is None:
            return prs
        return [pr for pr in prs if pr.repository_full_name == repository_full_name]
