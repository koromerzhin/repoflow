"""Initialisation de la base de données.

En production, les schémas sont gérés par Alembic. Pour le développement et
les tests, ``AUTO_CREATE_TABLES`` permet de créer les tables au démarrage.
"""

from __future__ import annotations

from sqlalchemy import Engine

# Import nécessaire pour enregistrer les modèles dans les métadonnées.
from app import models  # noqa: F401
from app.core.logging import get_logger
from app.db.base import Base
from app.db.session import get_engine

logger = get_logger(__name__)


def create_all(engine: Engine | None = None) -> None:
    """Crée toutes les tables déclarées."""
    target = engine or get_engine()
    Base.metadata.create_all(bind=target)
    logger.info("Tables de base de données initialisées")
