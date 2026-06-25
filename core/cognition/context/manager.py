"""Context Manager — Assemble le contexte pour le raisonnement."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ContextManager:
    """Assemble le contexte cognitif pour une requête.

    Combine :
    - Historique de session
    - Mémoire à long terme
    - Contexte système
    """

    def __init__(self, memory_store=None):
        self._memory = memory_store

    async def assemble(
        self,
        session_id: str,
        query: str,
        intent: Any,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Assemble le contexte complet.

        Args:
            session_id: ID de session
            query: Requête utilisateur
            intent: Intent analysé
            max_tokens: Budget tokens

        Returns:
            Contexte assemblé
        """
        context = {
            "session_id": session_id,
            "query": query,
            "intent": intent.type.value if hasattr(intent, 'type') else str(intent),
            "messages": [],
            "memory_items": [],
            "system_state": {},
        }

        # 1. Récupérer l'historique de session
        if self._memory:
            try:
                history = await self._memory.search(f"session:{session_id}", query, limit=5)
                context["messages"] = [
                    {"role": "history", "content": r.value, "score": r.score}
                    for r in history
                ]
            except Exception as e:
                logger.warning(f"Failed to retrieve history: {e}")

        # 2. TODO: Récupérer les connaissances (VectorStore)

        # 3. TODO: Récupérer les goals actifs

        return context

    async def add_message(self, session_id: str, role: str, content: str) -> None:
        """Ajoute un message au contexte de session.

        Args:
            session_id: ID de session
            role: Rôle (user, assistant, system)
            content: Contenu du message
        """
        if self._memory:
            try:
                await self._memory.store(
                    f"session:{session_id}",
                    f"msg:{len(content)}",
                    {"role": role, "content": content},
                    ttl=3600,  # 1 heure
                )
            except Exception as e:
                logger.warning(f"Failed to store message: {e}")