"""Tests de la route du journal d'audit."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.services import audit_service


@pytest.fixture
def session() -> Iterator[Session]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def _seed(session: Session) -> None:
    audit_service.record(
        session,
        event_type="merge_succeeded",
        message="PR #142 fusionnée",
        repository_full_name="acme/web-app",
        pull_request_number=142,
        payload={"sha": "abc"},
    )
    audit_service.record(
        session,
        event_type="merge_blocked",
        message="PR #138 non éligible",
        repository_full_name="acme/api-gateway",
        pull_request_number=138,
    )
    session.commit()


def test_liste_vide(client: TestClient) -> None:
    response = client.get("/api/v1/audit")
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "next_cursor": None}


def test_liste_et_ordre(client: TestClient, session: Session) -> None:
    _seed(session)

    response = client.get("/api/v1/audit")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert len(payload["items"]) == 2
    first = payload["items"][0]
    assert first["event_type"] == "merge_blocked"
    assert first["repository_full_name"] == "acme/api-gateway"
    assert first["actor"] == "system"


def test_pagination_par_curseur(client: TestClient, session: Session) -> None:
    _seed(session)

    first_page = client.get("/api/v1/audit", params={"limit": 1}).json()
    assert len(first_page["items"]) == 1
    assert first_page["next_cursor"] == first_page["items"][0]["id"]

    second_page = client.get(
        "/api/v1/audit", params={"limit": 1, "before_id": first_page["next_cursor"]}
    ).json()
    assert len(second_page["items"]) == 1
    assert second_page["items"][0]["id"] != first_page["items"][0]["id"]
    assert second_page["next_cursor"] == second_page["items"][0]["id"]

    third_page = client.get(
        "/api/v1/audit", params={"limit": 1, "before_id": second_page["next_cursor"]}
    ).json()
    assert third_page["items"] == []
    assert third_page["next_cursor"] is None


def test_curseur_sans_page_suivante(client: TestClient, session: Session) -> None:
    _seed(session)

    payload = client.get("/api/v1/audit", params={"limit": 5}).json()
    assert len(payload["items"]) == 2
    assert payload["next_cursor"] is None


def test_filtre_par_type(client: TestClient, session: Session) -> None:
    _seed(session)

    payload = client.get("/api/v1/audit", params={"event_type": "merge_succeeded"}).json()
    assert payload["total"] == 1
    assert payload["items"][0]["payload"] == {"sha": "abc"}


def test_filtre_par_depot(client: TestClient, session: Session) -> None:
    _seed(session)

    payload = client.get("/api/v1/audit", params={"repository": "acme/web-app"}).json()
    assert payload["total"] == 1
    assert payload["items"][0]["pull_request_number"] == 142


def test_limite_invalide(client: TestClient) -> None:
    assert client.get("/api/v1/audit", params={"limit": 0}).status_code == 422


def test_message_localise_en_francais(client: TestClient, session: Session) -> None:
    audit_service.record(
        session,
        event_type="analysis",
        message="Analyse terminée : 3 PR, 1 éligible(s), 1 fusion(s).",
        payload={
            "repositories": 1,
            "pull_requests": 3,
            "eligible": 1,
            "blocked": 0,
            "merged": 1,
            "skipped": 0,
            "errors": 0,
        },
    )
    session.commit()

    items = client.get("/api/v1/audit").json()["items"]
    assert items[0]["message"] == "Analyse terminée : 3 PR, 1 éligible(s), 1 fusion(s)."


def test_message_localise_en_anglais(client: TestClient, session: Session) -> None:
    audit_service.record(
        session,
        event_type="analysis",
        message="Analyse terminée : 3 PR, 1 éligible(s), 1 fusion(s).",
        payload={"pull_requests": 3, "eligible": 1, "merged": 1},
    )
    session.commit()

    items = client.get("/api/v1/audit", headers={"Accept-Language": "en"}).json()["items"]
    assert items[0]["message"] == "Analysis finished: 3 PR(s), 1 eligible, 1 merged."


def test_motif_de_diffusion_localise(client: TestClient, session: Session) -> None:
    audit_service.record(
        session,
        event_type="merge_skipped",
        message="Fusion de PR #7 différée (kill_switch).",
        repository_full_name="acme/web-app",
        pull_request_number=7,
        payload={"reason": "kill_switch", "rule_id": 3},
    )
    session.commit()

    fr = client.get("/api/v1/audit").json()["items"][0]["message"]
    assert fr == "Fusion de PR #7 différée (arrêt d'urgence actif)."

    en = client.get("/api/v1/audit", headers={"Accept-Language": "en"}).json()["items"][0][
        "message"
    ]
    assert en == "Merge of PR #7 deferred (emergency stop engaged)."


def test_compteur_de_blocages_derive_du_payload(client: TestClient, session: Session) -> None:
    audit_service.record(
        session,
        event_type="merge_blocked",
        message="PR #5 non éligible (2 blocage(s)).",
        repository_full_name="acme/web-app",
        pull_request_number=5,
        payload={"blockers": ["not_approved", "check_not_success"]},
    )
    session.commit()

    items = client.get("/api/v1/audit").json()["items"]
    assert items[0]["message"] == "PR #5 non éligible (2 blocage(s))."


def test_repli_sur_message_persiste_si_parametre_absent(
    client: TestClient, session: Session
) -> None:
    audit_service.record(
        session,
        event_type="merge_failed",
        message="Échec de fusion de PR #9 : connexion perdue",
        repository_full_name="acme/web-app",
        pull_request_number=9,
        payload={"rule_id": 2},
    )
    session.commit()

    items = client.get("/api/v1/audit", headers={"Accept-Language": "en"}).json()["items"]
    assert items[0]["message"] == "Échec de fusion de PR #9 : connexion perdue"


def test_repli_sur_message_persiste_si_type_inconnu(session: Session) -> None:
    event = audit_service.record(
        session,
        event_type="evenement_inconnu",
        message="Message libre.",
        payload={"foo": "bar"},
    )
    session.commit()

    assert audit_service.localized_message(event, "en") == "Message libre."


def test_purge_retention(session: Session) -> None:
    ancienne = audit_service.record(
        session,
        event_type="analysis",
        message="Analyse ancienne",
    )
    ancienne.occurred_at = datetime.now(UTC) - timedelta(days=10)
    audit_service.record(session, event_type="analysis", message="Analyse récente")
    session.commit()

    purged = audit_service.purge_expired(session, retention_days=7)

    assert purged == 1
    remaining = audit_service.list_events(session)
    assert [event.message for event in remaining] == ["Analyse récente"]


def test_purge_desactivee(session: Session) -> None:
    audit_service.record(session, event_type="analysis", message="Analyse")
    session.commit()

    assert audit_service.purge_expired(session, retention_days=0) == 0
    assert audit_service.count_events(session) == 1
