"""Task Decomposer — Décompose les goals en tâches.

Stratégies :
- LLM (intelligente)
- Règles (déterministe)
- HTN (hiérarchique)
"""

from __future__ import annotations

import logging
from typing import Any

from core.planner.types import Goal, Task, Priority

logger = logging.getLogger(__name__)


class TaskDecomposer:
    """Décompose un goal en tâches atomiques."""

    def __init__(self):
        self._rules = self._load_rules()

    async def decompose(self, goal: Goal) -> list[Task]:
        """Décompose un goal en tâches.

        Args:
            goal: Goal à décomposer

        Returns:
            Liste de tâches
        """
        # Stratégie 1: Essayer LLM (si disponible)
        try:
            tasks = await self._decompose_with_llm(goal)
            if tasks:
                return tasks
        except Exception as e:
            logger.warning(f"LLM decomposition failed: {e}")

        # Stratégie 2: Règles
        tasks = self._decompose_by_rules(goal)
        if tasks:
            return tasks

        # Stratégie 3: Tâche générique
        return [self._create_generic_task(goal)]

    async def _decompose_with_llm(self, goal: Goal) -> list[Task]:
        """Décomposition intelligente avec LLM.

        Args:
            goal: Goal à décomposer

        Returns:
            Liste de tâches
        """
        # TODO: Intégrer LLM
        # Pour l'instant, retourner vide pour utiliser les règles
        return []

    def _decompose_by_rules(self, goal: Goal) -> list[Task]:
        """Décomposition par règles.

        Args:
            goal: Goal à décomposer

        Returns:
            Liste de tâches
        """
        tasks = []
        desc_lower = goal.description.lower()

        # Règle: Docker build
        if "docker" in desc_lower and "build" in desc_lower:
            tasks.append(Task(
                id="t1",
                capability="docker.build",
                params={"image": "app"},
                priority=Priority.HIGH,
            ))
            tasks.append(Task(
                id="t2",
                capability="docker.push",
                depends_on=["t1"],
                priority=Priority.HIGH,
            ))

        # Règle: Deploy
        elif "deploy" in desc_lower:
            tasks.append(Task(
                id="t1",
                capability="deploy.prepare",
                priority=Priority.HIGH,
            ))
            tasks.append(Task(
                id="t2",
                capability="deploy.execute",
                depends_on=["t1"],
                priority=Priority.HIGH,
            ))
            tasks.append(Task(
                id="t3",
                capability="health.check",
                depends_on=["t2"],
                priority=Priority.MEDIUM,
            ))

        # Règle: Test
        elif "test" in desc_lower:
            tasks.append(Task(
                id="t1",
                capability="test.run",
                priority=Priority.MEDIUM,
            ))

        # Règle: Build + Deploy
        elif "build" in desc_lower and "deploy" in desc_lower:
            tasks.append(Task(
                id="t1",
                capability="docker.build",
                params={"image": "app"},
                priority=Priority.HIGH,
            ))
            tasks.append(Task(
                id="t2",
                capability="docker.push",
                depends_on=["t1"],
                priority=Priority.HIGH,
            ))
            tasks.append(Task(
                id="t3",
                capability="deploy.prepare",
                depends_on=["t2"],
                priority=Priority.HIGH,
            ))
            tasks.append(Task(
                id="t4",
                capability="deploy.execute",
                depends_on=["t3"],
                priority=Priority.HIGH,
            ))
            tasks.append(Task(
                id="t5",
                capability="health.check",
                depends_on=["t4"],
                priority=Priority.MEDIUM,
            ))

        return tasks

    def _create_generic_task(self, goal: Goal) -> Task:
        """Crée une tâche générique.

        Args:
            goal: Goal

        Returns:
            Tâche générique
        """
        return Task(
            id="t1",
            capability="generic.execute",
            params={"description": goal.description},
            priority=Priority.MEDIUM,
        )

    def _load_rules(self) -> list[dict[str, Any]]:
        """Charge les règles de décomposition.

        Returns:
            Liste de règles
        """
        # TODO: Charger depuis un fichier de config
        return []

    async def _decompose_hierarchical(self, goal: Goal) -> list[Task]:
        """Décomposition hiérarchique (HTN).

        Args:
            goal: Goal à décomposer

        Returns:
            Liste de tâches
        """
        # TODO: Implémenter HTN
        return []