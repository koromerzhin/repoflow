"""Métriques d'observation au format Prometheus.

Registre en mémoire, par processus, sans dépendance externe. Un middleware
enregistre le nombre de requêtes et leur durée (histogramme) ; ``GET /api/metrics``
expose le texte Prometheus. Des compteurs métier (fusions, passes du worker,
appels fournisseur, événements de cache) complètent les métriques HTTP.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from app.core.config import get_settings

#: Bornes supérieures des buckets d'histogramme de latence (secondes).
_DURATION_BUCKETS: tuple[float, ...] = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
)

_LabelSet = tuple[tuple[str, str], ...]


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _format_labels(labels: _LabelSet) -> str:
    if not labels:
        return ""
    inner = ",".join(f'{name}="{_escape_label(value)}"' for name, value in labels)
    return "{" + inner + "}"


def _format_float(value: float) -> str:
    return f"{value:.6g}"


@dataclass
class _Histogram:
    """Compteurs d'un histogramme Prometheus (buckets, somme, total)."""

    buckets: list[int] = field(default_factory=lambda: [0] * (len(_DURATION_BUCKETS) + 1))
    total: float = 0.0
    count: int = 0

    def observe(self, value: float) -> None:
        for index, bound in enumerate(_DURATION_BUCKETS):
            if value <= bound:
                self.buckets[index] += 1
        self.buckets[-1] += 1
        self.total += value
        self.count += 1


class MetricsRegistry:
    """Registre minimal : requêtes, histogrammes et compteurs métier."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counts: dict[tuple[str, str, str], int] = {}
        self._durations: dict[tuple[str, str], _Histogram] = {}
        self._counters: dict[str, dict[_LabelSet, float]] = {}
        self._counter_help: dict[str, str] = {}
        self._gauges: dict[str, float] = {}
        self._gauge_help: dict[str, str] = {}
        self.start_time = time.time()

    def observe(
        self,
        method: str,
        path: str,
        status: int,
        duration_seconds: float,
    ) -> None:
        """Enregistre une requête HTTP observée."""
        method = method or "UNKNOWN"
        path = path or "unknown"
        with self._lock:
            key = (method, path, str(status))
            self._counts[key] = self._counts.get(key, 0) + 1
            histogram = self._durations.setdefault((method, path), _Histogram())
            histogram.observe(duration_seconds)

    def increment(
        self,
        name: str,
        *,
        help: str,
        labels: dict[str, str] | None = None,
        value: float = 1.0,
    ) -> None:
        """Incrémente un compteur métier nommé."""
        label_set: _LabelSet = tuple(sorted((labels or {}).items()))
        with self._lock:
            self._counter_help.setdefault(name, help)
            series = self._counters.setdefault(name, {})
            series[label_set] = series.get(label_set, 0.0) + value

    def set_gauge(self, name: str, value: float, *, help: str) -> None:
        """Fixe la valeur d'une jauge nommée."""
        with self._lock:
            self._gauge_help.setdefault(name, help)
            self._gauges[name] = value

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
            counters = {name: dict(series) for name, series in self._counters.items()}
            counter_help = dict(self._counter_help)
            gauges = dict(self._gauges)
            gauge_help = dict(self._gauge_help)

        lines.append("# HELP repoflow_http_requests_total Nombre de requêtes HTTP.")
        lines.append("# TYPE repoflow_http_requests_total counter")
        for method, path, status in sorted(counts):
            lines.append(
                f'repoflow_http_requests_total{{method="{_escape_label(method)}",'
                f'path="{_escape_label(path)}",status="{_escape_label(status)}"}} '
                f"{counts[(method, path, status)]}"
            )

        lines.append("# HELP repoflow_http_request_duration_seconds Durée des requêtes HTTP.")
        lines.append("# TYPE repoflow_http_request_duration_seconds histogram")
        for method, path in sorted(durations):
            histogram = durations[(method, path)]
            base = f'method="{_escape_label(method)}",path="{_escape_label(path)}"'
            for index, bound in enumerate(_DURATION_BUCKETS):
                lines.append(
                    f"repoflow_http_request_duration_seconds_bucket{{{base},"
                    f'le="{_format_float(bound)}"}} {histogram.buckets[index]}'
                )
            lines.append(
                f"repoflow_http_request_duration_seconds_bucket{{{base},"
                f'le="+Inf"}} {histogram.buckets[-1]}'
            )
            lines.append(
                f"repoflow_http_request_duration_seconds_sum{{{base}}} {histogram.total:.3f}"
            )
            lines.append(
                f"repoflow_http_request_duration_seconds_count{{{base}}} {histogram.count}"
            )

        for name in sorted(counters):
            lines.append(f"# HELP {name} {counter_help.get(name, name)}.")
            lines.append(f"# TYPE {name} counter")
            for label_set in sorted(counters[name]):
                value = _format_float(counters[name][label_set])
                lines.append(f"{name}{_format_labels(label_set)} {value}")

        for name in sorted(gauges):
            lines.append(f"# HELP {name} {gauge_help.get(name, name)}.")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {_format_float(gauges[name])}")

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


_WORKER_LAST_SUCCESS = "repoflow_worker_last_success_timestamp_seconds"
_MERGE_HELP = "Tentatives de fusion automatique, par résultat."
_WORKER_HELP = "Passes d'analyse du worker, par résultat."
_PROVIDER_HELP = "Appels sortants vers le fournisseur, par transport."
_CACHE_HELP = "Événements du cache, par type."


def record_merge(result: str) -> None:
    """Comptabilise une tentative de fusion (``succeeded`` ou ``failed``)."""
    registry.increment("repoflow_merges_total", help=_MERGE_HELP, labels={"result": result})


def record_worker_run(result: str) -> None:
    """Comptabilise une passe du worker (``success`` ou ``error``)."""
    registry.increment("repoflow_worker_runs_total", help=_WORKER_HELP, labels={"result": result})
    if result == "success":
        registry.set_gauge(
            _WORKER_LAST_SUCCESS,
            time.time(),
            help="Horodatage de la dernière passe d'analyse réussie.",
        )


def record_provider_request(transport: str) -> None:
    """Comptabilise un appel sortant vers le fournisseur (``rest``/``graphql``)."""
    registry.increment(
        "repoflow_provider_requests_total",
        help=_PROVIDER_HELP,
        labels={"transport": transport},
    )


def record_cache_event(event: str) -> None:
    """Comptabilise un événement de cache (``hit``, ``miss``, ``fallback``)."""
    registry.increment(
        "repoflow_cache_events_total",
        help=_CACHE_HELP,
        labels={"event": event},
    )


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
