"""Dépendances FastAPI partagées."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.integrations.github.factory import get_provider
from app.integrations.github.provider import Provider

SettingsDep = Annotated[Settings, Depends(get_settings)]
ProviderDep = Annotated[Provider, Depends(get_provider)]
