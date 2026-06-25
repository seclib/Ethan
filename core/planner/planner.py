"""Planner — Module principal de planification.

Responsabilités :
- Créer des plans à partir de goals
- Modifier des plans
- Interrompre/reprendre
- Gérer plusieurs objectifs
- Prioriser
"""

from __future__ import annotations

import logging
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.planner.dag import DAGBuilder
from core.planner.decomposer import TaskDecomposer
from core.planner.goal_manager import GoalManager
from core.planner.optimizer import PlanOptimizer
from core.planner.types import Goal, Plan, PlanState, Priority
from core.types.event import Event, EventType
from core.types.result import Result

logger = logging.getLogger(__name__)


class PlannerModule(Agent):
    """Module Planner — transforme les goals en plans exécutables."""

    def __init__(self, config: AgentConfig, bus=None):
        super().__init__(config, bus)
        self._config = config

        # Composants
        self.goal_manager = GoalManager()
        self.decomposer = TaskDecomposer()
        self.dag_builder = DAGBuilder()
        self.optimizer = PlanOptimizer()
        self.checkpoint_mgr = None  # Initialisé dans _on_init

        # Plans actifs
        self._plans: dict[str, Plan] = {}

    async def _on_init(self) -> None:
        """Initialise le module."""
        logger.info("Planner module initializing...")

        # Initialiser le checkpoint manager avec le store
        from core.memory.manager import MemoryManager
        from core.memory.redis_store import RedisStore

        store = RedisStore(url="redis://localhost:6379", prefix="ethan:planner:")
        await store.connect()

        from core.planner.checkpoint import CheckpointManager
        self.checkpoint_mgr = CheckpointManager(store)

    async def _subscribe_events(self) -> None:
        """S'abonne aux événements."""
        await self.subscribe("ethan.executive.goal.created", self._handle_goal_created)
        await self.subscribe("ethan.planner.plan.pause", self._handle_pause)
        await self.subscribe("ethan.planner.plan.resume", self._handle_resume)
        await self.subscribe("ethan.planner.plan.cancel", self._handle_cancel)

    async def _handle_goal_created(self, event: Event) -> None:
        """Reçoit un goal et crée un plan."""
        goal_id = event.payload.get("goal_id")
        description = event.payload.get("description", "")
        priority = event.payload.get("priority", "medium")
        required_capabilities = event.payload.get("required_capabilities", [])

        logger.info(f"Planner received goal: {goal_id} — {description[:50]}")

        # Créer le goal
        goal = Goal(
            id=goal_id,
            description=description,
            priority=Priority(priority),
            required_capabilities=required_capabilities,
        )

        # Créer le plan
        plan = await self.create_plan(goal)

        # Publier le plan
        await self.publish(
            EventType.PLANNER_PLAN_CREATED,
            {
                "plan_id": plan.id,
                "goal_id": goal_id,
                "state": plan.state.value,
                "tasks": [
                    {
                        "id": t.id,
                        "capability": t.capability,
                        "depends_on": t.depends_on,
                        "params": t.params,
                        "priority": t.priority.value,
                    }
                    for t in plan.tasks
                ],
            },
            correlation_id=event.correlation_id,
        )

        logger.info(f"Plan created: {plan.id} with {len(plan.tasks)} tasks")

    async def create_plan(self, goal: Goal) -> Plan:
        """Crée un plan à partir d'un goal.

        Args:
            goal: Goal à planifier

        Returns:
            Plan créé
        """
        # 1. Décomposer en tâches
        tasks = await self.decomposer.decompose(goal)

        # 2. Construire le DAG
        dag = self.dag_builder.build(tasks)

        # 3. Créer le plan
        plan = Plan(
            id=f"plan-{goal.id}",
            goal_id=goal.id,
            state=PlanState.READY,
            tasks=tasks,
            dag=dag,
            priority=goal.priority,
        )

        # 4. Optimiser
        plan = self.optimizer.optimize(plan)

        # 5. Sauvegarder checkpoint initial
        if self.checkpoint_mgr:
            await self.checkpoint_mgr.save_checkpoint(plan, {
                "completed": [],
                "running": [],
                "pending": [t.id for t in tasks],
            })

        # 6. Stocker le plan
        self._plans[plan.id] = plan

        logger.info(f"Plan created: {plan.id} ({len(tasks)} tasks)")
        return plan

    async def modify_plan(self, plan_id: str, modifications: dict[str, Any]) -> Plan:
        """Modifie un plan en cours.

        Args:
            plan_id: ID du plan
            modifications: Modifications à appliquer

        Returns:
            Plan modifié

        Raises:
            ValueError: Si le plan n'existe pas ou est dans un état invalide
        """
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")

        # Vérifier l'état
        if plan.state not in [PlanState.READY, PlanState.PAUSED]:
            raise ValueError(f"Cannot modify plan in state {plan.state}")

        # Appliquer les modifications
        if "add_task" in modifications:
            new_task = modifications["add_task"]
            plan.tasks.append(new_task)
            self.dag_builder.add_task(plan.dag, new_task)

        if "remove_task" in modifications:
            task_id = modifications["remove_task"]
            plan.tasks = [t for t in plan.tasks if t.id != task_id]
            self.dag_builder.remove_task(plan.dag, task_id)

        if "reprioritize" in modifications:
            plan.priority = modifications["reprioritize"]

        # Sauvegarder checkpoint
        if self.checkpoint_mgr:
            await self.checkpoint_mgr.save_checkpoint(plan, self._get_execution_state(plan))

        logger.info(f"Plan modified: {plan_id}")
        return plan

    async def pause_plan(self, plan_id: str) -> None:
        """Met en pause un plan.

        Args:
            plan_id: ID du plan
        """
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")

        if plan.state != PlanState.EXECUTING:
            raise ValueError(f"Cannot pause plan in state {plan.state}")

        # Sauvegarder checkpoint
        if self.checkpoint_mgr:
            await self.checkpoint_mgr.save_checkpoint(plan, self._get_execution_state(plan))

        plan.state = PlanState.PAUSED
        logger.info(f"Plan paused: {plan_id}")

    async def resume_plan(self, plan_id: str) -> Plan:
        """Reprend un plan en pause.

        Args:
            plan_id: ID du plan

        Returns:
            Plan repris
        """
        plan = self._plans.get(plan_id)
        if not plan:
            # Essayer de charger depuis checkpoint
            if self.checkpoint_mgr:
                checkpoint = await self.checkpoint_mgr.load_checkpoint(plan_id)
                if checkpoint:
                    plan = self._plans.get(plan_id)
                    if plan:
                        # Restaurer les états des tâches
                        for task_id in checkpoint.completed_tasks:
                            task = plan.get_task(task_id)
                            if task:
                                task.state = "completed"
                        for task_id in checkpoint.running_tasks:
                            task = plan.get_task(task_id)
                            if task:
                                task.state = "running"

        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")

        if plan.state != PlanState.PAUSED:
            raise ValueError(f"Cannot resume plan in state {plan.state}")

        plan.state = PlanState.EXECUTING
        logger.info(f"Plan resumed: {plan_id}")
        return plan

    async def cancel_plan(self, plan_id: str) -> None:
        """Annule un plan.

        Args:
            plan_id: ID du plan
        """
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")

        plan.state = PlanState.CANCELLED

        # Supprimer les checkpoints
        if self.checkpoint_mgr:
            await self.checkpoint_mgr.delete_checkpoint(plan_id)

        logger.info(f"Plan cancelled: {plan_id}")

    def get_plan(self, plan_id: str) -> Plan | None:
        """Récupère un plan.

        Args:
            plan_id: ID du plan

        Returns:
            Plan ou None
        """
        return self._plans.get(plan_id)

    def list_plans(self) -> list[Plan]:
        """Liste tous les plans actifs.

        Returns:
            Liste de plans
        """
        return list(self._plans.values())

    def _get_execution_state(self, plan: Plan) -> dict[str, Any]:
        """Récupère l'état d'exécution d'un plan."""
        return {
            "completed": [t.id for t in plan.tasks if t.state == "completed"],
            "running": [t.id for t in plan.tasks if t.state == "running"],
            "pending": [t.id for t in plan.tasks if t.state == "pending"],
            "metadata": plan.metadata,
        }

    async def run(self, input_data: dict[str, Any] | None = None) -> Result:
        """Point d'entrée standalone."""
        return Result.ok(data={"status": "planner ready"})