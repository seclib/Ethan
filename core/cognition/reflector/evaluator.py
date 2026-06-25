"""Reflector — Évalue les résultats et produit des insights."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class Reflector:
    """Réflecteur pour le module Cognition.

    Responsabilités :
    - Évaluer les résultats d'exécution
    - Détecter les échecs
    - Générer des insights
    - Proposer des améliorations
    """

    def __init__(self):
        pass

    async def evaluate(
        self,
        query: str,
        plan: dict[str, Any],
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Évalue les résultats d'un plan.

        Args:
            query: Requête originale
            plan: Plan exécuté
            results: Résultats d'exécution

        Returns:
            Évaluation avec succès, confiance, output
        """
        total_tasks = len(results)
        failed_tasks = [r for r in results if r.get("status") != "completed"]

        success = len(failed_tasks) == 0 and total_tasks > 0
        success_rate = (total_tasks - len(failed_tasks)) / total_tasks if total_tasks > 0 else 0

        # Extraire le output
        output = ""
        if results:
            output = results[0].get("result", "")

        # Calculer la confiance
        confidence = success_rate * 0.9 + 0.1  # Minimum 0.1

        # Générer des insights
        insights = []
        if success_rate == 1.0:
            insights.append("All tasks completed successfully")
        elif success_rate >= 0.8:
            insights.append(f"Mostly successful ({success_rate:.0%})")
        else:
            insights.append(f"Significant failures ({success_rate:.0%})")
            if failed_tasks:
                failed_caps = [r.get("capability") for r in failed_tasks]
                insights.append(f"Failed capabilities: {', '.join(failed_caps)}")

        # Calculer la latence
        total_duration = sum(r.get("duration_ms", 0) for r in results)

        return {
            "success": success,
            "output": output,
            "confidence": confidence,
            "latency_ms": total_duration,
            "success_rate": success_rate,
            "insights": insights,
            "total_tasks": total_tasks,
            "failed_tasks": len(failed_tasks),
        }

    async def generate_improvement(self, evaluation: dict[str, Any]) -> str | None:
        """Génère une suggestion d'amélioration.

        Args:
            evaluation: Résultat de l'évaluation

        Returns:
            Suggestion d'amélioration ou None
        """
        if evaluation.get("success_rate", 0) < 0.5:
            failed_caps = []
            for insight in evaluation.get("insights", []):
                if "Failed capabilities:" in insight:
                    failed_caps = insight.split(":")[1].strip()
                    break

            return f"Consider reviewing capabilities: {failed_caps}"

        return None