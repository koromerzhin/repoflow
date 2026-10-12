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
        changedFiles
        additions
        deletions
        commits(last: 1) {
          nodes {
            commit {
              statusCheckRollup {
                contexts(first: 100) {
                  nodes {
                    __typename
                    ... on CheckRun { name conclusion status detailsUrl }
                    ... on StatusContext { context state targetUrl }
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
    return {
        "id": node.get("id"),
        "number": node.get("number"),
        "title": node.get("title"),
        "user": {"login": author.get("login")},
        "draft": node.get("isDraft"),
        "mergeable": node.get("mergeable") == "MERGEABLE",
        "changed_files": node.get("changedFiles"),
        "additions": node.get("additions"),
        "deletions": node.get("deletions"),
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
                    "context": context.get("context"),
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


# ---------------------------------------------------------------------------
# Issues : interrogation par lots de dépôts (alias GraphQL).
#
# Contrairement à REST, la connexion GraphQL ``issues`` n'inclut jamais les
# pull requests : aucun filtrage ``is_pull_request`` n'est nécessaire. Un seul
# document regroupe plusieurs dépôts via des alias (``r0``, ``r1``…), ce qui
# remplace une requête REST par dépôt par une requête par lot.
# ---------------------------------------------------------------------------

#: Dépôts interrogés par document GraphQL.
ISSUES_BATCH_CHUNK = 10
#: Issues demandées par page et par dépôt.
ISSUES_PAGE_SIZE = 50

_ISSUES_NODE_FIELDS = """{
  id number title body
  author { login }
  state createdAt updatedAt url
  labels(first: 20) { nodes { name } }
  assignees(first: 10) { nodes { login } }
  milestone { title }
}"""


def issues_batch_query(
    entries: list[tuple[str, str]],
    cursors: dict[str, str | None],
    *,
    state: str | None,
    first: int = ISSUES_PAGE_SIZE,
) -> tuple[str, dict[str, Any]]:
    """Construit un document interrogeant plusieurs dépôts en alias.

    ``entries`` liste les couples ``(owner, name)`` ; ``cursors`` donne le
    curseur de pagination courant par nom complet (``None`` pour la première
    page). Renvoie le texte de la requête et les variables associées.
    """
    parts: list[str] = []
    variables: dict[str, Any] = {}
    declarations = ["$first: Int!"]
    for index, (owner, name) in enumerate(entries):
        states_clause = ""
        if state in ("open", "closed"):
            variables[f"states{index}"] = [state.upper()]
            declarations.append(f"$states{index}: [IssueState!]")
            states_clause = f", states: $states{index}"
        variables[f"o{index}"] = owner
        variables[f"n{index}"] = name
        variables[f"a{index}"] = cursors.get(f"{owner}/{name}")
        declarations.append(f"$o{index}: String!")
        declarations.append(f"$n{index}: String!")
        declarations.append(f"$a{index}: String")
        parts.append(
            f"r{index}: repository(owner: $o{index}, name: $n{index}) {{"
            f" issues(first: $first{states_clause}, after: $a{index},"
            f" orderBy: {{field: UPDATED_AT, direction: DESC}}) {{"
            f" pageInfo {{ hasNextPage endCursor }}"
            f" nodes {_ISSUES_NODE_FIELDS} }} }}"
        )
    variables["first"] = first
    query = "query(" + ", ".join(declarations) + ") { " + " ".join(parts) + " }"
    return query, variables


def issue_rest(node: dict[str, Any]) -> dict[str, Any]:
    """Convertit un nœud issue GraphQL en dict au format REST."""
    author = node.get("author") or {}
    labels = [(label or {}).get("name") for label in (node.get("labels") or {}).get("nodes") or []]
    assignees = [
        (assignee or {}).get("login")
        for assignee in (node.get("assignees") or {}).get("nodes") or []
    ]
    milestone = node.get("milestone") or {}
    return {
        "id": node.get("id"),
        "number": node.get("number"),
        "title": node.get("title"),
        "body": node.get("body"),
        "user": {"login": author.get("login")},
        "state": node.get("state"),
        "labels": [{"name": label} for label in labels if label],
        "assignees": [{"login": login} for login in assignees if login],
        "milestone": {"title": milestone.get("title")} if milestone else None,
        "created_at": node.get("createdAt"),
        "updated_at": node.get("updatedAt"),
        "html_url": node.get("url"),
    }


def issues_batch_page(
    data: dict[str, Any], entries: list[tuple[str, str]]
) -> list[tuple[str, list[dict[str, Any]], bool, str | None]]:
    """Extrait, dans l'ordre des entrées, la page d'issues de chaque dépôt.

    Renvoie une liste de ``(nom_complet, éléments REST, page_suivante,
    curseur)`` ; un dépôt absent de la réponse (supprimé entre-temps) donne
    une page vide.
    """
    pages: list[tuple[str, list[dict[str, Any]], bool, str | None]] = []
    for index, (owner, name) in enumerate(entries):
        repository = data.get(f"r{index}") or {}
        connection = repository.get("issues") or {}
        page_info = connection.get("pageInfo") or {}
        items = [issue_rest(node) for node in connection.get("nodes") or []]
        has_next = bool(page_info.get("hasNextPage"))
        cursor = page_info.get("endCursor") if has_next else None
        pages.append((f"{owner}/{name}", items, has_next, cursor))
    return pages


# ---------------------------------------------------------------------------
# Détail d'une pull request : un seul document GraphQL remplace les 5-6
# requêtes REST (détail, check-runs, statut combiné, revues, fichiers,
# chronologie).
# ---------------------------------------------------------------------------

PULL_REQUEST_DETAIL_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      id number title body isDraft mergeable createdAt updatedAt url
      author { login }
      headRefName baseRefName changedFiles additions deletions
      commits(last: 1) {
        nodes {
          commit {
            statusCheckRollup {
              contexts(first: 100) {
                nodes {
                  __typename
                  ... on CheckRun { name conclusion status detailsUrl }
                  ... on StatusContext { context state targetUrl }
                }
              }
            }
          }
        }
      }
      reviews(last: 100) { nodes { id author { login } state submittedAt body } }
      files(first: 100) { nodes { path additions deletions } }
      timelineItems(first: 100) {
        nodes {
          __typename
          ... on IssueComment { id author { login } body createdAt }
          ... on PullRequestReview { id author { login } state submittedAt body }
          ... on ClosedEvent { id actor { login } createdAt }
          ... on ReopenedEvent { id actor { login } createdAt }
          ... on MergedEvent { id actor { login } createdAt }
          ... on LabeledEvent { id actor { login } createdAt label { name } }
          ... on UnlabeledEvent { id actor { login } createdAt label { name } }
          ... on HeadRefForcePushedEvent { id actor { login } createdAt }
          ... on RenamedTitleEvent { id actor { login } createdAt currentTitle }
          ... on PullRequestCommit { id commit { oid } }
        }
      }
    }
  }
}
"""


def timeline_rest(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convertit les nœuds ``timelineItems`` GraphQL au format REST.

    Seuls les types portés par la requête sont convertis ; les autres
    (mentions, références croisées…) sont ignorés.
    """
    events: list[dict[str, Any]] = []
    for node in nodes:
        typename = node.get("__typename")
        actor = {"login": (node.get("actor") or node.get("author") or {}).get("login") or ""}
        created_at = node.get("createdAt") or node.get("submittedAt")
        base = {"id": str(node.get("id") or ""), "actor": actor, "created_at": created_at}
        if typename == "IssueComment":
            events.append({**base, "event": "commented", "body": node.get("body")})
        elif typename == "PullRequestReview":
            events.append(
                {
                    **base,
                    "event": "reviewed",
                    "user": actor,
                    "state": node.get("state"),
                    "submitted_at": node.get("submittedAt"),
                    "body": node.get("body"),
                }
            )
        elif typename == "ClosedEvent":
            events.append({**base, "event": "closed"})
        elif typename == "ReopenedEvent":
            events.append({**base, "event": "reopened"})
        elif typename == "MergedEvent":
            events.append({**base, "event": "merged"})
        elif typename in ("LabeledEvent", "UnlabeledEvent"):
            label = (node.get("label") or {}).get("name")
            events.append(
                {
                    **base,
                    "event": "labeled" if typename == "LabeledEvent" else "unlabeled",
                    "label": {"name": label},
                }
            )
        elif typename == "HeadRefForcePushedEvent":
            events.append({**base, "event": "head_ref_force_pushed"})
        elif typename == "RenamedTitleEvent":
            events.append({**base, "event": "renamed"})
        elif typename == "PullRequestCommit":
            sha = (node.get("commit") or {}).get("oid")
            events.append({**base, "event": "committed", "sha": sha})
    return events


def pull_request_detail_parts(
    node: dict[str, Any],
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Décompose un nœud détail GraphQL en éléments au format REST.

    Renvoie ``(détail PR, check-runs, statuts, revues, fichiers,
    chronologie)`` prêts pour ``map_pull_request_detail``.
    """
    detail = {**pull_request_rest(node), "body": node.get("body")}
    commits = (node.get("commits") or {}).get("nodes") or []
    commit = commits[0].get("commit") if commits else None
    check_runs, statuses = checks_from_commit(commit)
    reviews = reviews_rest((node.get("reviews") or {}).get("nodes") or [])
    files = [
        {
            "filename": (file_node or {}).get("path"),
            "additions": (file_node or {}).get("additions"),
            "deletions": (file_node or {}).get("deletions"),
        }
        for file_node in (node.get("files") or {}).get("nodes") or []
    ]
    timeline = timeline_rest((node.get("timelineItems") or {}).get("nodes") or [])
    return detail, check_runs, statuses, reviews, files, timeline
