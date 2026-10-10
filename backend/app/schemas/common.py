"""Schémas Pydantic communs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DataSource(StrEnum):
    """Origine des données renvoyées par l'API."""

    DEMO = "demo"
    GITHUB = "github"


class ProviderInfo(BaseModel):
    """Informations sur le fournisseur de données actif."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Identifiant du fournisseur (demo, github).")
    is_demo: bool = Field(description="Vrai si les données sont fictives.")
    requires_token: bool = Field(description="Vrai si un token d'accès est requis.")


class ErrorDetail(BaseModel):
    """Corps d'une réponse d'erreur."""

    code: str
    message: str
