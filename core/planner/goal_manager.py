"""Goal Manager — Gestionnaire de multiples objectifs.

Responsabilités :
- Gérer plusieurs goals simultanément
- Prioriser les goals
- Détecter les conflits
- Ordonnancer l'exécution
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.planner.types import Goal, Priority, Conflict

logger = logging.getLogger(__name__)


class GoalManager:
    """Gestionnaire de multiples objectifs."""

    def __init__(self):
        self._goals: dict[str, Goal] = {}
        self._queue: list[tuple[float, str]] = []  # (score, goal_id)

    async def add_goal(self, goal: Goal) -> str:
        """Ajoute un goal.

        Args:
            goal: Goal à ajouter

        Returns:
            ID du goal
        """
        self._goals[goal.id] = goal

        # Calculer le score de priorité
        score = self._calculate_priority_score(goal)
        self._queue.append((score, goal.id))
        self._queue.sort(reverse=True)  # Plus haut score en premier

        logger.info(f"Goal added: {goal.id} (priority: {goal.priority}, score: {score:.2f})")
        return goal.id

    async def get_next_goal(self) -> Goal | None:
        """Récupère le goal le plus prioritaire.

        Returns:
            Goal le plus prioritaire ou None
        """
        if not self._queue:
            return None

        # Récupérer le goal avec le plus haut score
        _, goal_id = self._queue.pop(0)
        return self._goals.get(goal_id)

    async def prioritize(self, goal_id: str, new_priority: Priority) -> None:
        """Change la priorité d'un goal.

        Args:
            goal_id: ID du goal
            new_priority: Nouvelle priorité
        """
        goal = self._goals.get(goal_id)
        if not goal:
            logger.warning(f"Goal not found: {goal_id}")
            return

        goal.priority = new_priority

        # Recalculer le score et mettre à jour la queue
        score = self._calculate_priority_score(goal)
        self._queue = [(s, gid) for s, gid in self._queue if gid != goal_id]
        self._queue.append((score, goal_id))
        self._queue.sort(reverse=True)

        logger.info(f"Goal reprioritized: {goal_id} → {new_priority}")

    async def detect_conflicts(self, goal1: Goal, goal2: Goal) -> list[Conflict]:
        """Détecte les conflits entre deux goals.

        Args:
            goal1: Premier goal
            goal2: Second goal

        Returns:
            Liste de conflits
        """
        conflicts = []

        # Conflit de capabilities
        caps1 = set(goal1.required_capabilities)
        caps2 = set(goal2.required_capabilities)
        common_caps = caps1 & caps2

        if common_caps:
            conflicts.append(Conflict(
                type="capability_conflict",
                goals=[goal1.id, goal2.id],
                description=f"Both goals require capabilities: {', '.join(common_caps)}",
                severity="warning",
            ))

        # Conflit de ressources (TODO: implémenter avec ResourceManager)
        # if goal1.resources & goal2.resources:
        #     conflicts.append(...)

        return conflicts

    async def remove_goal(self, goal_id: str) -> None:
        """Supprime un goal.

        Args:
            goal_id: ID du goal
        """
        if goal_id in self._goals:
            del self._goals[goal_id]
            self._queue = [(s, gid) for s, gid in self._queue if gid != goal_id]
            logger.info(f"Goal removed: {goal_id}")

    def get_goal(self, goal_id: str) -> Goal | None:
        """Récupère un goal.

        Args:
            goal_id: ID du goal

        Returns:
            Goal ou None
        """
        return self._goals.get(goal_id)

    def list_goals(self) -> list[Goal]:
        """Liste tous les goals.

        Returns:
            Liste de goals
        """
        return list(self._goals.values())

    def _calculate_priority_score(self, goal: Goal) -> float:
        """Calcule un score de priorité dynamique.

        Facteurs :
        - Priorité de base (40%)
        - Urgence (30%)
        - Importance (20%)
        - Dépendances (10%)

        Args:
            goal: Goal à évaluer

        Returns:
            Score de 0.0 à 1.0
        """
        score = 0.0

        # Priorité de base (40%)
        priority_scores = {
            Priority.CRITICAL: 1.0,
            Priority.HIGH: 0.8,
            Priority.MEDIUM: 0.6,
            Priority.LOW: 0.4,
            Priority.BACKGROUND: 0.2,
        }
        score += priority_scores.get(goal.priority, 0.5) * 0.4

        # Urgence (30%)
        if goal.deadline:
            hours_remaining = (goal.deadline - datetime.utcnow()).total_seconds() / 3600
            urgency = max(0.0, min(1.0, 1.0 - (hours_remaining / 24.0)))
            score += urgency * 0.3

        # Importance (20%)
        score += goal.importance * 0.2

        # Dépendances (10%)
        if goal.metadata.get("blocks_other_goals"):
            score += 0.1

        return min(1.0, score)