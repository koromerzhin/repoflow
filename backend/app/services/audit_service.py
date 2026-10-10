"""Journal d'audit persistant.

Chaque action notable (analyse, décision, tentative de fusion) est enregistrée
de façon immuable. Le journal est consultable via l'API et la page Historique.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.entities import AuditEvent
from app.schemas.audit import AuditEventRead


def record(
    session: Session,
    *,
    event_type: str,
    message: str,
    repository_full_name: str | None = None,
    pull_request_number: int | None = None,
    actor: str = "system",
    payload: dict[str, Any] | None = None,
) -> AuditEvent:
    """Ajoute une entrée d'audit (sans commit : regroupé par l'appelant)."""
    event = AuditEvent(
        event_type=event_type,
        repository_full_name=repository_full_name,
        pull_request_number=pull_request_number,
        actor=actor,
        message=message,
        payload=json.dumps(payload, default=str) if payload is not None else None,
        occurred_at=datetime.now(UTC),
    )
    session.add(event)
    return event


def _parse_payload(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def to_schema(event: AuditEvent) -> AuditEventRead:
    """Convertit une entrée ORM en schéma d'API."""
    return AuditEventRead(
        id=event.id,
        event_type=event.event_type,
        repository_full_name=event.repository_full_name,
        pull_request_number=event.pull_request_number,
        actor=event.actor,
        message=event.message,
        payload=_parse_payload(event.payload),
        occurred_at=event.occurred_at,
    )


def list_events(
    session: Session,
    *,
    limit: int = 100,
    offset: int = 0,
    event_type: str | None = None,
    repository_full_name: str | None = None,
    before_id: int | None = None,
) -> list[AuditEvent]:
    """Liste les entrées d'audit, les plus récentes d'abord.

    ``before_id`` permet une pagination par curseur : ne renvoie que les
    entrées strictement antérieures à l'entrée identifiée.
    """
    statement = select(AuditEvent)
    if event_type:
        statement = statement.where(AuditEvent.event_type == event_type)
    if repository_full_name:
        statement = statement.where(AuditEvent.repository_full_name == repository_full_name)
    if before_id is not None:
        statement = statement.where(AuditEvent.id < before_id)
    statement = statement.order_by(AuditEvent.occurred_at.desc(), AuditEvent.id.desc())
    statement = statement.offset(offset).limit(limit)
    return list(session.scalars(statement).all())


def purge_expired(session: Session, retention_days: int) -> int:
    """Supprime les entrées plus anciennes que la rétention configurée.

    Renvoie le nombre d'entrées supprimées. ``retention_days`` vaut 0 ou moins :
    aucune suppression (rétention désactivée).
    """
    if retention_days <= 0:
        return 0
    threshold = datetime.now(UTC) - timedelta(days=retention_days)
    result = session.execute(delete(AuditEvent).where(AuditEvent.occurred_at < threshold))
    return int(result.rowcount or 0)


def count_events(
    session: Session,
    *,
    event_type: str | None = None,
    repository_full_name: str | None = None,
) -> int:
    """Compte les entrées d'audit correspondant aux filtres."""
    statement = select(func.count()).select_from(AuditEvent)
    if event_type:
        statement = statement.where(AuditEvent.event_type == event_type)
    if repository_full_name:
        statement = statement.where(AuditEvent.repository_full_name == repository_full_name)
    return int(session.scalar(statement) or 0)
