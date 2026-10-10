"""Fabrique du fournisseur de données actif."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.core.errors import NotConfiguredError
from app.integrations.github.demo_provider import DemoProvider
from app.integrations.github.github_provider import GithubProvider
from app.integrations.github.provider import Provider


@lru_cache
def _provider_for(
    name: str,
    token: str | None,
    api_url: str,
    timeout: float,
    per_page: int,
    max_pages: int,
) -> Provider:
    """Construit et met en cache le fournisseur.

    La mise en cache s'appuie sur des arguments hachables car les instances
    ``Settings`` de Pydantic ne sont pas hachables.
    """
    if name == "demo":
        return DemoProvider()
    if name == "github":
        if not token:
            raise NotConfiguredError(
                "REPOFLOW_GITHUB_TOKEN doit être défini pour le fournisseur 'github'.",
                code="github_token_missing",
            )
        return GithubProvider(
            token=token,
            api_url=api_url,
            timeout=timeout,
            per_page=per_page,
            max_pages=max_pages,
        )
    raise NotConfiguredError(
        f"Fournisseur inconnu : {name!r}.",
        code="unknown_provider",
    )


def build_provider(settings: Settings) -> Provider:
    """Construit le fournisseur courant selon la configuration."""
    token = settings.github_token.get_secret_value() if settings.github_token else None
    return _provider_for(
        settings.github_provider,
        token,
        settings.github_api_url,
        settings.github_timeout,
        settings.github_per_page,
        settings.github_max_pages,
    )


def get_provider() -> Provider:
    """Retourne le fournisseur configuré (dépendance FastAPI)."""
    return build_provider(get_settings())
