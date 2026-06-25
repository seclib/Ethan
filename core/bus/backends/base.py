"""Storage Backend — Interface abstraite pour les backends de stockage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator

from core.bus.store import StoredEvent, Checkpoint
from core.bus.snapshot import Snapshot


class StorageBackend(ABC):
    """Interface abstraite pour les backends de stockage."""

    @abstractmethod
    async def write(self, stored_event: StoredEvent) -> None:
        """Écrit un événement."""
        pass

    @abstractmethod
    def read(
        self,
        subject_pattern: str,
        start_time: datetime,
        end_time: datetime | None = None,
    ) -> AsyncIterator[StoredEvent]:
        """Lit les événements."""
        pass

    @abstractmethod
    async def save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Sauvegarde un checkpoint."""
        pass

    @abstractmethod
    async def get_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """Récupère un checkpoint."""
        pass

    @abstractmethod
    async def get_latest_checkpoint(self, subject_pattern: str) -> Checkpoint | None:
        """Récupère le dernier checkpoint."""
        pass

    @abstractmethod
    async def save_snapshot(self, snapshot: Snapshot) -> None:
        """Sauvegarde un snapshot."""
        pass

    @abstractmethod
    async def get_snapshot(self, snapshot_id: str) -> Snapshot | None:
        """Récupère un snapshot."""
        pass

    @abstractmethod
    async def get_latest_snapshot(self) -> Snapshot | None:
        """Récupère le dernier snapshot."""
        pass

    @abstractmethod
    async def get_snapshot_at_position(self, position: int) -> Snapshot | None:
        """Récupère le snapshot le plus proche d'une position."""
        pass

    @abstractmethod
    async def delete_snapshot(self, snapshot_id: str) -> None:
        """Supprime un snapshot."""
        pass