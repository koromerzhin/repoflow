"""Gestion des sessions et du moteur de base de données."""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def create_engine_from_url(database_url: str) -> Engine:
    """Crée un moteur SQLAlchemy adapté au type de base de données."""
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(database_url, connect_args=connect_args, future=True)


@lru_cache
def get_engine() -> Engine:
    """Retourne le moteur partagé de l'application."""
    return create_engine_from_url(get_settings().database_url)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Retourne la fabrique de sessions partagée."""
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Dépendance FastAPI fournissant une session de base de données."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
