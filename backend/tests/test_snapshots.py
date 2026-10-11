"""Tests de l'historisation quotidienne (snapshots) et de sa route."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.integrations.github.factory import build_provider
from app.services import snapshot_service


def _session() -> Session:
    return get_session_factory()()


def _record(provider_name: str = "demo") -> int:
    provider = build_provider(get_settings())
    session = _session()
    try:
        return asyncio.run(snapshot_service.record_daily_snapshot(session, provider))
    finally:
        session.close()


def test_route_vide(client: TestClient) -> None:
    response = client.get("/api/v1/snapshots")
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "data_source": "demo"}


def test_snapshot_par_depot_et_idempotence(client: TestClient) -> None:
    covered = _record()
    assert covered == 3  # trois dépôts en mode démo

    first = client.get("/api/v1/snapshots").json()
    assert first["total"] == 3
    assert all(item["data_source"] == "demo" for item in first["items"])
    assert all(
        item["snapshot_date"] == datetime.now(UTC).date().isoformat() for item in first["items"]
    )

    # Une seconde passe le même jour met à jour, jamais dupliquée.
    _record()
    second = client.get("/api/v1/snapshots").json()
    assert second["total"] == 3
    assert {item["id"] for item in first["items"]} == {item["id"] for item in second["items"]}


def test_agregats_coherents_avec_le_fournisseur(client: TestClient) -> None:
    _record()

    snapshots = client.get("/api/v1/snapshots").json()["items"]
    total_open_prs = sum(item["open_pull_requests"] for item in snapshots)
    assert total_open_prs == 5  # la démo expose 5 PR « open » (1 draft, 1 merged)
    assert all(item["open_pull_requests"] >= 0 for item in snapshots)
    assert all(item["open_issues"] >= 0 for item in snapshots)


def test_filtre_par_depot(client: TestClient) -> None:
    _record()

    payload = client.get("/api/v1/snapshots", params={"repository": "acme/web-app"}).json()
    assert payload["total"] == 1
    assert payload["items"][0]["repository_full_name"] == "acme/web-app"


def test_filtre_since_exclusif(client: TestClient) -> None:
    _record()

    futur = (datetime.now(UTC).date() + timedelta(days=1)).isoformat()
    payload = client.get("/api/v1/snapshots", params={"since": futur}).json()
    assert payload["total"] == 0

    aujourdhui = datetime.now(UTC).date().isoformat()
    payload = client.get("/api/v1/snapshots", params={"since": aujourdhui}).json()
    assert payload["total"] == 3


def test_mise_a_jour_des_compteurs_le_meme_jour(client: TestClient) -> None:
    _record()
    snapshots = client.get("/api/v1/snapshots", params={"repository": "acme/web-app"}).json()
    initial = snapshots["items"][0]

    session = _session()
    try:
        stored = snapshot_service.list_snapshots(session, repository_full_name="acme/web-app")
        assert len(stored) == 1
        assert stored[0].snapshot_date == datetime.now(UTC).date()
        assert stored[0].open_pull_requests == initial["open_pull_requests"]
    finally:
        session.close()


def test_limit(client: TestClient) -> None:
    _record()

    payload = client.get("/api/v1/snapshots", params={"limit": 2}).json()
    assert len(payload["items"]) == 2
    assert payload["total"] == 2


def test_limit_invalide(client: TestClient) -> None:
    assert client.get("/api/v1/snapshots", params={"limit": 0}).status_code == 422
