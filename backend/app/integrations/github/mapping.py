"""Conversion des données GitHub brutes vers les enregistrements de domaine.

Ces fonctions sont pures (pas d'appel réseau) et donc facilement testables.

Choix de sécurité : tous les checks résolus sont marqués ``required=True``.
Sans accès aux protections de branche, considérer un check comme obligatoire
est la position la plus prudente : un check échoué, en cours ou inconnu
bloquera la fusion.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.integrations.github.types import (
    CheckRecord,
    IssueRecord,
    PullRequestDetailRecord,
    PullRequestFileRecord,
    PullRequestRecord,
    PullRequestReviewRecord,
    RepositoryRecord,
    TimelineEventRecord,
)
from app.schemas.issue import IssueState
from app.schemas.pull_request import (
    CheckState,
    PullRequestState,
    ReviewDecision,
    ReviewState,
)

# Conclusions de check-run considérées comme réussies.
_CHECK_RUN_SUCCESS = {"success", "neutral", "skipped"}
# Conclusions de check-run considérées comme en échec.
_CHECK_RUN_FAILURE = {"failure", "timed_out", "cancelled", "action_required", "stale"}

# États de commit status (API « statuses ») vers notre modèle.
_STATUS_STATE = {
    "success": CheckState.SUCCESS,
    "failure": CheckState.FAILURE,
    "error": CheckState.FAILURE,
    "pending": CheckState.PENDING,
}


def parse_datetime(value: str | None) -> datetime:
    """Convertit une date ISO 8601 GitHub en ``datetime`` conscient du fuseau."""
    if not value:
        return datetime.now(UTC)
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.now(UTC)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def map_check_run(data: dict[str, Any]) -> CheckRecord:
    """Convertit un check-run GitHub en ``CheckRecord``."""
    status = data.get("status")
    conclusion = data.get("conclusion")
    if status != "completed":
        state = CheckState.PENDING
    elif conclusion in _CHECK_RUN_SUCCESS:
        state = CheckState.SUCCESS
    elif conclusion in _CHECK_RUN_FAILURE:
        state = CheckState.FAILURE
    else:
        state = CheckState.UNKNOWN
    return CheckRecord(
        name=str(data.get("name") or "check"),
        state=state,
        conclusion=conclusion,
        required=True,
        details_url=data.get("details_url"),
    )


def map_status_context(data: dict[str, Any]) -> CheckRecord:
    """Convertit un commit status GitHub en ``CheckRecord``."""
    raw_state = str(data.get("state") or "").lower()
    state = _STATUS_STATE.get(raw_state, CheckState.UNKNOWN)
    return CheckRecord(
        name=str(data.get("context") or "status"),
        state=state,
        conclusion=raw_state or None,
        required=True,
        details_url=data.get("target_url"),
    )


def map_combined_checks(
    check_runs: list[dict[str, Any]], statuses: list[dict[str, Any]]
) -> list[CheckRecord]:
    """Fusionne check-runs et commit statuses en dédupliquant par nom."""
    combined: dict[str, CheckRecord] = {}
    for status in statuses:
        record = map_status_context(status)
        combined.setdefault(record.name, record)
    for run in check_runs:
        record = map_check_run(run)
        combined[record.name] = record
    return list(combined.values())


def map_review_decision(reviews: list[dict[str, Any]]) -> ReviewDecision:
    """Déduit la décision de revue à partir des revues GitHub.

    On retient le dernier état de chaque relecteur, puis on applique la règle :
    ``changes_requested`` prime, sinon ``approved``, sinon revue requise.
    """
    latest: dict[str, str] = {}
    for review in sorted(reviews, key=lambda item: item.get("submitted_at") or ""):
        user = (review.get("user") or {}).get("login")
        state = review.get("state")
        if not user or not state:
            continue
        if state == "DISMISSED":
            latest.pop(user, None)
        elif state in ("APPROVED", "CHANGES_REQUESTED"):
            latest[user] = state

    states = set(latest.values())
    if "CHANGES_REQUESTED" in states:
        return ReviewDecision.CHANGES_REQUESTED
    if "APPROVED" in states:
        return ReviewDecision.APPROVED
    if reviews:
        return ReviewDecision.REVIEW_REQUIRED
    return ReviewDecision.NONE


def map_repository(data: dict[str, Any]) -> RepositoryRecord:
    """Convertit un dépôt GitHub en ``RepositoryRecord``.

    ``open_issues_count`` renvoyé par GitHub inclut les pull requests ; le
    nombre de PR ouvertes n'est pas fourni par cet endpoint (valeur 0).
    """
    owner = (data.get("owner") or {}).get("login") or ""
    name = str(data.get("name") or "")
    return RepositoryRecord(
        id=str(data.get("id")),
        owner=owner,
        name=name,
        full_name=str(data.get("full_name") or (f"{owner}/{name}" if owner else name)),
        default_branch=str(data.get("default_branch") or "main"),
        private=bool(data.get("private")),
        open_issues_count=int(data.get("open_issues_count") or 0),
        open_pull_requests_count=0,
        updated_at=parse_datetime(data.get("updated_at")),
        html_url=str(data.get("html_url") or ""),
    )


def _map_pr_state(data: dict[str, Any]) -> PullRequestState:
    if data.get("merged_at") is not None or data.get("merged") is True:
        return PullRequestState.MERGED
    if str(data.get("state")) == "closed":
        return PullRequestState.CLOSED
    if data.get("draft") is True:
        return PullRequestState.DRAFT
    return PullRequestState.OPEN


def map_pull_request(
    data: dict[str, Any],
    repository_full_name: str,
    checks: list[CheckRecord],
    review_decision: ReviewDecision,
) -> PullRequestRecord:
    """Convertit une pull request GitHub en ``PullRequestRecord``.

    ``mergeable`` peut valoir ``null`` tant que GitHub n'a pas terminé le
    calcul ; par prudence, un état inconnu est traité comme non fusionnable.
    """
    mergeable_raw = data.get("mergeable")
    head = data.get("head") or {}
    base = data.get("base") or {}
    return PullRequestRecord(
        id=str(data.get("id")),
        number=int(data.get("number")),
        repository_full_name=repository_full_name,
        title=str(data.get("title") or ""),
        author=str((data.get("user") or {}).get("login") or ""),
        source_branch=str(head.get("ref") or ""),
        target_branch=str(base.get("ref") or ""),
        state=_map_pr_state(data),
        is_draft=bool(data.get("draft")),
        mergeable=bool(mergeable_raw) if mergeable_raw is not None else False,
        changed_files=int(data.get("changed_files") or 0),
        additions=int(data.get("additions") or 0),
        deletions=int(data.get("deletions") or 0),
        review_decision=review_decision,
        checks=checks,
        created_at=parse_datetime(data.get("created_at")),
        updated_at=parse_datetime(data.get("updated_at")),
        html_url=str(data.get("html_url") or ""),
    )


def map_issue(
    data: dict[str, Any], repository_full_name: str, *, is_pull_request: bool = False
) -> IssueRecord:
    """Convertit une issue GitHub en ``IssueRecord``.

    L'endpoint ``/issues`` de GitHub renvoie aussi les pull requests ; elles
    sont normalement filtrées en amont (``is_pull_request=True``).
    """
    raw_state = str(data.get("state") or "").lower()
    state = IssueState.CLOSED if raw_state == "closed" else IssueState.OPEN
    return IssueRecord(
        id=str(data.get("id")),
        number=int(data.get("number")),
        repository_full_name=repository_full_name,
        title=str(data.get("title") or ""),
        author=str((data.get("user") or {}).get("login") or ""),
        state=state,
        is_pull_request=is_pull_request,
        created_at=parse_datetime(data.get("created_at")),
        updated_at=parse_datetime(data.get("updated_at")),
        html_url=str(data.get("html_url") or ""),
    )


# États de revue GitHub vers notre modèle.
_REVIEW_STATE = {
    "APPROVED": ReviewState.APPROVED,
    "CHANGES_REQUESTED": ReviewState.CHANGES_REQUESTED,
    "COMMENTED": ReviewState.COMMENTED,
    "DISMISSED": ReviewState.DISMISSED,
    "PENDING": ReviewState.PENDING,
}


def map_pull_request_file(data: dict[str, Any]) -> PullRequestFileRecord:
    """Convertit un fichier modifié GitHub en ``PullRequestFileRecord``."""
    additions = int(data.get("additions") or 0)
    deletions = int(data.get("deletions") or 0)
    return PullRequestFileRecord(
        filename=str(data.get("filename") or ""),
        status=str(data.get("status") or "modified"),
        additions=additions,
        deletions=deletions,
        changes=int(data.get("changes") or (additions + deletions)),
    )


def map_pull_request_review(data: dict[str, Any]) -> PullRequestReviewRecord:
    """Convertit une revue GitHub en ``PullRequestReviewRecord``."""
    raw_state = str(data.get("state") or "").upper()
    return PullRequestReviewRecord(
        id=str(data.get("id")),
        author=str((data.get("user") or {}).get("login") or ""),
        state=_REVIEW_STATE.get(raw_state, ReviewState.COMMENTED),
        body=data.get("body") or None,
        submitted_at=parse_datetime(data.get("submitted_at")) if data.get("submitted_at") else None,
    )


def _actor_login(data: dict[str, Any]) -> str:
    return str(
        (data.get("actor") or {}).get("login")
        or (data.get("user") or {}).get("login")
        or (data.get("committer") or {}).get("login")
        or ""
    )


def _timeline_message(event_type: str, data: dict[str, Any]) -> str:
    if event_type == "commented":
        body = str(data.get("body") or "").strip()
        return body if body else "a commenté"
    if event_type == "reviewed":
        state = map_pull_request_review(data).state
        return {
            ReviewState.APPROVED: "a approuvé la pull request",
            ReviewState.CHANGES_REQUESTED: "a demandé des modifications",
            ReviewState.DISMISSED: "a rejeté sa revue",
        }.get(state, "a commenté une revue")
    if event_type == "committed":
        sha = str(data.get("sha") or "")[:7]
        return f"a poussé le commit {sha}" if sha else "a poussé un commit"
    if event_type in ("labeled", "unlabeled"):
        label = str((data.get("label") or {}).get("name") or "?")
        verb = "a ajouté" if event_type == "labeled" else "a retiré"
        return f"{verb} le label « {label} »"
    if event_type == "closed":
        return "a fermé la pull request"
    if event_type == "reopened":
        return "a réouvert la pull request"
    if event_type == "merged":
        return "a fusionné la pull request"
    if event_type == "head_ref_force_pushed":
        return "a réécrit l'historique de la branche"
    if event_type == "renamed":
        return "a renommé la pull request"
    return event_type or "événement"


def map_timeline_event(data: dict[str, Any]) -> TimelineEventRecord:
    """Convertit un événement de chronologie GitHub en ``TimelineEventRecord``."""
    event_type = str(data.get("event") or "")
    created_at = parse_datetime(data.get("created_at"))
    return TimelineEventRecord(
        id=str(data.get("id") or f"{event_type}-{created_at.isoformat()}"),
        event_type=event_type or "unknown",
        actor=_actor_login(data),
        message=_timeline_message(event_type, data),
        created_at=created_at,
    )


def map_pull_request_detail(
    data: dict[str, Any],
    repository_full_name: str,
    checks: list[CheckRecord],
    reviews: list[dict[str, Any]],
    files: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
) -> PullRequestDetailRecord:
    """Convertit une pull request GitHub détaillée en ``PullRequestDetailRecord``."""
    base = map_pull_request(data, repository_full_name, checks, map_review_decision(reviews))
    return PullRequestDetailRecord(
        **base.model_dump(),
        body=data.get("body") or None,
        files=[map_pull_request_file(item) for item in files],
        reviews=[map_pull_request_review(item) for item in reviews],
        timeline=[map_timeline_event(item) for item in timeline],
    )
