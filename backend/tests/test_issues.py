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


def test_issues_exposent_labels_assignes_jalon(client: TestClient) -> None:
    payload = _get_issues(client, search="réinitialisation")
    assert payload["total"] == 1
    item = payload["items"][0]
    assert item["labels"] == ["bug", "authentification"]
    assert item["assignees"] == ["lea.b"]
    assert item["milestone"] == "Sprint 12"


def test_issues_exposent_le_corps_markdown(client: TestClient) -> None:
    payload = _get_issues(client)
    items = payload["items"]
    assert items, "la démonstration doit exposer des issues"
    for item in items:
        assert item["body"] is not None
        assert "Données de démonstration" in item["body"]
        # Le corps est du Markdown structuré (titres, listes ou tableaux).
        assert any(marker in item["body"] for marker in ("##", "- [", "| -", "**"))


def test_issues_recherche_serveur_par_label(client: TestClient) -> None:
    payload = _get_issues(client, search="observabilité")
    assert payload["total"] == 1
    assert payload["items"][0]["number"] == 53


def test_issues_recherche_serveur_sans_accent(client: TestClient) -> None:
    payload = _get_issues(client, search="reinitialisation")
    assert payload["total"] == 1
    assert payload["items"][0]["number"] == 201


def test_issues_recherche_sans_resultat(client: TestClient) -> None:
    payload = _get_issues(client, search="inexistant")
    assert payload["total"] == 0
    assert payload["items"] == []


def test_issues_pagination_offset_cursor(client: TestClient) -> None:
    first = _get_issues(client, limit=3, offset=0)
    assert len(first["items"]) == 3
    assert first["total"] == 7
    assert first["next_cursor"] == 3

    second = _get_issues(client, limit=3, offset=first["next_cursor"])
    assert len(second["items"]) == 3
    assert second["next_cursor"] == 6

    third = _get_issues(client, limit=3, offset=second["next_cursor"])
    assert len(third["items"]) == 1
    assert third["next_cursor"] is None

    seen = [item["id"] for page in (first, second, third) for item in page["items"]]
    assert len(seen) == len(set(seen)) == 7


def test_issues_pagination_avec_filtre_depot(client: TestClient) -> None:
    payload = _get_issues(client, repository="acme/api-gateway", limit=1, offset=0)
    assert payload["total"] == 2
    assert payload["items"][0]["repository_full_name"] == "acme/api-gateway"
    assert payload["next_cursor"] == 1
