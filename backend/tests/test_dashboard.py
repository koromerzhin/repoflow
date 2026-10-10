"""Tests de la route du tableau de bord."""

from __future__ import annotations

from fastapi.testclient import TestClient


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


def test_dashboard_recent_activity_sorted(client: TestClient) -> None:
    response = client.get("/api/v1/dashboard")
    activity = response.json()["recent_activity"]
    timestamps = [item["occurred_at"] for item in activity]
    assert timestamps == sorted(timestamps, reverse=True)
