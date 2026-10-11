"""Moteur d'analyse des pull requests et de décision de fusion contrôlée.

Ce module applique les règles d'automatisation configurées. Il n'exécute une
fusion que si **toutes** les conditions suivantes sont réunies :

1. la règle correspond au dépôt et à la branche cible ;
2. la pull request est éligible (ni brouillon, ni en conflit, checks exigés
   réussis, approbations suffisantes) ;
3. ``auto_merge_enabled`` vaut vrai **sur la règle** ;
4. ``REPOFLOW_AUTO_MERGE_ENABLED_GLOBALLY`` vaut vrai ;
5. l'arrêt d'urgence global est désengagé.

Par défaut, aucune fusion n'a donc lieu.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.logging import get_logger
from app.integrations.github.provider import Provider
from app.integrations.github.types import PullRequestDetailRecord
from app.models.entities import AutomationRule, RepositoryConfig
from app.schemas.pull_request import MergeBlocker, MergeEligibility, PullRequestState
from app.services import audit_service, config_service, system_service
from app.services.merge_rules import count_approved_reviews, evaluate_merge_eligibility

logger = get_logger(__name__)


@dataclass
class AnalysisSummary:
    """Compteurs d'une exécution d'analyse."""

    repositories: int = 0
    pull_requests: int = 0
    eligible: int = 0
    blocked: int = 0
    merged: int = 0
    skipped: int = 0
    errors: int = 0
    details: list[str] = field(default_factory=list)


def match_rule(rules: list[AutomationRule], target_branch: str) -> AutomationRule | None:
    """Retourne la première règle dont le motif correspond à la branche cible."""
    for rule in sorted(rules, key=lambda item: item.id):
        if fnmatch.fnmatchcase(target_branch, rule.branch_pattern):
            return rule
    return None


def evaluate_pr_for_rule(
    pr: PullRequestDetailRecord,
    rule: AutomationRule,
    *,
    default_branch: str,
) -> MergeEligibility:
    """Évalue une pull request au regard d'une règle donnée.

    Une restriction supplémentaire est appliquée : la fusion n'est envisagée
    que vers la branche par défaut du dépôt (protection de branche prudente).
    """
    approved = count_approved_reviews(pr.reviews)
    eligibility = evaluate_merge_eligibility(
        pr,
        required_approvals=rule.required_approvals,
        require_green_checks=rule.require_green_checks,
        approved_count=approved,
    )
    blockers: list[MergeBlocker] = list(eligibility.blockers)
    if pr.target_branch != default_branch:
        blockers.append(
            MergeBlocker(
                code="protected_branch",
                message=(
                    "La branche cible n'est pas la branche par défaut du dépôt ; "
                    "fusion automatique refusée."
                ),
            )
        )
    return MergeEligibility(eligible=not blockers, blockers=blockers)


def merge_gating_reason(
    session: Session,
    settings: Settings,
    rule: AutomationRule,
) -> str | None:
    """Retourne le motif de blocage d'une fusion, ou ``None`` si autorisée."""
    if system_service.is_kill_switch_engaged(session):
        return "kill_switch"
    if not settings.auto_merge_enabled_globally:
        return "global_disabled"
    if not rule.auto_merge_enabled:
        return "rule_disabled"
    return None


async def _analyze_repository(
    session: Session,
    provider: Provider,
    settings: Settings,
    config: RepositoryConfig,
    summary: AnalysisSummary,
) -> None:
    rules = list(config.rules)
    pull_requests = await provider.list_pull_requests(config.full_name)
    for pr in pull_requests:
        if pr.state != PullRequestState.OPEN:
            continue
        summary.pull_requests += 1
        rule = match_rule(rules, pr.target_branch)
        if rule is None:
            continue

        try:
            detail = await provider.get_pull_request(config.full_name, pr.number)
        except AppError as exc:
            summary.errors += 1
            summary.details.append(f"{config.full_name}#{pr.number}: {exc.message}")
            audit_service.record(
                session,
                event_type="analysis_error",
                message=f"Analyse impossible pour PR #{pr.number} : {exc.message}",
                repository_full_name=config.full_name,
                pull_request_number=pr.number,
                payload={
                    "rule_id": rule.id,
                    "error": exc.code,
                    "error_message": exc.message,
                },
            )
            continue

        eligibility = evaluate_pr_for_rule(detail, rule, default_branch=config.default_branch)
        if not eligibility.eligible:
            summary.blocked += 1
            if rule.auto_merge_enabled:
                audit_service.record(
                    session,
                    event_type="merge_blocked",
                    message=(
                        f"PR #{pr.number} non éligible ({len(eligibility.blockers)} blocage(s))."
                    ),
                    repository_full_name=config.full_name,
                    pull_request_number=pr.number,
                    payload={"blockers": [blocker.code for blocker in eligibility.blockers]},
                )
            continue

        summary.eligible += 1
        if not rule.auto_merge_enabled:
            continue

        reason = merge_gating_reason(session, settings, rule)
        if reason is not None:
            summary.skipped += 1
            audit_service.record(
                session,
                event_type="merge_skipped",
                message=f"Fusion de PR #{pr.number} différée ({reason}).",
                repository_full_name=config.full_name,
                pull_request_number=pr.number,
                payload={"reason": reason, "rule_id": rule.id},
            )
            continue

        result = await provider.merge_pull_request(
            config.full_name, pr.number, merge_method="squash"
        )
        if result.merged:
            summary.merged += 1
            audit_service.record(
                session,
                event_type="merge_succeeded",
                message=f"PR #{pr.number} fusionnée (squash).",
                repository_full_name=config.full_name,
                pull_request_number=pr.number,
                payload={"sha": result.sha, "rule_id": rule.id},
            )
        else:
            summary.errors += 1
            summary.details.append(f"{config.full_name}#{pr.number}: {result.message}")
            audit_service.record(
                session,
                event_type="merge_failed",
                message=f"Échec de fusion de PR #{pr.number} : {result.message}",
                repository_full_name=config.full_name,
                pull_request_number=pr.number,
                payload={"rule_id": rule.id, "error_message": result.message},
            )


async def run_analysis(
    session: Session,
    provider: Provider,
    settings: Settings | None = None,
) -> AnalysisSummary:
    """Analyse les dépôts suivis et applique les règles d'automatisation."""
    settings = settings or get_settings()
    summary = AnalysisSummary()

    configs = [
        config for config in config_service.list_repository_configs(session) if config.enabled
    ]
    summary.repositories = len(configs)

    for config in configs:
        try:
            await _analyze_repository(session, provider, settings, config, summary)
        except AppError as exc:
            summary.errors += 1
            summary.details.append(f"{config.full_name}: {exc.message}")
            logger.warning("Analyse échouée pour %s : %s", config.full_name, exc.message)

    audit_service.record(
        session,
        event_type="analysis",
        message=(
            f"Analyse terminée : {summary.pull_requests} PR, "
            f"{summary.eligible} éligible(s), {summary.merged} fusion(s)."
        ),
        payload={
            "repositories": summary.repositories,
            "pull_requests": summary.pull_requests,
            "eligible": summary.eligible,
            "blocked": summary.blocked,
            "merged": summary.merged,
            "skipped": summary.skipped,
            "errors": summary.errors,
        },
    )
    session.commit()
    return summary
