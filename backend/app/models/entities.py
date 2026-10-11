"""Modèles ORM de RepoFlow.

Ces tables stockent la configuration locale (dépôts suivis, règles
d'automatisation), l'historique d'audit et les agrégats quotidiens. Les
données GitHub détaillées ne sont pas persistées : seuls des agrégats par
dépôt le sont, pour suivre leur évolution.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class RepositoryConfig(TimestampMixin, Base):
    """Dépôt GitHub suivi par l'application."""

    __tablename__ = "repository_configs"
    __table_args__ = (UniqueConstraint("full_name", name="uq_repository_full_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(255), default="main", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    rules: Mapped[list[AutomationRule]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )


class AutomationRule(TimestampMixin, Base):
    """Règle d'automatisation attachée à un dépôt.

    ``auto_merge_enabled`` vaut ``False`` par défaut : la fusion automatique
    n'est jamais activée implicitement.
    """

    __tablename__ = "automation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repository_configs.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    branch_pattern: Mapped[str] = mapped_column(String(255), default="*", nullable=False)
    auto_merge_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    required_approvals: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    require_green_checks: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    repository: Mapped[RepositoryConfig] = relationship(back_populates="rules")


class AuditEvent(TimestampMixin, Base):
    """Entrée de journal d'audit, immuable par convention."""

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    repository_full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pull_request_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor: Mapped[str] = mapped_column(String(255), default="system", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )


class SystemSetting(TimestampMixin, Base):
    """Réglage persistant modifiable à chaud (ex. arrêt d'urgence).

    Permet à l'arrêt d'urgence de survivre à un redémarrage, sans redéployer.
    """

    __tablename__ = "system_settings"
    __table_args__ = (UniqueConstraint("key", name="uq_system_settings_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class DailySnapshot(TimestampMixin, Base):
    """Agrégat quotidien par dépôt, alimenté par le worker.

    Une seule ligne par dépôt et par jour (UTC) : la passe du worker met à
    jour la ligne du jour au lieu d'en créer une nouvelle. Aucune donnée
    GitHub détaillée n'est copiée, seulement les compteurs.
    """

    __tablename__ = "daily_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "repository_full_name", "snapshot_date", name="uq_daily_snapshots_repo_date"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repository_full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_source: Mapped[str] = mapped_column(String(50), nullable=False, default="demo")
    open_pull_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pull_requests_ready_to_merge: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pull_requests_with_failing_checks: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    pull_requests_pending_checks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    open_issues: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
