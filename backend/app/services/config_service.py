"""Service de gestion des dépôts suivis et des règles d'automatisation.

Toute la validation métier et l'accès base vivent ici. Les routes ne font que
sérialiser les entrées/sorties.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import ConflictError, NotFoundError
from app.models.entities import AutomationRule, RepositoryConfig
from app.schemas.config import (
    AutomationRuleCreate,
    AutomationRuleRead,
    AutomationRuleUpdate,
    RepositoryConfigCreate,
    RepositoryConfigRead,
    RepositoryConfigUpdate,
)


def rule_to_schema(rule: AutomationRule) -> AutomationRuleRead:
    """Convertit une règle ORM en schéma d'API."""
    return AutomationRuleRead(
        id=rule.id,
        repository_id=rule.repository_id,
        name=rule.name,
        branch_pattern=rule.branch_pattern,
        auto_merge_enabled=rule.auto_merge_enabled,
        required_approvals=rule.required_approvals,
        require_green_checks=rule.require_green_checks,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def config_to_schema(config: RepositoryConfig) -> RepositoryConfigRead:
    """Convertit un dépôt suivi ORM en schéma d'API, règles incluses."""
    return RepositoryConfigRead(
        id=config.id,
        full_name=config.full_name,
        owner=config.owner,
        name=config.name,
        default_branch=config.default_branch,
        enabled=config.enabled,
        rules=[rule_to_schema(rule) for rule in config.rules],
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def list_repository_configs(session: Session) -> list[RepositoryConfig]:
    """Liste les dépôts suivis, règles incluses, triés par nom."""
    statement = (
        select(RepositoryConfig)
        .options(selectinload(RepositoryConfig.rules))
        .order_by(RepositoryConfig.full_name)
    )
    return list(session.scalars(statement).all())


def get_repository_config(session: Session, config_id: int) -> RepositoryConfig:
    """Retourne un dépôt suivi ou lève ``NotFoundError``."""
    config = session.get(RepositoryConfig, config_id)
    if config is None:
        raise NotFoundError(
            f"Dépôt suivi #{config_id} introuvable.",
            code="repository_config_not_found",
            params={"config_id": config_id},
        )
    return config


def create_repository_config(session: Session, payload: RepositoryConfigCreate) -> RepositoryConfig:
    """Crée un dépôt suivi ; refuse les doublons de ``full_name``."""
    existing = session.scalar(
        select(RepositoryConfig).where(RepositoryConfig.full_name == payload.full_name)
    )
    if existing is not None:
        raise ConflictError(
            f"Le dépôt {payload.full_name} est déjà suivi.",
            code="repository_config_exists",
            params={"full_name": payload.full_name},
        )

    owner, _, name = payload.full_name.partition("/")
    config = RepositoryConfig(
        full_name=payload.full_name,
        owner=owner,
        name=name,
        default_branch=payload.default_branch,
        enabled=payload.enabled,
    )
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


def update_repository_config(
    session: Session, config_id: int, payload: RepositoryConfigUpdate
) -> RepositoryConfig:
    """Met à jour partiellement un dépôt suivi."""
    config = get_repository_config(session, config_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(config, field, value)
    session.commit()
    session.refresh(config)
    return config


def delete_repository_config(session: Session, config_id: int) -> None:
    """Supprime un dépôt suivi et ses règles (cascade)."""
    config = get_repository_config(session, config_id)
    session.delete(config)
    session.commit()


def list_rules(session: Session, config_id: int) -> list[AutomationRule]:
    """Liste les règles d'un dépôt suivi."""
    config = get_repository_config(session, config_id)
    return list(config.rules)


def create_rule(session: Session, config_id: int, payload: AutomationRuleCreate) -> AutomationRule:
    """Crée une règle rattachée à un dépôt suivi."""
    config = get_repository_config(session, config_id)
    rule = AutomationRule(
        repository_id=config.id,
        name=payload.name,
        branch_pattern=payload.branch_pattern,
        auto_merge_enabled=payload.auto_merge_enabled,
        required_approvals=payload.required_approvals,
        require_green_checks=payload.require_green_checks,
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def get_rule(session: Session, rule_id: int) -> AutomationRule:
    """Retourne une règle ou lève ``NotFoundError``."""
    rule = session.get(AutomationRule, rule_id)
    if rule is None:
        raise NotFoundError(
            f"Règle #{rule_id} introuvable.",
            code="automation_rule_not_found",
            params={"rule_id": rule_id},
        )
    return rule


def update_rule(session: Session, rule_id: int, payload: AutomationRuleUpdate) -> AutomationRule:
    """Met à jour partiellement une règle."""
    rule = get_rule(session, rule_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(rule, field, value)
    session.commit()
    session.refresh(rule)
    return rule


def delete_rule(session: Session, rule_id: int) -> None:
    """Supprime une règle."""
    rule = get_rule(session, rule_id)
    session.delete(rule)
    session.commit()
