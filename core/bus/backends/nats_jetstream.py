"""NATS JetStream Backend — Stockage via NATS JetStream."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, AsyncIterator

from core.bus.backends.base import StorageBackend
from core.bus.store import StoredEvent, Checkpoint
from core.bus.snapshot import Snapshot

logger = logging.getLogger(__name__)


class NATSJetStreamBackend(StorageBackend):
    """Backend NATS JetStream.
    
    Pour production.
    - Persistance distribuée
    - Retentions configurables
    - Replay natif
    """

    def __init__(self, nats_client: Any, stream_name: str = "ETHAN_EVENTS"):
        self._nc = nats_client
        self._stream_name = stream_name
        self._js = None

    async def initialize(self) -> None:
        """Initialise le stream JetStream."""
        if self._nc:
            self._js = self._nc.jetstream()
            # Créer le stream si nécessaire
            try:
                await self._js.stream_info(self._stream_name)
            except Exception:
                await self._js.add_stream(
                    name=self._stream_name,
                    subjects=["ethan.>"],
                    retention="limits",
                    max_age=3600,  # 1 heure par défaut
                    max_bytes=10 * 1024 * 1024 * 1024,  # 10 GB
                )
                logger.info(f"JetStream created: {self._stream_name}")

    async def write(self, stored_event: StoredEvent) -> None:
        """Écrit un événement."""
        if not self._js:
            raise RuntimeError("JetStream not initialized")

        import json
        data = json.dumps({
            "id": stored_event.event.id,
            "type": stored_event.event.type.value,
            "source": stored_event.event.source,
            "timestamp": stored_event.event.timestamp.isoformat(),
            "payload": stored_event.event.payload,
            "metadata": stored_event.event.metadata,
            "position": stored_event.position,
        }).encode("utf-8")

        await self._js.publish(
            f"ethan.event.{stored_event.event.type.value}",
            data,
        )

    async def read(
        self,
        subject_pattern: str,
        start_time: datetime,
        end_time: datetime | None = None,
    ) -> AsyncIterator[StoredEvent]:
        """Lit les événements."""
        # TODO: Implémenter avec JetStream consumer
        # Pour l'instant, yield vide
        return
        yield  # type: ignore

    async def save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Sauvegarde un checkpoint."""
        # Stocker dans un sujet dédié
        pass

    async def get_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """Récupère un checkpoint."""
        return None

    async def get_latest_checkpoint(self, subject_pattern: str) -> Checkpoint | None:
        """Récupère le dernier checkpoint."""
        return None

    async def save_snapshot(self, snapshot: Snapshot) -> None:
        """Sauvegarde un snapshot."""
        pass

    async def get_snapshot(self, snapshot_id: str) -> Snapshot | None:
        """Récupère un snapshot."""
        return None

    async def get_latest_snapshot(self) -> Snapshot | None:
        """Récupère le dernier snapshot."""
        return None

    async def get_snapshot_at_position(self, position: int) -> Snapshot | None:
        """Récupère le snapshot le plus proche."""
        return None

    async def delete_snapshot(self, snapshot_id: str) -> None:
        """Supprime un snapshot."""
        pass