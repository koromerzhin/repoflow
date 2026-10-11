"""Tests de la fabrique de fournisseur et des erreurs."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.errors import NotConfiguredError
from app.integrations.github.demo_provider import DemoProvider
from app.integrations.github.factory import build_provider
from app.integrations.github.github_provider import GithubProvider


def test_build_demo_provider() -> None:
    settings = Settings(github_provider="demo")
    provider = build_provider(settings)
    assert isinstance(provider, DemoProvider)
    assert provider.is_demo is True
    assert provider.requires_token is False


def test_build_github_provider_without_token_raises() -> None:
    settings = Settings(github_provider="github", github_token=None)
    with pytest.raises(NotConfiguredError):
        build_provider(settings)


def test_build_github_provider_with_app() -> None:
    settings = Settings(
        github_provider="github",
        github_app_id="123456",
        github_app_private_key="-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
        github_app_installation_id=789,
    )
    provider = build_provider(settings)
    assert isinstance(provider, GithubProvider)
    assert provider.name == "github"
    assert provider._client._token_provider is not None


def test_build_github_provider_app_incomplete_raises() -> None:
    settings = Settings(
        github_provider="github",
        github_app_id="123456",
        github_app_installation_id=789,
        github_app_private_key=None,
    )
    with pytest.raises(NotConfiguredError) as excinfo:
        build_provider(settings)
    assert excinfo.value.code == "github_app_incomplete"


def test_build_github_provider_prefers_app_over_token() -> None:
    settings = Settings(
        github_provider="github",
        github_token="ghp_pat",
        github_app_id="123456",
        github_app_private_key="-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
        github_app_installation_id=789,
    )
    provider = build_provider(settings)
    assert isinstance(provider, GithubProvider)
    # Aucun token statique : l'authentification passe par le jeton d'installation.
    assert "Authorization" not in provider._client._client.headers


def test_build_github_provider_transport_graphql() -> None:
    settings = Settings(
        github_provider="github",
        github_token="ghp_pat",
        github_use_graphql=True,
    )
    provider = build_provider(settings)
    assert isinstance(provider, GithubProvider)
    assert provider._use_graphql is True


def test_build_github_provider_transport_rest_par_defaut() -> None:
    settings = Settings(github_provider="github", github_token="ghp_pat")
    provider = build_provider(settings)
    assert isinstance(provider, GithubProvider)
    assert provider._use_graphql is False


def test_error_format(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/api/route-inexistante")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"
