"""Search — unified search across ETHAN domains.

Configuration belongs to Core. The WebUI only renders results and sends
queries through the API.

Four search types:
- web: Internet search (via web search skill / integration)
- knowledge: Knowledge nodes (labels, sources, content)
- library: Knowledge collections (documents, RAG)
- conversation: Chat history (messages, titles)

No duplicate search system — this manager delegates to existing Core
managers (KnowledgeManager, ChatStore, RAGPipeline).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["SearchManager", "SearchType"]

SEARCH_TYPES = ("web", "knowledge", "library", "conversation")


class SearchType:
    WEB = "web"
    KNOWLEDGE = "knowledge"
    LIBRARY = "library"
    CONVERSATION = "conversation"


class SearchManager:
    """Unified search across ETHAN domains.

    Delegates to existing Core managers — does NOT duplicate their logic.
    """

    def __init__(
        self,
        knowledge_manager: Any = None,
        chat_store: Any = None,
        rag_pipeline: Any = None,
        web_search_fn=None,
    ) -> None:
        self._knowledge = knowledge_manager
        self._chat = chat_store
        self._rag = rag_pipeline
        self._web_search = web_search_fn

    async def search(
        self,
        query: str,
        search_type: str = "knowledge",
        *,
        limit: int = 20,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Run a search across the specified domain."""
        if not query.strip():
            return {"query": query, "type": search_type, "results": [], "total": 0}

        if search_type == SearchType.WEB:
            return await self._search_web(query, limit=limit)
        if search_type == SearchType.KNOWLEDGE:
            return await self._search_knowledge(query, limit=limit)
        if search_type == SearchType.LIBRARY:
            return await self._search_library(query, limit=limit, **kwargs)
        if search_type == SearchType.CONVERSATION:
            return await self._search_conversation(query, limit=limit)

        logger.warning(f"Unknown search type: {search_type}")
        return {"query": query, "type": search_type, "results": [], "total": 0}

    async def _search_web(self, query: str, *, limit: int) -> dict[str, Any]:
        """Web search via configured web search function."""
        if self._web_search is None:
            return {
                "query": query,
                "type": "web",
                "results": [],
                "total": 0,
                "error": "No web search provider configured",
            }
        try:
            results = await self._web_search(query, limit=limit)
            return {"query": query, "type": "web", "results": results, "total": len(results)}
        except Exception as exc:
            logger.error(f"Web search failed: {exc}")
            return {"query": query, "type": "web", "results": [], "total": 0, "error": str(exc)}

    async def _search_knowledge(self, query: str, *, limit: int) -> dict[str, Any]:
        """Search knowledge nodes (labels, sources, content)."""
        if self._knowledge is None:
            return {
                "query": query,
                "type": "knowledge",
                "results": [],
                "total": 0,
                "error": "Knowledge manager not available",
            }
        try:
            nodes = await self._knowledge.search(query, limit=limit)
            results = [
                {
                    "id": n.get("id"),
                    "title": n.get("label", ""),
                    "content": n.get("content", ""),
                    "source": n.get("source", ""),
                    "type": n.get("node_type", ""),
                    "created_at": n.get("created_at"),
                }
                for n in nodes
            ]
            return {"query": query, "type": "knowledge", "results": results, "total": len(results)}
        except Exception as exc:
            logger.error(f"Knowledge search failed: {exc}")
            return {"query": query, "type": "knowledge", "results": [], "total": 0, "error": str(exc)}

    async def _search_library(self, query: str, *, limit: int, **kwargs: Any) -> dict[str, Any]:
        """Search knowledge library (collections + RAG documents)."""
        results: list[dict[str, Any]] = []

        # Search collections by name/description
        if self._knowledge is not None:
            try:
                collections = await self._knowledge.list_collections()
                terms = [t for t in query.casefold().split() if t]
                for col in collections:
                    haystack = f"{col.get('name', '')} {col.get('description', '')}".casefold()
                    if any(t in haystack for t in terms):
                        results.append({
                            "id": col.get("id"),
                            "title": col.get("name", ""),
                            "description": col.get("description", ""),
                            "type": "collection",
                            "document_count": len(col.get("document_ids", [])),
                        })
            except Exception as exc:
                logger.debug(f"Library collection search skipped: {exc}")

        # Search RAG documents if available
        if self._rag is not None:
            try:
                rag_results = await self._rag.retrieve(query, top_k=limit)
                for item in rag_results:
                    chunk = item.get("chunk", {})
                    results.append({
                        "id": chunk.get("id"),
                        "title": item.get("document_title", ""),
                        "content": chunk.get("content", ""),
                        "score": item.get("score", 0),
                        "type": "rag_chunk",
                    })
            except Exception as exc:
                logger.debug(f"RAG search skipped: {exc}")

        return {"query": query, "type": "library", "results": results[:limit], "total": len(results)}

    async def _search_conversation(self, query: str, *, limit: int) -> dict[str, Any]:
        """Search chat history (titles + message content)."""
        if self._chat is None:
            return {
                "query": query,
                "type": "conversation",
                "results": [],
                "total": 0,
                "error": "Chat store not available",
            }
        try:
            terms = [t for t in query.casefold().split() if t]
            if not terms:
                return {"query": query, "type": "conversation", "results": [], "total": 0}

            scored: list[dict[str, Any]] = []
            chats = await self._chat.list_chats()
            for chat in chats:
                title = chat.get("title", "").casefold()
                if any(t in title for t in terms):
                    scored.append({
                        "id": chat.get("id"),
                        "title": chat.get("title", ""),
                        "type": "chat",
                        "created_at": chat.get("created_at"),
                        "match_in": "title",
                    })

            # Search messages
            messages = await self._chat._store.list("chat-messages")
            for msg in messages:
                content = msg.get("content", "").casefold()
                if any(t in content for t in terms):
                    scored.append({
                        "id": msg.get("id"),
                        "title": msg.get("content", "")[:100],
                        "chat_id": msg.get("chat_id"),
                        "type": "message",
                        "created_at": msg.get("created_at"),
                        "match_in": "content",
                    })

            scored.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return {
                "query": query,
                "type": "conversation",
                "results": scored[:limit],
                "total": len(scored),
            }
        except Exception as exc:
            logger.error(f"Conversation search failed: {exc}")
            return {
                "query": query,
                "type": "conversation",
                "results": [],
                "total": 0,
                "error": str(exc),
            }
