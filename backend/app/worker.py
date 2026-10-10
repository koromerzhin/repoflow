"""Worker d'analyse périodique.

Peut être lancé de deux façons :

- intégré à l'application FastAPI (``REPOFLOW_WORKER_ENABLED=true``) ;
- en processus séparé, avec la même image backend :

    python -m app.worker

Le worker évalue les règles d'automatisation et, uniquement si elles sont
explicitement activées (règle + global) et que l'arrêt d'urgence est
désengagé, déclenche une fusion ``squash``.
"""

from __future__ import annotations

import asyncio

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.init_db import create_all
from app.db.session import get_session_factory
from app.integrations.github.factory import get_provider
from app.services import audit_service
from app.services.analysis_service import run_analysis

logger = get_logger(__name__)


async def run_once() -> None:
    """Exécute une passe d'analyse, puis ferme la session."""
    settings = get_settings()
    provider = get_provider()
    session = get_session_factory()()
    try:
        summary = await run_analysis(session, provider, settings)
        logger.info(
            "Analyse : %s dépôt(s), %s PR, %s fusion(s).",
            summary.repositories,
            summary.pull_requests,
            summary.merged,
        )
        _purge_audit(session, settings.audit_retention_days)
    finally:
        session.close()


def _purge_audit(session: Session, retention_days: int) -> None:
    """Applique la rétention du journal d'audit (aucun effet si 0)."""
    if retention_days <= 0:
        return
    purged = audit_service.purge_expired(session, retention_days)
    if purged:
        session.commit()
        logger.info("Rétention d'audit : %s entrée(s) supprimée(s).", purged)


async def run_forever(interval_seconds: int | None = None) -> None:
    """Boucle d'analyse périodique, tolérante aux erreurs transitoires."""
    settings = get_settings()
    interval = interval_seconds or settings.worker_interval_seconds
    while True:
        try:
            await run_once()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Échec d'une passe d'analyse ; nouvelle tentative plus tard.")
        await asyncio.sleep(interval)


async def main() -> None:
    """Point d'entrée du worker en processus séparé."""
    settings = get_settings()
    configure_logging(settings)
    if settings.auto_create_tables:
        create_all()
    logger.info(
        "Worker RepoFlow démarré (intervalle=%ss, merge global=%s, arrêt d'urgence=%s).",
        settings.worker_interval_seconds,
        settings.auto_merge_enabled_globally,
        settings.kill_switch_engaged,
    )
    await run_forever()


if __name__ == "__main__":
    asyncio.run(main())
