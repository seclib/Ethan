"""Memory — abstraction mémoire d'ETHAN (ADR-1005).

Deux contrats abstraits, technologies remplaçables :
- ``MemoryStore`` (ABC)  : working memory (Redis) / long-term (PostgreSQL) ;
- ``MemoryBackend`` (ABC): backends vectoriels (ChromaDB, Qdrant, …).

Le Core ne consomme que ces abstractions — l'infrastructure est un détail
d'implémentation injecté au démarrage.
"""

from abc import ABC

from .interface import (
    MemoryBackend as _InterfaceMemoryBackend,
    MemoryEntry as _MemoryEntryInterface,
    MemoryStore,
    SearchResult,
    VectorSearchResult,
)


class MemoryBackend(_InterfaceMemoryBackend, ABC):
    """Facade canonique conservant le contrat MemoryBackend de l'interface."""

class MemoryEntry(_MemoryEntryInterface, ):
    """Cogitive entry key value namespace metadata timestamp ttl embedding."""

    pass


class MemorySystem(_InterfaceMemoryBackend):
    """Cogitive backend with methods store retrieve search delete list_namespaces clear."""

    def __init__(self, backend: Any | None = None):
        self._backend = backend

    async def store(self, entry: Any) -> None:
        if self._backend is not None:
            await self._backend.store(entry)

    async def retrieve(self, key: str, namespace: str = "default"):
        if self._backend is not None:
            return await self._backend.retrieve(key, namespace)
        return None

    async def search(self, *args: Any, **kwargs: Any):
        if self._backend is not None:
            return await self._backend.search(*args, **kwargs)
        return []

    async def delete(self, key: str, namespace: str = "default") -> bool:
        if self._backend is not None:
            return await self._backend.delete(key, namespace)
        return False

    async def list_namespaces(self) -> list[str]:
        if self._backend is not None:
            return await self._backend.list_namespaces()
        return []

    async def clear(self, namespace: str | None = None) -> None:
        if self._backend is not None:
            await self._backend.clear(namespace)
from .types import MemoryItem, MemoryQuery, MemoryResult, MemoryType
from .recall import CrossSessionRecall
from .consolidation import ConsolidationAgent
from .user_model import UserModel
from .manager import MemoryManager

# Façade unifiée pour les faits structurés (core.facts)
try:
    from core.facts import Fact, FactCategory, FactStatus, FactStore
except ImportError:
    Fact = None  # type: ignore
    FactCategory = None  # type: ignore
    FactStatus = None  # type: ignore
    FactStore = None  # type: ignore

__all__ = [
    "ConsolidationAgent",
    "CrossSessionRecall",
    "Fact",
    "FactCategory",
    "FactStatus",
    "FactStore",
    "MemoryBackend",
    "MemoryEntry",
    "MemoryItem",
    "MemoryManager",
    "MemoryQuery",
    "MemoryResult",
    "MemoryStore",
    "MemoryType",
    "SearchResult",
    "UserModel",
    "VectorSearchResult",
]
