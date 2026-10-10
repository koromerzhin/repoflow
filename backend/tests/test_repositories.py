"""Tests de la route des dépôts."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_repositories_list(client: TestClient) -> None:
    response = client.get("/api/v1/repositories")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data_source"] == "demo"
    assert payload["total"] == 3
    assert len(payload["items"]) == 3

    for item in payload["items"]:
        assert item["is_demo"] is True
        assert item["full_name"] == f"{item['owner']}/{item['name']}"
        assert item["open_issues_count"] >= 0


def test_repositories_limit(client: TestClient) -> None:
    response = client.get("/api/v1/repositories", params={"limit": 1})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["total"] == 3


def test_repositories_invalid_limit(client: TestClient) -> None:
    response = client.get("/api/v1/repositories", params={"limit": 0})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
