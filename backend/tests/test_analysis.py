"""Tests du moteur d'analyse et des garde-fous de fusion."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.session import get_session_factory
from app.integrations.github.demo_provider import DemoProvider
from app.schemas.config import AutomationRuleCreate, RepositoryConfigCreate
from app.services import audit_service, config_service, system_service
from app.services.analysis_service import (
    evaluate_pr_for_rule,
    match_rule,
    run_analysis,
)


@pytest.fixture
def session() -> Iterator[Session]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def _setup(session: Session, *, auto_merge: bool = True) -> None:
    repo = config_service.create_repository_config(
        session, RepositoryConfigCreate(full_name="acme/web-app", default_branch="main")
    )
    config_service.create_rule(
        session,
        repo.id,
        AutomationRuleCreate(
            name="Fusion main",
            branch_pattern="*",
            auto_merge_enabled=auto_merge,
            required_approvals=1,
            require_green_checks=True,
        ),
    )


async def test_analyse_fusionne_pr_eligible(session: Session) -> None:
    _setup(session, auto_merge=True)
    provider = DemoProvider()

    summary = await run_analysis(session, provider, Settings(auto_merge_enabled_globally=True))

    assert summary.merged == 1
    assert summary.eligible >= 1
    assert summary.blocked >= 1

    events = audit_service.list_events(session)
    merged = [event for event in events if event.event_type == "merge_succeeded"]
    assert len(merged) == 1
    assert merged[0].pull_request_number == 142


async def test_analyse_sans_autorisation_globale(session: Session) -> None:
    _setup(session, auto_merge=True)
    provider = DemoProvider()

    summary = await run_analysis(session, provider, Settings(auto_merge_enabled_globally=False))

    assert summary.merged == 0
    assert summary.skipped == 1
    events = audit_service.list_events(session, event_type="merge_skipped")
    assert audit_service.to_schema(events[0]).payload["reason"] == "global_disabled"


async def test_analyse_arret_urgence(session: Session) -> None:
    _setup(session, auto_merge=True)
    system_service.set_kill_switch(session, True)
    provider = DemoProvider()

    summary = await run_analysis(session, provider, Settings(auto_merge_enabled_globally=True))

    assert summary.merged == 0
    assert summary.skipped == 1
    events = audit_service.list_events(session, event_type="merge_skipped")
    assert audit_service.to_schema(events[0]).payload["reason"] == "kill_switch"


async def test_analyse_regle_desactivee(session: Session) -> None:
    _setup(session, auto_merge=False)
    provider = DemoProvider()

    summary = await run_analysis(session, provider, Settings(auto_merge_enabled_globally=True))

    assert summary.eligible >= 1
    assert summary.merged == 0
    assert summary.skipped == 0
    assert audit_service.list_events(session, event_type="merge_succeeded") == []


def test_match_rule_par_branche() -> None:
    from app.models.entities import AutomationRule

    main_rule = AutomationRule(repository_id=1, name="main", branch_pattern="main")
    main_rule.id = 1
    release_rule = AutomationRule(repository_id=1, name="release", branch_pattern="release/*")
    release_rule.id = 2
    rules = [release_rule, main_rule]

    assert match_rule(rules, "main") is main_rule
    assert match_rule(rules, "release/1.2") is release_rule
    assert match_rule(rules, "develop") is None


async def test_evaluate_bloque_branche_non_defaut(session: Session) -> None:
    from app.models.entities import AutomationRule

    provider = DemoProvider()
    pr = await provider.get_pull_request("acme/client-sdk", 31)
    rule = AutomationRule(
        repository_id=1,
        name="r",
        branch_pattern="*",
        auto_merge_enabled=True,
        required_approvals=1,
        require_green_checks=False,
    )
    rule.id = 1

    eligibility = evaluate_pr_for_rule(pr, rule, default_branch="main")
    assert eligibility.eligible is False
    assert "protected_branch" in {blocker.code for blocker in eligibility.blockers}
