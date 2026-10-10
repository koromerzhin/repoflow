"""Tests du point de contrôle de santé."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.integrations.github import ratelimit
from app.integrations.github.factory import get_provider
from app.main import app


class _StubGithubProvider:
    name = "github"
    is_demo = False
    requires_token = True


def test_health_ok(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app"] == "RepoFlow"
    assert payload["environment"] == "test"
    assert payload["data_source"] == "demo"
    assert payload["database"] == "ok"
    assert payload["kill_switch_engaged"] is False
    assert payload["github_rate_limit"] is None


def test_health_expose_quota_github(client: TestClient) -> None:
    ratelimit.reset()
    ratelimit.update(remaining=4123, limit=5000, reset_at=1_700_000_000)
    app.dependency_overrides[get_provider] = lambda: _StubGithubProvider()
    try:
        payload = client.get("/api/health").json()
    finally:
        app.dependency_overrides.clear()
        ratelimit.reset()

    quota = payload["github_rate_limit"]
    assert quota is not None
    assert quota["remaining"] == 4123
    assert quota["limit"] == 5000
    assert quota["reset_at"] is not None


def test_health_does_not_leak_secrets(client: TestClient) -> None:
    response = client.get("/api/health")
    body = response.text.lower()
    assert "token" not in body
    assert "secret" not in body
