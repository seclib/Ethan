"""Event Monitor — Monitoring temps réel de l'Event Bus."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Coroutine
from uuid import uuid4

from core.types.event import Event

logger = logging.getLogger(__name__)


@dataclass
class MetricQuery:
    """Requête de métrique."""
    name: str
    type: str  # "counter", "histogram", "gauge"
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class Dashboard:
    """Dashboard de monitoring."""
    id: str
    name: str
    queries: list[MetricQuery]
    created_at: datetime = field(default_factory=datetime.utcnow)


class EventMonitor:
    """Monitor temps réel de l'Event Bus.
    
    Responsabilités :
    - Collecte de métriques (throughput, latency, errors)
    - Dashboards
    - Alertes
    - Traces distribuées
    """

    def __init__(self, metrics_collector: Any, alerting: Any | None = None):
        self._metrics = metrics_collector
        self._alerting = alerting
        self._dashboards: dict[str, Dashboard] = {}
        self._alert_thresholds: dict[str, dict[str, Any]] = {
            "backlog_size": {"warning": 1000, "critical": 10000},
            "error_rate": {"warning": 0.05, "critical": 0.10},
            "latency_p99": {"warning": 1.0, "critical": 5.0},
        }

    async def record_publish(self, event: Event, latency_ms: float) -> None:
        """Enregistre une publication.

        Args:
            event: Événement
            latency_ms: Latence de publication
        """
        # Compteur
        self._metrics.increment("eventbus.published", tags={
            "type": event.type.value,
            "source": event.source,
        })

        # Latence
        self._metrics.histogram("eventbus.publish.latency", latency_ms)

        # Taille
        size = len(str(event.payload))
        self._metrics.histogram("eventbus.publish.size", size)

    async def record_consume(self, event: Event, latency_ms: float, success: bool) -> None:
        """Enregistre une consommation.

        Args:
            event: Événement
            latency_ms: Latence de consommation
            success: Succès ou échec
        """
        # Compteur
        self._metrics.increment("eventbus.consumed", tags={
            "type": event.type.value,
            "success": str(success),
        })

        # Latence
        self._metrics.histogram("eventbus.consume.latency", latency_ms)

        # Erreur
        if not success:
            self._metrics.increment("eventbus.errors", tags={
                "type": event.type.value,
            })

            # Alerte
            if self._alerting:
                await self._alerting.send_alert(
                    severity="warning",
                    title=f"Event consumption failed: {event.type}",
                    details={"event_id": event.id},
                )

    async def record_backlog(self, subject: str, size: int) -> None:
        """Enregistre la taille de la backlog.

        Args:
            subject: Sujet
            size: Taille
        """
        self._metrics.gauge("eventbus.backlog", size, tags={"subject": subject})

        # Alertes
        if size > self._alert_thresholds["backlog_size"]["critical"]:
            if self._alerting:
                await self._alerting.send_alert(
                    severity="critical",
                    title=f"Event backlog too large: {subject}",
                    details={"size": size},
                )
        elif size > self._alert_thresholds["backlog_size"]["warning"]:
            if self._alerting:
                await self._alerting.send_alert(
                    severity="warning",
                    title=f"Event backlog growing: {subject}",
                    details={"size": size},
                )

    async def record_retry(self, event: Event, attempt: int) -> None:
        """Enregistre un retry.

        Args:
            event: Événement
            attempt: Numéro de tentative
        """
        self._metrics.increment("eventbus.retries", tags={
            "type": event.type.value,
            "attempt": str(attempt),
        })

    def create_dashboard(self, name: str, queries: list[MetricQuery]) -> Dashboard:
        """Crée un dashboard.

        Args:
            name: Nom
            queries: Requêtes de métriques

        Returns:
            Dashboard
        """
        dashboard = Dashboard(
            id=str(uuid4()),
            name=name,
            queries=queries,
        )
        self._dashboards[dashboard.id] = dashboard
        logger.info(f"Dashboard created: {name}")
        return dashboard

    def get_dashboard(self, dashboard_id: str) -> Dashboard | None:
        """Récupère un dashboard.

        Args:
            dashboard_id: ID

        Returns:
            Dashboard ou None
        """
        return self._dashboards.get(dashboard_id)

    def list_dashboards(self) -> list[Dashboard]:
        """Liste les dashboards.

        Returns:
            Liste de dashboards
        """
        return list(self._dashboards.values())

    def get_stats(self) -> dict[str, Any]:
        """Récupère les statistiques.

        Returns:
            Statistiques
        """
        return {
            "dashboards": len(self._dashboards),
            "alert_thresholds": self._alert_thresholds,
        }