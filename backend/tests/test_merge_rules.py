"""Tests unitaires des règles métier (sans couche HTTP)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.integrations.github.types import CheckRecord, PullRequestRecord
from app.schemas.pull_request import CheckState, PullRequestState, ReviewDecision
from app.services.merge_rules import aggregate_checks_state, evaluate_merge_eligibility

_NOW = datetime.now(UTC)


def _check(state: CheckState, required: bool = True) -> CheckRecord:
    return CheckRecord(name="build", state=state, required=required)


def _pr(**overrides: object) -> PullRequestRecord:
    base: dict[str, object] = {
        "id": "pr-1",
        "number": 1,
        "repository_full_name": "acme/demo",
        "title": "Titre",
        "author": "tester",
        "source_branch": "feat/x",
        "target_branch": "main",
        "state": PullRequestState.OPEN,
        "is_draft": False,
        "mergeable": True,
        "changed_files": 1,
        "additions": 10,
        "deletions": 2,
        "review_decision": ReviewDecision.APPROVED,
        "checks": [_check(CheckState.SUCCESS)],
        "created_at": _NOW,
        "updated_at": _NOW,
        "html_url": "https://example.test/pr/1",
    }
    base.update(overrides)
    return PullRequestRecord(**base)  # type: ignore[arg-type]


def test_aggregate_empty_is_unknown() -> None:
    assert aggregate_checks_state([]) == CheckState.UNKNOWN


def test_aggregate_priority_failure_then_pending_then_unknown() -> None:
    assert (
        aggregate_checks_state([_check(CheckState.SUCCESS), _check(CheckState.FAILURE)])
        == CheckState.FAILURE
    )
    assert (
        aggregate_checks_state([_check(CheckState.SUCCESS), _check(CheckState.PENDING)])
        == CheckState.PENDING
    )
    assert (
        aggregate_checks_state([_check(CheckState.SUCCESS), _check(CheckState.UNKNOWN)])
        == CheckState.UNKNOWN
    )
    assert aggregate_checks_state([_check(CheckState.SUCCESS)]) == CheckState.SUCCESS


def test_eligible_pull_request() -> None:
    assert evaluate_merge_eligibility(_pr()).eligible is True


def test_draft_blocks_merge() -> None:
    result = evaluate_merge_eligibility(_pr(is_draft=True))
    assert result.eligible is False
    assert "draft" in {blocker.code for blocker in result.blockers}


def test_conflict_blocks_merge() -> None:
    result = evaluate_merge_eligibility(_pr(mergeable=False))
    assert result.eligible is False
    assert "conflict" in {blocker.code for blocker in result.blockers}


def test_non_approved_blocks_merge() -> None:
    result = evaluate_merge_eligibility(_pr(review_decision=ReviewDecision.REVIEW_REQUIRED))
    assert result.eligible is False
    assert "not_approved" in {blocker.code for blocker in result.blockers}


def test_optional_failing_check_does_not_block() -> None:
    pr = _pr(checks=[_check(CheckState.SUCCESS), _check(CheckState.FAILURE, required=False)])
    assert evaluate_merge_eligibility(pr).eligible is True


def test_unknown_check_blocks_merge() -> None:
    pr = _pr(checks=[_check(CheckState.UNKNOWN)])
    result = evaluate_merge_eligibility(pr)
    assert result.eligible is False
    assert "check_not_success" in {blocker.code for blocker in result.blockers}


def test_closed_pull_request_not_eligible() -> None:
    result = evaluate_merge_eligibility(_pr(state=PullRequestState.CLOSED))
    assert result.eligible is False
    assert "not_open" in {blocker.code for blocker in result.blockers}
