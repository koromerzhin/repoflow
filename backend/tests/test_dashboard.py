"""Tests de la route du tableau de bord."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.integrations.github.types import RepositoryRecord
from app.services.dashboard_service import _counters


def _repo(full_name: str, *, archived: bool, issues: int) -> RepositoryRecord:
    owner, name = full_name.split("/", 1)
    return RepositoryRecord(
        id=f"repo-{name}",
        owner=owner,
        name=name,
        full_name=full_name,
        default_branch="main",
        private=False,
        archived=archived,
        open_issues_count=issues,
        open_pull_requests_count=0,
        updated_at=datetime.now(UTC),
        html_url=f"https://example.test/{full_name}",
    )


def test_compteur_issues_ignore_les_depots_archives() -> None:
    counters = _counters(
        [
            _repo("acme/actif", archived=False, issues=3),
            _repo("acme/archive", archived=True, issues=10),
        ],
        [],
    )
    assert counters.repositories == 2
    assert counters.open_issues == 3


def test_dashboard_structure(client: TestClient) -> None:
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    payload = response.json()

    assert payload["data_source"] == "demo"
    assert payload["provider"] == {"name": "demo", "is_demo": True, "requires_token": False}

    counters = payload["counters"]
    assert counters["repositories"] == 3
    # Une pull request est en brouillon : seules les autres sont « ouvertes ».
    assert counters["open_pull_requests"] == 5
    assert counters["open_issues"] == 23
    assert counters["pull_requests_with_failing_checks"] >= 1
    assert counters["pull_requests_pending_checks"] >= 1

    assert len(payload["recent_activity"]) > 0
    first = payload["recent_activity"][0]
    assert first["repository_full_name"]
    assert first["occurred_at"]
    # Chaque activité référence sa PR : le client peut lier vers son détail.
    assert isinstance(first["pull_request_number"], int)
    assert first["pull_request_number"] >= 1


def test_dashboard_recent_activity_sorted(client: TestClient) -> None:
    response = client.get("/api/v1/dashboard")
    activity = response.json()["recent_activity"]
    timestamps = [item["occurred_at"] for item in activity]
    assert timestamps == sorted(timestamps, reverse=True)
