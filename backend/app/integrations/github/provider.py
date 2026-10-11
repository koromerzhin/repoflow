"""Interface abstraite des fournisseurs de données GitHub.

L'ensemble de l'application dépend de cette interface, jamais d'un
fournisseur concret. Cela permet de remplacer le fournisseur de
démonstration par une intégration GitHub réelle sans réécrire les couches
métier et API.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from typing import Protocol

import httpx

from app.core.config import get_settings
from app.core.errors import ProviderError
from app.core.logging import get_logger
from app.integrations.github.types import (
    IssueRecord,
    MergeResultRecord,
    PullRequestDetailRecord,
    PullRequestRecord,
    RepositoryRecord,
)

logger = get_logger(__name__)


class Provider(Protocol):
    """Contrat de tout fournisseur de données GitHub."""

    name: str
    is_demo: bool
    requires_token: bool

    async def list_repositories(self) -> Awaitable[list[RepositoryRecord]]: ...

    async def list_pull_requests(
        self, repository_full_name: str | None = None
    ) -> Awaitable[list[PullRequestRecord]]: ...

    async def get_pull_request(
        self, repository_full_name: str, number: int
    ) -> Awaitable[PullRequestDetailRecord]: ...

    async def list_issues(
        self,
        repository_full_name: str | None = None,
        state: str | None = None,
    ) -> Awaitable[list[IssueRecord]]: ...

    async def merge_pull_request(
        self,
        repository_full_name: str,
        number: int,
        *,
        merge_method: str = "squash",
    ) -> Awaitable[MergeResultRecord]: ...


async def collect(provider: Provider) -> tuple[list[RepositoryRecord], list[PullRequestRecord]]:
    """Rassemble les dépôts et pull requests du fournisseur.

    Les dépôts sont interrogés en parallèle, avec une concurrence bornée
    (``REPOFLOW_GITHUB_MAX_CONCURRENCY``) et un budget de temps par dépôt
    (``REPOFLOW_GITHUB_COLLECTION_TIMEOUT``). Un dépôt lent ou en erreur est
    ignoré (ses PR sont omises) plutôt que de faire échouer toute la requête :
    l'agrégat reste exploitable même quand l'API GitHub est partiellement
    indisponible.
    """
    settings = get_settings()
    repositories = list(await provider.list_repositories())
    if not repositories:
        return repositories, []

    semaphore = asyncio.Semaphore(settings.github_max_concurrency)
    timeout = settings.github_collection_timeout

    async def fetch(repository: RepositoryRecord) -> list[PullRequestRecord]:
        async with semaphore:
            try:
                return await asyncio.wait_for(
                    provider.list_pull_requests(repository.full_name), timeout=timeout
                )
            except TimeoutError:
                logger.warning(
                    "Délai dépassé pour la récupération des PR de %s (%.1f s) ; dépôt ignoré.",
                    repository.full_name,
                    timeout,
                )
                return []
            except ProviderError:
                # Erreurs applicatives (limite de requêtes, authentification,
                # permissions) : elles concernent tout le fournisseur et doivent
                # remonter au client, jamais être masquées.
                raise
            except httpx.HTTPError as exc:
                logger.warning(
                    "Échec réseau pour la récupération des PR de %s : %s",
                    repository.full_name,
                    exc,
                )
                return []

    results = await asyncio.gather(*(fetch(repository) for repository in repositories))
    pull_requests = [item for group in results for item in group]
    return repositories, pull_requests
