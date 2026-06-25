"""NATS Bus — Implémentation NATS JetStream pour la production.

Utilisé en mode distribué (avec Kernel Go).
Communication inter-processus et inter-machine.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from core.bus.interface import EventBus, EventHandler, Subscription
from core.types.event import Event, EventType

logger = logging.getLogger(__name__)


class NATSBus(EventBus):
    """Bus d'événements NATS JetStream.

    Utilisé en production pour la communication distribuée.
    Nécessite un serveur NATS accessible.

    Avantages :
    - Distribution (multi-processus, multi-machine)
    - Persistance JetStream (events survivent aux crashs)
    - Queue groups (load balancing entre workers)
    """

    def __init__(self):
        self._nc: Any = None  # NATS connection
        self._js: Any = None  # JetStream context
        self._subscriptions: list[Any] = []
        self._connected = False

    async def connect(self, servers: str) -> None:
        """Connexion au serveur NATS."""
        try:
            import nats
            from nats.errors import ConnectionError

            self._nc = await nats.connect(
                servers,
                name="ethan-core",
                pedantic=True,
            )
            self._js = self._nc.jetstream()
            self._connected = True
            logger.info(f"NATSBus connected to {servers}")

        except ImportError:
            raise RuntimeError(
                "NATS not installed. Install with: pip install nats-py"
            )
        except ConnectionError as e:
            raise ConnectionError(
                f"Cannot connect to NATS at {servers}: {e}"
            )

    async def publish(self, subject: str, event: Event) -> None:
        """Publie un événement sur un sujet NATS."""
        if not self._connected or self._nc is None:
            raise RuntimeError("NATSBus not connected")

        data = self._serialize_event(event)
        await self._nc.publish(subject, data)
        logger.debug(f"Published {event.type} on {subject}")

    async def subscribe(
        self,
        pattern: str,
        handler: EventHandler,
        queue: str | None = None,
    ) -> Subscription:
        """Souscrit à un pattern NATS."""
        if not self._connected or self._nc is None:
            raise RuntimeError("NATSBus not connected")

        async def _handler(msg: Any) -> None:
            event = self._deserialize_event(msg.data)
            await handler(event)

        sub_id = str(uuid4())

        if queue:
            sub = await self._nc.subscribe(
                pattern,
                cb=_handler,
                queue=queue,
            )
        else:
            sub = await self._nc.subscribe(pattern, cb=_handler)

        self._subscriptions.append(sub)

        logger.debug(f"Subscribed to {pattern} (queue: {queue})")
        return Subscription(id=sub_id, pattern=pattern, handler=handler)

    async def request(
        self,
        subject: str,
        event: Event,
        timeout: float = 30.0,
    ) -> Event | None:
        """Publie une requête et attend une réponse via NATS request/reply."""
        if not self._connected or self._nc is None:
            raise RuntimeError("NATSBus not connected")

        data = self._serialize_event(event)
        try:
            response = await self._nc.request(subject, data, timeout=timeout)
            return self._deserialize_event(response.data)
        except Exception as e:
            logger.warning(f"Request timeout on {subject}: {e}")
            return None

    async def close(self) -> None:
        """Ferme la connexion NATS."""
        # Se désabonner
        for sub in self._subscriptions:
            try:
                await sub.unsubscribe()
            except Exception:
                pass
        self._subscriptions.clear()

        # Fermer la connexion
        if self._nc:
            await self._nc.drain()
            await self._nc.close()
        self._connected = False
        logger.info("NATSBus closed")

    async def is_connected(self) -> bool:
        """Vérifie la connexion NATS."""
        if self._nc is None:
            return False
        return self._nc.is_connected

    # ─── Sérialisation ───────────────────────────────────────────────

    def _serialize_event(self, event: Event) -> bytes:
        """Sérialise un Event en JSON bytes."""
        data = {
            "id": event.id,
            "type": event.type.value,
            "source": event.source,
            "timestamp": event.timestamp.isoformat(),
            "payload": event.payload,
            "metadata": event.metadata,
        }
        return json.dumps(data).encode("utf-8")

    def _deserialize_event(self, data: bytes) -> Event:
        """Désérialise des bytes JSON en Event."""
        raw = json.loads(data.decode("utf-8"))
        return Event(
            id=raw.get("id", str(uuid4())),
            type=EventType(raw.get("type", "ethan.system.boot")),
            source=raw.get("source", "system"),
            timestamp=datetime.fromisoformat(raw.get("timestamp", datetime.utcnow().isoformat())),
            payload=raw.get("payload", {}),
            metadata=raw.get("metadata", {}),
        )