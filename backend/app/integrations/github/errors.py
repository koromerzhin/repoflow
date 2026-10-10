"""Erreurs spécifiques à l'intégration GitHub.

Ces erreurs héritent de :class:`app.core.errors.ProviderError` afin d'être
exposées proprement par la couche API. Aucun message ne doit contenir de
token ni d'en-tête d'authentification.
"""

from __future__ import annotations

from app.core.errors import ProviderError


class GitHubError(ProviderError):
    """Erreur générique du fournisseur GitHub."""


class GitHubAuthError(GitHubError):
    """Authentification refusée (token invalide, expiré ou absent)."""

    status_code = 502
    code = "github_auth_error"


class GitHubPermissionError(GitHubError):
    """Permissions insuffisantes pour la ressource demandée."""

    status_code = 502
    code = "github_permission_error"


class GitHubRateLimitError(GitHubError):
    """Limite de requêtes GitHub atteinte."""

    status_code = 503
    code = "github_rate_limited"

    def __init__(self, message: str, *, reset_at: int | None = None) -> None:
        super().__init__(message)
        self.reset_at = reset_at
