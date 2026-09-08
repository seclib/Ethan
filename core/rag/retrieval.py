"""RAG Retrieval — Récupération de chunks pertinents.

Recherche les chunks les plus pertinents pour une requête en utilisant
la similarité cosinus sur les embeddings.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass

from core.rag.embeddings import RAGEmbeddings
from core.rag.ingestion import DocumentChunk, IngestedDocument
from core.rag.strategies import normalize_strategy
from core.rag.vector_store import RAGVectorStore

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
        vector_store: RAGVectorStore | None = None,
    ):
        self._embeddings = embeddings or RAGEmbeddings()
        self._top_k = top_k
        self._documents: dict[str, IngestedDocument] = {}
        # Index vectoriel optionnel (ChromaDB/Qdrant) : s'il est fourni, la
        # recherche vectorielle passe par lui ; sinon le calcul cosinus se
        # fait en mémoire sur les chunks enregistrés (comportement historique).
        self._vector_store: RAGVectorStore | None = vector_store

    def attach_vector_store(self, vector_store: RAGVectorStore | None) -> None:
        """Branche (ou remplace) l'index vectoriel externe."""
        self._vector_store = vector_store

    async def index_document(self, document: IngestedDocument) -> None:
        """Indexe les chunks d'un document dans l'index vectoriel externe.

        Une panne runtime du backend (ex: Qdrant injoignable) ne casse pas
        l'ingestion : le document reste dans le catalogue mémoire et sera
        ré-indexé à l'ouverture suivante (``_load_vector_store``).
        """
        if self._vector_store is None:
            return
        records = [
            {
                "chunk_id": chunk.id,
                "embedding": chunk.embedding,
                "document_id": document.id,
                "content": chunk.content,
                "metadata": {"chunk_index": chunk.order, "title": document.title},
            }
            for chunk in document.chunks
            if chunk.embedding
        ]
        if not records:
            return
        try:
            await self._vector_store.upsert(records)
        except Exception as exc:
            logger.warning(
                "Vector store upsert failed for document %s (%s) — document "
                "kept in catalogue, re-indexing will retry",
                document.id,
                exc,
            )

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
        if self._vector_store is not None:
            # La purge de l'index externe est fire-and-forget planifiée par
            # le pipeline (delete_document) — ici on ne bloque pas le sync.
            import asyncio

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._vector_store.delete_document(document_id))
            except RuntimeError:
                pass  # pas de boucle : la purge sera faite par le pipeline

    def set_top_k(self, top_k: int) -> None:
        """Reconfigure le nombre de chunks retournés par défaut."""
        if top_k > 0:
            self._top_k = int(top_k)

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        document_ids: list[str] | None = None,
        strategy: str | None = None,
    ) -> list[RetrievedChunk]:
        """Récupère les chunks les plus pertinents selon la stratégie.

        Args:
            query: Requête
            top_k: Nombre de chunks à retourner
            document_ids: Documents à inclure (scope collections).
            strategy: Stratégie de recherche (``auto``, ``keyword``,
                ``semantic``, ``hybrid``). ``None`` → ``auto`` (comportement
                historique).

        Returns:
            Chunks récupérés avec scores

        Les stratégies mappent des chemins de code réels (voir
        ``core/rag/strategies.py``) ; aucune stratégie non implémentée n'est
        exposée. ``keyword`` et ``hybrid`` dégradent proprement si les
        embeddings sont mock (tous zéros).
        """
        k = top_k or self._top_k
        strategy = normalize_strategy(strategy)
        query_embedding = await self._embeddings.embed_text(query)
        has_real_embeddings = not all(v == 0.0 for v in query_embedding)

        if strategy == "keyword":
            return self._textual_retrieve(query, k, document_ids=document_ids)

        if strategy == "hybrid":
            return await self._hybrid_retrieve(
                query, query_embedding, has_real_embeddings, k,
                document_ids=document_ids,
            )

        # semantic (ou auto) — le chemin vectoriel exige des embeddings réels.
        if not has_real_embeddings:
            if strategy == "semantic":
                logger.warning(
                    "RAG strategy 'semantic' requested but embeddings are mock "
                    "— falling back to keyword retrieval"
                )
            return self._textual_retrieve(query, k, document_ids=document_ids)
        return await self._semantic_retrieve(
            query_embedding, k, document_ids=document_ids
        )

    async def _semantic_retrieve(
        self,
        query_embedding: list[float],
        k: int,
        document_ids: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        """Recherche vectorielle (index externe ou cosinus mémoire)."""
        # Construire l'index chunk_id → (chunk, titre, source) une seule fois
        by_chunk_id: dict[str, tuple[DocumentChunk, str, str]] = {}
        for doc in self._documents.values():
            for chunk in doc.chunks:
                by_chunk_id[chunk.id] = (chunk, doc.title, doc.source)

        # Recherche via l'index vectoriel externe (ChromaDB/Qdrant) si branché
        if self._vector_store is not None:
            scored: list[RetrievedChunk] = []
            try:
                hits = await self._vector_store.search(
                    query_embedding, k,
                    document_ids=document_ids,
                )
            except Exception as exc:
                logger.warning(
                    "Vector store indisponible (%s) — fallback cosinus mémoire", exc
                )
                hits = None
            if hits is not None:
                for chunk_id, score in hits:
                    entry = by_chunk_id.get(chunk_id)
                    if entry is None:
                        continue  # chunk inconnu du catalogue (index stale)
                    chunk, doc_title, doc_source = entry
                    scored.append(RetrievedChunk(
                        chunk=chunk, score=score,
                        document_title=doc_title, document_source=doc_source,
                    ))
                scored.sort(key=lambda x: x.score, reverse=True)
                return scored[:k]

        # Calculer les scores de similarité cosinus (chemin mémoire)
        allowed: set[str] | None = (
            set(document_ids) if document_ids is not None else None
        )
        scored = []
        for doc in self._documents.values():
            if allowed is not None and doc.id not in allowed:
                continue
            for chunk in doc.chunks:
                if not chunk.embedding:
                    continue
                score = self._cosine_similarity(query_embedding, chunk.embedding)
                scored.append(RetrievedChunk(
                    chunk=chunk,
                    score=score,
                    document_title=doc.title,
                    document_source=doc.source,
                ))

        # Trier par score décroissant
        scored.sort(key=lambda x: x.score, reverse=True)

        return scored[:k]

    async def _hybrid_retrieve(
        self,
        query: str,
        query_embedding: list[float],
        has_real_embeddings: bool,
        k: int,
        document_ids: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        """Fusion mots-clés + sémantique par filtrage réciproque (RRF).

        Si les embeddings sont mock, la composante sémantique ne peut rien
        trouver de significatif : la stratégie hybride se replie proprement
        sur la recherche textuelle (dégradation documentée).
        """
        candidates = max(k * 2, 20)
        keyword = self._textual_retrieve(query, candidates, document_ids=document_ids)
        if not has_real_embeddings:
            logger.warning(
                "RAG strategy 'hybrid' requested but embeddings are mock "
                "— keyword component only"
            )
            return keyword[:k]
        semantic = await self._semantic_retrieve(
            query_embedding, candidates, document_ids=document_ids
        )
        return self._reciprocal_rank_fusion([semantic, keyword], k)

    @staticmethod
    def _reciprocal_rank_fusion(
        rankings: list[list[RetrievedChunk]], k: int, rrf_k: int = 60
    ) -> list[RetrievedChunk]:
        """Fusionne plusieurs classements par filtrage réciproque (RRF).

        Score RRF d'un chunk = Σ 1/(rrf_k + rang) sur chaque liste. Aucune
        normalisation des scores bruts n'est nécessaire, ce qui rend la fusion
        robuste entre des recherches aux échelles différentes (cosinus vs
        présence de mots).
        """
        fused: dict[str, float] = {}
        best: dict[str, RetrievedChunk] = {}
        for ranking in rankings:
            for rank, item in enumerate(ranking, start=1):
                chunk_id = item.chunk.id
                fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank)
                if chunk_id not in best or item.score > best[chunk_id].score:
                    best[chunk_id] = item
        results = [
            RetrievedChunk(
                chunk=item.chunk,
                score=fused[chunk_id],
                document_title=item.document_title,
                document_source=item.document_source,
            )
            for chunk_id, item in best.items()
        ]
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]

    def _textual_retrieve(
        self,
        query: str,
        k: int,
        document_ids: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        """Recherche textuelle simple (fallback sans embeddings).

        Args:
            query: Requête
            k: Nombre de chunks à retourner
            document_ids: Documents à inclure (scope collections).

        Returns:
            Chunks récupérés
        """
        q_lower = query.lower()
        scored: list[RetrievedChunk] = []

        allowed: set[str] | None = (
            set(document_ids) if document_ids is not None else None
        )
        for doc in self._documents.values():
            if allowed is not None and doc.id not in allowed:
                continue
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
