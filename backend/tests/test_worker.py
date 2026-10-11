"""Tests du worker : passe complète, snapshot et tolérance aux erreurs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.integrations.github.factory import build_provider
from app.services import audit_service, snapshot_service
from app.worker import _purge_audit, _record_snapshot, run_once


def _session() -> Session:
    return get_session_factory()()


async def _fake_analysis(session: Session, provider: object, settings: object) -> SimpleNamespace:
    return SimpleNamespace(repositories=3, pull_requests=7, merged=0)


async def test_run_once_execute_analyse_snapshot_et_purge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.worker as worker

    calls: dict[str, int] = {}

    async def analysis(session: Session, provider: object, settings: object) -> SimpleNamespace:
        calls["analysis"] = 1
        return SimpleNamespace(repositories=3, pull_requests=7, merged=0)

    monkeypatch.setattr(worker, "run_analysis", analysis)
    monkeypatch.setattr(worker, "get_settings", lambda: get_settings())
    monkeypatch.setattr(worker, "get_provider", lambda: build_provider(get_settings()))
    monkeypatch.setattr(worker, "get_session_factory", lambda: get_session_factory())

    await run_once()

    assert calls["analysis"] == 1
    session = _session()
    try:
        snapshots = snapshot_service.list_snapshots(session)
        assert len(snapshots) == 3
    finally:
        session.close()


async def test_run_once_survit_a_un_echec_de_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.worker as worker

    class BrokenProvider:
        name = "demo"

        async def list_repositories(self) -> list[Any]:
            raise RuntimeError("indisponible")

    monkeypatch.setattr(worker, "run_analysis", _fake_analysis)
    monkeypatch.setattr(worker, "get_settings", lambda: get_settings())
    monkeypatch.setattr(worker, "get_provider", lambda: BrokenProvider())
    monkeypatch.setattr(worker, "get_session_factory", lambda: get_session_factory())

    await run_once()


async def test_record_snapshot_couvre_les_depots() -> None:
    provider = build_provider(get_settings())
    session = _session()
    try:
        await _record_snapshot(session, provider)
        snapshots = snapshot_service.list_snapshots(session)
    finally:
        session.close()

    assert len(snapshots) == 3


async def test_record_snapshot_tolerant_aux_erreurs() -> None:
    class BrokenProvider:
        name = "demo"

        async def list_repositories(self) -> list[Any]:
            raise RuntimeError("indisponible")

    session = _session()
    try:
        await _record_snapshot(session, BrokenProvider())
    finally:
        session.close()


def test_purge_audit_sans_retention_ne_suppresse_rien() -> None:
    session = _session()
    try:
        audit_service.record(session, event_type="analysis", message="Analyse")
        session.commit()
        before = audit_service.count_events(session)

        _purge_audit(session, 0)

        assert audit_service.count_events(session) == before
    finally:
        session.close()


def test_purge_audit_applique_la_retention() -> None:
    session = _session()
    try:
        ancienne = audit_service.record(session, event_type="analysis", message="Analyse ancienne")
        ancienne.occurred_at = datetime.now(UTC) - timedelta(days=30)
        audit_service.record(session, event_type="analysis", message="Analyse récente")
        session.commit()

        _purge_audit(session, 7)
        session.commit()

        messages = [event.message for event in audit_service.list_events(session)]
        assert messages == ["Analyse récente"]
    finally:
        session.close()
