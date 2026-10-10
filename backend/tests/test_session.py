"""Tests de création de moteur SQLAlchemy selon la base de données."""

from __future__ import annotations

from app.core.config import get_settings
from app.db.session import create_engine_from_url


def test_moteur_sqlite_check_same_thread() -> None:
    engine = create_engine_from_url("sqlite+pysqlite:///:memory:")
    assert engine.dialect.name == "sqlite"


def test_moteur_postgresql_options_de_pool() -> None:
    engine = create_engine_from_url("postgresql+psycopg://repoflow:secret@localhost:5432/repoflow")
    assert engine.dialect.name == "postgresql"
    settings = get_settings()
    assert engine.pool._pre_ping is True
    assert engine.pool.size() == settings.db_pool_size
    assert engine.pool._max_overflow == settings.db_max_overflow
