"""RAG Embeddings — Génération d'embeddings pour le RAG.

Utilise le LLMClient du Core pour générer des embeddings via les providers
disponibles (Ollama, OpenAI, etc.).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class RAGEmbeddings:
    """Génère des embeddings pour les documents RAG.

    Args:
        llm_client: Client LLM du Core (optionnel — mode mock si absent).
        model: Modèle d'embedding par défaut.
    """

    def __init__(self, llm_client: Any | None = None, model: str | None = None):
        self._llm_client = llm_client
        self._model = model

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Génère des embeddings pour une liste de textes.

        Args:
            texts: Textes à encoder

        Returns:
            Liste d'embeddings (vecteurs)
        """
        if not texts:
            return []

        # Mode mock si pas de LLM client
        if self._llm_client is None:
            logger.warning("RAGEmbeddings: no LLM client — using mock embeddings")
            return [[0.0] * 8 for _ in texts]

        try:
            return await self._llm_client.embed(texts, model=self._model)
        except Exception as e:
            logger.error("RAGEmbeddings: embedding failed: %s", e)
            return [[0.0] * 8 for _ in texts]

    async def embed_text(self, text: str) -> list[float]:
        """Génère un embedding pour un texte.

        Args:
            text: Texte à encoder

        Returns:
            Embedding (vecteur)
        """
        result = await self.embed_texts([text])
        return result[0] if result else []

    def configure(
        self,
        llm_client: Any | None = None,
        model: str | None = None,
    ) -> None:
        """Reconfigure les embeddings à chaud (client LLM et/ou modèle).

        Permet de passer du mode dégradé (fallback textuel) au mode réel
        dès qu'un client LLM est disponible dans le Core.
        """
        if llm_client is not None:
            self._llm_client = llm_client
        if model is not None:
            self._model = model