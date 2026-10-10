"""Tests de la route des pull requests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _get_prs(client: TestClient, **params: object) -> dict:
    response = client.get("/api/v1/pull-requests", params=params)
    assert response.status_code == 200
    return response.json()


def test_pull_requests_list(client: TestClient) -> None:
    payload = _get_prs(client)
    assert payload["data_source"] == "demo"
    assert payload["total"] == 7
    for item in payload["items"]:
        assert item["is_demo"] is True
        assert item["checks_state"] in {"success", "failure", "pending", "unknown"}
        assert "merge_eligibility" in item


def test_pull_requests_filter_by_repository(client: TestClient) -> None:
    payload = _get_prs(client, repository="acme/api-gateway")
    assert payload["total"] == 2
    assert all(item["repository_full_name"] == "acme/api-gateway" for item in payload["items"])


def test_failing_checks_are_reported_as_failure(client: TestClient) -> None:
    payload = _get_prs(client, repository="acme/client-sdk")
    pr = payload["items"][0]
    assert pr["checks_state"] == "failure"
    assert pr["merge_eligibility"]["eligible"] is False
    codes = {blocker["code"] for blocker in pr["merge_eligibility"]["blockers"]}
    assert "check_not_success" in codes


def test_draft_pull_request_is_not_mergeable(client: TestClient) -> None:
    payload = _get_prs(client, repository="acme/web-app")
    drafts = [item for item in payload["items"] if item["is_draft"]]
    assert drafts, "Une PR en brouillon est attendue dans les données de démonstration."
    codes = {
        blocker["code"] for draft in drafts for blocker in draft["merge_eligibility"]["blockers"]
    }
    assert "draft" in codes


def test_ready_pull_request_is_eligible(client: TestClient) -> None:
    payload = _get_prs(client, repository="acme/web-app")
    pr_142 = next(item for item in payload["items"] if item["number"] == 142)
    assert pr_142["merge_eligibility"]["eligible"] is True
    assert pr_142["checks_state"] == "success"


def test_unknown_check_is_not_treated_as_success(client: TestClient) -> None:
    payload = _get_prs(client, repository="acme/api-gateway")
    pr_77 = next(item for item in payload["items"] if item["number"] == 77)
    assert pr_77["checks_state"] == "unknown"
    assert pr_77["merge_eligibility"]["eligible"] is False
