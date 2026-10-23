"""Qdrant Memory Backend — Production vector database for long-term memory."""

import logging
import time
from typing import Any

from core.memory.interface import MemoryBackend, MemoryEntry, VectorSearchResult

logger = logging.getLogger(__name__)


class QdrantBackend(MemoryBackend):
    """Qdrant backend for production vector memory storage.

    Used for:
    - Long-term memory with high-performance vector search
    - Large-scale embeddings storage
    - Production semantic search
    - Multi-tenant memory with collections per namespace
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        grpc_port: int = 6334,
        api_key: str | None = None,
        collection_name: str = "jarvis_memory",
        vector_size: int = 384,
        distance: str = "Cosine",
    ):
        self._host = host
        self._port = port
        self._grpc_port = grpc_port
        self._api_key = api_key
        self._collection_name = collection_name
        self._vector_size = vector_size
        self._distance = distance
        self._client = None

    async def _ensure_client(self):
        """Initialize Qdrant client if not already done."""
        if self._client is not None:
            return

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models

            self._client = QdrantClient(
                host=self._host,
                port=self._port,
                grpc_port=self._grpc_port,
                api_key=self._api_key,
                prefer_grpc=False,  # Use HTTP for simplicity
            )

            # Create collection if not exists
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self._collection_name not in collection_names:
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=models.VectorParams(
                        size=self._vector_size,
                        distance=self._distance,
                    ),
                )
                logger.info(f"Created Qdrant collection: {self._collection_name}")

            logger.info(f"Connected to Qdrant: {self._host}:{self._port}")

        except ImportError:
            raise ImportError(
                "Qdrant package not installed. Install: pip install qdrant-client"
            )
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant: {e}")
            raise

    async def store(self, entry: MemoryEntry) -> None:
        """Store an entry with embedding."""
        await self._ensure_client()

        from qdrant_client.http import models

        # Build payload
        payload = {
            "value": str(entry.value),
            "namespace": entry.namespace,
            "timestamp": entry.timestamp or time.time(),
        }
        if entry.metadata:
            payload["metadata"] = entry.metadata

        # Upsert point
        self._client.upsert(
            collection_name=self._collection_name,
            points=[
                models.PointStruct(
                    id=hash(entry.key) % (2**63),  # Convert string key to int64
                    vector=entry.embedding or [0.0] * self._vector_size,
                    payload=payload,
                )
            ],
        )

    async def retrieve(self, key: str, namespace: str = "default") -> MemoryEntry | None:
        """Retrieve an entry by key."""
        await self._ensure_client()

        from qdrant_client.http import models

        point_id = hash(key) % (2**63)

        try:
            result = self._client.retrieve(
                collection_name=self._collection_name,
                ids=[point_id],
                with_payload=True,
                with_vectors=False,
            )

            if not result:
                return None

            point = result[0]
            payload = point.payload or {}

            # Filter by namespace
            if payload.get("namespace") != namespace:
                return None

            return MemoryEntry(
                key=key,
                value=payload.get("value", ""),
                namespace=namespace,
                metadata=payload.get("metadata"),
                timestamp=payload.get("timestamp", time.time()),
            )

        except Exception:
            return None

    async def search(
        self,
        query: str,
        namespace: str = "default",
        limit: int = 10,
        threshold: float = 0.0,
    ) -> list[VectorSearchResult]:
        """Search for similar entries using vector similarity."""
        await self._ensure_client()

        from qdrant_client.http import models

        # Note: In production, you would generate an embedding for the query
        # using your embedding provider. Here we use a dummy vector.
        # TODO: Integrate with embedding provider
        query_vector = [0.0] * self._vector_size

        try:
            results = self._client.search(
                collection_name=self._collection_name,
                query_vector=query_vector,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="namespace",
                            match=models.MatchValue(value=namespace),
                        )
                    ]
                ),
                limit=limit,
                score_threshold=threshold,
            )

            entries = []
            for point in results:
                payload = point.payload or {}
                entries.append(VectorSearchResult(
                    key=str(point.id),
                    value=payload.get("value", ""),
                    namespace=namespace,
                    metadata=payload.get("metadata"),
                    score=point.score,
                    timestamp=payload.get("timestamp", 0),
                ))

            return entries

        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete an entry."""
        await self._ensure_client()

        from qdrant_client.http import models

        point_id = hash(key) % (2**63)

        try:
            # First check if the key exists in the correct namespace
            result = await self.retrieve(key, namespace)
            if not result:
                return False

            self._client.delete(
                collection_name=self._collection_name,
                points_selector=models.PointIdsList(points=[point_id]),
            )
            return True

        except Exception:
            return False

    async def list_namespaces(self) -> list[str]:
        """List all namespaces."""
        await self._ensure_client()

        try:
            # Scroll through all points to extract namespaces
            namespaces = set()
            offset = None

            while True:
                points, offset = self._client.scroll(
                    collection_name=self._collection_name,
                    with_payload=["namespace"],
                    limit=100,
                    offset=offset,
                )

                for point in points:
                    if point.payload and "namespace" in point.payload:
                        namespaces.add(point.payload["namespace"])

                if offset is None:
                    break

            return sorted(namespaces)

        except Exception:
            return []

    async def clear(self, namespace: str | None = None) -> None:
        """Clear entries, optionally for a namespace."""
        await self._ensure_client()

        from qdrant_client.http import models

        try:
            if namespace:
                # Delete points matching namespace
                self._client.delete(
                    collection_name=self._collection_name,
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="namespace",
                                    match=models.MatchValue(value=namespace),
                                )
                            ]
                        )
                    ),
                )
            else:
                # Delete entire collection and recreate
                self._client.delete_collection(self._collection_name)
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=models.VectorParams(
                        size=self._vector_size,
                        distance=self._distance,
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to clear Qdrant: {e}")

    async def close(self) -> None:
        """Close Qdrant connection."""
        if self._client:
            self._client.close()
            self._client = None