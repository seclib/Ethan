"""Redis Streams Backend — Stockage via Redis Streams."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, AsyncIterator

from core.bus.backends.base import StorageBackend
from core.bus.store import StoredEvent, Checkpoint
from core.bus.snapshot import Snapshot

logger = logging.getLogger(__name__)


class RedisStreamsBackend(StorageBackend):
    """Backend Redis Streams.
    
    Pour cache hot et streaming rapide.
    - Très rapide
    - TTL automatique
    - Consumer groups
    """

    def __init__(self, redis_client: Any, stream_key: str = "ethan:events"):
        self._redis = redis_client
        self._stream_key = stream_key

    async def initialize(self) -> None:
        """Initialise le stream."""
        logger.info(f"Redis Streams backend initialized ({self._stream_key})")

    async def write(self, stored_event: StoredEvent) -> None:
        """Écrit un événement."""
        import json

        data = {
            "id": stored_event.event.id,
            "type": stored_event.event.type.value,
            "source": stored_event.event.source,
            "timestamp": stored_event.event.timestamp.isoformat(),
            "payload": json.dumps(stored_event.event.payload),
            "metadata": json.dumps(stored_event.event.metadata),
            "position": str(stored_event.position),
        }

        await self._redis.xadd(
            self._stream_key,
            data,
            maxlen=100000,  # Limiter à 100k événements
        )

    async def read(
        self,
        subject_pattern: str,
        start_time: datetime,
        end_time: datetime | None = None,
    ) -> AsyncIterator[StoredEvent]:
        """Lit les événements."""
        # TODO: Implémenter avec Redis consumer
        # Pour l'instant, yield vide
        return
        yield  # type: ignore

    async def save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Sauvegarde un checkpoint."""
        import json

        key = f"ethan:checkpoint:{checkpoint.id}"
        await self._redis.hset(key, mapping={
            "id": checkpoint.id,
            "subject_pattern": checkpoint.subject_pattern,
            "timestamp": checkpoint.timestamp.isoformat(),
            "position": str(checkpoint.position),
            "metadata": json.dumps(checkpoint.metadata),
        })

    async def get_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """Récupère un checkpoint."""
        key = f"ethan:checkpoint:{checkpoint_id}"
        data = await self._redis.hgetall(key)

        if not data:
            return None

        return Checkpoint(
            id=data["id"],
            subject_pattern=data["subject_pattern"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            position=int(data["position"]),
            metadata=__import__("json").loads(data.get("metadata", "{}")),
        )

    async def get_latest_checkpoint(self, subject_pattern: str) -> Checkpoint | None:
        """Récupère le dernier checkpoint."""
        # TODO: Implémenter
        return None

    async def save_snapshot(self, snapshot: Snapshot) -> None:
        """Sauvegarde un snapshot."""
        import json

        key = f"ethan:snapshot:{snapshot.id}"
        await self._redis.hset(key, mapping={
            "id": snapshot.id,
            "position": str(snapshot.position),
            "state": json.dumps(snapshot.state),
            "created_at": snapshot.created_at.isoformat(),
            "metadata": json.dumps(snapshot.metadata),
        })

    async def get_snapshot(self, snapshot_id: str) -> Snapshot | None:
        """Récupère un snapshot."""
        key = f"ethan:snapshot:{snapshot_id}"
        data = await self._redis.hgetall(key)

        if not data:
            return None

        return Snapshot(
            id=data["id"],
            position=int(data["position"]),
            state=__import__("json").loads(data["state"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=__import__("json").loads(data.get("metadata", "{}")),
        )

    async def get_latest_snapshot(self) -> Snapshot | None:
        """Récupère le dernier snapshot."""
        # TODO: Implémenter
        return None

    async def get_snapshot_at_position(self, position: int) -> Snapshot | None:
        """Récupère le snapshot le plus proche."""
        # TODO: Implémenter
        return None

    async def delete_snapshot(self, snapshot_id: str) -> None:
        """Supprime un snapshot."""
        key = f"ethan:snapshot:{snapshot_id}"
        await self._redis.delete(key)