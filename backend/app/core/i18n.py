"""Internationalisation des messages renvoyés par l'API.

Les codes d'erreur restent neutres (stables, indépendants de la langue) ;
seuls les messages sont localisés. La langue est déterminée par l'en-tête
``Accept-Language`` de la requête, avec repli sur le français.
"""

from __future__ import annotations

from starlette.requests import Request

SUPPORTED_LOCALES: tuple[str, ...] = ("fr", "en")
DEFAULT_LOCALE = "fr"

#: Catalogue des messages par code d'erreur.
#: Les motifs ``{param}`` sont interpolés avec les paramètres portés par
#: l'exception ; ``{x!r}`` utilise le ``repr`` de Python (c.-à-d. avec guillemets).
MESSAGES: dict[str, dict[str, str]] = {
    "github_token_missing": {
        "fr": "REPOFLOW_GITHUB_TOKEN doit être défini pour le fournisseur « github ».",
        "en": "REPOFLOW_GITHUB_TOKEN must be set for the 'github' provider.",
    },
    "unknown_provider": {
        "fr": "Fournisseur inconnu : {name!r}.",
        "en": "Unknown provider: {name!r}.",
    },
    "repository_config_not_found": {
        "fr": "Dépôt suivi #{config_id} introuvable.",
        "en": "Tracked repository #{config_id} not found.",
    },
    "repository_config_exists": {
        "fr": "Le dépôt {full_name} est déjà suivi.",
        "en": "Repository {full_name} is already tracked.",
    },
    "automation_rule_not_found": {
        "fr": "Règle #{rule_id} introuvable.",
        "en": "Rule #{rule_id} not found.",
    },
    "invalid_repository": {
        "fr": "Nom de dépôt invalide ; format attendu : « owner/name ».",
        "en": 'Invalid repository name; expected format: "owner/name".',
    },
    "github_resource_not_found": {
        "fr": "Ressource GitHub introuvable.",
        "en": "GitHub resource not found.",
    },
    "github_unavailable": {
        "fr": "Erreur côté GitHub, réessayez plus tard.",
        "en": "Error on GitHub side, please try again later.",
    },
    "github_bad_request": {
        "fr": "Requête GitHub invalide (statut {status_code}).",
        "en": "Invalid GitHub request (status {status_code}).",
    },
    "pull_request_not_found": {
        "fr": "Pull request #{number} introuvable pour {repository_full_name}.",
        "en": "Pull request #{number} not found for {repository_full_name}.",
    },
    "validation_error": {
        "fr": "La requête est invalide.",
        "en": "The request is invalid.",
    },
    "internal_error": {
        "fr": "Une erreur interne est survenue.",
        "en": "An internal error occurred.",
    },
    "blocker.not_open": {
        "fr": "La pull request n'est pas ouverte.",
        "en": "The pull request is not open.",
    },
    "blocker.draft": {
        "fr": "Une pull request en brouillon ne peut pas être fusionnée.",
        "en": "A draft pull request cannot be merged.",
    },
    "blocker.conflict": {
        "fr": "La pull request présente des conflits de fusion.",
        "en": "The pull request has merge conflicts.",
    },
    "blocker.not_approved": {
        "fr": "Approbations insuffisantes : {approved}/{required} requises.",
        "en": "Not enough approvals: {approved}/{required} required.",
    },
    "blocker.check_not_success": {
        "fr": "Le check obligatoire « {name} » n'est pas réussi.",
        "en": 'The required check "{name}" did not succeed.',
    },
    # Messages du journal d'audit. Le code est le ``event_type`` et les
    # paramètres proviennent du ``payload`` persisté (voir audit_service).
    "audit.analysis": {
        "fr": "Analyse terminée : {pull_requests} PR, {eligible} éligible(s), {merged} fusion(s).",
        "en": "Analysis finished: {pull_requests} PR(s), {eligible} eligible, {merged} merged.",
    },
    "audit.analysis_error": {
        "fr": "Analyse impossible pour PR #{number} : {error_message}",
        "en": "Analysis impossible for PR #{number}: {error_message}",
    },
    "audit.merge_blocked": {
        "fr": "PR #{number} non éligible ({count} blocage(s)).",
        "en": "PR #{number} not eligible ({count} blocker(s)).",
    },
    "audit.merge_skipped": {
        "fr": "Fusion de PR #{number} différée ({reason}).",
        "en": "Merge of PR #{number} deferred ({reason}).",
    },
    "audit.merge_succeeded": {
        "fr": "PR #{number} fusionnée (squash).",
        "en": "PR #{number} merged (squash).",
    },
    "audit.merge_failed": {
        "fr": "Échec de fusion de PR #{number} : {error_message}",
        "en": "Failed to merge PR #{number}: {error_message}",
    },
    "audit.reason.kill_switch": {
        "fr": "arrêt d'urgence actif",
        "en": "emergency stop engaged",
    },
    "audit.reason.global_disabled": {
        "fr": "fusion automatique désactivée globalement",
        "en": "auto-merge disabled globally",
    },
    "audit.reason.rule_disabled": {
        "fr": "fusion automatique désactivée sur la règle",
        "en": "auto-merge disabled on the rule",
    },
}


def pick_locale(accept_language: str) -> str:
    """Retourne la première langue supportée décrite dans l'en-tête."""
    for part in accept_language.split(","):
        tag = part.strip().split(";", 1)[0].strip().lower()
        locale = tag.split("-", 1)[0]
        if locale in SUPPORTED_LOCALES:
            return locale
    return DEFAULT_LOCALE


def get_locale(request: Request) -> str:
    """Détermine la langue de la requête."""

    return pick_locale(request.headers.get("accept-language", ""))


def render_message(
    code: str,
    locale: str,
    params: dict[str, object] | None,
    fallback: str,
) -> str:
    """Localise un message d'erreur, avec repli sur le message d'origine."""

    template = MESSAGES.get(code, {}).get(locale)
    if template is None:
        return fallback
    if not params:
        return template
    try:
        return template.format(**params)
    except (KeyError, IndexError, ValueError):
        return fallback
