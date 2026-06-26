"""Event Store — Persistance et replay des événements."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator
from uuid import uuid4

from core.types.event import Event

logger = logging.getLogger(__name__)


@dataclass
class StoredEvent:
    """Événement stocké avec métadonnées."""
    event: Event
    position: int
    stored_at: datetime
    size_bytes: int


@dataclass
class Checkpoint:
    """Checkpoint pour replay."""
    id: str
    subject_pattern: str
    timestamp: datetime
    position: int
    metadata: dict[str, Any] = field(default_factory=dict)


class EventStore:
    """Stocke les événements pour replay et audit.
    
    Responsabilités :
    - Append-only log
    - Rétention configurable
    - Replay depuis un point
    - Checkpoints
    """

    def __init__(self, backend: Any):
        self._backend = backend
        self._retention_days = 30
        self._max_size_gb = 100
        self._position = 0

    async def append(self, event: Event) -> int:
        """Ajoute un événement au store.

        Args:
            event: Événement

        Returns:
            Position dans le log
        """
        self._position += 1
        
        stored_event = StoredEvent(
            event=event,
            position=self._position,
            stored_at=datetime.utcnow(),
            size_bytes=len(str(event.payload)),
        )

        await self._backend.write(stored_event)
        logger.debug(f"Event stored at position {self._position}: {event.type}")

        # Vérifier la rétention
        await self._apply_retention()

        return self._position

    async def read(
        self,
        subject_pattern: str,
        start_time: datetime,
        end_time: datetime | None = None,
    ) -> AsyncIterator[Event]:
        """Lit les événements.

        Args:
            subject_pattern: Pattern de sujets
            start_time: Date de début
            end_time: Date de fin (optionnel)

        Yields:
            Événements
        """
        async for stored_event in self._backend.read(subject_pattern, start_time, end_time):
            yield stored_event.event

    async def replay(
        self,
        subject_pattern: str,
        start_time: datetime,
        end_time: datetime | None = None,
    ) -> AsyncIterator[Event]:
        """Replay des événements.

        Args:
            subject_pattern: Pattern de sujets
            start_time: Date de début
            end_time: Date de fin (optionnel)

        Yields:
            Événements
        """
        logger.info(f"Replaying events from {start_time} to {end_time or 'now'}")
        
        count = 0
        async for event in self.read(subject_pattern, start_time, end_time):
            count += 1
            yield event
        
        logger.info(f"Replay complete: {count} events")

    async def replay_from_checkpoint(self, checkpoint_id: str) -> AsyncIterator[Event]:
        """Replay depuis un checkpoint.

        Args:
            checkpoint_id: ID du checkpoint

        Yields:
            Événements après le checkpoint
        """
        checkpoint = await self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        async for event in self.replay(
            checkpoint.subject_pattern,
            checkpoint.timestamp,
        ):
            yield event

    async def create_checkpoint(self, subject_pattern: str) -> str:
        """Crée un checkpoint.

        Args:
            subject_pattern: Pattern de sujets

        Returns:
            ID du checkpoint
        """
        checkpoint_id = str(uuid4())
        checkpoint = Checkpoint(
            id=checkpoint_id,
            subject_pattern=subject_pattern,
            timestamp=datetime.utcnow(),
            position=self._position,
        )

        await self._backend.save_checkpoint(checkpoint)
        logger.info(f"Checkpoint created: {checkpoint_id} at position {self._position}")

        return checkpoint_id

    async def get_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """Récupère un checkpoint.

        Args:
            checkpoint_id: ID du checkpoint

        Returns:
            Checkpoint ou None
        """
        return await self._backend.get_checkpoint(checkpoint_id)

    async def get_latest_checkpoint(self, subject_pattern: str) -> Checkpoint | None:
        """Récupère le dernier checkpoint pour un pattern.

        Args:
            subject_pattern: Pattern de sujets

        Returns:
            Checkpoint ou None
        """
        return await self._backend.get_latest_checkpoint(subject_pattern)

    async def _apply_retention(self) -> None:
        """Applique la politique de rétention."""
        # TODO: Implémenter la suppression des vieux événements
        pass

    async def get_stats(self) -> dict[str, Any]:
        """Récupère les statistiques.

        Returns:
            Statistiques
        """
        return {
            "total_events": self._position,
            "retention_days": self._retention_days,
            "max_size_gb": self._max_size_gb,
        }