"""Fixtures partagées des tests backend."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

# Configuration de test définie AVANT l'import de l'application afin que la
# configuration mise en cache utilise bien ces valeurs.
_db_fd, _db_path = tempfile.mkstemp(prefix="repoflow-test-", suffix=".db")
os.close(_db_fd)
os.environ["REPOFLOW_ENVIRONMENT"] = "test"
os.environ["REPOFLOW_GITHUB_PROVIDER"] = "demo"
os.environ["REPOFLOW_DATABASE_URL"] = f"sqlite+pysqlite:///{_db_path}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import delete  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """Client HTTP de test, avec cycle de vie de l'application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _clean_tables() -> Iterator[None]:
    """Vide les tables de configuration et d'audit avant chaque test."""
    from app.db.init_db import create_all
    from app.db.session import get_session_factory
    from app.models.entities import (
        AuditEvent,
        AutomationRule,
        DailySnapshot,
        RepositoryConfig,
        SystemSetting,
    )

    create_all()
    session = get_session_factory()()
    try:
        for model in (AuditEvent, AutomationRule, RepositoryConfig, SystemSetting, DailySnapshot):
            session.execute(delete(model))
        session.commit()
    finally:
        session.close()
    yield


@pytest.fixture(scope="session", autouse=True)
def _cleanup_db() -> Iterator[None]:
    """Supprime le fichier de base temporaire en fin de session."""
    yield
    Path(_db_path).unlink(missing_ok=True)
