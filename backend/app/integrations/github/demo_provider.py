"""Fournisseur de démonstration : données fictives, clairement identifiées.

Aucune donnée de ce module ne provient de GitHub. Chaque réponse expose
``is_demo=True`` et ``data_source="demo"``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.errors import NotFoundError
from app.integrations.github.types import (
    CheckRecord,
    IssueRecord,
    MergeResultRecord,
    PullRequestDetailRecord,
    PullRequestFileRecord,
    PullRequestRecord,
    PullRequestReviewRecord,
    RepositoryRecord,
    TimelineEventRecord,
)
from app.schemas.issue import IssueState
from app.schemas.pull_request import (
    CheckState,
    PullRequestState,
    ReviewDecision,
    ReviewState,
)

_REVIEWERS = ["alice.dupont", "benoit.l", "chloe.m", "david.k"]


def _now() -> datetime:
    return datetime.now(UTC)


class DemoProvider:
    """Fournisseur servant des données de démonstration déterministes."""

    name = "demo"
    is_demo = True
    requires_token = False

    def __init__(self) -> None:
        self._data: (
            tuple[
                list[RepositoryRecord],
                list[PullRequestRecord],
                list[IssueRecord],
            ]
            | None
        ) = None

    def _build(
        self,
    ) -> tuple[list[RepositoryRecord], list[PullRequestRecord], list[IssueRecord]]:
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

        issues = [
            IssueRecord(
                id="issue-web-201",
                number=201,
                repository_full_name="acme/web-app",
                title="Le lien de réinitialisation de mot de passe expire trop vite",
                author="lea.b",
                state=IssueState.OPEN,
                is_pull_request=False,
                created_at=now - 2 * day,
                updated_at=now - timedelta(hours=5),
                labels=["bug", "authentification"],
                assignees=["lea.b"],
                milestone="Sprint 12",
                html_url="https://github.com/acme/web-app/issues/201",
            ),
            IssueRecord(
                id="issue-web-198",
                number=198,
                repository_full_name="acme/web-app",
                title="Accessibilité : le contraste du menu est insuffisant",
                author="camille.m",
                state=IssueState.OPEN,
                is_pull_request=False,
                created_at=now - 4 * day,
                updated_at=now - day,
                labels=["accessibilité", "ui"],
                assignees=["camille.m"],
                milestone="Sprint 12",
                html_url="https://github.com/acme/web-app/issues/198",
            ),
            IssueRecord(
                id="issue-web-194",
                number=194,
                repository_full_name="acme/web-app",
                title="Le tableau de bord se recharge inutilement à chaque navigation",
                author="jules.r",
                state=IssueState.OPEN,
                is_pull_request=False,
                created_at=now - 6 * day,
                updated_at=now - 2 * day,
                labels=["performance"],
                html_url="https://github.com/acme/web-app/issues/194",
            ),
            IssueRecord(
                id="issue-web-180",
                number=180,
                repository_full_name="acme/web-app",
                title="Documenter les variables d'environnement du déploiement",
                author="sami.h",
                state=IssueState.CLOSED,
                is_pull_request=False,
                created_at=now - 12 * day,
                updated_at=now - 8 * day,
                labels=["documentation"],
                assignees=["sami.h"],
                html_url="https://github.com/acme/web-app/issues/180",
            ),
            IssueRecord(
                id="issue-api-53",
                number=53,
                repository_full_name="acme/api-gateway",
                title="Échecs intermittents sur le endpoint /metrics",
                author="sami.h",
                state=IssueState.OPEN,
                is_pull_request=False,
                created_at=now - 3 * day,
                updated_at=now - timedelta(hours=9),
                labels=["bug", "observabilité"],
                assignees=["sami.h"],
                milestone="Sprint 13",
                html_url="https://github.com/acme/api-gateway/issues/53",
            ),
            IssueRecord(
                id="issue-api-49",
                number=49,
                repository_full_name="acme/api-gateway",
                title="Prévoir un retry automatique pour les tokens expirés",
                author="camille.m",
                state=IssueState.OPEN,
                is_pull_request=False,
                created_at=now - 5 * day,
                updated_at=now - 2 * day,
                labels=["fiabilité"],
                assignees=["camille.m"],
                milestone="Sprint 13",
                html_url="https://github.com/acme/api-gateway/issues/49",
            ),
            IssueRecord(
                id="issue-api-38",
                number=38,
                repository_full_name="acme/api-gateway",
                title="Allonger le délai de rétention des journaux d'accès",
                author="lea.b",
                state=IssueState.CLOSED,
                is_pull_request=False,
                created_at=now - 15 * day,
                updated_at=now - 9 * day,
                html_url="https://github.com/acme/api-gateway/issues/38",
            ),
            IssueRecord(
                id="issue-sdk-18",
                number=18,
                repository_full_name="acme/client-sdk",
                title="Exposer un événement quand la connexion est perdue",
                author="jules.r",
                state=IssueState.OPEN,
                is_pull_request=False,
                created_at=now - 3 * day,
                updated_at=now - day,
                html_url="https://github.com/acme/client-sdk/issues/18",
            ),
            IssueRecord(
                id="issue-sdk-15",
                number=15,
                repository_full_name="acme/client-sdk",
                title="Réduire la taille du paquet npm du SDK",
                author="lea.b",
                state=IssueState.OPEN,
                is_pull_request=False,
                created_at=now - 7 * day,
                updated_at=now - 3 * day,
                html_url="https://github.com/acme/client-sdk/issues/15",
            ),
            IssueRecord(
                id="issue-sdk-9",
                number=9,
                repository_full_name="acme/client-sdk",
                title="Revue de la documentation TypeScript du SDK",
                author="camille.m",
                state=IssueState.CLOSED,
                is_pull_request=False,
                created_at=now - 20 * day,
                updated_at=now - 10 * day,
                html_url="https://github.com/acme/client-sdk/issues/9",
            ),
        ]

        return repos, prs, issues

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

    async def get_pull_request(
        self, repository_full_name: str, number: int
    ) -> PullRequestDetailRecord:
        self._ensure_built()
        assert self._data is not None
        pr = next(
            (
                item
                for item in self._data[1]
                if item.repository_full_name == repository_full_name and item.number == number
            ),
            None,
        )
        if pr is None:
            raise NotFoundError(
                f"Pull request #{number} introuvable pour {repository_full_name}.",
                code="pull_request_not_found",
                params={"number": number, "repository_full_name": repository_full_name},
            )
        return self._detail_from(pr)

    def _detail_from(self, pr: PullRequestRecord) -> PullRequestDetailRecord:
        """Construit une fiche détaillée déterministe à partir d'une PR."""
        reviewer = _REVIEWERS[pr.number % len(_REVIEWERS)]
        body = (
            f"## Contexte\n\nCette pull request ({pr.source_branch} → {pr.target_branch}) "
            f"a été ouverte par {pr.author}.\n\n"
            "> Données de démonstration : aucun contenu réel de GitHub n'est affiché."
        )
        return PullRequestDetailRecord(
            **pr.model_dump(),
            body=body,
            files=self._files_for(pr),
            reviews=self._reviews_for(pr, reviewer),
            timeline=self._timeline_for(pr, reviewer),
        )

    @staticmethod
    def _files_for(pr: PullRequestRecord) -> list[PullRequestFileRecord]:
        count = min(pr.changed_files, 8)
        if count <= 0:
            return []
        prefixes = ["src/", "tests/", "docs/", "frontend/src/"]
        files: list[PullRequestFileRecord] = []
        for index in range(count):
            additions = pr.additions // count + (1 if index < pr.additions % count else 0)
            deletions = pr.deletions // count + (1 if index < pr.deletions % count else 0)
            status = "added" if index == 0 else "modified"
            if index == count - 1 and pr.deletions > pr.additions:
                status = "removed"
            files.append(
                PullRequestFileRecord(
                    filename=f"{prefixes[index % len(prefixes)]}module_{index + 1}.py",
                    status=status,
                    additions=additions,
                    deletions=deletions,
                    changes=additions + deletions,
                )
            )
        return files

    @staticmethod
    def _reviews_for(pr: PullRequestRecord, reviewer: str) -> list[PullRequestReviewRecord]:
        submitted = pr.updated_at
        if pr.review_decision == ReviewDecision.APPROVED:
            state, body = ReviewState.APPROVED, "Tout me semble bon, merci !"
        elif pr.review_decision == ReviewDecision.CHANGES_REQUESTED:
            state, body = ReviewState.CHANGES_REQUESTED, "Il reste des points à corriger."
        elif pr.review_decision == ReviewDecision.REVIEW_REQUIRED:
            state, body = ReviewState.COMMENTED, "Quelques questions avant validation."
        else:
            return []
        return [
            PullRequestReviewRecord(
                id=f"review-{pr.number}",
                author=reviewer,
                state=state,
                body=body,
                submitted_at=submitted,
            )
        ]

    @staticmethod
    def _timeline_for(pr: PullRequestRecord, reviewer: str) -> list[TimelineEventRecord]:
        events = [
            TimelineEventRecord(
                id=f"tl-{pr.number}-opened",
                event_type="opened",
                actor=pr.author,
                message="a ouvert la pull request",
                created_at=pr.created_at,
            ),
            TimelineEventRecord(
                id=f"tl-{pr.number}-commit",
                event_type="committed",
                actor=pr.author,
                message="a poussé un commit",
                created_at=pr.created_at,
            ),
        ]
        if pr.review_decision != ReviewDecision.NONE:
            events.append(
                TimelineEventRecord(
                    id=f"tl-{pr.number}-reviewed",
                    event_type="reviewed",
                    actor=reviewer,
                    message="a déposé une revue",
                    created_at=pr.updated_at,
                )
            )
        if pr.state == PullRequestState.MERGED:
            events.append(
                TimelineEventRecord(
                    id=f"tl-{pr.number}-merged",
                    event_type="merged",
                    actor="mainteneur",
                    message="a fusionné la pull request",
                    created_at=pr.updated_at,
                )
            )
        return events

    async def list_issues(
        self,
        repository_full_name: str | None = None,
        state: str | None = None,
    ) -> list[IssueRecord]:
        self._ensure_built()
        assert self._data is not None
        issues = self._data[2]
        if repository_full_name is not None:
            issues = [
                issue for issue in issues if issue.repository_full_name == repository_full_name
            ]
        if state is not None:
            issues = [issue for issue in issues if issue.state.value == state]
        return issues

    async def merge_pull_request(
        self,
        repository_full_name: str,
        number: int,
        *,
        merge_method: str = "squash",
    ) -> MergeResultRecord:
        """Simule une fusion (mode démonstration).

        La pull request est marquée fusionnée en mémoire. Aucune donnée réelle
        n'est modifiée.
        """
        self._ensure_built()
        assert self._data is not None
        pr = next(
            (
                item
                for item in self._data[1]
                if item.repository_full_name == repository_full_name and item.number == number
            ),
            None,
        )
        if pr is None:
            raise NotFoundError(
                f"Pull request #{number} introuvable pour {repository_full_name}.",
                code="pull_request_not_found",
                params={"number": number, "repository_full_name": repository_full_name},
            )
        if pr.state != PullRequestState.OPEN:
            return MergeResultRecord(
                merged=False,
                message=f"Pull request #{number} non ouverte (état {pr.state.value}).",
            )
        pr.state = PullRequestState.MERGED
        return MergeResultRecord(
            merged=True,
            message=f"Pull request #{number} fusionnée ({merge_method}, démo).",
            sha=f"demo-merge-{pr.number}",
        )
