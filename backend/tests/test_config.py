"""Tests de la configuration applicative."""

from __future__ import annotations

import pytest

from app.core.config import Settings


def test_cors_origins_accepte_une_liste_sans_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REPOFLOW_CORS_ORIGINS", "http://a.test,http://b.test")
    settings = Settings()
    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_cors_origins_par_defaut() -> None:
    settings = Settings()
    assert "http://localhost:5173" in settings.cors_origins


def test_configuration_initie_sans_secret() -> None:
    settings = Settings(github_provider="demo")
    assert settings.github_token is None
    assert settings.auto_merge_enabled_globally is False
    assert settings.kill_switch_engaged is False


def test_variables_github_app_vides_signifient_non_configurees(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REPOFLOW_GITHUB_APP_ID", "")
    monkeypatch.setenv("REPOFLOW_GITHUB_APP_PRIVATE_KEY", "")
    monkeypatch.setenv("REPOFLOW_GITHUB_APP_INSTALLATION_ID", "")

    settings = Settings()

    assert settings.github_app_id is None
    assert settings.github_app_private_key is None
    assert settings.github_app_installation_id is None
