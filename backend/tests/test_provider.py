"""Tests de la fabrique de fournisseur et des erreurs."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.errors import NotConfiguredError
from app.integrations.github.demo_provider import DemoProvider
from app.integrations.github.factory import build_provider


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


def test_error_format(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/api/route-inexistante")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"
