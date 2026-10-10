"""Tests de la route du détail d'une pull request."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_pull_request_detail(client: TestClient) -> None:
    response = client.get("/api/v1/pull-requests/142", params={"repository": "acme/web-app"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["number"] == 142
    assert payload["repository_full_name"] == "acme/web-app"
    assert payload["is_demo"] is True
    assert payload["body"]
    assert payload["files"]
    assert payload["reviews"]
    assert payload["timeline"]
    file_item = payload["files"][0]
    assert {"filename", "status", "additions", "deletions", "changes"} <= set(file_item)


def test_pull_request_detail_inconnue(client: TestClient) -> None:
    response = client.get("/api/v1/pull-requests/999999", params={"repository": "acme/web-app"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "pull_request_not_found"


def test_pull_request_detail_repository_requis(client: TestClient) -> None:
    response = client.get("/api/v1/pull-requests/142")
    assert response.status_code == 422


def test_pull_request_detail_numero_invalide(client: TestClient) -> None:
    response = client.get("/api/v1/pull-requests/0", params={"repository": "acme/web-app"})
    assert response.status_code == 422


def test_pull_request_detail_approuvee_a_une_revue(client: TestClient) -> None:
    response = client.get("/api/v1/pull-requests/142", params={"repository": "acme/web-app"})
    payload = response.json()
    assert payload["review_decision"] == "approved"
    assert payload["reviews"][0]["state"] == "approved"
    assert payload["merge_eligibility"]["eligible"] is True
