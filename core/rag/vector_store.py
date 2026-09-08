"""RAG Vector Store — Index vectoriel pluggable pour la retrieval.

Le catalogue des documents (chunks, contenus, ordre) reste la propriété du
RAGPipeline (CoreRecordStore persistant).  Le vector store n'est qu'un index
de scores : il stocke (chunk_id, embedding, metadata) et retourne les
(chunk_id, score) les plus proches, éventuellement filtrés par document.

Backends :
- ``memory`` (défaut)   : InMemoryVectorStore — comportement historique,
  aucune dépendance.
- ``chromadb``          : ChromaDBVectorStore (HTTP ou persistant) — import
  paresseux, erreur explicite si le package est absent.
- ``qdrant``            : QdrantVectorStore — import paresseux, erreur
  explicite si le package est absent.

Le backend est choisi via la configuration RAG persistée
(``rag-config.vector_backend``) et survit aux redémarrages ; à l'ouverture,
le pipeline ré-indexe les chunks persistés (upsert idempotent par chunk_id).
"""

from __future__ import annotations

import logging
import math
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)

VectorRecord = dict[str, Any]  # {chunk_id, embedding, document_id, ...}


class RAGVectorStore(ABC):
    """Interface d'index vectoriel pour la retrieval RAG."""

    name: str = "abstract"

    @abstractmethod
    async def upsert(self, records: list[VectorRecord]) -> None:
        """Indexe (ou ré-indexe) des chunks — idempotent par chunk_id."""
        ...

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[tuple[str, float]]:
        """Retourne les (chunk_id, score) les plus proches de la requête.

        ``document_ids`` restreint la recherche (scope collections).
        """
        ...

    @abstractmethod
    async def delete_document(self, document_id: str) -> None:
        """Supprime tous les vecteurs d'un document."""
        ...

    async def close(self) -> None:  # pragma: no cover - interface
        """Libère les ressources backend (optionnel)."""


def _cosine(a: list[float], b: list[float]) -> float:
    """Similarité cosinus stdlib (identique à RAGRetrieval)."""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class InMemoryVectorStore(RAGVectorStore):
    """Index en mémoire (process-local) — backend par défaut."""

    name = "memory"

    def __init__(self) -> None:
        self._records: dict[str, VectorRecord] = {}

    async def upsert(self, records: list[VectorRecord]) -> None:
        for record in records:
            self._records[record["chunk_id"]] = record

    async def search(
        self,
        query_embedding: list[float],
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[tuple[str, float]]:
        allowed = set(document_ids) if document_ids is not None else None
        scored: list[tuple[str, float]] = []
        for chunk_id, record in self._records.items():
            if allowed is not None and record.get("document_id") not in allowed:
                continue
            embedding = record.get("embedding") or []
            if not embedding:
                continue
            scored.append((chunk_id, _cosine(query_embedding, embedding)))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]

    async def delete_document(self, document_id: str) -> None:
        stale = [
            chunk_id
            for chunk_id, record in self._records.items()
            if record.get("document_id") == document_id
        ]
        for chunk_id in stale:
            del self._records[chunk_id]

    def __len__(self) -> int:
        return len(self._records)


class ChromaDBVectorStore(RAGVectorStore):
    """Backend ChromaDB (HTTP Docker ou client persistant local)."""

    name = "chromadb"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        persist_directory: str | None = None,
        collection_name: str = "ethan_rag",
    ) -> None:
        self._host = host
        self._port = port
        self._persist_directory = persist_directory
        self._collection_name = collection_name
        self._collection: Any = None

    def _ensure_collection(self) -> Any:
        if self._collection is not None:
            return self._collection
        try:
            import chromadb
            from chromadb.config import Settings

            if self._persist_directory:
                client = chromadb.PersistentClient(
                    path=self._persist_directory,
                    settings=Settings(anonymized_telemetry=False),
                )
            else:
                client = chromadb.HttpClient(
                    host=self._host,
                    port=self._port,
                    settings=Settings(anonymized_telemetry=False),
                )
            self._collection = client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            return self._collection
        except ImportError as exc:
            raise RuntimeError(
                "Backend vectoriel 'chromadb' indisponible : "
                "installez le package chromadb (pip install chromadb)"
            ) from exc

    async def upsert(self, records: list[VectorRecord]) -> None:
        if not records:
            return
        collection = self._ensure_collection()
        collection.upsert(
            ids=[r["chunk_id"] for r in records],
            embeddings=[r["embedding"] for r in records],
            metadatas=[
                {"document_id": r["document_id"], **(r.get("metadata") or {})}
                for r in records
            ],
            documents=[r.get("content", "") for r in records],
        )

    async def search(
        self,
        query_embedding: list[float],
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[tuple[str, float]]:
        collection = self._ensure_collection()
        where = {"document_id": {"$in": document_ids}} if document_ids else None
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )
        ids = result.get("ids") or [[]]
        distances = result.get("distances") or [[]]
        # ChromaDB retourne une distance (cosine) : score = 1 - distance.
        return [
            (chunk_id, max(0.0, 1.0 - float(distance)))
            for chunk_id, distance in zip(ids[0], distances[0])
        ]

    async def delete_document(self, document_id: str) -> None:
        collection = self._ensure_collection()
        collection.delete(where={"document_id": document_id})


class QdrantVectorStore(RAGVectorStore):
    """Backend Qdrant (HTTP)."""

    name = "qdrant"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: str | None = None,
        collection_name: str = "ethan_rag",
        vector_size: int | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._api_key = api_key
        self._collection_name = collection_name
        self._vector_size = vector_size
        self._client: Any = None
        self._models: Any = None

    def _ensure_client(self, sample_embedding: list[float] | None = None) -> Any:
        if self._client is not None:
            return self._client
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
        except ImportError as exc:
            raise RuntimeError(
                "Backend vectoriel 'qdrant' indisponible : installez le "
                "package qdrant-client (pip install qdrant-client)"
            ) from exc

        self._client = QdrantClient(host=self._host, port=self._port, api_key=self._api_key)
        self._models = models
        size = self._vector_size or (len(sample_embedding) if sample_embedding else None)
        if size is None:
            raise RuntimeError(
                "vector_size requis pour initialiser la collection Qdrant "
                "(aucun embedding de référence disponible)"
            )
        if not self._client.collection_exists(self._collection_name):
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=models.VectorParams(size=size, distance=models.Distance.COSINE),
            )
        return self._client

    async def upsert(self, records: list[VectorRecord]) -> None:
        if not records:
            return
        client = self._ensure_client(sample_embedding=records[0].get("embedding"))
        models = self._models
        # Valider les dimensions avant d'atteindre Qdrant (erreur claire locale).
        for r in records:
            embedding = r.get("embedding") or []
            vector_size = self._vector_size
            if vector_size is not None and len(embedding) != vector_size:
                raise ValueError(
                    f"dimension mismatch: chunk {r.get('chunk_id')} has dim "
                    f"{len(embedding)} but Qdrant collection {self._collection_name} "
                    f"expects {vector_size}"
                )
        points = [
            models.PointStruct(
                id=r["chunk_id"],
                vector=r["embedding"],
                payload={"document_id": r["document_id"], **(r.get("metadata") or {})},
            )
            for r in records
        ]
        client.upsert(collection_name=self._collection_name, points=points, wait=True)

    async def search(
        self,
        query_embedding: list[float],
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[tuple[str, float]]:
        client = self._ensure_client(sample_embedding=query_embedding)
        models = self._models
        query_filter = None
        if document_ids:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchAny(any=document_ids),
                    )
                ]
            )
        result = client.query_points(
            collection_name=self._collection_name,
            query=query_embedding,
            limit=top_k,
            query_filter=query_filter,
        )
        return [(str(point.id), float(point.score)) for point in (result.points or [])]

    async def delete_document(self, document_id: str) -> None:
        client = self._ensure_client()
        models = self._models
        client.delete(
            collection_name=self._collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )


def create_vector_store(
    backend: str,
    *,
    config: dict[str, Any] | None = None,
) -> RAGVectorStore | None:
    """Fabrique le backend vectoriel demandé.

    ``memory`` (ou backend vide) → InMemoryVectorStore.  Les backends
    externes lèvent une ``RuntimeError`` explicite si le package est absent
    (fail-closed : jamais de perte silencieuse d'index).
    """
    backend = (backend or "memory").strip().lower()
    config = dict(config or {})
    if backend == "memory":
        return InMemoryVectorStore()
    if backend == "chromadb":
        return ChromaDBVectorStore(
            host=config.get("host", "localhost"),
            port=int(config.get("port", 8000)),
            persist_directory=config.get("persist_directory"),
            collection_name=config.get("collection_name", "ethan_rag"),
        )
    if backend == "qdrant":
        return QdrantVectorStore(
            host=config.get("host", "localhost"),
            port=int(config.get("port", 6333)),
            api_key=config.get("api_key"),
            collection_name=config.get("collection_name", "ethan_rag"),
            vector_size=config.get("vector_size"),
        )
    raise ValueError(
        f"Backend vectoriel inconnu : {backend!r} (memory, chromadb ou qdrant)"
    )


__all__ = [
    "RAGVectorStore",
    "InMemoryVectorStore",
    "ChromaDBVectorStore",
    "QdrantVectorStore",
    "create_vector_store",
]
