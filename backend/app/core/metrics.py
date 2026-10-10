"""Métriques d'observation au format Prometheus.

Registre en mémoire, par processus, sans dépendance externe. Un middleware
enregistre le nombre de requêtes et leur durée ; ``GET /api/metrics`` expose le
texte Prometheus.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from app.core.config import get_settings


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


class MetricsRegistry:
    """Registre minimal : compteurs de requêtes et de durée cumulée."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counts: dict[tuple[str, str, str], int] = {}
        self._durations: dict[tuple[str, str], tuple[float, int]] = {}
        self.start_time = time.time()

    def observe(
        self,
        method: str,
        path: str,
        status: int,
        duration_seconds: float,
    ) -> None:
        """Enregistre une requête observée."""
        method = method or "UNKNOWN"
        path = path or "unknown"
        with self._lock:
            key = (method, path, str(status))
            self._counts[key] = self._counts.get(key, 0) + 1
            duration_key = (method, path)
            duration_sum, duration_count = self._durations.get(duration_key, (0.0, 0))
            self._durations[duration_key] = (duration_sum + duration_seconds, duration_count + 1)

    def render(self, *, version: str, environment: str) -> str:
        """Produit l'exposition Prometheus déterministe (triée)."""
        lines: list[str] = []
        now = time.time()

        lines.append("# HELP repoflow_build_info Informations de build.")
        lines.append("# TYPE repoflow_build_info gauge")
        lines.append(
            f'repoflow_build_info{{version="{_escape_label(version)}",'
            f'environment="{_escape_label(environment)}"}} 1'
        )
        lines.append("# HELP repoflow_process_start_time_seconds Heure de démarrage du processus.")
        lines.append("# TYPE repoflow_process_start_time_seconds gauge")
        lines.append(f"repoflow_process_start_time_seconds {now - self.start_time:.3f}")

        with self._lock:
            counts = dict(self._counts)
            durations = dict(self._durations)

        lines.append("# HELP repoflow_http_requests_total Nombre de requêtes HTTP.")
        lines.append("# TYPE repoflow_http_requests_total counter")
        for method, path, status in sorted(counts):
            lines.append(
                f'repoflow_http_requests_total{{method="{_escape_label(method)}",'
                f'path="{_escape_label(path)}",status="{_escape_label(status)}"}} '
                f"{counts[(method, path, status)]}"
            )

        lines.append("# HELP repoflow_http_request_duration_seconds Durée des requêtes HTTP.")
        lines.append("# TYPE repoflow_http_request_duration_seconds summary")
        for method, path in sorted(durations):
            duration_sum, duration_count = durations[(method, path)]
            lines.append(
                f'repoflow_http_request_duration_seconds_sum{{method="{_escape_label(method)}",'
                f'path="{_escape_label(path)}"}} {duration_sum:.3f}'
            )
            lines.append(
                f'repoflow_http_request_duration_seconds_count{{method="{_escape_label(method)}",'
                f'path="{_escape_label(path)}"}} {duration_count}'
            )
        return "\n".join(lines) + "\n"


registry = MetricsRegistry()


def observe_request(
    method: str,
    path: str,
    status: int,
    duration_seconds: float,
) -> None:
    """Point d'entrée d'enregistrement (voir ``MetricsRegistry.observe``)."""
    registry.observe(method, path, status, duration_seconds)


def render_metrics() -> str:
    """Expose les métriques avec les identifiants du contexte applicatif."""
    settings = get_settings()
    return registry.render(version=settings.version, environment=settings.environment)


class MetricsMiddleware:
    """Middleware ASGI : chronologie des réponses et comptage des requêtes."""

    def __init__(
        self,
        app,
        *,
        metrics_registry: MetricsRegistry | None = None,
    ) -> None:
        self.app = app
        self._registry = metrics_registry if metrics_registry is not None else registry

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "UNKNOWN")
        start = time.perf_counter()
        status_holder = {"status": 500}

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.perf_counter() - start
            path = getattr(scope.get("route"), "path", None) or scope.get("path", "unknown")
            if path not in ("/api/metrics", "/metrics"):
                self._registry.observe(method, path, status_holder["status"], duration)
