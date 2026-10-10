"""Gestion des sessions et du moteur de base de données."""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def create_engine_from_url(database_url: str) -> Engine:
    """Crée un moteur SQLAlchemy adapté au type de base de données.

    SQLite : ``check_same_thread=False`` pour le mode serveur.
    Autres bases (ex. PostgreSQL) : ``pool_pre_ping`` et taille de pool
    configurables, pour des connexions fiables derrière un réseau.
    """
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            future=True,
        )
    settings = get_settings()
    return create_engine(
        database_url,
        pool_pre_ping=settings.db_pool_pre_ping,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        future=True,
    )


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
