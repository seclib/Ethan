"""RAG Ingestion — Pipeline d'ingestion de documents pour le RAG.

Découpe les documents en chunks, génère les embeddings et les stocke
dans le vector store.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from core.rag.embeddings import RAGEmbeddings

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Chunk de document avec son embedding."""
    id: str
    document_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] = field(default_factory=list)
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize a chunk for durable RAG storage."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentChunk":
        """Rebuild a chunk from its stored representation."""
        return cls(
            id=data["id"],
            document_id=data["document_id"],
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            embedding=list(data.get("embedding", [])),
            order=int(data.get("order", 0)),
        )


@dataclass
class IngestedDocument:
    """Document ingéré avec ses chunks."""
    id: str
    title: str
    source: str = ""
    content: str = ""
    chunks: list[DocumentChunk] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize an ingested document and all of its chunks."""
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "content": self.content,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IngestedDocument":
        """Rebuild an ingested document from durable storage."""
        return cls(
            id=data["id"],
            title=data.get("title", "Untitled"),
            source=data.get("source", ""),
            content=data.get("content", ""),
            chunks=[DocumentChunk.from_dict(chunk) for chunk in data.get("chunks", [])],
            metadata=data.get("metadata", {}),
        )


class RAGIngestion:
    """Pipeline d'ingestion de documents.

    Args:
        embeddings: Générateur d'embeddings.
        chunk_size: Taille maximale d'un chunk (caractères).
        chunk_overlap: Chevauchement entre chunks (caractères).
    """

    def __init__(
        self,
        embeddings: RAGEmbeddings | None = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self._embeddings = embeddings or RAGEmbeddings()
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._documents: dict[str, IngestedDocument] = {}

    async def ingest(
        self,
        content: str,
        title: str = "",
        source: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> IngestedDocument:
        """Ingère un document.

        Args:
            content: Contenu du document
            title: Titre
            source: Source (fichier, URL, etc.)
            metadata: Métadonnées

        Returns:
            Document ingéré avec ses chunks
        """
        doc = IngestedDocument(
            id=str(uuid4()),
            title=title or source or "Untitled",
            source=source,
            content=content,
            metadata=metadata or {},
        )

        # Découper en chunks
        chunks = self._chunk_text(content)
        logger.info("RAGIngestion: %d chunks for %s", len(chunks), doc.title)

        # Générer les embeddings
        embeddings = await self._embeddings.embed_texts(chunks)

        # Créer les DocumentChunk
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk = DocumentChunk(
                id=str(uuid4()),
                document_id=doc.id,
                content=chunk_text,
                metadata={**doc.metadata, "chunk_index": i},
                embedding=embedding,
                order=i,
            )
            doc.chunks.append(chunk)

        # Stocker
        self._documents[doc.id] = doc
        logger.info("RAGIngestion: document %s ingested (%d chunks)", doc.id, len(doc.chunks))
        return doc

    def _chunk_text(self, text: str) -> list[str]:
        """Découpe un texte en chunks.

        Args:
            text: Texte à découper

        Returns:
            Liste de chunks
        """
        if not text:
            return []

        # Découpage simple par taille
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self._chunk_size, len(text))
            chunk = text[start:end]

            # Essayer de couper à la fin d'une phrase
            if end < len(text):
                last_period = chunk.rfind(". ")
                if last_period > self._chunk_size // 2:
                    end = start + last_period + 1
                    chunk = text[start:end]

            chunks.append(chunk.strip())
            start = max(end - self._chunk_overlap, start + 1)

        return chunks

    def get_document(self, document_id: str) -> IngestedDocument | None:
        """Récupère un document ingéré.

        Args:
            document_id: ID du document

        Returns:
            Document ou None
        """
        return self._documents.get(document_id)

    def register_document(self, document: IngestedDocument) -> None:
        """Restore or register a document without re-running ingestion."""
        self._documents[document.id] = document

    def remove_document(self, document_id: str) -> None:
        """Remove a document from the in-process ingestion catalogue."""
        self._documents.pop(document_id, None)

    def list_documents(self) -> list[IngestedDocument]:
        """Liste les documents ingérés.

        Returns:
            Liste de documents
        """
        return list(self._documents.values())

    def get_chunks(self, document_id: str) -> list[DocumentChunk]:
        """Récupère les chunks d'un document.

        Args:
            document_id: ID du document

        Returns:
            Liste de chunks
        """
        doc = self._documents.get(document_id)
        return doc.chunks if doc else []
