"""Interface abstraite des fournisseurs de données GitHub.

L'ensemble de l'application dépend de cette interface, jamais d'un
fournisseur concret. Cela permet de remplacer le fournisseur de
démonstration par une intégration GitHub réelle sans réécrire les couches
métier et API.
"""

from __future__ import annotations

from collections.abc import Awaitable, Iterable
from typing import Protocol

from app.integrations.github.types import PullRequestRecord, RepositoryRecord


class Provider(Protocol):
    """Contrat de tout fournisseur de données GitHub."""

    name: str
    is_demo: bool
    requires_token: bool

    async def list_repositories(self) -> Awaitable[list[RepositoryRecord]]: ...

    async def list_pull_requests(
        self, repository_full_name: str | None = None
    ) -> Awaitable[list[PullRequestRecord]]: ...


async def collect(provider: Provider) -> tuple[list[RepositoryRecord], list[PullRequestRecord]]:
    """Rassemble les dépôts et pull requests du fournisseur.

    Fonction utilitaire destinée aux services et aux tests. Le paramètre
    ``repository_full_name`` optionnel de ``list_pull_requests`` est propagé
    ici pour ne pas coupler les services à chaque signature.
    """
    repositories: Iterable[RepositoryRecord] = await provider.list_repositories()
    pull_requests: list[PullRequestRecord] = []
    for repository in repositories:
        pull_requests.extend(await provider.list_pull_requests(repository.full_name))
    return list(repositories), pull_requests
