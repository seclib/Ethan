"""Memory Backend — Stockage en mémoire pour tests."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import AsyncIterator

from core.bus.backends.base import StorageBackend
from core.bus.store import StoredEvent, Checkpoint
from core.bus.snapshot import Snapshot

logger = logging.getLogger(__name__)


class MemoryBackend(StorageBackend):
    """Backend de stockage en mémoire.
    
    Pour tests et développement.
    Pas de persistance (données perdues au redémarrage).
    """

    def __init__(self):
        self._events: list[StoredEvent] = []
        self._checkpoints: dict[str, Checkpoint] = {}
        self._snapshots: dict[str, Snapshot] = {}

    async def write(self, stored_event: StoredEvent) -> None:
        """Écrit un événement."""
        self._events.append(stored_event)

    async def read(
        self,
        subject_pattern: str,
        start_time: datetime,
        end_time: datetime | None = None,
    ) -> AsyncIterator[StoredEvent]:
        """Lit les événements."""
        for stored_event in self._events:
            if stored_event.event.timestamp < start_time:
                continue
            if end_time and stored_event.event.timestamp > end_time:
                continue
            yield stored_event

    async def save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Sauvegarde un checkpoint."""
        self._checkpoints[checkpoint.id] = checkpoint

    async def get_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """Récupère un checkpoint."""
        return self._checkpoints.get(checkpoint_id)

    async def get_latest_checkpoint(self, subject_pattern: str) -> Checkpoint | None:
        """Récupère le dernier checkpoint."""
        latest = None
        for checkpoint in self._checkpoints.values():
            if checkpoint.subject_pattern == subject_pattern:
                if latest is None or checkpoint.timestamp > latest.timestamp:
                    latest = checkpoint
        return latest

    async def save_snapshot(self, snapshot: Snapshot) -> None:
        """Sauvegarde un snapshot."""
        self._snapshots[snapshot.id] = snapshot

    async def get_snapshot(self, snapshot_id: str) -> Snapshot | None:
        """Récupère un snapshot."""
        return self._snapshots.get(snapshot_id)

    async def get_latest_snapshot(self) -> Snapshot | None:
        """Récupère le dernier snapshot."""
        latest = None
        for snapshot in self._snapshots.values():
            if latest is None or snapshot.created_at > latest.created_at:
                latest = snapshot
        return latest

    async def get_snapshot_at_position(self, position: int) -> Snapshot | None:
        """Récupère le snapshot le plus proche d'une position."""
        closest = None
        min_diff = float('inf')
        for snapshot in self._snapshots.values():
            diff = abs(snapshot.position - position)
            if diff < min_diff:
                min_diff = diff
                closest = snapshot
        return closest

    async def delete_snapshot(self, snapshot_id: str) -> None:
        """Supprime un snapshot."""
        self._snapshots.pop(snapshot_id, None)