"""DAG Builder — Construit et valide le graphe de tâches.

Responsabilités :
- Construire le DAG
- Valider les dépendances
- Détecter les cycles
- Calculer les niveaux d'exécution (topological sort)
"""

from __future__ import annotations

import logging
from typing import Any

from core.planner.types import Task, TaskDAG

logger = logging.getLogger(__name__)


class CyclicDependencyError(Exception):
    """Erreur: cycle détecté dans les dépendances."""
    pass


class DAGBuilder:
    """Construit un DAG de tâches valide."""

    def build(self, tasks: list[Task]) -> TaskDAG:
        """Construit le DAG.

        Args:
            tasks: Liste de tâches

        Returns:
            DAG validé

        Raises:
            CyclicDependencyError: Si un cycle est détecté
        """
        dag = TaskDAG()

        # Ajouter les tâches
        for task in tasks:
            dag.add_task(task)

        # Valider les dépendances
        self._validate_dependencies(dag)

        # Détecter les cycles
        if self._has_cycles(dag):
            raise CyclicDependencyError("Plan contains cyclic dependencies")

        # Calculer les niveaux
        self._compute_levels(dag)

        logger.info(f"DAG built: {len(tasks)} tasks, {len(dag.levels)} levels")
        return dag

    def _validate_dependencies(self, dag: TaskDAG) -> None:
        """Valide que toutes les dépendances existent.

        Args:
            dag: DAG à valider

        Raises:
            ValueError: Si une dépendance n'existe pas
        """
        for task in dag.tasks.values():
            for dep_id in task.depends_on:
                if dep_id not in dag.tasks:
                    raise ValueError(
                        f"Task {task.id} depends on non-existent task {dep_id}"
                    )

    def _has_cycles(self, dag: TaskDAG) -> bool:
        """Détecte les cycles (DFS).

        Args:
            dag: DAG à vérifier

        Returns:
            True si un cycle existe
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {tid: WHITE for tid in dag.tasks}

        def dfs(tid: str) -> bool:
            color[tid] = GRAY
            task = dag.tasks[tid]

            for dep_id in task.depends_on:
                if dep_id not in color:
                    continue
                if color[dep_id] == GRAY:
                    return True  # Cycle détecté
                if color[dep_id] == WHITE:
                    if dfs(dep_id):
                        return True

            color[tid] = BLACK
            return False

        for tid in dag.tasks:
            if color[tid] == WHITE:
                if dfs(tid):
                    return True

        return False

    def _compute_levels(self, dag: TaskDAG) -> None:
        """Calcule les niveaux d'exécution (topological sort - Kahn's algorithm).

        Args:
            dag: DAG à traiter
        """
        # Calculer les in-degrees
        in_degree = {tid: 0 for tid in dag.tasks}
        adjacency = {tid: [] for tid in dag.tasks}

        for task in dag.tasks.values():
            for dep_id in task.depends_on:
                in_degree[task.id] += 1
                adjacency[dep_id].append(task.id)

        # BFS depuis les nœuds avec in-degree = 0
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        level = 0

        while queue:
            dag.add_level(queue, level)
            next_queue = []

            for tid in queue:
                for neighbor in adjacency[tid]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_queue.append(neighbor)

            queue = next_queue
            level += 1

    def add_task(self, dag: TaskDAG, task: Task) -> None:
        """Ajoute une tâche au DAG.

        Args:
            dag: DAG
            task: Tâche à ajouter
        """
        dag.add_task(task)
        self._validate_dependencies(dag)

        if self._has_cycles(dag):
            raise CyclicDependencyError("Adding this task creates a cycle")

        # Recalculer les niveaux
        dag.levels = []
        self._compute_levels(dag)

    def remove_task(self, dag: TaskDAG, task_id: str) -> None:
        """Supprime une tâche du DAG.

        Args:
            dag: DAG
            task_id: ID de la tâche à supprimer
        """
        if task_id not in dag.tasks:
            return

        # Supprimer la tâche
        del dag.tasks[task_id]

        # Supprimer des dépendances
        for task in dag.tasks.values():
            if task_id in task.depends_on:
                task.depends_on.remove(task_id)

        # Recalculer les niveaux
        dag.levels = []
        self._compute_levels(dag)

    def get_parallel_groups(self, dag: TaskDAG) -> list[list[Task]]:
        """Récupère les groupes de tâches parallélisables.

        Args:
            dag: DAG

        Returns:
            Liste de groupes (chaque groupe peut s'exécuter en parallèle)
        """
        groups = []
        for level_ids in dag.levels:
            group = [dag.tasks[tid] for tid in level_ids]
            groups.append(group)
        return groups

    def get_critical_path(self, dag: TaskDAG) -> list[Task]:
        """Calcule le chemin critique (plus longue chaîne de dépendances).

        Args:
            dag: DAG

        Returns:
            Liste de tâches sur le chemin critique
        """
        # TODO: Implémenter avec algorithm de chemin critique
        # Pour l'instant, retourner toutes les tâches
        return list(dag.tasks.values())