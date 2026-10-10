"""Tests du CRUD de configuration des dépôts et des règles."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create_repo(client: TestClient, full_name: str = "acme/web-app") -> dict:
    response = client.post(
        "/api/v1/configs/repositories",
        json={"full_name": full_name, "default_branch": "main"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_creation_et_liste(client: TestClient) -> None:
    created = _create_repo(client)
    assert created["full_name"] == "acme/web-app"
    assert created["owner"] == "acme"
    assert created["name"] == "web-app"
    assert created["enabled"] is True
    assert created["rules"] == []

    listing = client.get("/api/v1/configs/repositories")
    assert listing.status_code == 200
    payload = listing.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == created["id"]


def test_creation_doublon_refusee(client: TestClient) -> None:
    _create_repo(client)
    response = client.post(
        "/api/v1/configs/repositories",
        json={"full_name": "acme/web-app"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "repository_config_exists"


def test_creation_full_name_invalide(client: TestClient) -> None:
    response = client.post("/api/v1/configs/repositories", json={"full_name": "pas-valide"})
    assert response.status_code == 422


def test_mise_a_jour_et_suppression(client: TestClient) -> None:
    created = _create_repo(client)

    patched = client.patch(
        f"/api/v1/configs/repositories/{created['id']}",
        json={"enabled": False, "default_branch": "develop"},
    )
    assert patched.status_code == 200
    assert patched.json()["enabled"] is False
    assert patched.json()["default_branch"] == "develop"

    deleted = client.delete(f"/api/v1/configs/repositories/{created['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/configs/repositories/{created['id']}").status_code == 404


def test_introuvable(client: TestClient) -> None:
    assert client.get("/api/v1/configs/repositories/999").status_code == 404
    response = client.patch("/api/v1/configs/repositories/999", json={"enabled": True})
    assert response.status_code == 404


def test_creation_regle_et_liste(client: TestClient) -> None:
    repo = _create_repo(client)

    response = client.post(
        f"/api/v1/configs/repositories/{repo['id']}/rules",
        json={"name": "Fusion auto main", "branch_pattern": "main"},
    )
    assert response.status_code == 201, response.text
    rule = response.json()
    assert rule["auto_merge_enabled"] is False
    assert rule["required_approvals"] == 1
    assert rule["require_green_checks"] is True

    listed = client.get(f"/api/v1/configs/repositories/{repo['id']}/rules")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1


def test_mise_a_jour_regle(client: TestClient) -> None:
    repo = _create_repo(client)
    rule = client.post(
        f"/api/v1/configs/repositories/{repo['id']}/rules",
        json={"name": "Règle", "branch_pattern": "main"},
    ).json()

    patched = client.patch(
        f"/api/v1/configs/rules/{rule['id']}",
        json={"auto_merge_enabled": True, "required_approvals": 2},
    )
    assert patched.status_code == 200
    assert patched.json()["auto_merge_enabled"] is True
    assert patched.json()["required_approvals"] == 2


def test_suppression_regle(client: TestClient) -> None:
    repo = _create_repo(client)
    rule = client.post(
        f"/api/v1/configs/repositories/{repo['id']}/rules",
        json={"name": "Règle", "branch_pattern": "main"},
    ).json()

    assert client.delete(f"/api/v1/configs/rules/{rule['id']}").status_code == 204
    response = client.patch(f"/api/v1/configs/rules/{rule['id']}", json={"name": "x"})
    assert response.status_code == 404


def test_suppression_repo_supprime_regles(client: TestClient) -> None:
    repo = _create_repo(client)
    rule = client.post(
        f"/api/v1/configs/repositories/{repo['id']}/rules",
        json={"name": "Règle", "branch_pattern": "main"},
    ).json()

    assert client.delete(f"/api/v1/configs/repositories/{repo['id']}").status_code == 204
    response = client.patch(f"/api/v1/configs/rules/{rule['id']}", json={"name": "x"})
    assert response.status_code == 404


def test_regle_approbations_hors_bornes(client: TestClient) -> None:
    repo = _create_repo(client)
    response = client.post(
        f"/api/v1/configs/repositories/{repo['id']}/rules",
        json={"name": "Règle", "required_approvals": 99},
    )
    assert response.status_code == 422
