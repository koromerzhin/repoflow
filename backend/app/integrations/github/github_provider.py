"""Fournisseur GitHub réel (non implémenté dans cette version).

Ce module définit l'emplacement de l'intégration GitHub réelle : prise en
charge de l'authentification (token côté serveur), pagination, gestion des
limites de requêtes (rate limits) et des erreurs API. Il ne doit jamais
recevoir de token en provenance du frontend.
"""

from __future__ import annotations

from app.core.errors import NotConfiguredError
from app.integrations.github.types import PullRequestRecord, RepositoryRecord


class GithubProvider:
    """Emplacement réservé de l'intégration GitHub réelle."""

    name = "github"
    is_demo = False
    requires_token = True

    def __init__(self, token: str) -> None:
        # Stockage uniquement en mémoire, jamais dans les journaux ni les URL.
        self._token = token

    async def list_repositories(self) -> list[RepositoryRecord]:
        raise NotConfiguredError(
            "L'intégration GitHub réelle n'est pas encore disponible. "
            "Utilisez REPOFLOW_GITHUB_PROVIDER=demo pour le mode démonstration.",
            code="github_provider_pending",
        )

    async def list_pull_requests(
        self, repository_full_name: str | None = None
    ) -> list[PullRequestRecord]:
        raise NotConfiguredError(
            "L'intégration GitHub réelle n'est pas encore disponible. "
            "Utilisez REPOFLOW_GITHUB_PROVIDER=demo pour le mode démonstration.",
            code="github_provider_pending",
        )
