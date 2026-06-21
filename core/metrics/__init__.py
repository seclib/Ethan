"""Prometheus Metrics — Export des métriques OpenJarvis."""

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# Métriques backend
REQUEST_COUNT = None
REQUEST_LATENCY = None
ACTIVE_AGENTS = None
ACTIVE_SESSIONS = None
ERROR_COUNT = None

try:
    from prometheus_client import Counter, Histogram, Gauge

    # Compteur de requêtes
    REQUEST_COUNT = Counter(
        "openjarvis_requests_total",
        "Total des requêtes API",
        ["method", "endpoint", "status"],
    )

    # Latence des requêtes
    REQUEST_LATENCY = Histogram(
        "openjarvis_request_duration_seconds",
        "Durée des requêtes API en secondes",
        ["method", "endpoint"],
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
    )

    # Agents actifs
    ACTIVE_AGENTS = Gauge(
        "openjarvis_active_agents",
        "Nombre d'agents actifs",
        ["agent_type"],
    )

    # Sessions actives
    ACTIVE_SESSIONS = Gauge(
        "openjarvis_active_sessions",
        "Nombre de sessions utilisateur actives",
    )

    # Erreurs
    ERROR_COUNT = Counter(
        "openjarvis_errors_total",
        "Total des erreurs",
        ["error_type", "severity"],
    )

except ImportError:
    logger.warning("prometheus_client not installed. Metrics will not be available.")


class MetricsCollector:
    """Collecteur de métriques pour Prometheus."""

    def __init__(self):
        self._start_times: dict[str, float] = {}

    def record_request(self, method: str, endpoint: str, status: int) -> None:
        """Enregistre une requête API."""
        if REQUEST_COUNT is None:
            return
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()

    def record_latency(self, method: str, endpoint: str, duration: float) -> None:
        """Enregistre la latence d'une requête."""
        if REQUEST_LATENCY is None:
            return
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

    def set_active_agents(self, agent_type: str, count: int) -> None:
        """Met à jour le nombre d'agents actifs."""
        if ACTIVE_AGENTS is None:
            return
        ACTIVE_AGENTS.labels(agent_type=agent_type).set(count)

    def set_active_sessions(self, count: int) -> None:
        """Met à jour le nombre de sessions actives."""
        if ACTIVE_SESSIONS is None:
            return
        ACTIVE_SESSIONS.set(count)

    def record_error(self, error_type: str, severity: str) -> None:
        """Enregistre une erreur."""
        if ERROR_COUNT is None:
            return
        ERROR_COUNT.labels(error_type=error_type, severity=severity).inc()

    def start_timer(self, name: str) -> None:
        """Démarre un timer pour mesurer la latence."""
        self._start_times[name] = time.time()

    def stop_timer(self, name: str) -> float:
        """Arrête le timer et retourne la durée en secondes."""
        if name not in self._start_times:
            return 0.0
        duration = time.time() - self._start_times[name]
        del self._start_times[name]
        return duration


# Instance globale
metrics = MetricsCollector()