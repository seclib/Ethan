"""Memory — abstraction mémoire d'ETHAN (ADR-1005).

Deux contrats abstraits, technologies remplaçables :
- ``MemoryStore`` (ABC)  : working memory (Redis) / long-term (PostgreSQL) ;
- ``MemoryBackend`` (ABC): backends vectoriels (ChromaDB, Qdrant, …).

Le Core ne consomme que ces abstractions — l'infrastructure est un détail
d'implémentation injecté au démarrage.
"""

from .interface import (
    MemoryBackend,
    MemoryEntry,
    MemoryStore,
    SearchResult,
    VectorSearchResult,
)
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
