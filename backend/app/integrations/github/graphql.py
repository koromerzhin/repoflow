"""Requête GraphQL agrégée et conversion vers les formes REST du mapping.

Une seule requête GraphQL par dépôt ramène les pull requests ouvertes avec
leurs checks CI et leurs revues, là où l'API REST nécessite 4-5 requêtes par
pull request. Les nœuds GraphQL sont convertis en dictionnaires au format
REST afin de réutiliser le mapping existant (``mapping.py``) tel quel.
"""

from __future__ import annotations

from typing import Any

PULL_REQUESTS_QUERY = """
query($owner: String!, $name: String!, $first: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(
        first: $first
        after: $after
        states: [OPEN]
        orderBy: {field: UPDATED_AT, direction: DESC}
    ) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        number
        title
        isDraft
        mergeable
        createdAt
        updatedAt
        url
        author { login }
        headRefName
        baseRefName
        files { changedFiles additions deletions }
        commits(last: 1) {
          nodes {
            commit {
              statusCheckRollup {
                contexts(first: 100) {
                  nodes {
                    __typename
                    ... on CheckRun { name conclusion status detailsUrl }
                    ... on StatusContext { name state targetUrl }
                  }
                }
              }
            }
          }
        }
        reviews(last: 100) {
          nodes { author { login } state submittedAt body }
        }
      }
    }
  }
}
"""


def pull_request_rest(node: dict[str, Any]) -> dict[str, Any]:
    """Convertit un nœud pull request GraphQL en dict au format REST."""
    author = node.get("author") or {}
    files = node.get("files") or {}
    return {
        "id": node.get("id"),
        "number": node.get("number"),
        "title": node.get("title"),
        "user": {"login": author.get("login")},
        "draft": node.get("isDraft"),
        "mergeable": node.get("mergeable") == "MERGEABLE",
        "changed_files": files.get("changedFiles"),
        "additions": files.get("additions"),
        "deletions": files.get("deletions"),
        "head": {"ref": node.get("headRefName")},
        "base": {"ref": node.get("baseRefName")},
        "created_at": node.get("createdAt"),
        "updated_at": node.get("updatedAt"),
        "html_url": node.get("url"),
    }


def checks_from_commit(
    commit: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Sépare le ``statusCheckRollup`` en check-runs et statuts au format REST."""
    rollup = (commit or {}).get("statusCheckRollup") or {}
    contexts = (rollup.get("contexts") or {}).get("nodes") or []
    check_runs: list[dict[str, Any]] = []
    statuses: list[dict[str, Any]] = []
    for context in contexts:
        typename = context.get("__typename")
        if typename == "CheckRun":
            conclusion = context.get("conclusion")
            check_runs.append(
                {
                    "name": context.get("name"),
                    "status": str(context.get("status") or "").lower(),
                    "conclusion": str(conclusion).lower() if conclusion else None,
                    "details_url": context.get("detailsUrl"),
                }
            )
        elif typename == "StatusContext":
            statuses.append(
                {
                    "state": str(context.get("state") or "").lower(),
                    "context": context.get("name"),
                    "target_url": context.get("targetUrl"),
                }
            )
    return check_runs, statuses


def reviews_rest(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convertit les nœuds reviews GraphQL en dicts au format REST."""
    return [
        {
            "state": review.get("state"),
            "user": {"login": (review.get("author") or {}).get("login")},
            "submitted_at": review.get("submittedAt"),
            "body": review.get("body"),
        }
        for review in nodes
    ]


def pull_requests_page(data: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    """Extrait la page courante et le curseur suivant depuis la réponse.

    Chaque élément converti embarque ``_check_runs``, ``_statuses`` et
    ``_reviews`` au format REST, prêts pour le mapping.
    """
    connection = (data.get("repository") or {}).get("pullRequests") or {}
    page_info = connection.get("pageInfo") or {}
    next_cursor = page_info.get("endCursor") if page_info.get("hasNextPage") else None
    items: list[dict[str, Any]] = []
    for node in connection.get("nodes") or []:
        rest = pull_request_rest(node)
        commits = (node.get("commits") or {}).get("nodes") or []
        commit = commits[0].get("commit") if commits else None
        check_runs, statuses = checks_from_commit(commit)
        rest["_check_runs"] = check_runs
        rest["_statuses"] = statuses
        rest["_reviews"] = reviews_rest((node.get("reviews") or {}).get("nodes") or [])
        items.append(rest)
    return items, next_cursor
