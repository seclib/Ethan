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


_SPLITTING_STRATEGIES = ("character", "sentence", "paragraph")


class RAGIngestion:
    """Pipeline d'ingestion de documents.

    Args:
        embeddings: Générateur d'embeddings.
        chunk_size: Taille maximale d'un chunk (caractères).
        chunk_overlap: Chevauchement entre chunks (caractères).
        splitting_strategy: Stratégie de découpage — ``character`` (défaut,
            découpage par taille avec coupure de phrase), ``sentence``
            (regroupe les phrases jusqu'à ``chunk_size``), ``paragraph``
            (un paragraphe par chunk, fusion si trop court).
    """

    def __init__(
        self,
        embeddings: RAGEmbeddings | None = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        splitting_strategy: str = "character",
    ):
        self._embeddings = embeddings or RAGEmbeddings()
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._splitting_strategy = self._validate_strategy(splitting_strategy)
        self._documents: dict[str, IngestedDocument] = {}
        # Dimension d'embedding établie (cohérence validée à l'ingestion).
        self._embedding_dim: int | None = None

    @staticmethod
    def _validate_strategy(value: str) -> str:
        candidate = str(value or "character").strip().lower()
        if candidate not in _SPLITTING_STRATEGIES:
            raise ValueError(
                f"Splitting strategy inconnue : {value!r} "
                f"(disponibles : {', '.join(_SPLITTING_STRATEGIES)})"
            )
        return candidate

    async def ingest(
        self,
        content: str,
        title: str = "",
        source: str = "",
        metadata: dict[str, Any] | None = None,
        document_id: str | None = None,
    ) -> IngestedDocument:
        """Ingère un document.

        Args:
            content: Contenu du document
            title: Titre
            source: Source (fichier, URL, etc.)
            metadata: Métadonnées
            document_id: Identifiant externe (ex: id du record projet).
                ``None`` → uuid généré. Permet d'aligner l'id RAG sur l'entité
                source (projet) pour une purge cohérente à la suppression.

        Returns:
            Document ingéré avec ses chunks

        Raises:
            ValueError: si les embeddings retournés ont des dimensions
                incohérentes (``dimension mismatch``) ou si la stratégie de
                découpage est inconnue.
        """
        doc = IngestedDocument(
            id=document_id or str(uuid4()),
            title=title or source or "Untitled",
            source=source,
            content=content,
            metadata=metadata or {},
        )

        # Découper en chunks
        chunks = self._chunk_text(content)
        logger.info("RAGIngestion: %d chunks for %s", len(chunks), doc.title)

        # Générer les embeddings et valider leurs dimensions
        embeddings = await self._embeddings.embed_texts(chunks)
        embeddings = self._validate_embeddings(embeddings, doc.title)

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

    def _validate_embeddings(
        self,
        embeddings: list[list[float]],
        title: str,
    ) -> list[list[float]]:
        """Valide la cohérence dimensionnelle des embeddings d'un document.

        Tous les chunks d'un même document doivent partager la même dimension
        d'embedding (non vide). Si le moteur a déjà établi une dimension sur un
        document précédent, elle doit rester stable — sinon un backend type
        Qdrant échouerait silencieusement à l'upsert.

        Raises:
            ValueError: ``dimension mismatch`` si les longueurs diffèrent.
        """
        for i, emb in enumerate(embeddings):
            if not emb:
                raise ValueError(
                    f"dimension mismatch: chunk {i} returned an empty embedding "
                    f"for '{title}'"
                )
            if i > 0 and len(emb) != len(embeddings[0]):
                raise ValueError(
                    f"dimension mismatch: chunk {i} has dim {len(emb)} but "
                    f"chunk 0 has dim {len(embeddings[0])} for '{title}'"
                )
        if not embeddings:
            return embeddings
        dim = len(embeddings[0])
        if self._embedding_dim is not None and dim != self._embedding_dim:
            raise ValueError(
                f"dimension mismatch: embedding dim {dim} differs from the "
                f"established dim {self._embedding_dim} for '{title}'"
            )
        self._embedding_dim = dim
        return embeddings

    def set_chunking(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        splitting_strategy: str | None = None,
    ) -> None:
        """Reconfigure le découpage à chaud (les documents déjà ingérés ne sont pas re-découpés)."""
        if chunk_size is not None and chunk_size > 0:
            self._chunk_size = int(chunk_size)
        if chunk_overlap is not None and chunk_overlap >= 0:
            self._chunk_overlap = int(chunk_overlap)
        if splitting_strategy is not None:
            self._splitting_strategy = self._validate_strategy(splitting_strategy)

    def get_document(self, document_id: str) -> IngestedDocument | None:
        """Récupère un document ingéré.

        Args:
            document_id: ID du document

        Returns:
            Document ou None
        """

        return self._documents.get(document_id)

    def _chunk_text(self, text: str, strategy: str | None = None) -> list[str]:
        """Découpe un texte en chunks selon la stratégie configurée.

        Args:
            text: Texte à découper
            strategy: Surcharge ponctuelle de la stratégie (optionnel).

        Returns:
            Liste de chunks
        """
        strategy = self._validate_strategy(strategy) if strategy else self._splitting_strategy
        if not text:
            return []

        if strategy == "paragraph":
            return self._chunk_paragraphs(text)
        if strategy == "sentence":
            return self._chunk_sentences(text)
        return self._chunk_character(text)

    def _chunk_character(self, text: str) -> list[str]:
        """Découpage par taille (historique) avec coupure de phrase si possible."""
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

    def _chunk_sentences(self, text: str) -> list[str]:
        """Découpage par phrases : regroupe les phrases jusqu'à ``chunk_size``."""
        import re as _re

        sentences = [
            s.strip()
            for s in _re.split(r"(?<=[.!?])\s+", text)
            if s.strip()
        ]
        chunks: list[str] = []
        current = ""
        for sentence in sentences:
            if not current:
                current = sentence
                continue
            candidate = f"{current} {sentence}".strip()
            if len(candidate) <= self._chunk_size:
                current = candidate
            else:
                chunks.append(current)
                if len(sentence) > self._chunk_size:
                    chunks.extend(self._chunk_character(sentence))
                    current = ""
                else:
                    current = sentence
        if current:
            chunks.append(current)
        return [c.strip() for c in chunks if c.strip()]

    def _chunk_paragraphs(self, text: str) -> list[str]:
        """Découpage par paragraphes (lignes vides). Fusion si trop court,
        découpage par taille si trop long."""
        import re as _re

        paragraphs = [
            p.strip()
            for p in _re.split(r"\n\s*\n", text)
            if p.strip()
        ]
        if not paragraphs:
            return []
        chunks: list[str] = []
        buffer = ""
        min_merge = self._chunk_size // 2
        for para in paragraphs:
            if len(para) > self._chunk_size:
                if buffer:
                    chunks.append(buffer)
                    buffer = ""
                chunks.extend(self._chunk_character(para))
                continue
            if not buffer:
                buffer = para
            elif len(buffer) + len(para) + 1 <= self._chunk_size:
                buffer = f"{buffer}\n\n{para}"
            else:
                if len(buffer) < min_merge and len(para) <= self._chunk_size:
                    buffer = f"{buffer}\n\n{para}"
                else:
                    chunks.append(buffer)
                    buffer = para
        if buffer:
            chunks.append(buffer)
        return [c.strip() for c in chunks if c.strip()]

    def register_document(self, document: IngestedDocument) -> None:
        """Restore or register a document without re-running ingestion."""
        self._documents[document.id] = document

    async def delete_document(self, document_id: str) -> None:
        """Retire un document du catalogue d'ingestion (contrat aligné avec
        ``RAGPipeline.delete_document`` — appelé par ``ProjectManager``)."""
        self.remove_document(document_id)

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
