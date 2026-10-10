"""Tests de la route du journal d'audit."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.services import audit_service


@pytest.fixture
def session() -> Iterator[Session]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def _seed(session: Session) -> None:
    audit_service.record(
        session,
        event_type="merge_succeeded",
        message="PR #142 fusionnée",
        repository_full_name="acme/web-app",
        pull_request_number=142,
        payload={"sha": "abc"},
    )
    audit_service.record(
        session,
        event_type="merge_blocked",
        message="PR #138 non éligible",
        repository_full_name="acme/api-gateway",
        pull_request_number=138,
    )
    session.commit()


def test_liste_vide(client: TestClient) -> None:
    response = client.get("/api/v1/audit")
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_liste_et_ordre(client: TestClient, session: Session) -> None:
    _seed(session)

    response = client.get("/api/v1/audit")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert len(payload["items"]) == 2
    first = payload["items"][0]
    assert first["event_type"] == "merge_blocked"
    assert first["repository_full_name"] == "acme/api-gateway"
    assert first["actor"] == "system"


def test_filtre_par_type(client: TestClient, session: Session) -> None:
    _seed(session)

    payload = client.get("/api/v1/audit", params={"event_type": "merge_succeeded"}).json()
    assert payload["total"] == 1
    assert payload["items"][0]["payload"] == {"sha": "abc"}


def test_filtre_par_depot(client: TestClient, session: Session) -> None:
    _seed(session)

    payload = client.get("/api/v1/audit", params={"repository": "acme/web-app"}).json()
    assert payload["total"] == 1
    assert payload["items"][0]["pull_request_number"] == 142


def test_limite_invalide(client: TestClient) -> None:
    assert client.get("/api/v1/audit", params={"limit": 0}).status_code == 422
