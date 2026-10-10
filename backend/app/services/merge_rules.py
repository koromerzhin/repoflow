"""Règles métier d'éligibilité à la fusion.

IMPORTANT : ces règles fournissent une évaluation en lecture seule. Aucune
fusion n'est déclenchée par ce module. Celui-ci sera étendu par un worker
d'automatisation plus tard, sans changer les règles elles-mêmes.

Un check CI réussi n'est jamais, à lui seul, une autorisation de fusionner.
"""

from __future__ import annotations

from app.integrations.github.types import CheckRecord, PullRequestRecord
from app.schemas.pull_request import (
    CheckState,
    MergeBlocker,
    MergeEligibility,
    PullRequestState,
    ReviewDecision,
)


def aggregate_checks_state(checks: list[CheckRecord]) -> CheckState:
    """Agrège l'état d'une liste de checks.

    Règles :
    - un seul échec => ``failure`` ;
    - sinon un seul ``pending`` => ``pending`` ;
    - sinon un seul ``unknown`` => ``unknown`` ;
    - uniquement des ``success`` => ``success`` ;
    - liste vide => ``unknown``.
    """
    if not checks:
        return CheckState.UNKNOWN
    if any(check.state == CheckState.FAILURE for check in checks):
        return CheckState.FAILURE
    if any(check.state == CheckState.PENDING for check in checks):
        return CheckState.PENDING
    if any(check.state == CheckState.UNKNOWN for check in checks):
        return CheckState.UNKNOWN
    return CheckState.SUCCESS


def evaluate_merge_eligibility(pr: PullRequestRecord) -> MergeEligibility:
    """Évalue (sans exécuter) si la pull request remplit les conditions.

    Ne considère jamais un check échoué, en cours ou inconnu comme un succès.
    """
    blockers: list[MergeBlocker] = []

    if pr.state != PullRequestState.OPEN:
        blockers.append(MergeBlocker(code="not_open", message="La pull request n'est pas ouverte."))
    if pr.is_draft:
        blockers.append(
            MergeBlocker(
                code="draft",
                message="Une pull request en brouillon ne peut pas être fusionnée.",
            )
        )
    if not pr.mergeable:
        blockers.append(
            MergeBlocker(
                code="conflict",
                message="La pull request présente des conflits de fusion.",
            )
        )
    if pr.review_decision != ReviewDecision.APPROVED:
        blockers.append(
            MergeBlocker(
                code="not_approved",
                message="Les approbations requises ne sont pas réunies.",
            )
        )
    for check in pr.checks:
        if not check.required:
            continue
        if check.state != CheckState.SUCCESS:
            blockers.append(
                MergeBlocker(
                    code="check_not_success",
                    message=f"Le check obligatoire « {check.name} » n'est pas réussi.",
                )
            )

    return MergeEligibility(eligible=len(blockers) == 0, blockers=blockers)
