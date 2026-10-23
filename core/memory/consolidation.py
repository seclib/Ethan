"""ConsolidationAgent — Extraction post-échange fire-and-forget."""
from __future__ import annotations
import asyncio
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ConsolidationAgent:
    """Extrait les faits déchange après chaque tour de conversation."""
    
    def __init__(
        self,
        ingest_fn: Callable[[str, str, str], Any] | None = None,
    ):
        self._ingest = ingest_fn
    
    def fire(self, user_message: str, assistant_message: str) -> None:
        """Lance l’extraction en fire-and-forget."""
        if self._ingest is None:
            return
        asyncio.create_task(self._run(user_message, assistant_message))
    
    async def _run(self, user: str, assistant: str) -> None:
        try:
            exchange = f"User: {user}\nAssistant: {assistant}"
            await self._ingest(exchange, "consolidation", "exchange")
            logger.debug("ConsolidationAgent: done")
        except Exception as e:
            logger.warning("ConsolidationAgent: error: %s", e)
