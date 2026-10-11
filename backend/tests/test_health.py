"""Tests du point de contrôle de santé."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.integrations.github import ratelimit
from app.integrations.github.factory import get_provider
from app.main import app
from app.schemas.health import DatabaseStatus


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


def test_liveness_repond_toujours(client: TestClient) -> None:
    response = client.get("/api/health/live")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["timestamp"]


def test_readiness_ok(client: TestClient) -> None:
    response = client.get("/api/health/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "ok"
    assert payload["cache"] == "memory"
    assert payload["provider"] == "demo"


def test_readiness_ko_si_base_indisponible(client: TestClient, monkeypatch) -> None:
    from app.api.v1.routes import health as health_module

    monkeypatch.setattr(health_module, "_database_status", lambda: DatabaseStatus.UNAVAILABLE)
    response = client.get("/api/health/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["database"] == "unavailable"


async def test_cache_status_redis_indisponible(monkeypatch) -> None:
    from app.api.v1.routes import health as health_module
    from app.core.config import Settings

    async def _boom():
        raise RuntimeError("redis down")

    monkeypatch.setattr(health_module, "get_redis_client", _boom)
    settings = Settings(cache_backend="redis")
    assert await health_module._cache_status(settings) == "unavailable"
