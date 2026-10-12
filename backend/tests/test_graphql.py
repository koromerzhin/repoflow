"""Tests du transport GraphQL (requête agrégée et conversions)."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from app.core.errors import ProviderError
from app.integrations.github.client import GitHubClient
from app.integrations.github.github_provider import GithubProvider
from app.integrations.github.graphql import (
    PULL_REQUESTS_QUERY,
    checks_from_commit,
    pull_request_rest,
    pull_requests_page,
    reviews_rest,
)
from app.integrations.github.mapping import (
    map_combined_checks,
    map_pull_request,
    map_review_decision,
)

_NODE: dict[str, Any] = {
    "id": "PR_kwDOG",
    "number": 142,
    "title": "Refonte du module de facturation",
    "isDraft": False,
    "mergeable": "MERGEABLE",
    "createdAt": "2026-01-01T08:00:00Z",
    "updatedAt": "2026-01-02T08:00:00Z",
    "url": "https://github.com/acme/web-app/pull/142",
    "author": {"login": "sam.r"},
    "headRefName": "feat/billing",
    "baseRefName": "main",
    "changedFiles": 3,
    "additions": 40,
    "deletions": 6,
    "commits": {
        "nodes": [
            {
                "commit": {
                    "statusCheckRollup": {
                        "contexts": {
                            "nodes": [
                                {
                                    "__typename": "CheckRun",
                                    "name": "ci/tests",
                                    "conclusion": "SUCCESS",
                                    "status": "COMPLETED",
                                    "detailsUrl": "https://example.com/run/1",
                                },
                                {
                                    "__typename": "StatusContext",
                                    "context": "deploy",
                                    "state": "PENDING",
                                    "targetUrl": "https://example.com/deploy",
                                },
                            ]
                        }
                    }
                }
            }
        ]
    },
    "reviews": {
        "nodes": [
            {
                "author": {"login": "lea.b"},
                "state": "APPROVED",
                "submittedAt": "2026-01-01T12:00:00Z",
                "body": "",
            }
        ]
    },
}


def test_pull_request_rest_conversions() -> None:
    rest = pull_request_rest(_NODE)

    assert rest["number"] == 142
    assert rest["user"] == {"login": "sam.r"}
    assert rest["draft"] is False
    assert rest["mergeable"] is True
    assert rest["changed_files"] == 3
    assert rest["head"] == {"ref": "feat/billing"}
    assert rest["html_url"].endswith("/pull/142")


def test_checks_from_commit_separe_check_runs_et_statuts() -> None:
    commit = _NODE["commits"]["nodes"][0]["commit"]
    check_runs, statuses = checks_from_commit(commit)

    assert check_runs == [
        {
            "name": "ci/tests",
            "status": "completed",
            "conclusion": "success",
            "details_url": "https://example.com/run/1",
        }
    ]
    assert statuses == [
        {"state": "pending", "context": "deploy", "target_url": "https://example.com/deploy"}
    ]

    records = map_combined_checks(check_runs, statuses)
    by_name = {record.name: record for record in records}
    assert by_name["ci/tests"].state.value == "success"
    assert by_name["deploy"].state.value == "pending"


def test_reviews_rest_conversions() -> None:
    reviews = reviews_rest(_NODE["reviews"]["nodes"])

    assert reviews[0]["state"] == "APPROVED"
    assert reviews[0]["user"] == {"login": "lea.b"}
    assert map_review_decision(reviews).value == "approved"


def test_pull_requests_page_extrait_items_et_curseur() -> None:
    data = {
        "repository": {
            "pullRequests": {
                "pageInfo": {"hasNextPage": True, "endCursor": "cur-1"},
                "nodes": [_NODE],
            }
        }
    }

    items, cursor = pull_requests_page(data)

    assert cursor == "cur-1"
    assert len(items) == 1
    assert items[0]["_reviews"] and items[0]["_check_runs"]


def test_pull_requests_page_derniere_page() -> None:
    data = {
        "repository": {
            "pullRequests": {
                "pageInfo": {"hasNextPage": False, "endCursor": "cur-9"},
                "nodes": [],
            }
        }
    }
    items, cursor = pull_requests_page(data)
    assert items == []
    assert cursor is None


def test_node_vers_record_complet() -> None:
    item = pull_request_rest(_NODE)
    check_runs, statuses = checks_from_commit(_NODE["commits"]["nodes"][0]["commit"])
    record = map_pull_request(
        item,
        "acme/web-app",
        map_combined_checks(check_runs, statuses),
        map_review_decision(reviews_rest(_NODE["reviews"]["nodes"])),
    )

    assert record.id == "PR_kwDOG"
    assert record.state.value == "open"
    assert record.is_draft is False
    assert record.mergeable is True
    assert record.review_decision.value == "approved"
    assert record.source_branch == "feat/billing"
    assert {check.name for check in record.checks} == {"ci/tests", "deploy"}


async def test_execute_graphql_renvoie_data() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).endswith("/graphql")
        return httpx.Response(200, json={"data": {"repository": {"pullRequests": {}}}})

    client = GitHubClient("t", "https://api.github.com", transport=httpx.MockTransport(handler))
    try:
        data = await client.execute_graphql(PULL_REQUESTS_QUERY, {"owner": "acme"})
    finally:
        await client.aclose()

    assert data == {"repository": {"pullRequests": {}}}


async def test_execute_graphql_erreur_leve_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errors": [{"message": "Field 'foo' doesn't exist"}]})

    client = GitHubClient("t", "https://api.github.com", transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ProviderError):
            await client.execute_graphql(PULL_REQUESTS_QUERY)
    finally:
        await client.aclose()


async def test_transport_graphql_passe_par_une_seule_requete_par_page() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url.path))
        return httpx.Response(
            200,
            json={
                "data": {
                    "repository": {
                        "pullRequests": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [_NODE],
                        }
                    }
                }
            },
        )

    async def token() -> str:
        return "ghs_x"

    provider = GithubProvider(
        client=GitHubClient(
            None,
            "https://api.github.com",
            transport=httpx.MockTransport(handler),
            token_provider=token,
        ),
        use_graphql=True,
    )
    try:
        records = await provider.list_pull_requests("acme/web-app")
    finally:
        await provider.aclose()

    assert calls == ["/graphql"]
    assert len(records) == 1
    assert records[0].number == 142


def test_issues_batch_query_alias_et_variables() -> None:
    from app.integrations.github.graphql import issues_batch_query

    query, variables = issues_batch_query(
        [("acme", "alpha"), ("acme", "beta")],
        {"acme/alpha": None, "acme/beta": "CUR1"},
        state="open",
    )

    assert "r0: repository(owner: $o0, name: $n0)" in query
    assert "r1: repository(owner: $o1, name: $n1)" in query
    assert "states: $states0" in query and "states: $states1" in query
    assert variables["o0"] == "acme" and variables["n0"] == "alpha"
    assert variables["a0"] is None and variables["a1"] == "CUR1"
    assert variables["states0"] == ["OPEN"]
    assert variables["first"] == 50


def test_issues_batch_query_sans_filtre_d_etat() -> None:
    from app.integrations.github.graphql import issues_batch_query

    query, variables = issues_batch_query([("acme", "alpha")], {"acme/alpha": None}, state=None)

    assert "states:" not in query
    assert "states0" not in variables


def test_issues_batch_page_parse_les_depots() -> None:
    from app.integrations.github.graphql import issue_rest, issues_batch_page

    node = {
        "id": "I_1",
        "number": 5,
        "title": "Bug ouvert",
        "body": "**Description**",
        "author": {"login": "dev"},
        "state": "OPEN",
        "createdAt": "2026-01-01T08:00:00Z",
        "updatedAt": "2026-01-02T08:00:00Z",
        "url": "https://github.com/acme/alpha/issues/5",
        "labels": {"nodes": [{"name": "bug"}]},
        "assignees": {"nodes": [{"login": "lea.b"}]},
        "milestone": {"title": "Sprint 1"},
    }
    rest = issue_rest(node)
    assert rest["user"] == {"login": "dev"}
    assert rest["labels"] == [{"name": "bug"}]
    assert rest["assignees"] == [{"login": "lea.b"}]
    assert rest["milestone"] == {"title": "Sprint 1"}
    assert rest["body"] == "**Description**"

    data = {
        "r0": {"issues": {"pageInfo": {"hasNextPage": True, "endCursor": "C1"}, "nodes": [node]}},
        "r1": None,
    }
    pages = issues_batch_page(data, [("acme", "alpha"), ("acme", "beta")])
    assert pages[0][0] == "acme/alpha"
    assert len(pages[0][1]) == 1
    assert pages[0][2] is True and pages[0][3] == "C1"
    assert pages[1] == ("acme/beta", [], False, None)


def test_timeline_rest_mappe_les_types_connus() -> None:
    from app.integrations.github.graphql import timeline_rest

    nodes = [
        {
            "__typename": "IssueComment",
            "id": "c1",
            "author": {"login": "lea.b"},
            "body": "Merci",
            "createdAt": "2026-01-01T10:00:00Z",
        },
        {
            "__typename": "PullRequestReview",
            "id": "r1",
            "author": {"login": "sam.r"},
            "state": "APPROVED",
            "submittedAt": "2026-01-01T11:00:00Z",
            "body": "LGTM",
        },
        {
            "__typename": "MergedEvent",
            "id": "m1",
            "actor": {"login": "bot"},
            "createdAt": "2026-01-01T12:00:00Z",
        },
        {
            "__typename": "LabeledEvent",
            "id": "l1",
            "actor": {"login": "bot"},
            "createdAt": "2026-01-01T12:30:00Z",
            "label": {"name": "dependencies"},
        },
        {
            "__typename": "PullRequestCommit",
            "id": "p1",
            "actor": {"login": "bot"},
            "createdAt": "2026-01-01T13:00:00Z",
            "commit": {"oid": "abc123def456"},
        },
        {"__typename": "MentionedEvent", "id": "x1", "createdAt": "2026-01-01T14:00:00Z"},
    ]
    events = timeline_rest(nodes)

    assert [event["event"] for event in events] == [
        "commented",
        "reviewed",
        "merged",
        "labeled",
        "committed",
    ]
    assert events[0]["body"] == "Merci"
    assert events[1]["state"] == "APPROVED" and events[1]["user"] == {"login": "sam.r"}
    assert events[3]["label"] == {"name": "dependencies"}
    assert events[4]["sha"] == "abc123def456"


def test_pull_request_detail_parts_decompose_le_noeud() -> None:
    from app.integrations.github.graphql import pull_request_detail_parts

    node = {
        "id": "PR_1",
        "number": 26,
        "title": "Bump release-it",
        "body": "## Contexte",
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "createdAt": "2026-01-01T08:00:00Z",
        "updatedAt": "2026-01-02T08:00:00Z",
        "url": "https://github.com/acme/alpha/pull/26",
        "author": {"login": "renovate"},
        "headRefName": "deps/x",
        "baseRefName": "main",
        "changedFiles": 2,
        "additions": 10,
        "deletions": 4,
        "commits": {
            "nodes": [
                {
                    "commit": {
                        "statusCheckRollup": {
                            "contexts": {
                                "nodes": [
                                    {
                                        "__typename": "CheckRun",
                                        "name": "build",
                                        "conclusion": "SUCCESS",
                                        "status": "COMPLETED",
                                        "detailsUrl": "https://ci/run/1",
                                    },
                                    {
                                        "__typename": "StatusContext",
                                        "context": "deploy",
                                        "state": "SUCCESS",
                                        "targetUrl": "https://ci/deploy",
                                    },
                                ]
                            }
                        }
                    }
                }
            ]
        },
        "reviews": {
            "nodes": [
                {
                    "id": "rv1",
                    "author": {"login": "lea.b"},
                    "state": "APPROVED",
                    "submittedAt": "2026-01-02T09:00:00Z",
                    "body": "RAS",
                }
            ]
        },
        "files": {"nodes": [{"path": "package.json", "additions": 2, "deletions": 2}]},
        "timelineItems": {
            "nodes": [
                {
                    "__typename": "IssueComment",
                    "id": "c1",
                    "author": {"login": "bot"},
                    "body": "Done",
                    "createdAt": "2026-01-01T10:00:00Z",
                },
            ]
        },
    }
    detail, check_runs, statuses, reviews, files, timeline = pull_request_detail_parts(node)

    assert detail["body"] == "## Contexte"
    assert detail["changed_files"] == 2
    assert [check["name"] for check in check_runs] == ["build"]
    assert [status["context"] for status in statuses] == ["deploy"]
    assert reviews[0]["state"] == "APPROVED"
    assert files[0]["filename"] == "package.json"
    assert timeline[0]["event"] == "commented"
