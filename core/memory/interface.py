"""Memory Store — Interface abstraite pour le stockage.

Deux tiers :
- Working Memory (Redis) : rapide, TTL, état live
- Long-term Memory (PostgreSQL) : persistant, append-only
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class SearchResult:
    """Résultat de recherche mémoire."""
    key: str
    value: Any
    score: float = 1.0
    metadata: dict[str, Any] | None = None


@dataclass
class MemoryEntry:
    """Entrée mémoire vectorielle (contrat des ``MemoryBackend``)."""
    key: str
    value: Any
    namespace: str = "default"
    metadata: dict[str, Any] | None = None
    ttl: int | None = None
    embedding: list[float] | None = None
    timestamp: float | None = None


@dataclass
class VectorSearchResult:
    """Résultat de recherche vectorielle (backends ``MemoryBackend``).

    Distinct de ``types.MemoryResult`` (contrat du moteur de recall) : le
    backend vectoriel retourne des correspondances brutes clé/valeur/score.
    """
    key: str
    value: Any
    namespace: str = "default"
    metadata: dict[str, Any] | None = None
    score: float = 1.0
    timestamp: float | None = None


class MemoryBackend(ABC):
    """Interface abstraite des backends mémoire vectoriels (ADR-1005).

    Le Core consomme cette abstraction ; la technologie (ChromaDB, Qdrant,
    …) reste remplaçable sans toucher au code métier.
    """

    @abstractmethod
    async def store(self, entry: MemoryEntry) -> None:
        """Stocke une entrée (avec embedding optionnel)."""
        ...

    @abstractmethod
    async def retrieve(self, key: str, namespace: str = "default") -> MemoryEntry | None:
        """Retourne une entrée par clé, ou ``None``."""
        ...

    @abstractmethod
    async def search(
        self,
        query: str,
        namespace: str = "default",
        limit: int = 10,
        threshold: float = 0.0,
    ) -> list[VectorSearchResult]:
        """Recherche sémantique dans un namespace."""
        ...

    @abstractmethod
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Supprime une entrée. ``True`` si supprimée."""
        ...

    @abstractmethod
    async def list_namespaces(self) -> list[str]:
        """Liste les namespaces présents."""
        ...

    @abstractmethod
    async def clear(self, namespace: str | None = None) -> None:
        """Vide tout, ou un namespace donné."""
        ...

    async def close(self) -> None:
        """Libère les ressources (no-op par défaut)."""
        return None


class MemoryStore(ABC):
    """Interface abstraite pour le stockage mémoire.

    Deux implémentations :
    - RedisStore : working memory (rapide, TTL)
    - PGStore : long-term memory (persistant)
    """

    @abstractmethod
    async def connect(self) -> None:
        """Établit la connexion au backend."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Ferme la connexion."""
        ...

    @abstractmethod
    async def store(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Stocke une valeur.

        Args:
            namespace: Namespace (e.g., "session", "agent", "goal")
            key: Clé unique dans le namespace
            value: Valeur à stocker (sérialisable JSON)
            ttl: Time-to-live en secondes (None = pas d'expiration)
        """
        ...

    @abstractmethod
    async def get(self, namespace: str, key: str) -> Any | None:
        """Récupère une valeur.

        Returns:
            Valeur stockée ou None si absente
        """
        ...

    @abstractmethod
    async def delete(self, namespace: str, key: str) -> None:
        """Supprime une valeur."""
        ...

    @abstractmethod
    async def list_namespace(self, namespace: str) -> list[str]:
        """Liste toutes les clés dans un namespace.

        Returns:
            Liste des clés
        """
        ...

    @abstractmethod
    async def search(
        self,
        namespace: str,
        query: str,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Recherche sémantique dans un namespace.

        Args:
            namespace: Namespace à chercher
            query: Requête textuelle
            limit: Nombre max de résultats

        Returns:
            Liste de résultats triés par pertinence
        """
        ...

    @abstractmethod
    async def exists(self, namespace: str, key: str) -> bool:
        """Vérifie si une clé existe."""
        ...

    @abstractmethod
    async def ttl(self, namespace: str, key: str) -> int | None:
        """Retourne le TTL restant en secondes, ou None."""
        ...