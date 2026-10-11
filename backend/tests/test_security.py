"""Tests du durcissement sécurité (en-têtes HTTP et limitation de débit)."""

from __future__ import annotations

import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.security import (
    RateLimiter,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)


def _mini_app(
    *,
    rate_limited: bool = False,
    requests: int = 2,
    window_seconds: int = 60,
    secure: bool | None = None,
) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        enabled=rate_limited,
        requests=requests,
        window_seconds=window_seconds,
    )
    app.add_middleware(SecurityHeadersMiddleware, secure_request=lambda _: bool(secure))

    @app.get("/api/ping")
    def ping() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/docs")
    def docs() -> dict[str, str]:
        return {"page": "docs"}

    return app


def test_en_tetes_de_securite_sur_api() -> None:
    client = TestClient(_mini_app())
    response = client.get("/api/ping")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "Content-Security-Policy" in response.headers


def test_csp_absent_hors_api() -> None:
    client = TestClient(_mini_app())
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Content-Security-Policy" not in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_hsts_uniquement_en_fonction_du_contexte() -> None:
    client = TestClient(_mini_app(secure=False))
    assert "Strict-Transport-Security" not in client.get("/api/ping").headers
    secured_client = TestClient(_mini_app(secure=True))
    assert "Strict-Transport-Security" in secured_client.get("/api/ping").headers


async def test_limiteur_seuil_et_remise_a_zero() -> None:
    limiter = RateLimiter(requests=2, window_seconds=60)
    assert await limiter.allow("client-a") is True
    assert await limiter.allow("client-a") is True
    assert await limiter.allow("client-a") is False
    assert await limiter.remaining("client-a") == 0
    assert await limiter.allow("client-b") is True
    limiter.reset()
    assert await limiter.allow("client-a") is True


async def test_limiteur_fenetre_expire() -> None:
    limiter = RateLimiter(requests=1, window_seconds=1)
    assert await limiter.allow("client") is True
    assert await limiter.allow("client") is False
    time.sleep(1.05)
    assert await limiter.allow("client") is True


@pytest.mark.parametrize("requests", [0, -1])
def test_limiteur_rejette_parametres_invalides(requests: int) -> None:
    with pytest.raises(ValueError):
        RateLimiter(requests=requests, window_seconds=60)


def test_depassement_debit_retourne_429() -> None:
    client = TestClient(_mini_app(rate_limited=True, requests=2))
    assert client.get("/api/ping").status_code == 200
    assert client.get("/api/ping").status_code == 200
    response = client.get("/api/ping")
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
    assert response.json()["error"]["code"] == "rate_limit_exceeded"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_limitation_desactivee_transparente() -> None:
    client = TestClient(_mini_app(rate_limited=False, requests=1))
    assert client.get("/api/ping").status_code == 200
    assert client.get("/api/ping").status_code == 200
