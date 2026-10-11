"""Historisation légère : un agrégat quotidien par dépôt.

À chaque passe du worker, les compteurs du tableau de bord sont persistés
par dépôt dans ``daily_snapshots`` (une ligne par dépôt et par jour UTC).
La ligne du jour est mise à jour, jamais dupliquée. Aucune donnée GitHub
détaillée n'est copiée.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.github.provider import Provider
from app.integrations.github.types import PullRequestRecord, RepositoryRecord
from app.models.entities import DailySnapshot
from app.schemas.snapshot import DailySnapshotRead
from app.services.dashboard_service import pull_request_stats
from app.services.data_service import get_combined_data


def to_schema(snapshot: DailySnapshot) -> DailySnapshotRead:
    """Convertit une entrée ORM en schéma d'API."""
    return DailySnapshotRead(
        id=snapshot.id,
        repository_full_name=snapshot.repository_full_name,
        snapshot_date=snapshot.snapshot_date,
        data_source=snapshot.data_source,
        open_pull_requests=snapshot.open_pull_requests,
        pull_requests_ready_to_merge=snapshot.pull_requests_ready_to_merge,
        pull_requests_with_failing_checks=snapshot.pull_requests_with_failing_checks,
        pull_requests_pending_checks=snapshot.pull_requests_pending_checks,
        open_issues=snapshot.open_issues,
    )


def _repository_stats(
    repository: RepositoryRecord, pull_requests: list[PullRequestRecord]
) -> dict[str, int]:
    stats = pull_request_stats(pull_requests)
    stats["open_issues"] = repository.open_issues_count
    return stats


async def record_daily_snapshot(
    session: Session, provider: Provider, *, refresh: bool = False
) -> int:
    """Enregistre (ou met à jour) le snapshot du jour pour chaque dépôt.

    Renvoie le nombre de dépôts couverts. Les données proviennent du cache
    fournisseur : la passe est quasi gratuite après la première analyse.
    """
    repositories, pull_requests = await get_combined_data(provider, refresh=refresh)
    today = datetime.now(UTC).date()
    covered = 0
    for repository in repositories:
        stats = _repository_stats(
            repository,
            [pr for pr in pull_requests if pr.repository_full_name == repository.full_name],
        )
        snapshot = session.scalar(
            select(DailySnapshot).where(
                DailySnapshot.repository_full_name == repository.full_name,
                DailySnapshot.snapshot_date == today,
            )
        )
        if snapshot is None:
            session.add(
                DailySnapshot(
                    repository_full_name=repository.full_name,
                    snapshot_date=today,
                    data_source=provider.name,
                    **stats,
                )
            )
        else:
            for field, value in stats.items():
                setattr(snapshot, field, value)
            snapshot.data_source = provider.name
        covered += 1
    session.commit()
    return covered


def list_snapshots(
    session: Session,
    *,
    repository_full_name: str | None = None,
    since: date | None = None,
    limit: int = 100,
) -> list[DailySnapshot]:
    """Snapshots les plus récents d'abord, filtrables et bornés."""
    statement = select(DailySnapshot)
    if repository_full_name:
        statement = statement.where(DailySnapshot.repository_full_name == repository_full_name)
    if since is not None:
        statement = statement.where(DailySnapshot.snapshot_date >= since)
    statement = statement.order_by(
        DailySnapshot.snapshot_date.desc(), DailySnapshot.repository_full_name
    ).limit(limit)
    return list(session.scalars(statement).all())
