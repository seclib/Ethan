"""Public RAG pipeline composing ingestion, retrieval and LLM context."""

from __future__ import annotations

from typing import Any

from core.rag.context import RAGContext
from core.rag.embeddings import RAGEmbeddings
from core.rag.ingestion import IngestedDocument, RAGIngestion
from core.rag.retrieval import RAGRetrieval, RetrievedChunk
from core.state.record_store import CoreRecordStore


class RAGPipeline:
    """Core API for sourced documents and retrieval-augmented LLM context.

    The pipeline keeps its three responsibilities explicit while ensuring that
    ingestion and retrieval always use the same document catalogue.  It has no
    dependency on an API, CLI, or graphical interface.
    """

    _DOMAIN = "rag-documents"

    def __init__(
        self,
        embeddings: RAGEmbeddings | None = None,
        store: CoreRecordStore | None = None,
        *,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        top_k: int = 5,
        max_context_chars: int = 8000,
    ) -> None:
        shared_embeddings = embeddings or RAGEmbeddings()
        self._store = store or CoreRecordStore()
        self._ingestion = RAGIngestion(
            embeddings=shared_embeddings,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self._retrieval = RAGRetrieval(embeddings=shared_embeddings, top_k=top_k)
        self._context = RAGContext(max_context_chars=max_context_chars)
        self._loaded = False

    async def ingest(
        self,
        content: str,
        *,
        title: str = "",
        source: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> IngestedDocument:
        """Chunk, embed and persist a sourced document."""
        if not content.strip():
            raise ValueError("RAG document content must not be empty")
        await self._ensure_loaded()
        document = await self._ingestion.ingest(
            content,
            title=title,
            source=source,
            metadata=metadata,
        )
        self._retrieval.register_document(document)
        await self._store.save(self._DOMAIN, document.id, document.to_dict())
        return document

    async def get_document(self, document_id: str) -> IngestedDocument | None:
        """Retrieve one durable RAG document."""
        await self._ensure_loaded()
        return self._ingestion.get_document(document_id)

    async def list_documents(self) -> list[IngestedDocument]:
        """List documents managed by this RAG pipeline."""
        await self._ensure_loaded()
        return self._ingestion.list_documents()

    async def delete_document(self, document_id: str) -> bool:
        """Remove a document from storage and the retrieval index."""
        await self._ensure_loaded()
        existed = await self._store.delete(self._DOMAIN, document_id)
        self._ingestion.remove_document(document_id)
        self._retrieval.remove_document(document_id)
        return existed

    async def retrieve(self, query: str, *, top_k: int | None = None) -> list[RetrievedChunk]:
        """Find the most relevant document chunks for a query."""
        if not query.strip():
            return []
        await self._ensure_loaded()
        return await self._retrieval.retrieve(query, top_k=top_k)

    async def build_context(self, query: str, *, top_k: int | None = None) -> str:
        """Build bounded source-attributed context ready for an LLM prompt."""
        chunks = await self.retrieve(query, top_k=top_k)
        return self._context.build_context(chunks, query)

    async def build_messages(self, query: str, *, top_k: int | None = None) -> list[dict[str, str]]:
        """Build system messages containing RAG context for an LLM client."""
        chunks = await self.retrieve(query, top_k=top_k)
        return self._context.build_messages(chunks, query)

    async def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        for data in await self._store.list(self._DOMAIN):
            document = IngestedDocument.from_dict(data)
            self._ingestion.register_document(document)
            self._retrieval.register_document(document)
        self._loaded = True
