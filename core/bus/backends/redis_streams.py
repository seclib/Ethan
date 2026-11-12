"""Redis Streams Backend — Stockage via Redis Streams."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, AsyncIterator

from core.bus.backends.base import StorageBackend
from core.bus.snapshot import Snapshot
from core.bus.store import Checkpoint, StoredEvent

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
        """Lit les événements depuis Redis Streams."""
        if not self._redis:
            return

        # Redis Streams ne supporte pas nativement les patterns de sujets comme NATS.
        # Pour le replay, on lit le stream principal.
        stream_key = self._stream_key

        # On commence la lecture depuis le début ou un ID spécifique
        last_id = "0-0"

        while True:
            # XREADGROUP ou XREAD
            # On récupère des chunks de 100 événements
            events = await self._redis.xread({stream_key: last_id}, count=100)
            if not events:
                break

            for stream, messages in events:
                for msg_id, data in messages:
                    # data est un dict : {"id": ..., "type": ..., ...}
                    import json
                    event_time = datetime.fromisoformat(data["timestamp"])

                    if event_time < start_time:
                        last_id = msg_id
                        continue
                    if end_time and event_time > end_time:
                        return

                    # Filtrage par pattern de sujet (simulation car Redis Stream est plat ici)
                    # On vérifie si le type d'événement correspond au pattern
                    from core.bus.router import EventRouter
                    # On utilise fnmatch pour le pattern matching comme dans le Router
                    import fnmatch
                    event_type = data["type"]
                    if not fnmatch.fnmatch(event_type, subject_pattern):
                        last_id = msg_id
                        continue

                    event = Event(
                        id=data["id"],
                        type=EventType(data["type"]),
                        source=data["source"],
                        timestamp=event_time,
                        payload=json.loads(data["payload"]),
                        metadata=json.loads(data["metadata"]),
                    )

                    yield StoredEvent(
                        event=event,
                        position=int(data["position"]),
                        stored_at=event_time,
                        size_bytes=len(str(data)),
                    )
                    last_id = msg_id


    async def save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Sauvegarde un checkpoint."""
        import json

        key = f"ethan:checkpoint:{checkpoint.id}"
        await self._redis.hset(
            key,
            mapping={
                "id": checkpoint.id,
                "subject_pattern": checkpoint.subject_pattern,
                "timestamp": checkpoint.timestamp.isoformat(),
                "position": str(checkpoint.position),
                "metadata": json.dumps(checkpoint.metadata),
            },
        )

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
        await self._redis.hset(
            key,
            mapping={
                "id": snapshot.id,
                "position": str(snapshot.position),
                "state": json.dumps(snapshot.state),
                "created_at": snapshot.created_at.isoformat(),
                "metadata": json.dumps(snapshot.metadata),
            },
        )

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
