"""Tests du contexte de requête (identifiant de corrélation)."""

from __future__ import annotations

import logging
import re

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.request_context import REQUEST_ID_HEADER, RequestContextMiddleware, get_request_id


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/ok")
    def ok() -> dict[str, str]:
        return {"request_id": get_request_id()}

    return app


def test_identifiant_relance_depuis_en_tete() -> None:
    client = TestClient(_make_app())
    response = client.get("/ok", headers={REQUEST_ID_HEADER: "corr-123"})
    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == "corr-123"
    assert response.json()["request_id"] == "corr-123"


def test_identifiant_genere_si_absent() -> None:
    client = TestClient(_make_app())
    response = client.get("/ok")
    request_id = response.headers[REQUEST_ID_HEADER]
    assert re.fullmatch(r"[0-9a-f]{32}", request_id)
    assert response.json()["request_id"] == request_id


def test_identifiant_invalide_regenere() -> None:
    client = TestClient(_make_app())
    response = client.get("/ok", headers={REQUEST_ID_HEADER: "x@y z!"})
    request_id = response.headers[REQUEST_ID_HEADER]
    assert re.fullmatch(r"[0-9a-f]{32}", request_id)


def test_identifiant_est_tronque() -> None:
    long_id = "a" * 200
    client = TestClient(_make_app())
    response = client.get("/ok", headers={REQUEST_ID_HEADER: long_id})
    request_id = response.headers[REQUEST_ID_HEADER]
    assert len(request_id) == 64


def test_journal_acces_descriptif(caplog) -> None:
    caplog.set_level(logging.INFO, logger="app.access")
    client = TestClient(_make_app())
    client.get("/ok", headers={REQUEST_ID_HEADER: "corr-log"})
    records = [record for record in caplog.records if record.name == "app.access"]
    assert records
    assert "GET /ok -> 200" in records[-1].message
