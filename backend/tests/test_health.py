"""Tests du point de contrôle de santé."""

from __future__ import annotations

from fastapi.testclient import TestClient


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


def test_health_does_not_leak_secrets(client: TestClient) -> None:
    response = client.get("/api/health")
    body = response.text.lower()
    assert "token" not in body
    assert "secret" not in body
