"""Dépendances FastAPI partagées."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.integrations.github.factory import get_provider
from app.integrations.github.provider import Provider

SettingsDep = Annotated[Settings, Depends(get_settings)]
ProviderDep = Annotated[Provider, Depends(get_provider)]
DbDep = Annotated[Session, Depends(get_db)]
