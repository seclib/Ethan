"""Plan Optimizer — Optimise les plans d'exécution.

Responsabilités :
- Parallélisation maximale
- Minimisation du makespan
- Priorisation intelligente
- Équilibrage de charge
"""

from __future__ import annotations

import logging
from typing import Any

from core.planner.types import Plan, Task, Priority, TaskDAG

logger = logging.getLogger(__name__)


class PlanOptimizer:
    """Optimiseur de plans."""

    def __init__(self):
        pass

    def optimize(self, plan: Plan) -> Plan:
        """Optimise un plan.

        Args:
            plan: Plan à optimiser

        Returns:
            Plan optimisé
        """
        # 1. Parallélisation
        plan = self._optimize_parallelism(plan)

        # 2. Priorisation
        plan = self._optimize_priority(plan)

        # 3. Équilibrage (TODO)

        logger.info(f"Plan optimized: {plan.id}")
        return plan

    def _optimize_parallelism(self, plan: Plan) -> Plan:
        """Maximise le parallélisme.

        Les tâches au même niveau du DAG peuvent s'exécuter en parallèle.

        Args:
            plan: Plan à optimiser

        Returns:
            Plan optimisé
        """
        if not plan.dag:
            return plan

        # Les niveaux sont déjà calculés par DAGBuilder
        # Juste vérifier que max_parallel est respecté
        max_parallel = plan.max_parallel

        for level in plan.dag.levels:
            if len(level) > max_parallel:
                logger.warning(
                    f"Level has {len(level)} tasks but max_parallel={max_parallel}. "
                    f"Some tasks will be serialized."
                )

        return plan

    def _optimize_priority(self, plan: Plan) -> Plan:
        """Ajuste les priorités selon le goal.

        Args:
            plan: Plan à optimiser

        Returns:
            Plan optimisé
        """
        # Les priorités sont déjà définies lors de la décomposition
        # Ici on peut ajuster selon le contexte

        for task in plan.tasks:
            # Tâches critiques = haute priorité
            if task.capability in ["health.check", "deploy.execute"]:
                task.priority = Priority.HIGH

        return plan

    def optimize_for_duration(self, plan: Plan, durations: dict[str, float]) -> Plan:
        """Optimise pour minimiser la durée totale (makespan).

        Args:
            plan: Plan à optimiser
            durations: Durées estimées par tâche {task_id: duration}

        Returns:
            Plan optimisé
        """
        # TODO: Utiliser un solver (CP-SAT, ILP)
        # Pour l'instant, retourner le plan tel quel
        return plan

    def optimize_for_resources(self, plan: Plan, resources: dict[str, int]) -> Plan:
        """Optimise pour respecter les limites de ressources.

        Args:
            plan: Plan à optimiser
            resources: Ressources disponibles {resource_name: capacity}

        Returns:
            Plan optimisé
        """
        # TODO: Implémenter un scheduler avec contraintes de ressources
        return plan

    def reorder_tasks(self, plan: Plan, order: list[str]) -> Plan:
        """Réordonne les tâches selon un ordre donné.

        Args:
            plan: Plan à modifier
            order: Liste d'IDs de tâches dans l'ordre souhaité

        Returns:
            Plan modifié
        """
        # Créer un mapping id -> task
        task_map = {t.id: t for t in plan.tasks}

        # Réordonner
        plan.tasks = [task_map[tid] for tid in order if tid in task_map]

        # Reconstruire le DAG
        from core.planner.dag import DAGBuilder
        builder = DAGBuilder()
        plan.dag = builder.build(plan.tasks)

        return plan