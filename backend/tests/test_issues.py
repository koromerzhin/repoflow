"""Tests de la route des issues."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _get_issues(client: TestClient, **params: object) -> dict:
    response = client.get("/api/v1/issues", params=params)
    assert response.status_code == 200
    return response.json()


def test_issues_open_par_defaut(client: TestClient) -> None:
    payload = _get_issues(client)
    assert payload["data_source"] == "demo"
    assert payload["total"] == 7
    assert all(item["state"] == "open" for item in payload["items"])
    assert all(item["is_demo"] is True for item in payload["items"])
    assert all(item["is_pull_request"] is False for item in payload["items"])


def test_issues_filter_par_repository(client: TestClient) -> None:
    payload = _get_issues(client, repository="acme/web-app")
    assert payload["total"] == 3
    assert all(item["repository_full_name"] == "acme/web-app" for item in payload["items"])


def test_issues_toutes_etats(client: TestClient) -> None:
    payload = _get_issues(client, state="all")
    assert payload["total"] == 10
    assert {item["state"] for item in payload["items"]} == {"open", "closed"}


def test_issues_filter_par_etat_ferme(client: TestClient) -> None:
    payload = _get_issues(client, state="closed", repository="acme/client-sdk")
    assert payload["total"] == 1
    item = payload["items"][0]
    assert item["state"] == "closed"
    assert item["repository_full_name"] == "acme/client-sdk"
    assert item["title"]


def test_issues_limit(client: TestClient) -> None:
    payload = _get_issues(client, limit=2)
    assert payload["total"] == 7
    assert len(payload["items"]) == 2


def test_issues_etat_invalide(client: TestClient) -> None:
    response = client.get("/api/v1/issues", params={"state": "bogus"})
    assert response.status_code == 422
