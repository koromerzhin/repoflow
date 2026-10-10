"""Schémas de configuration des dépôts suivis et des règles d'automatisation.

La validation est stricte : ces schémas sont la seule porte d'entrée des
données de configuration, jamais le client.
"""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

FULL_NAME_PATTERN = re.compile(r"^[\w.-]+/[\w.-]+$")


class RepositoryConfigCreate(BaseModel):
    """Entrée de création d'un dépôt suivi."""

    full_name: str = Field(description="Format ``owner/name``.", max_length=255)
    default_branch: str = Field(default="main", min_length=1, max_length=255)
    enabled: bool = True

    @field_validator("full_name")
    @classmethod
    def _validate_full_name(cls, value: str) -> str:
        value = value.strip()
        if not FULL_NAME_PATTERN.match(value):
            raise ValueError("Le nom du dépôt doit respecter le format « owner/name ».")
        return value

    @field_validator("default_branch")
    @classmethod
    def _validate_branch(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("La branche par défaut ne peut pas être vide.")
        return value


class RepositoryConfigUpdate(BaseModel):
    """Entrée de mise à jour partielle d'un dépôt suivi."""

    default_branch: str | None = Field(default=None, min_length=1, max_length=255)
    enabled: bool | None = None

    @field_validator("default_branch")
    @classmethod
    def _validate_branch(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("La branche par défaut ne peut pas être vide.")
        return value


class AutomationRuleCreate(BaseModel):
    """Entrée de création d'une règle d'automatisation."""

    name: str = Field(min_length=1, max_length=255)
    branch_pattern: str = Field(default="*", min_length=1, max_length=255)
    auto_merge_enabled: bool = False
    required_approvals: int = Field(default=1, ge=0, le=10)
    require_green_checks: bool = True

    @field_validator("name", "branch_pattern")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Ce champ ne peut pas être vide.")
        return value


class AutomationRuleUpdate(BaseModel):
    """Entrée de mise à jour partielle d'une règle d'automatisation."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    branch_pattern: str | None = Field(default=None, min_length=1, max_length=255)
    auto_merge_enabled: bool | None = None
    required_approvals: int | None = Field(default=None, ge=0, le=10)
    require_green_checks: bool | None = None

    @field_validator("name", "branch_pattern")
    @classmethod
    def _not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Ce champ ne peut pas être vide.")
        return value


class AutomationRuleRead(BaseModel):
    """Règle d'automatisation telle que renvoyée par l'API."""

    id: int
    repository_id: int
    name: str
    branch_pattern: str
    auto_merge_enabled: bool
    required_approvals: int
    require_green_checks: bool
    created_at: datetime
    updated_at: datetime


class RepositoryConfigRead(BaseModel):
    """Dépôt suivi tel que renvoyé par l'API."""

    id: int
    full_name: str
    owner: str
    name: str
    default_branch: str
    enabled: bool
    rules: list[AutomationRuleRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class RepositoryConfigListResponse(BaseModel):
    """Réponse de ``GET /api/v1/configs/repositories``."""

    items: list[RepositoryConfigRead]
    total: int = Field(ge=0)


class AutomationRuleListResponse(BaseModel):
    """Réponse de ``GET /api/v1/configs/repositories/{id}/rules``."""

    items: list[AutomationRuleRead]
    total: int = Field(ge=0)
