"""Telemetry — Collecte de métriques système.

Collecte et expose des métriques pour le monitoring :
- Compteurs d'événements
- Latences
- Health des modules
- Ressources système
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Point de métrique."""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: dict[str, str] = field(default_factory=dict)


class TelemetryCollector:
    """Collecteur de métriques.

    Collecte des métriques système et les expose pour Prometheus.
    """

    def __init__(self):
        self._metrics: dict[str, list[MetricPoint]] = {}
        self._counters: dict[str, float] = {}
        self._start_time = time.time()

    def increment(self, name: str, labels: dict[str, str] = None) -> None:
        """Incrémente un compteur."""
        key = self._make_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + 1

    def record(self, name: str, value: float, labels: dict[str, str] = None) -> None:
        """Enregistre une valeur."""
        point = MetricPoint(name=name, value=value, labels=labels or {})
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(point)

    def record_latency(self, operation: str, duration_ms: float, labels: dict[str, str] = None) -> None:
        """Enregistre une latence."""
        self.record(f"{operation}_latency_ms", duration_ms, labels)
        self.increment(f"{operation}_total", labels)

    def get_counter(self, name: str, labels: dict[str, str] = None) -> float:
        """Récupère un compteur."""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0)

    def get_metrics_summary(self) -> dict[str, Any]:
        """Résumé des métriques."""
        return {
            "uptime_seconds": time.time() - self._start_time,
            "counters": dict(self._counters),
            "metric_names": list(self._metrics.keys()),
        }

    def _make_key(self, name: str, labels: dict[str, str] = None) -> str:
        """Crée une clé unique pour une métrique."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}[{label_str}]"

    def reset(self) -> None:
        """Réinitialise les métriques."""
        self._metrics.clear()
        self._counters.clear()
        self._start_time = time.time()