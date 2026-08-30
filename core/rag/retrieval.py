"""RAG Retrieval — Récupération de chunks pertinents.

Recherche les chunks les plus pertinents pour une requête en utilisant
la similarité cosinus sur les embeddings.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any

from core.rag.embeddings import RAGEmbeddings
from core.rag.ingestion import DocumentChunk, IngestedDocument

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """Chunk récupéré avec son score de pertinence."""
    chunk: DocumentChunk
    score: float
    document_title: str = ""
    document_source: str = ""


class RAGRetrieval:
    """Récupère les chunks pertinents pour une requête.

    Args:
        embeddings: Générateur d'embeddings.
        top_k: Nombre de chunks à retourner par défaut.
    """

    def __init__(
        self,
        embeddings: RAGEmbeddings | None = None,
        top_k: int = 5,
    ):
        self._embeddings = embeddings or RAGEmbeddings()
        self._top_k = top_k
        self._documents: dict[str, IngestedDocument] = {}

    def register_documents(self, documents: list[IngestedDocument]) -> None:
        """Enregistre des documents pour la recherche.

        Args:
            documents: Documents à enregistrer
        """
        for doc in documents:
            self._documents[doc.id] = doc

    def register_document(self, document: IngestedDocument) -> None:
        """Enregistre un document pour la recherche.

        Args:
            document: Document à enregistrer
        """
        self._documents[document.id] = document

    def remove_document(self, document_id: str) -> None:
        """Remove a document from the retrieval index."""
        self._documents.pop(document_id, None)

    def set_top_k(self, top_k: int) -> None:
        """Reconfigure le nombre de chunks retournés par défaut."""
        if top_k > 0:
            self._top_k = int(top_k)

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """Récupère les chunks les plus pertinents.

        Args:
            query: Requête
            top_k: Nombre de chunks à retourner

        Returns:
            Chunks récupérés avec scores
        """
        k = top_k or self._top_k

        # Générer l'embedding de la requête
        query_embedding = await self._embeddings.embed_text(query)

        # Si embedding mock (tous zéros), fallback sur la recherche textuelle
        if all(v == 0.0 for v in query_embedding):
            return self._textual_retrieve(query, k)

        # Collecter tous les chunks
        all_chunks: list[tuple[DocumentChunk, str, str]] = []
        for doc in self._documents.values():
            for chunk in doc.chunks:
                all_chunks.append((chunk, doc.title, doc.source))

        # Calculer les scores de similarité cosinus
        scored: list[RetrievedChunk] = []
        for chunk, doc_title, doc_source in all_chunks:
            if not chunk.embedding:
                continue
            score = self._cosine_similarity(query_embedding, chunk.embedding)
            scored.append(RetrievedChunk(
                chunk=chunk,
                score=score,
                document_title=doc_title,
                document_source=doc_source,
            ))

        # Trier par score décroissant
        scored.sort(key=lambda x: x.score, reverse=True)

        return scored[:k]

    def _textual_retrieve(self, query: str, k: int) -> list[RetrievedChunk]:
        """Recherche textuelle simple (fallback sans embeddings).

        Args:
            query: Requête
            k: Nombre de chunks à retourner

        Returns:
            Chunks récupérés
        """
        q_lower = query.lower()
        scored: list[RetrievedChunk] = []

        for doc in self._documents.values():
            for chunk in doc.chunks:
                # Score basé sur la présence des mots de la requête
                content_lower = chunk.content.lower()
                score = 0.0
                for word in q_lower.split():
                    if word in content_lower:
                        score += 1.0
                if score > 0:
                    scored.append(RetrievedChunk(
                        chunk=chunk,
                        score=score,
                        document_title=doc.title,
                        document_source=doc.source,
                    ))

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:k]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Calcule la similarité cosinus entre deux vecteurs.

        Args:
            a: Premier vecteur
            b: Second vecteur

        Returns:
            Similarité (0.0 à 1.0)
        """
        if len(a) != len(b) or not a:
            return 0.0

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)
