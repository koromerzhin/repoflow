"""Tests du paramètre de rafraîchissement manuel ``refresh``."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_refresh_accepte_sur_les_listes(client: TestClient) -> None:
    paths = (
        "/api/v1/dashboard",
        "/api/v1/repositories",
        "/api/v1/pull-requests",
        "/api/v1/issues",
    )
    for path in paths:
        response = client.get(path, params={"refresh": "true"})
        assert response.status_code == 200, path


def test_refresh_sur_le_detail_pr(client: TestClient) -> None:
    response = client.get(
        "/api/v1/pull-requests/142",
        params={"repository": "acme/web-app", "refresh": "true"},
    )
    assert response.status_code == 200
    assert response.json()["number"] == 142


def test_refresh_invalide_rejete(client: TestClient) -> None:
    response = client.get("/api/v1/repositories", params={"refresh": "peut-être"})
    assert response.status_code == 422
