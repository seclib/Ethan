"""Context Agent — Module d'assemblage du contexte.

Responsabilités :
- Assemble le contexte pour les agents (mémoire + historique)
- Gère la fenêtre de contexte (token budget)
- Filtre et priorise les informations pertinentes

Communication :
- Reçoit : ethan.context.assemble.request
- Publie : ethan.context.assembled
"""

from __future__ import annotations

import logging
from typing import Any

from core.agents.base import Agent, AgentConfig
from core.memory.interface import MemoryStore
from core.types.event import Event, EventType
from core.types.result import Result

logger = logging.getLogger(__name__)


class ContextAgent(Agent):
    """Agent contexte — assemble le contexte pour les requêtes."""

    def __init__(self, config: AgentConfig, bus=None, store: MemoryStore | None = None):
        super().__init__(config, bus)
        self._store = store

    async def _on_init(self) -> None:
        logger.info("Context agent initializing...")

    async def _subscribe_events(self) -> None:
        await self.subscribe("ethan.context.assemble.request", self._handle_assemble)

    async def _handle_assemble(self, event: Event) -> None:
        """Assemble le contexte pour une requête."""
        session_id = event.payload.get("session_id", "default")
        query = event.payload.get("query", "")
        max_tokens = event.payload.get("max_tokens", 4096)

        logger.info(f"Context agent assembling context for session {session_id}")

        context_items = []

        # 1. Récupérer l'historique de la session
        if self._store:
            try:
                history = await self._store.search(f"session:{session_id}", query, limit=10)
                context_items.extend([
                    {"type": "history", "content": r.value, "score": r.score}
                    for r in history
                ])
            except Exception as e:
                logger.warning(f"Failed to retrieve history: {e}")

        # 2. TODO: Récupérer les connaissances pertinentes (VectorStore)

        # 3. TODO: Récupérer les goals actifs

        # Publier le contexte assemblé
        await self.publish(
            EventType.CONTEXT_ASSEMBLED,
            {
                "session_id": session_id,
                "query": query,
                "context": context_items,
                "token_count": len(str(context_items)),  # Approximation
                "max_tokens": max_tokens,
            },
            correlation_id=event.correlation_id,
        )

        logger.info(f"Context assembled: {len(context_items)} items")

    async def run(self, input_data=None) -> Result:
        """Point d'entrée standalone."""
        return Result.ok(data={"status": "context ready"})