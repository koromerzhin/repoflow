"""Tests de l'authentification par jeton porteur."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import AuthMiddleware

_TOKEN = "s3cret-token"


def _mini_app(*, prefixes: tuple[str, ...] = ("/api/v1",)) -> FastAPI:
    app = FastAPI()
    app.add_middleware(AuthMiddleware, token=_TOKEN, protected_prefixes=prefixes)

    @app.get("/api/v1/resource")
    def resource() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/api/health/live")
    def live() -> dict[str, bool]:
        return {"ok": True}

    return app


def test_route_protegee_sans_jeton_renvoie_401() -> None:
    response = TestClient(_mini_app()).get("/api/v1/resource")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_route_protegee_avec_jeton_valide() -> None:
    response = TestClient(_mini_app()).get(
        "/api/v1/resource", headers={"Authorization": f"Bearer {_TOKEN}"}
    )
    assert response.status_code == 200


def test_jeton_invalide_renvoie_401() -> None:
    response = TestClient(_mini_app()).get(
        "/api/v1/resource", headers={"Authorization": "Bearer mauvais"}
    )
    assert response.status_code == 401


def test_scheme_non_bearer_refuse() -> None:
    response = TestClient(_mini_app()).get(
        "/api/v1/resource", headers={"Authorization": f"Basic {_TOKEN}"}
    )
    assert response.status_code == 401


def test_sondes_non_protegees() -> None:
    assert TestClient(_mini_app()).get("/api/health/live").status_code == 200


def test_message_localise_en() -> None:
    response = TestClient(_mini_app()).get(
        "/api/v1/resource", headers={"Accept-Language": "en-US,en;q=0.9"}
    )
    assert "Authentication required" in response.json()["error"]["message"]


def test_prefixe_hors_perimetre_laisse_passer() -> None:
    client = TestClient(_mini_app(prefixes=("/api/v2",)))
    assert client.get("/api/v1/resource").status_code == 200


def test_auth_enabled_selon_jeton() -> None:
    assert Settings(api_token=None).auth_enabled is False
    assert Settings(api_token="").auth_enabled is False
    assert Settings(api_token="jeton").auth_enabled is True
