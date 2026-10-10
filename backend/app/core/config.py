"""Configuration centralisée de RepoFlow, chargée depuis l'environnement."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ProviderName = Literal["demo", "github"]


class Settings(BaseSettings):
    """Paramètres applicatifs.

    Toutes les variables peuvent être surchargées via l'environnement en
    utilisant le préfixe ``REPOFLOW_`` (ex. ``REPOFLOW_DATABASE_URL``).
    Aucune valeur secrète n'a de défaut.
    """

    model_config = SettingsConfigDict(
        env_prefix="REPOFLOW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "RepoFlow"
    version: str = "0.1.0"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    api_v1_prefix: str = "/api/v1"
    # ``NoDecode`` : on accepte une liste séparée par des virgules plutôt que
    # du JSON, décodée par le validateur ci-dessous.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    database_url: str = "sqlite+pysqlite:///./repoflow.db"
    auto_create_tables: bool = True

    # Durée de mise en cache mémoire des données du fournisseur (secondes).
    # 0 désactive le cache. Le cache est invalidé par ``?refresh=true``.
    cache_ttl_seconds: int = Field(default=30, ge=0)

    # Intégration GitHub.
    # ``demo`` n'exige aucun token : des données fictives sont servies.
    # ``github`` nécessite un token et interroge l'API GitHub réelle.
    github_provider: ProviderName = "demo"
    github_token: SecretStr | None = None
    github_api_url: str = "https://api.github.com"
    github_timeout: float = 30.0
    github_per_page: int = Field(default=100, ge=1, le=100)
    github_max_pages: int = Field(default=10, ge=1, le=100)

    # La fusion automatique est désactivée par défaut et ne doit pas être
    # activée tant que les garde-fous serveur ne sont pas en place.
    auto_merge_enabled_globally: bool = False
    kill_switch_engaged: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_demo(self) -> bool:
        return self.github_provider == "demo"


@lru_cache
def get_settings() -> Settings:
    """Retourne l'instance de configuration mise en cache."""
    return Settings()
