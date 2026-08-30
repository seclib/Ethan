"""RAG Context — Assemblage du contexte LLM.

Construit le contexte à injecter dans les prompts LLM à partir des
chunks récupérés par le RAGRetrieval.
"""

from __future__ import annotations

import logging
from typing import Any

from core.rag.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


class RAGContext:
    """Assemble le contexte LLM à partir des chunks RAG.

    Args:
        max_context_chars: Taille maximale du contexte (caractères).
        include_sources: Inclure les sources dans le contexte.
    """

    def __init__(
        self,
        max_context_chars: int = 8000,
        include_sources: bool = True,
    ):
        self._max_context_chars = max_context_chars
        self._include_sources = include_sources

    def set_max_context_chars(self, max_context_chars: int) -> None:
        """Reconfigure la borne de contexte à chaud."""
        if max_context_chars > 0:
            self._max_context_chars = int(max_context_chars)

    def build_context(
        self,
        chunks: list[RetrievedChunk],
        query: str = "",
    ) -> str:
        """Construit le contexte à injecter dans le prompt.

        Args:
            chunks: Chunks récupérés
            query: Requête originale (pour le contexte)

        Returns:
            Contexte formaté
        """
        if not chunks:
            return ""

        parts: list[str] = []
        total_chars = 0

        for i, item in enumerate(chunks, 1):
            chunk_text = item.chunk.content.strip()
            if not chunk_text:
                continue

            # Ajouter le chunk
            part = f"[{i}] {chunk_text}"

            # Ajouter la source si demandé
            if self._include_sources and item.document_title:
                part += f"\n(Source: {item.document_title}"
                if item.document_source:
                    part += f" — {item.document_source}"
                part += ")"

            # Vérifier la taille maximale
            if total_chars + len(part) > self._max_context_chars:
                break

            parts.append(part)
            total_chars += len(part)

        if not parts:
            return ""

        header = "Contexte de référence :\n"
        if query:
            header = f"Contexte de référence pour la requête « {query} » :\n"

        return header + "\n\n".join(parts)

    def build_messages(
        self,
        chunks: list[RetrievedChunk],
        query: str = "",
    ) -> list[dict[str, str]]:
        """Construit les messages système avec le contexte.

        Args:
            chunks: Chunks récupérés
            query: Requête originale

        Returns:
            Liste de messages système
        """
        context = self.build_context(chunks, query)
        if not context:
            return []

        return [
            {
                "role": "system",
                "content": (
                    "Tu es ETHAN, un assistant IA autonome. "
                    "Utilise le contexte de référence ci-dessous pour répondre "
                    "à la requête de l'utilisateur. "
                    "Si le contexte ne contient pas la réponse, dis-le clairement.\n\n"
                    f"{context}"
                ),
            }
        ]