"""Metacognition Agent — Module de méta-cognition.

Responsabilités :
- Surveille la santé du système
- Détecte les anomalies
- Ajuste les paramètres système
- Émet des alertes

Communication :
- Reçoit : ethan.system.telemetry, ethan.module.heartbeat
- Publie : ethan.metacognition.report, ethan.metacognition.warning
"""

from __future__ import annotations

import logging
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.types.event import Event, EventType
from core.types.result import Result

logger = logging.getLogger(__name__)


class MetacognitionAgent(Agent):
    """Agent de méta-cognition — surveille et ajuste le système."""

    def __init__(self, config: AgentConfig, bus=None):
        super().__init__(config, bus)
        self._module_heartbeats: dict[str, float] = {}
        self._heartbeat_timeout = 30  # secondes

    async def _on_init(self) -> None:
        logger.info("Metacognition agent initializing...")

    async def _subscribe_events(self) -> None:
        await self.subscribe("ethan.system.telemetry", self._handle_telemetry)
        await self.subscribe("ethan.module.heartbeat", self._handle_heartbeat)

    async def _handle_telemetry(self, event: Event) -> None:
        """Traite la télémetrie système."""
        metrics = event.payload.get("metrics", {})

        # Vérifier les seuils critiques
        warnings = []

        # CPU
        cpu_usage = metrics.get("cpu_usage", 0)
        if cpu_usage > 90:
            warnings.append(f"High CPU usage: {cpu_usage}%")

        # Mémoire
        memory_usage = metrics.get("memory_usage", 0)
        if memory_usage > 85:
            warnings.append(f"High memory usage: {memory_usage}%")

        # Latence
        latency_ms = metrics.get("latency_ms", 0)
        if latency_ms > 5000:
            warnings.append(f"High latency: {latency_ms}ms")

        # Émettre des alertes si nécessaire
        for warning in warnings:
            await self.publish(
                EventType.METACOGNITION_WARNING,
                {
                    "level": "critical",
                    "message": warning,
                    "metrics": metrics,
                },
            )

        # Publier un rapport périodique
        await self.publish(
            EventType.METACOGNITION_REPORT,
            {
                "status": "healthy" if not warnings else "degraded",
                "warnings": warnings,
                "metrics": metrics,
                "active_modules": len(self._module_heartbeats),
            },
        )

    async def _handle_heartbeat(self, event: Event) -> None:
        """Traite les heartbeats des modules."""
        module_name = event.payload.get("module", event.source)
        timestamp = event.payload.get("timestamp", 0)

        self._module_heartbeats[module_name] = timestamp

        # Vérifier les modules en retard
        import time
        now = time.time()
        stale_modules = [
            name for name, ts in self._module_heartbeats.items()
            if now - ts > self._heartbeat_timeout
        ]

        if stale_modules:
            await self.publish(
                EventType.METACOGNITION_WARNING,
                {
                    "level": "warning",
                    "message": f"Modules not responding: {', '.join(stale_modules)}",
                    "stale_modules": stale_modules,
                },
            )

    async def run(self, input_data=None) -> Result:
        """Point d'entrée standalone."""
        return Result.ok(data={"status": "metacognition ready"})