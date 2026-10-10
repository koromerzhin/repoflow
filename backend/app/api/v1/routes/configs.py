"""Routes de configuration des dépôts suivis et des règles d'automatisation."""

from __future__ import annotations

from fastapi import APIRouter, Path, Response, status

from app.api.deps import DbDep
from app.schemas.config import (
    AutomationRuleCreate,
    AutomationRuleListResponse,
    AutomationRuleRead,
    AutomationRuleUpdate,
    RepositoryConfigCreate,
    RepositoryConfigListResponse,
    RepositoryConfigRead,
    RepositoryConfigUpdate,
)
from app.services import config_service

router = APIRouter(prefix="/configs", tags=["configs"])


@router.get("/repositories", response_model=RepositoryConfigListResponse)
async def list_repository_configs(session: DbDep) -> RepositoryConfigListResponse:
    """Liste les dépôts suivis et leurs règles."""
    configs = config_service.list_repository_configs(session)
    items = [config_service.config_to_schema(config) for config in configs]
    return RepositoryConfigListResponse(items=items, total=len(items))


@router.post(
    "/repositories",
    response_model=RepositoryConfigRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_repository_config(
    session: DbDep, payload: RepositoryConfigCreate
) -> RepositoryConfigRead:
    """Ajoute un dépôt suivi (format ``owner/name``)."""
    config = config_service.create_repository_config(session, payload)
    return config_service.config_to_schema(config)


@router.get("/repositories/{config_id}", response_model=RepositoryConfigRead)
async def get_repository_config(
    session: DbDep, config_id: int = Path(ge=1)
) -> RepositoryConfigRead:
    """Détail d'un dépôt suivi."""
    config = config_service.get_repository_config(session, config_id)
    return config_service.config_to_schema(config)


@router.patch("/repositories/{config_id}", response_model=RepositoryConfigRead)
async def update_repository_config(
    session: DbDep, payload: RepositoryConfigUpdate, config_id: int = Path(ge=1)
) -> RepositoryConfigRead:
    """Met à jour un dépôt suivi."""
    config = config_service.update_repository_config(session, config_id, payload)
    return config_service.config_to_schema(config)


@router.delete("/repositories/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository_config(session: DbDep, config_id: int = Path(ge=1)) -> Response:
    """Supprime un dépôt suivi et ses règles."""
    config_service.delete_repository_config(session, config_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/repositories/{config_id}/rules",
    response_model=AutomationRuleListResponse,
)
async def list_rules(session: DbDep, config_id: int = Path(ge=1)) -> AutomationRuleListResponse:
    """Liste les règles d'automatisation d'un dépôt suivi."""
    rules = config_service.list_rules(session, config_id)
    items = [config_service.rule_to_schema(rule) for rule in rules]
    return AutomationRuleListResponse(items=items, total=len(items))


@router.post(
    "/repositories/{config_id}/rules",
    response_model=AutomationRuleRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_rule(
    session: DbDep, payload: AutomationRuleCreate, config_id: int = Path(ge=1)
) -> AutomationRuleRead:
    """Crée une règle pour un dépôt suivi."""
    rule = config_service.create_rule(session, config_id, payload)
    return config_service.rule_to_schema(rule)


@router.patch("/rules/{rule_id}", response_model=AutomationRuleRead)
async def update_rule(
    session: DbDep, payload: AutomationRuleUpdate, rule_id: int = Path(ge=1)
) -> AutomationRuleRead:
    """Met à jour une règle."""
    rule = config_service.update_rule(session, rule_id, payload)
    return config_service.rule_to_schema(rule)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(session: DbDep, rule_id: int = Path(ge=1)) -> Response:
    """Supprime une règle."""
    config_service.delete_rule(session, rule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
