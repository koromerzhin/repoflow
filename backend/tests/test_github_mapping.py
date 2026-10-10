"""Tests des conversions GitHub -> domaine (fonctions pures)."""

from __future__ import annotations

from app.integrations.github.mapping import (
    map_check_run,
    map_combined_checks,
    map_issue,
    map_pull_request,
    map_pull_request_detail,
    map_pull_request_file,
    map_pull_request_review,
    map_repository,
    map_review_decision,
    map_status_context,
    map_timeline_event,
    parse_datetime,
)
from app.schemas.issue import IssueState
from app.schemas.pull_request import (
    CheckState,
    PullRequestState,
    ReviewDecision,
    ReviewState,
)


def test_parse_datetime_iso_z() -> None:
    parsed = parse_datetime("2024-05-01T10:00:00Z")
    assert parsed.tzinfo is not None
    assert parsed.year == 2024


def test_parse_datetime_vide_renvoie_maintenant() -> None:
    assert parse_datetime(None).tzinfo is not None


def test_check_run_success() -> None:
    record = map_check_run({"name": "build", "status": "completed", "conclusion": "success"})
    assert record.state == CheckState.SUCCESS
    assert record.required is True


def test_check_run_neutral_et_skipped_sont_reussis() -> None:
    for conclusion in ("neutral", "skipped"):
        record = map_check_run({"name": "build", "status": "completed", "conclusion": conclusion})
        assert record.state == CheckState.SUCCESS


def test_check_run_failure() -> None:
    for conclusion in ("failure", "timed_out", "cancelled", "action_required", "stale"):
        record = map_check_run({"name": "build", "status": "completed", "conclusion": conclusion})
        assert record.state == CheckState.FAILURE


def test_check_run_en_cours_est_pending() -> None:
    record = map_check_run({"name": "build", "status": "in_progress", "conclusion": None})
    assert record.state == CheckState.PENDING


def test_check_run_conclusion_inconnue() -> None:
    record = map_check_run({"name": "build", "status": "completed", "conclusion": "quelque_chose"})
    assert record.state == CheckState.UNKNOWN


def test_status_context() -> None:
    assert map_status_context({"context": "ci", "state": "success"}).state == CheckState.SUCCESS
    assert map_status_context({"context": "ci", "state": "error"}).state == CheckState.FAILURE
    assert map_status_context({"context": "ci", "state": "pending"}).state == CheckState.PENDING
    assert map_status_context({"context": "ci", "state": "???"}).state == CheckState.UNKNOWN


def test_combined_checks_dedoublonne_par_nom() -> None:
    check_runs = [{"name": "build", "status": "completed", "conclusion": "failure"}]
    statuses = [{"context": "build", "state": "success"}, {"context": "lint", "state": "success"}]
    combined = map_combined_checks(check_runs, statuses)
    by_name = {c.name: c for c in combined}
    assert len(combined) == 2
    # Le check-run (plus récent) prime sur le commit status de même nom.
    assert by_name["build"].state == CheckState.FAILURE
    assert by_name["lint"].state == CheckState.SUCCESS


def test_review_decision_vide() -> None:
    assert map_review_decision([]) == ReviewDecision.NONE


def test_review_decision_commentaires_seulement() -> None:
    assert (
        map_review_decision([{"user": {"login": "a"}, "state": "COMMENTED"}])
        == ReviewDecision.REVIEW_REQUIRED
    )


def test_review_decision_approuvee() -> None:
    reviews = [
        {"user": {"login": "a"}, "state": "APPROVED", "submitted_at": "2024-01-02T00:00:00Z"}
    ]
    assert map_review_decision(reviews) == ReviewDecision.APPROVED


def test_review_decision_changements_priment() -> None:
    reviews = [
        {"user": {"login": "a"}, "state": "APPROVED", "submitted_at": "2024-01-02T00:00:00Z"},
        {
            "user": {"login": "b"},
            "state": "CHANGES_REQUESTED",
            "submitted_at": "2024-01-01T00:00:00Z",
        },
    ]
    assert map_review_decision(reviews) == ReviewDecision.CHANGES_REQUESTED


def test_review_decision_dernier_etat_par_relecteur() -> None:
    reviews = [
        {
            "user": {"login": "a"},
            "state": "CHANGES_REQUESTED",
            "submitted_at": "2024-01-01T00:00:00Z",
        },
        {"user": {"login": "a"}, "state": "APPROVED", "submitted_at": "2024-01-02T00:00:00Z"},
    ]
    assert map_review_decision(reviews) == ReviewDecision.APPROVED


def test_review_decision_dismissed_ignore() -> None:
    reviews = [
        {"user": {"login": "a"}, "state": "APPROVED", "submitted_at": "2024-01-01T00:00:00Z"},
        {"user": {"login": "a"}, "state": "DISMISSED", "submitted_at": "2024-01-02T00:00:00Z"},
    ]
    assert map_review_decision(reviews) == ReviewDecision.REVIEW_REQUIRED


def test_map_repository() -> None:
    record = map_repository(
        {
            "id": 42,
            "name": "web-app",
            "full_name": "acme/web-app",
            "owner": {"login": "acme"},
            "default_branch": "main",
            "private": False,
            "open_issues_count": 7,
            "updated_at": "2024-05-01T10:00:00Z",
            "html_url": "https://github.com/acme/web-app",
        }
    )
    assert record.id == "42"
    assert record.full_name == "acme/web-app"
    assert record.owner == "acme"
    assert record.open_issues_count == 7


def _pr_data(**overrides: object) -> dict:
    base: dict = {
        "id": 1,
        "number": 10,
        "title": "Titre",
        "user": {"login": "dev"},
        "head": {"ref": "feat/x", "sha": "abc"},
        "base": {"ref": "main"},
        "state": "open",
        "draft": False,
        "mergeable": True,
        "changed_files": 3,
        "additions": 10,
        "deletions": 2,
        "created_at": "2024-05-01T10:00:00Z",
        "updated_at": "2024-05-02T10:00:00Z",
        "html_url": "https://github.com/acme/web-app/pull/10",
    }
    base.update(overrides)
    return base


def test_map_pull_request_ouverte() -> None:
    record = map_pull_request(_pr_data(), "acme/web-app", [], ReviewDecision.NONE)
    assert record.state == PullRequestState.OPEN
    assert record.source_branch == "feat/x"
    assert record.target_branch == "main"
    assert record.mergeable is True


def test_map_pull_request_brouillon() -> None:
    record = map_pull_request(_pr_data(draft=True), "acme/web-app", [], ReviewDecision.NONE)
    assert record.state == PullRequestState.DRAFT
    assert record.is_draft is True


def test_map_pull_request_fermee() -> None:
    record = map_pull_request(_pr_data(state="closed"), "acme/web-app", [], ReviewDecision.NONE)
    assert record.state == PullRequestState.CLOSED


def test_map_pull_request_fusionnee() -> None:
    record = map_pull_request(
        _pr_data(state="closed", merged_at="2024-05-03T00:00:00Z"),
        "acme/web-app",
        [],
        ReviewDecision.NONE,
    )
    assert record.state == PullRequestState.MERGED


def test_map_pull_request_mergeable_inconnu_traite_comme_non_fusionnable() -> None:
    record = map_pull_request(_pr_data(mergeable=None), "acme/web-app", [], ReviewDecision.NONE)
    assert record.mergeable is False


def test_map_issue_ouverte() -> None:
    record = map_issue(
        {
            "id": 5,
            "number": 5,
            "title": "Un bug",
            "user": {"login": "dev"},
            "state": "open",
            "created_at": "2024-05-01T10:00:00Z",
            "updated_at": "2024-05-02T10:00:00Z",
            "html_url": "https://github.com/acme/web-app/issues/5",
        },
        "acme/web-app",
    )
    assert record.state == IssueState.OPEN
    assert record.repository_full_name == "acme/web-app"
    assert record.is_pull_request is False


def test_map_issue_fermee() -> None:
    record = map_issue({"id": 6, "number": 6, "state": "closed"}, "acme/web-app")
    assert record.state == IssueState.CLOSED


def test_map_issue_marque_comme_pull_request() -> None:
    record = map_issue({"id": 7, "number": 7}, "acme/web-app", is_pull_request=True)
    assert record.is_pull_request is True


def test_map_pull_request_file_calcule_les_changements() -> None:
    record = map_pull_request_file(
        {"filename": "src/a.py", "status": "modified", "additions": 3, "deletions": 2}
    )
    assert record.filename == "src/a.py"
    assert record.changes == 5


def test_map_pull_request_review_states() -> None:
    approved = map_pull_request_review(
        {"id": 1, "user": {"login": "alice"}, "state": "APPROVED", "body": "ok"}
    )
    assert approved.state == ReviewState.APPROVED
    assert approved.author == "alice"

    commented = map_pull_request_review({"id": 2, "user": {"login": "bob"}, "state": "COMMENTED"})
    assert commented.state == ReviewState.COMMENTED
    assert commented.submitted_at is None


def test_map_timeline_event_commented_reprend_le_corps() -> None:
    record = map_timeline_event(
        {
            "id": 10,
            "event": "commented",
            "actor": {"login": "alice"},
            "body": "Merci pour les retours.",
            "created_at": "2024-05-01T10:00:00Z",
        }
    )
    assert record.event_type == "commented"
    assert record.actor == "alice"
    assert record.message == "Merci pour les retours."


def test_map_timeline_event_labeled() -> None:
    record = map_timeline_event(
        {
            "id": 11,
            "event": "labeled",
            "label": {"name": "bug"},
            "created_at": "2024-05-01T10:00:00Z",
        }
    )
    assert record.message == "a ajouté le label « bug »"


def test_map_timeline_event_reviewed_changes_requested() -> None:
    record = map_timeline_event(
        {
            "id": 12,
            "event": "reviewed",
            "state": "CHANGES_REQUESTED",
            "user": {"login": "bob"},
            "created_at": "2024-05-01T10:00:00Z",
        }
    )
    assert record.message == "a demandé des modifications"


def test_map_pull_request_detail_agrege_les_sections() -> None:
    detail = map_pull_request_detail(
        _pr_data(body="Description."),
        "acme/web-app",
        [],
        [{"id": 1, "user": {"login": "alice"}, "state": "APPROVED"}],
        [{"filename": "src/a.py", "status": "modified", "additions": 1, "deletions": 0}],
        [
            {
                "id": 1,
                "event": "opened",
                "actor": {"login": "dev"},
                "created_at": "2024-05-01T10:00:00Z",
            }
        ],
    )
    assert detail.body == "Description."
    assert len(detail.files) == 1
    assert len(detail.reviews) == 1
    assert len(detail.timeline) == 1
    assert detail.review_decision == ReviewDecision.APPROVED
