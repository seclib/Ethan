"""CrossSessionRecall — Rappel cross-session."""
from __future__ import annotations
import asyncio
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class CrossSessionRecall:
    """Rappel cross-session : recherche FTS5 + résumé LLM."""

    def __init__(
        self,
        fts_search_fn: Callable[[str, int], list[dict]] | None = None,
        llm_summarize_fn: Callable[[str], str] | None = None,
        max_chars: int = 3000,
    ):
        self._fts = fts_search_fn
        self._llm = llm_summarize_fn
        self._max_chars = max_chars

    async def recall(self, query: str, k: int = 6) -> str | None:
        if not query.strip() or self._fts is None:
            return None
        try:
            results = self._fts(query, k)
        except Exception as e:
            logger.warning("CrossSessionRecall: FTS failed: %s", e)
            return None
        if not results:
            return None
        excerpts = [r.get("text", "")[:400].strip() for r in results if r.get("text")]
        if not excerpts:
            return None
        context = "\n---\n".join(excerpts)[:self._max_chars]
        if self._llm is None:
            return context[:500] or None
        try:
            summary = await self._llm(f"Résumé pour '{query}':\n{context}")
            return str(summary).strip() or None
        except Exception as e:
            logger.warning("CrossSessionRecall: LLM failed: %s", e)
            return context[:500] or None