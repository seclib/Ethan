"""Vector Store — Embeddings et recherche sémantique (pgvector).

Utilise pgvector pour stocker et rechercher des embeddings.
Nécessite PostgreSQL avec l'extension pgvector installée.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from core.memory.interface import MemoryStore, SearchResult

logger = logging.getLogger(__name__)


class VectorStore(MemoryStore):
    """Implémentation pgvector du MemoryStore.

    Stocke des embeddings pour la recherche sémantique.
    Nécessite PostgreSQL + pgvector.
    """

    def __init__(
        self,
        url: str = "postgresql://ethan:ethan@localhost:5432/ethan",
        dimension: int = 768,
        pool_size: int = 5,
    ):
        self._url = url
        self._dimension = dimension
        self._pool_size = pool_size
        self._pool: Any = None  # asyncpg.Pool

    async def connect(self) -> None:
        """Connexion à PostgreSQL avec pgvector."""
        try:
            import asyncpg
            self._pool = await asyncpg.create_pool(
                self._url,
                min_size=1,
                max_size=self._pool_size,
            )
            logger.info(f"VectorStore connected to {self._url}")
        except ImportError:
            raise RuntimeError(
                "asyncpg not installed. Install with: pip install asyncpg"
            )
        except Exception as e:
            raise ConnectionError(f"Cannot connect to PostgreSQL at {self._url}: {e}")

    async def close(self) -> None:
        """Ferme la connexion."""
        if self._pool:
            await self._pool.close()

    async def store(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Stocke une valeur avec son embedding.

        Args:
            namespace: Namespace
            key: Clé unique
            value: Valeur (dict avec 'text' et optionnellement 'embedding')
            ttl: Ignoré (PostgreSQL n'a pas de TTL natif)
        """
        if not self._pool:
            await self.connect()

        text = value.get("text", "") if isinstance(value, dict) else str(value)
        embedding = value.get("embedding") if isinstance(value, dict) else None

        if embedding is None:
            logger.warning(f"No embedding provided for {namespace}:{key}, skipping vector store")
            return

        if len(embedding) != self._dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self._dimension}, got {len(embedding)}"
            )

        now = datetime.utcnow()

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO vector_store (namespace, key, text, embedding, created_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (namespace, key) DO UPDATE
                SET text = $3, embedding = $4
                """,
                namespace,
                key,
                text,
                embedding,
                now,
            )

    async def get(self, namespace: str, key: str) -> Any | None:
        """Récupère une valeur."""
        if not self._pool:
            await self.connect()

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT text, embedding FROM vector_store WHERE namespace = $1 AND key = $2",
                namespace,
                key,
            )
            if not row:
                return None

            return {
                "text": row["text"],
                "embedding": list(row["embedding"]),
            }

    async def delete(self, namespace: str, key: str) -> None:
        """Supprime une valeur."""
        if not self._pool:
            await self.connect()

        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM vector_store WHERE namespace = $1 AND key = $2",
                namespace,
                key,
            )

    async def list_namespace(self, namespace: str) -> list[str]:
        """Liste toutes les clés dans un namespace."""
        if not self._pool:
            await self.connect()

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT key FROM vector_store WHERE namespace = $1",
                namespace,
            )
            return [row["key"] for row in rows]

    async def search(
        self,
        namespace: str,
        query: str,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Recherche sémantique par similarité cosinus.

        Args:
            namespace: Namespace à chercher
            query: Requête textuelle (doit être convertie en embedding avant)
            limit: Nombre max de résultats

        Returns:
            Liste de résultats triés par similarité
        """
        # NOTE: Cette méthode nécessite un embedding de la query.
        # L'embedding doit être généré par l'appelant (via LLM).
        # Ici on fait une recherche par texte simple (LIKE) comme fallback.
        logger.warning(
            "VectorStore.search() requires query embedding. "
            "Use search_by_embedding() instead."
        )

        if not self._pool:
            await self.connect()

        pattern = f"%{query}%"
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT key, text, created_at
                FROM vector_store
                WHERE namespace = $1 AND text ILIKE $2
                ORDER BY created_at DESC
                LIMIT $3
                """,
                namespace,
                pattern,
                limit,
            )

            results = []
            for row in rows:
                results.append(SearchResult(
                    key=row["key"],
                    value=row["text"],
                    score=1.0,
                    metadata={"created_at": row["created_at"].isoformat()},
                ))

            return results

    async def search_by_embedding(
        self,
        namespace: str,
        query_embedding: list[float],
        limit: int = 10,
        min_similarity: float = 0.7,
    ) -> list[SearchResult]:
        """Recherche sémantique par similarité cosinus.

        Args:
            namespace: Namespace à chercher
            query_embedding: Embedding de la requête (généré par LLM)
            limit: Nombre max de résultats
            min_similarity: Similarité minimale (0.0 à 1.0)

        Returns:
            Liste de résultats triés par similarité décroissante
        """
        if not self._pool:
            await self.connect()

        if len(query_embedding) != self._dimension:
            raise ValueError(
                f"Query embedding dimension mismatch: expected {self._dimension}, got {len(query_embedding)}"
            )

        # Convertir en vecteur pgvector
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT key, text, embedding,
                       1 - (embedding <=> $2::vector) AS similarity
                FROM vector_store
                WHERE namespace = $1
                AND 1 - (embedding <=> $2::vector) >= $3
                ORDER BY similarity DESC
                LIMIT $4
                """,
                namespace,
                embedding_str,
                min_similarity,
                limit,
            )

            results = []
            for row in rows:
                results.append(SearchResult(
                    key=row["key"],
                    value=row["text"],
                    score=float(row["similarity"]),
                    metadata={"created_at": row["created_at"].isoformat()},
                ))

            return results

    async def exists(self, namespace: str, key: str) -> bool:
        """Vérifie si une clé existe."""
        if not self._pool:
            await self.connect()

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM vector_store WHERE namespace = $1 AND key = $2",
                namespace,
                key,
            )
            return row is not None

    async def ttl(self, namespace: str, key: str) -> int | None:
        """PostgreSQL n'a pas de TTL natif. Retourne None."""
        return None

    async def init_schema(self) -> None:
        """Crée les tables et active pgvector."""
        if not self._pool:
            await self.connect()

        async with self._pool.acquire() as conn:
            # Activer pgvector
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Table vector_store
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS vector_store (
                    namespace VARCHAR(255) NOT NULL,
                    key VARCHAR(255) NOT NULL,
                    text TEXT,
                    embedding vector({dim}),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (namespace, key)
                )
            """.format(dim=self._dimension))

            # Index HNSW pour recherche rapide
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_store_embedding
                ON vector_store
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """)

            logger.info("✅ pgvector schema initialized")