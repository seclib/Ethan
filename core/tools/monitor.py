"""Tool Monitor — Surveille et apprend des exécutions.

Responsabilités :
- Enregistrer les exécutions
- Mettre à jour les métriques
- Détecter les anomalies
- Alimenter l'apprentissage
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from core.tools.types import Tool, ToolResult

logger = logging.getLogger(__name__)


class ToolMonitor:
    """Surveille et apprend des exécutions."""

    def __init__(self):
        self._executions: list[dict[str, Any]] = []

    async def record_execution(self, tool: Tool, result: ToolResult, params: dict[str, Any]) -> None:
        """Enregistre une exécution.

        Args:
            tool: Outil exécuté
            result: Résultat
            params: Paramètres utilisés
        """
        execution = {
            "timestamp": datetime.utcnow().isoformat(),
            "tool_id": tool.id,
            "tool_name": tool.name,
            "params": params,
            "status": result.status,
            "duration_ms": result.duration_ms,
            "cost": result.cost,
            "error": result.error,
        }

        self._executions.append(execution)

        # Mettre à jour les métriques de l'outil
        self._update_tool_metrics(tool, result)

        # Détecter les anomalies
        self._detect_anomalies(tool, result)

        logger.info(f"Execution recorded: {tool.id} ({result.status}, {result.duration_ms:.1f}ms)")

    def _update_tool_metrics(self, tool: Tool, result: ToolResult) -> None:
        """Met à jour les métriques d'un outil.

        Args:
            tool: Outil
            result: Résultat
        """
        tool.total_calls += 1

        # Moyenne mobile du temps
        n = tool.total_calls
        tool.avg_duration_ms = ((tool.avg_duration_ms * (n - 1)) + result.duration_ms) / n

        # Taux de succès
        if result.status == "success":
            tool.success_count += 1

        tool.success_rate = tool.success_count / tool.total_calls

    def _detect_anomalies(self, tool: Tool, result: ToolResult) -> None:
        """Détecte les anomalies.

        Args:
            tool: Outil
            result: Résultat
        """
        # Anomalie: temps anormalement long
        if result.duration_ms > tool.avg_duration_ms * 3:
            logger.warning(f"Anomaly detected: {tool.id} took {result.duration_ms:.1f}ms (avg: {tool.avg_duration_ms:.1f}ms)")

        # Anomalie: taux de succès en baisse
        if tool.total_calls >= 10 and tool.success_rate < 0.5:
            logger.warning(f"Anomaly detected: {tool.id} success rate dropped to {tool.success_rate:.2f}")

    def get_tool_stats(self, tool_id: str) -> dict[str, Any] | None:
        """Récupère les statistiques d'un outil.

        Args:
            tool_id: ID de l'outil

        Returns:
            Statistiques ou None
        """
        executions = [e for e in self._executions if e["tool_id"] == tool_id]

        if not executions:
            return None

        success_count = sum(1 for e in executions if e["status"] == "success")
        avg_duration = sum(e["duration_ms"] for e in executions) / len(executions)

        return {
            "total_calls": len(executions),
            "success_count": success_count,
            "success_rate": success_count / len(executions),
            "avg_duration_ms": avg_duration,
            "last_execution": executions[-1]["timestamp"],
        }

    def get_recent_executions(self, limit: int = 10) -> list[dict[str, Any]]:
        """Récupère les exécutions récentes.

        Args:
            limit: Nombre d'exécutions

        Returns:
            Liste d'exécutions
        """
        return self._executions[-limit:]

    def get_failure_rate(self, tool_id: str, window_minutes: int = 60) -> float:
        """Calcule le taux d'échec récent.

        Args:
            tool_id: ID de l'outil
            window_minutes: Fenêtre temporelle

        Returns:
            Taux d'échec (0.0 à 1.0)
        """
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        cutoff_str = cutoff.isoformat()

        recent = [
            e for e in self._executions
            if e["tool_id"] == tool_id and e["timestamp"] >= cutoff_str
        ]

        if not recent:
            return 0.0

        failures = sum(1 for e in recent if e["status"] != "success")
        return failures / len(recent)