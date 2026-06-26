"""Event Snapshots — Snapshots pour replay rapide."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class Snapshot:
    """Snapshot de l'état du système."""
    id: str
    position: int
    state: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


class SnapshotManager:
    """Gère les snapshots pour replay rapide.
    
    Responsabilités :
    - Création de snapshots
    - Récupération du dernier snapshot
    - Nettoyage des vieux snapshots
    """

    def __init__(self, backend: Any, max_snapshots: int = 100):
        self._backend = backend
        self._max_snapshots = max_snapshots

    async def create_snapshot(self, position: int, state: dict[str, Any]) -> str:
        """Crée un snapshot.

        Args:
            position: Position dans le WAL
            state: État du système

        Returns:
            ID du snapshot
        """
        snapshot_id = str(uuid4())
        snapshot = Snapshot(
            id=snapshot_id,
            position=position,
            state=state,
        )

        await self._backend.save_snapshot(snapshot)
        logger.info(f"Snapshot created: {snapshot_id} at position {position}")

        # Nettoyer les vieux snapshots
        await self._cleanup_old_snapshots()

        return snapshot_id

    async def get_snapshot(self, snapshot_id: str) -> Snapshot | None:
        """Récupère un snapshot.

        Args:
            snapshot_id: ID du snapshot

        Returns:
            Snapshot ou None
        """
        return await self._backend.get_snapshot(snapshot_id)

    async def get_latest_snapshot(self) -> Snapshot | None:
        """Récupère le dernier snapshot.

        Returns:
            Snapshot ou None
        """
        return await self._backend.get_latest_snapshot()

    async def get_snapshot_at_position(self, position: int) -> Snapshot | None:
        """Récupère le snapshot le plus proche d'une position.

        Args:
            position: Position cible

        Returns:
            Snapshot ou None
        """
        return await self._backend.get_snapshot_at_position(position)

    async def delete_snapshot(self, snapshot_id: str) -> None:
        """Supprime un snapshot.

        Args:
            snapshot_id: ID du snapshot
        """
        await self._backend.delete_snapshot(snapshot_id)
        logger.debug(f"Snapshot deleted: {snapshot_id}")

    async def _cleanup_old_snapshots(self) -> None:
        """Nettoie les vieux snapshots."""
        # TODO: Implémenter le nettoyage
        pass

    async def get_stats(self) -> dict[str, Any]:
        """Récupère les statistiques.

        Returns:
            Statistiques
        """
        return {
            "max_snapshots": self._max_snapshots,
        }