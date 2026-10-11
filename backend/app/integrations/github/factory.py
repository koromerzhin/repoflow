"""Fabrique du fournisseur de données actif."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.core.errors import NotConfiguredError
from app.integrations.github.app_auth import InstallationTokenProvider
from app.integrations.github.demo_provider import DemoProvider
from app.integrations.github.github_provider import GithubProvider
from app.integrations.github.provider import Provider


@lru_cache
def _provider_for(
    name: str,
    token: str | None,
    app_id: str | None,
    app_private_key: str | None,
    app_installation_id: int | None,
    use_graphql: bool,
    api_url: str,
    timeout: float,
    per_page: int,
    max_pages: int,
) -> Provider:
    """Construit et met en cache le fournisseur.

    La mise en cache s'appuie sur des arguments hachables car les instances
    ``Settings`` de Pydantic ne sont pas hachables. L'authentification GitHub
    App (jeton d'installation renouvelé) est prioritaire sur le token
    personnel.
    """
    if name == "demo":
        return DemoProvider()
    if name == "github":
        if app_id and app_private_key and app_installation_id:
            token_provider = InstallationTokenProvider(
                app_id,
                app_private_key,
                app_installation_id,
                api_url=api_url,
                timeout=timeout,
            )
            return GithubProvider(
                api_url=api_url,
                timeout=timeout,
                per_page=per_page,
                max_pages=max_pages,
                token_provider=token_provider,
                use_graphql=use_graphql,
            )
        if app_id or app_private_key or app_installation_id:
            raise NotConfiguredError(
                "GitHub App incomplète : REPOFLOW_GITHUB_APP_ID, "
                "REPOFLOW_GITHUB_APP_PRIVATE_KEY et "
                "REPOFLOW_GITHUB_APP_INSTALLATION_ID doivent être définis ensemble.",
                code="github_app_incomplete",
            )
        if not token:
            raise NotConfiguredError(
                "REPOFLOW_GITHUB_TOKEN ou les variables REPOFLOW_GITHUB_APP_* "
                "doivent être définis pour le fournisseur 'github'.",
                code="github_token_missing",
            )
        return GithubProvider(
            token=token,
            api_url=api_url,
            timeout=timeout,
            per_page=per_page,
            max_pages=max_pages,
            use_graphql=use_graphql,
        )
    raise NotConfiguredError(
        f"Fournisseur inconnu : {name!r}.",
        code="unknown_provider",
        params={"name": name},
    )


def build_provider(settings: Settings) -> Provider:
    """Construit le fournisseur courant selon la configuration."""
    token = settings.github_token.get_secret_value() if settings.github_token else None
    private_key = (
        settings.github_app_private_key.get_secret_value()
        if settings.github_app_private_key
        else None
    )
    return _provider_for(
        settings.github_provider,
        token,
        settings.github_app_id,
        private_key,
        settings.github_app_installation_id,
        settings.github_use_graphql,
        settings.github_api_url,
        settings.github_timeout,
        settings.github_per_page,
        settings.github_max_pages,
    )


def get_provider() -> Provider:
    """Retourne le fournisseur configuré (dépendance FastAPI)."""
    return build_provider(get_settings())
