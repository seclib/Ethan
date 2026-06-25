"""Executor — Exécute les tâches du plan."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class Executor:
    """Exécuteur de tâches pour le module Cognition.

    Responsabilités :
    - Exécuter les tâches du plan
    - Appeler les capabilities
    - Gérer les retries
    - Agrégation des résultats
    """

    def __init__(self, bus=None):
        self._bus = bus

    async def execute(self, plan: dict[str, Any]) -> list[dict[str, Any]]:
        """Exécute un plan.

        Args:
            plan: Plan à exécuter

        Returns:
            Liste de résultats
        """
        tasks = plan.get("tasks", [])
        results = []

        logger.info(f"Executor: executing {len(tasks)} tasks")

        # Exécution séquentielle (MVP)
        # Production : parallélisation selon les dépendances
        for task in tasks:
            result = await self._execute_task(task)
            results.append(result)

            # Si échec, arrêter l'exécution
            if result.get("status") != "completed":
                logger.warning(f"Task {task['id']} failed, stopping execution")
                break

        return results

    async def _execute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Exécute une tâche.

        Args:
            task: Tâche à exécuter

        Returns:
            Résultat de la tâche
        """
        task_id = task.get("id", "unknown")
        capability = task.get("capability", "unknown")

        logger.info(f"Executing task {task_id}: {capability}")

        try:
            # MVP : simulation
            # Production : appeler la capability via le bus
            if self._bus:
                # Publier l'événement d'exécution
                pass

            # Simulation d'exécution
            result = {
                "task_id": task_id,
                "capability": capability,
                "status": "completed",
                "result": f"Executed {capability}",
                "duration_ms": 100.0,
            }

            logger.info(f"Task {task_id} completed")
            return result

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            return {
                "task_id": task_id,
                "capability": capability,
                "status": "failed",
                "error": str(e),
            }

    async def _call_capability(self, capability: str, params: dict[str, Any]) -> Any:
        """Appelle une capability via le bus.

        Args:
            capability: Nom de la capability
            params: Paramètres

        Returns:
            Résultat de la capability
        """
        # TODO: Implémenter l'appel via EventBus
        raise NotImplementedError("Capability calling not implemented")