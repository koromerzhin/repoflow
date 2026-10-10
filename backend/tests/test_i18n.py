"""Tests de l'internationalisation des messages d'erreur de l'API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

REPO = "acme/web-app"

_BLOCKER_CODES = {"not_open", "draft", "conflict", "not_approved", "check_not_success"}


def _not_found(accept_language: str | None) -> dict[str, object]:
    headers = {"Accept-Language": accept_language} if accept_language else None
    response = client.get(
        "/api/v1/pull-requests/999",
        params={"repository": REPO},
        headers=headers,
    )
    assert response.status_code == 404
    return response.json()["error"]


def test_error_message_french_by_default() -> None:
    error = _not_found(None)
    assert error["message"] == "Pull request #999 introuvable pour acme/web-app."


def test_error_message_english_with_accept_language() -> None:
    error = _not_found("en")
    assert error["message"] == "Pull request #999 not found for acme/web-app."


def test_locale_selection_from_quality_list() -> None:
    error = _not_found("en-US, en;q=0.8, fr;q=0.5")
    assert error["message"].startswith("Pull request #999 not found for")


def test_unknown_locale_falls_back_to_french() -> None:
    error = _not_found("de-DE")
    assert error["message"].startswith("Pull request #999 introuvable pour")


def test_validation_envelope_localized() -> None:
    response = client.post(
        "/api/v1/configs/repositories",
        json={},
        headers={"Accept-Language": "en"},
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["message"] == "The request is invalid."


def test_error_code_stable_across_languages() -> None:
    fr = _not_found(None)
    en = _not_found("en")
    assert fr["code"] == en["code"] == "pull_request_not_found"


def test_merge_blockers_localized() -> None:
    response = client.get(
        "/api/v1/pull-requests",
        params={"repository": "acme/web-app"},
        headers={"Accept-Language": "en"},
    )
    assert response.status_code == 200
    blockers = [
        blocker
        for item in response.json()["items"]
        for blocker in item["merge_eligibility"]["blockers"]
    ]
    assert blockers
    assert all(
        blocker["code"] in _BLOCKER_CODES and _is_english(blocker["message"])
        for blocker in blockers
    )


def _is_english(message: str) -> bool:
    return not any(letter in message for letter in "àâéèêëîïôûùç")
