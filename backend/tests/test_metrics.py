"""Tests des métriques d'observation (format Prometheus)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.metrics import MetricsMiddleware, MetricsRegistry


def _sample_app(metrics_registry: MetricsRegistry) -> FastAPI:
    app = FastAPI()
    app.add_middleware(MetricsMiddleware, metrics_registry=metrics_registry)

    @app.get("/api/prs/{number:int}")
    def pr(number: int) -> dict[str, int]:
        return {"number": number}

    @app.get("/api/other")
    def other() -> dict[str, str]:
        return {"status": "ok"}

    return app


def test_registre_compte_et_cumule() -> None:
    registry = MetricsRegistry()
    registry.observe("GET", "/api/x", 200, 0.10)
    registry.observe("GET", "/api/x", 200, 0.05)
    registry.observe("GET", "/api/x", 500, 0.02)

    text = registry.render(version="0.1.0", environment="test")
    assert 'repoflow_http_requests_total{method="GET",path="/api/x",status="200"} 2' in text
    assert 'repoflow_http_requests_total{method="GET",path="/api/x",status="500"} 1' in text
    assert 'repoflow_http_request_duration_seconds_count{method="GET",path="/api/x"} 3' in text
    assert 'repoflow_build_info{version="0.1.0",environment="test"} 1' in text
    assert text.endswith("\n")


def test_registre_echappe_les_caracteres() -> None:
    registry = MetricsRegistry()
    registry.observe("GET", '/path"quoted', 200, 0.01)
    text = registry.render(version="v1", environment="prod")
    assert 'path="/path\\"quoted"' in text


def test_middleware_utilise_le_modele_de_route() -> None:
    registry = MetricsRegistry()
    client = TestClient(_sample_app(registry))
    assert client.get("/api/prs/42").status_code == 200
    assert client.get("/api/prs/99").status_code == 200
    assert client.get("/api/other").status_code == 200

    text = registry.render(version="0.1.0", environment="test")
    assert 'path="/api/prs/{number:int}",status="200"} 2' in text
    assert 'path="/api/other",status="200"} 1' in text


def test_route_metrics_expose_les_series(client) -> None:
    assert client.get("/api/health").status_code == 200
    response = client.get("/api/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert 'repoflow_http_requests_total{method="GET",path="/health"' in response.text
