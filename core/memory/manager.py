"""Memory Manager — Gestionnaire central du système mémoire.

Orchestre les 8 types de mémoire :
- Working Memory (Redis)
- Short-term Memory (Redis TTL)
- Episodic Memory (PostgreSQL)
- Semantic Memory (PostgreSQL + pgvector)
- Procedural Memory (PostgreSQL)
- Vector Memory (pgvector)
- Event Log (PostgreSQL)
- History (PostgreSQL)

Responsabilités :
- Routage des items vers la bonne mémoire
- Consolidation périodique
- Oubli intelligent
- Compression
- Récupération multi-niveaux
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from core.memory.types import MemoryItem, MemoryQuery, MemoryResult, MemoryType

logger = logging.getLogger(__name__)


class MemoryManager:
    """Gestionnaire central du système mémoire."""

    def __init__(self):
        # Stores (initialisés à None, connectés plus tard)
        self.working: Any = None
        self.short_term: Any = None
        self.episodic: Any = None
        self.semantic: Any = None
        self.procedural: Any = None
        self.vector: Any = None
        self.event_log: Any = None
        self.history: Any = None

        # Moteurs cognitifs
        self.forgetting: Any = None
        self.compression: Any = None
        self.retrieval: Any = None

    async def connect(self) -> None:
        """Connecte tous les stores."""
        # Import tardif pour éviter les dépendances circulaires
        from core.memory.redis_store import RedisStore
        from core.memory.pg_store import PGStore
        from core.memory.vector_store import VectorStore

        # Working Memory (Redis)
        self.working = RedisStore(url="redis://localhost:6379", prefix="ethan:working:")
        await self.working.connect()

        # Short-term Memory (Redis avec TTL)
        self.short_term = RedisStore(url="redis://localhost:6379", prefix="ethan:short:")
        await self.short_term.connect()

        # Episodic Memory (PostgreSQL)
        self.episodic = PGStore(url="postgresql://ethan:ethan@localhost:5432/ethan")
        await self.episodic.connect()
        await self.episodic.init_schema()

        # Semantic Memory (PostgreSQL + pgvector)
        self.semantic = PGStore(url="postgresql://ethan:ethan@localhost:5432/ethan")
        await self.semantic.connect()

        # Procedural Memory (PostgreSQL)
        self.procedural = PGStore(url="postgresql://ethan:ethan@localhost:5432/ethan")
        await self.procedural.connect()

        # Vector Memory (pgvector)
        self.vector = VectorStore(url="postgresql://ethan:ethan@localhost:5432/ethan")
        await self.vector.connect()
        await self.vector.init_schema()

        # Event Log (PostgreSQL)
        self.event_log = PGStore(url="postgresql://ethan:ethan@localhost:5432/ethan")
        await self.event_log.connect()

        # History (PostgreSQL)
        self.history = PGStore(url="postgresql://ethan:ethan@localhost:5432/ethan")
        await self.history.connect()

        # Moteurs cognitifs
        from core.memory.forgetting import ForgettingEngine
        from core.memory.compression import CompressionEngine
        from core.memory.retrieval import RetrievalEngine

        self.forgetting = ForgettingEngine(self)
        self.compression = CompressionEngine(self)
        self.retrieval = RetrievalEngine(self)

        logger.info("✅ Memory Manager connected to all stores")

    async def close(self) -> None:
        """Ferme toutes les connexions."""
        stores = [
            self.working, self.short_term, self.episodic, self.semantic,
            self.procedural, self.vector, self.event_log, self.history
        ]
        for store in stores:
            if store:
                try:
                    await store.close()
                except Exception as e:
                    logger.warning(f"Error closing store: {e}")

    async def store(self, item: MemoryItem) -> None:
        """Stocke un item dans la bonne mémoire.

        Args:
            item: Item à stocker
        """
        # Router vers la bonne mémoire
        store = self._route(item)
        namespace = self._get_namespace(item.type)

        # Stocker
        await store.store(
            namespace=namespace,
            key=self._generate_key(item),
            value=item.content,
            ttl=item.ttl,
        )

        # Mettre à jour Vector Memory
        if self.vector:
            try:
                await self.vector.store(
                    namespace=namespace,
                    key=self._generate_key(item),
                    value={
                        "text": str(item.content),
                        "embedding": [],  # TODO: Générer embedding
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to store in vector memory: {e}")

        # Logger l'événement
        if self.event_log:
            try:
                await self.event_log.store(
                    "events",
                    f"memory.store.{datetime.utcnow().timestamp()}",
                    {
                        "type": "memory.store",
                        "memory_type": item.type.value,
                        "key": self._generate_key(item),
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to log event: {e}")

    async def recall(self, query: str, context: dict[str, Any] | None = None) -> list[MemoryResult]:
        """Récupère des souvenirs.

        Args:
            query: Requête de recherche
            context: Contexte additionnel

        Returns:
            Liste de résultats
        """
        if not self.retrieval:
            logger.warning("Retrieval engine not initialized")
            return []

        return await self.retrieval.recall(query, context or {})

    async def consolidate(self) -> None:
        """Consolidation périodique."""
        logger.info("Starting memory consolidation...")

        # 1. Compression de l'ancien Episodic
        if self.episodic and self.compression:
            try:
                await self.compression.compress_old_episodic(days=30)
            except Exception as e:
                logger.error(f"Compression failed: {e}")

        # 2. Extraction de connaissances
        if self.episodic and self.semantic and self.compression:
            try:
                await self.compression.extract_knowledge()
            except Exception as e:
                logger.error(f"Knowledge extraction failed: {e}")

        # 3. Oubli
        if self.forgetting:
            try:
                await self.forgetting.run()
            except Exception as e:
                logger.error(f"Forgetting failed: {e}")

        logger.info("✅ Memory consolidation complete")

    def _route(self, item: MemoryItem) -> Any:
        """Route l'item vers la bonne mémoire."""
        # Si TTL court → Working
        if item.ttl and item.ttl < 3600:
            return self.working

        # Par type
        type_map = {
            MemoryType.WORKING: self.working,
            MemoryType.SHORT_TERM: self.short_term,
            MemoryType.EPISODIC: self.episodic,
            MemoryType.SEMANTIC: self.semantic,
            MemoryType.PROCEDURAL: self.procedural,
            MemoryType.VECTOR: self.vector,
            MemoryType.EVENT_LOG: self.event_log,
            MemoryType.HISTORY: self.history,
        }

        return type_map.get(item.type, self.short_term)

    def _get_namespace(self, memory_type: MemoryType) -> str:
        """Retourne le namespace pour un type de mémoire."""
        return f"memory:{memory_type.value}"

    def _generate_key(self, item: MemoryItem) -> str:
        """Génère une clé unique pour un item."""
        timestamp = datetime.utcnow().timestamp()
        return f"{timestamp}_{id(item)}"