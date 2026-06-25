"""Memory Agent — Module de gestion de la mémoire.

Responsabilités :
- Stocke et récupère des événements
- Gère les sessions
- Indexe pour recherche sémantique (via VectorStore)

Communication :
- Reçoit : ethan.memory.store.request, ethan.memory.recall.request
- Publie : ethan.memory.store.complete, ethan.memory.recall.complete
"""

from __future__ import annotations

import logging
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.memory.interface import MemoryStore
from core.types.event import Event, EventType
from core.types.result import Result

logger = logging.getLogger(__name__)


class MemoryAgent(Agent):
    """Agent mémoire — gestion du stockage et de la récupération."""

    def __init__(self, config: AgentConfig, bus=None, store: MemoryStore | None = None):
        super().__init__(config, bus)
        self._store = store

    async def _on_init(self) -> None:
        logger.info("Memory agent initializing...")
        if self._store:
            await self._store.connect()

    async def _subscribe_events(self) -> None:
        await self.subscribe("ethan.memory.store", self._handle_store)
        await self.subscribe("ethan.memory.recall", self._handle_recall)

    async def _handle_store(self, event: Event) -> None:
        """Stocke une valeur en mémoire."""
        namespace = event.payload.get("namespace", "default")
        key = event.payload.get("key", "")
        value = event.payload.get("value")
        ttl = event.payload.get("ttl")

        if not self._store:
            logger.warning("No memory store configured")
            return

        try:
            await self._store.store(namespace, key, value, ttl=ttl)
            await self.publish(
                EventType.MEMORY_STORE_COMPLETE,
                {"namespace": namespace, "key": key, "status": "stored"},
                correlation_id=event.correlation_id,
            )
            logger.debug(f"Stored: {namespace}:{key}")
        except Exception as e:
            logger.error(f"Failed to store {namespace}:{key}: {e}")

    async def _handle_recall(self, event: Event) -> None:
        """Récupère une valeur de la mémoire."""
        namespace = event.payload.get("namespace", "default")
        key = event.payload.get("key")
        query = event.payload.get("query")  # Pour recherche sémantique

        if not self._store:
            logger.warning("No memory store configured")
            return

        try:
            if query:
                # Recherche sémantique
                results = await self._store.search(namespace, query)
                await self.publish(
                    EventType.MEMORY_RECALL_COMPLETE,
                    {"namespace": namespace, "query": query, "results": results},
                    correlation_id=event.correlation_id,
                )
            elif key:
                # Récupération par clé
                value = await self._store.get(namespace, key)
                await self.publish(
                    EventType.MEMORY_RECALL_COMPLETE,
                    {"namespace": namespace, "key": key, "value": value},
                    correlation_id=event.correlation_id,
                )
        except Exception as e:
            logger.error(f"Failed to recall from {namespace}:{key}: {e}")

    async def run(self, input_data=None) -> Result:
        """Point d'entrée standalone."""
        return Result.ok(data={"status": "memory ready"})