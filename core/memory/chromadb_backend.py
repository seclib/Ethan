"""ChromaDB Memory Backend — Vector storage for semantic search."""

import logging
import os
from typing import Any

from core.memory.interface import MemoryBackend, MemoryEntry, VectorSearchResult

logger = logging.getLogger(__name__)


class ChromaDBBackend(MemoryBackend):
    """ChromaDB backend for vector memory storage.

    Used for:
    - Semantic search across documents
    - Long-term memory with embeddings
    - Knowledge base storage
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        collection_name: str = "jarvis_memory",
        persist_directory: str | None = None,
    ):
        self._host = host
        self._port = port
        self._collection_name = collection_name
        self._persist_directory = persist_directory
        self._client = None
        self._collection = None

    async def _ensure_client(self):
        """Initialize ChromaDB client if not already done."""
        if self._client is not None:
            return

        try:
            import chromadb
            from chromadb.config import Settings

            if self._persist_directory:
                # Persistent client
                self._client = chromadb.PersistentClient(
                    path=self._persist_directory,
                    settings=Settings(anonymized_telemetry=False),
                )
            else:
                # HTTP client (Docker)
                self._client = chromadb.HttpClient(
                    host=self._host,
                    port=self._port,
                    settings=Settings(anonymized_telemetry=False),
                )

            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Connected to ChromaDB: {self._host}:{self._port}/{self._collection_name}")

        except ImportError:
            raise ImportError(
                "ChromaDB package not installed. Install: pip install chromadb"
            )
        except Exception as e:
            logger.warning(f"Failed to connect to ChromaDB: {e}")
            raise

    async def store(self, entry: MemoryEntry) -> None:
        """Store an entry with embedding."""
        await self._ensure_client()

        metadata = dict(entry.metadata or {})
        metadata["namespace"] = entry.namespace
        if entry.ttl:
            metadata["ttl"] = str(entry.ttl)

        self._collection.add(
            ids=[entry.key],
            documents=[str(entry.value)],
            metadatas=[metadata],
            embeddings=[entry.embedding] if entry.embedding else None,
        )

    async def retrieve(self, key: str, namespace: str = "default") -> MemoryEntry | None:
        """Retrieve an entry by key."""
        await self._ensure_client()

        try:
            result = self._collection.get(
                ids=[key],
                where={"namespace": namespace},
            )
            if result["ids"]:
                return MemoryEntry(
                    key=result["ids"][0],
                    value=result["documents"][0] if result["documents"] else "",
                    namespace=namespace,
                    metadata=result["metadatas"][0] if result["metadatas"] else None,
                )
        except Exception:
            pass
        return None

    async def search(
        self,
        query: str,
        namespace: str = "default",
        limit: int = 10,
        threshold: float = 0.0,
    ) -> list[VectorSearchResult]:
        """Search for similar entries."""
        await self._ensure_client()

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=limit,
                where={"namespace": namespace},
            )

            entries = []
            if results["ids"]:
                for i, doc_id in enumerate(results["ids"][0]):
                    score = results["distances"][0][i] if results.get("distances") else 0.0
                    if score >= threshold:
                        entries.append(VectorSearchResult(
                            key=doc_id,
                            value=results["documents"][0][i] if results.get("documents") else "",
                            namespace=namespace,
                            metadata=results["metadatas"][0][i] if results.get("metadatas") else None,
                            score=1.0 - score,  # Convert distance to similarity
                        ))
            return entries

        except Exception as e:
            logger.error(f"ChromaDB search failed: {e}")
            return []

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete an entry."""
        await self._ensure_client()

        try:
            self._collection.delete(
                ids=[key],
                where={"namespace": namespace},
            )
            return True
        except Exception:
            return False

    async def list_namespaces(self) -> list[str]:
        """List all namespaces."""
        await self._ensure_client()

        try:
            results = self._collection.get()
            namespaces = set()
            if results["metadatas"]:
                for meta in results["metadatas"]:
                    if meta and "namespace" in meta:
                        namespaces.add(meta["namespace"])
            return sorted(namespaces)
        except Exception:
            return []

    async def clear(self, namespace: str | None = None) -> None:
        """Clear entries, optionally for a namespace."""
        await self._ensure_client()

        try:
            if namespace:
                self._collection.delete(where={"namespace": namespace})
            else:
                self._client.delete_collection(self._collection_name)
                self._collection = self._client.create_collection(
                    name=self._collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
        except Exception as e:
            logger.error(f"Failed to clear ChromaDB: {e}")