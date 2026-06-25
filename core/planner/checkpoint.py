"""Checkpoint Manager — Gère les checkpoints pour reprise.

Responsabilités :
- Sauvegarder l'état d'un plan
- Charger un checkpoint
- Reprendre un plan interrompu
- Gérer les tâches longues
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from core.planner.types import Plan, Checkpoint

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Gère les checkpoints pour reprise après interruption."""

    def __init__(self, store=None):
        self._store = store

    async def save_checkpoint(self, plan: Plan, execution_state: dict[str, Any]) -> str:
        """Sauvegarde un checkpoint.

        Args:
            plan: Plan en cours
            execution_state: État d'exécution

        Returns:
            ID du checkpoint
        """
        checkpoint = Checkpoint(
            id=f"checkpoint:{plan.id}:{datetime.utcnow().timestamp()}",
            plan_id=plan.id,
            timestamp=datetime.utcnow(),
            completed_tasks=execution_state.get("completed", []),
            running_tasks=execution_state.get("running", []),
            pending_tasks=execution_state.get("pending", []),
            metadata=execution_state.get("metadata", {}),
        )

        # Stocker dans le store (Redis de préférence pour TTL)
        if self._store:
            try:
                await self._store.store(
                    namespace="checkpoints",
                    key=checkpoint.id,
                    value={
                        "plan_id": checkpoint.plan_id,
                        "timestamp": checkpoint.timestamp.isoformat(),
                        "completed_tasks": checkpoint.completed_tasks,
                        "running_tasks": checkpoint.running_tasks,
                        "pending_tasks": checkpoint.pending_tasks,
                        "metadata": checkpoint.metadata,
                    },
                    ttl=86400,  # 24 heures
                )
            except Exception as e:
                logger.warning(f"Failed to save checkpoint: {e}")

        logger.info(f"Checkpoint saved: {checkpoint.id}")
        return checkpoint.id

    async def load_checkpoint(self, plan_id: str) -> Checkpoint | None:
        """Charge le dernier checkpoint d'un plan.

        Args:
            plan_id: ID du plan

        Returns:
            Checkpoint ou None
        """
        if not self._store:
            return None

        try:
            # Lister les checkpoints pour ce plan
            pattern = f"checkpoint:checkpoint:{plan_id}:*"
            keys = await self._store.list_namespace("checkpoints")

            # Filtrer par plan_id
            plan_checkpoints = [
                k for k in keys
                if k.startswith(f"checkpoint:{plan_id}:")
            ]

            if not plan_checkpoints:
                return None

            # Prendre le plus récent (tri par timestamp)
            plan_checkpoints.sort(reverse=True)
            latest_key = plan_checkpoints[0]

            # Charger
            data = await self._store.get("checkpoints", latest_key)
            if not data:
                return None

            return Checkpoint(
                id=latest_key,
                plan_id=data["plan_id"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                completed_tasks=data["completed_tasks"],
                running_tasks=data["running_tasks"],
                pending_tasks=data["pending_tasks"],
                metadata=data.get("metadata", {}),
            )

        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    async def resume_from_checkpoint(self, plan_id: str, tasks: list[Any]) -> Plan | None:
        """Reprend un plan depuis un checkpoint.

        Args:
            plan_id: ID du plan
            tasks: Liste de toutes les tâches du plan

        Returns:
            Plan restauré ou None
        """
        checkpoint = await self.load_checkpoint(plan_id)
        if not checkpoint:
            return None

        # Créer un mapping id -> task
        task_map = {t.id: t for t in tasks}

        # Restaurer les états
        for task_id in checkpoint.completed_tasks:
            if task_id in task_map:
                task_map[task_id].state = "completed"

        for task_id in checkpoint.running_tasks:
            if task_id in task_map:
                task_map[task_id].state = "running"

        for task_id in checkpoint.pending_tasks:
            if task_id in task_map:
                task_map[task_id].state = "pending"

        logger.info(f"Resumed plan {plan_id} from checkpoint {checkpoint.id}")
        return checkpoint

    async def delete_checkpoint(self, plan_id: str) -> None:
        """Supprime tous les checkpoints d'un plan.

        Args:
            plan_id: ID du plan
        """
        if not self._store:
            return

        try:
            keys = await self._store.list_namespace("checkpoints")
            plan_keys = [k for k in keys if k.startswith(f"checkpoint:{plan_id}:")]

            for key in plan_keys:
                await self._store.delete("checkpoints", key)

            logger.info(f"Deleted {len(plan_keys)} checkpoints for plan {plan_id}")

        except Exception as e:
            logger.error(f"Failed to delete checkpoints: {e}")

    async def list_checkpoints(self, plan_id: str) -> list[Checkpoint]:
        """Liste tous les checkpoints d'un plan.

        Args:
            plan_id: ID du plan

        Returns:
            Liste de checkpoints
        """
        if not self._store:
            return []

        try:
            keys = await self._store.list_namespace("checkpoints")
            plan_keys = [k for k in keys if k.startswith(f"checkpoint:{plan_id}:")]

            checkpoints = []
            for key in plan_keys:
                data = await self._store.get("checkpoints", key)
                if data:
                    checkpoints.append(Checkpoint(
                        id=key,
                        plan_id=data["plan_id"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        completed_tasks=data["completed_tasks"],
                        running_tasks=data["running_tasks"],
                        pending_tasks=data["pending_tasks"],
                        metadata=data.get("metadata", {}),
                    ))

            return sorted(checkpoints, key=lambda c: c.timestamp, reverse=True)

        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []