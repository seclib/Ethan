"""Retrieval Engine — Moteur de récupération mémoire.

Inspiré de la cognition humaine :
- Rappel associatif (multi-niveaux)
- Fusion de résultats hétérogènes
- Ranking par pertinence
- Contexte-aware
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class RetrievalEngine:
    """Moteur de récupération mémoire multi-niveaux."""

    def __init__(self, memory_manager):
        self._memory = memory_manager

    async def recall(self, query: str, context: dict[str, Any]) -> list[Any]:
        """Rappel associatif depuis toutes les mémoires.

        Args:
            query: Requête de recherche
            context: Contexte actuel

        Returns:
            Liste de résultats triés par pertinence
        """
        results = []

        # 1. Working Memory (exact match, ultra-rapide)
        if self._memory.working:
            try:
                working = await self._memory.working.search("working", query, limit=5)
                results.extend(working)
            except Exception as e:
                logger.warning(f"Working memory search failed: {e}")

        # 2. Short-term Memory (récents)
        if self._memory.short_term:
            try:
                short = await self._memory.short_term.search("short_term", query, limit=5)
                results.extend(short)
            except Exception as e:
                logger.warning(f"Short-term memory search failed: {e}")

        # 3. Vector Memory (sémantique)
        if self._memory.vector:
            try:
                # TODO: Générer embedding de la query
                # Pour l'instant, recherche par texte
                vectors = await self._memory.vector.search("vector", query, limit=10)
                results.extend(vectors)
            except Exception as e:
                logger.warning(f"Vector memory search failed: {e}")

        # 4. Semantic Memory (concepts)
        if self._memory.semantic:
            try:
                semantic = await self._memory.semantic.search("semantic", query, limit=5)
                results.extend(semantic)
            except Exception as e:
                logger.warning(f"Semantic memory search failed: {e}")

        # 5. Procedural Memory (skills)
        if self._memory.procedural:
            try:
                procedural = await self._memory.procedural.search("procedural", query, limit=5)
                results.extend(procedural)
            except Exception as e:
                logger.warning(f"Procedural memory search failed: {e}")

        # Fusion et ranking
        return self._rank_and_fuse(results, context)

    def _rank_and_fuse(self, results: list[Any], context: dict[str, Any]) -> list[Any]:
        """Fusionne et classe les résultats.

        Args:
            results: Résultats bruts
            context: Contexte

        Returns:
            Résultats triés par pertinence
        """
        # Supprimer les doublons (par clé)
        seen = set()
        unique = []
        for r in results:
            key = getattr(r, 'key', str(r))
            if key not in seen:
                seen.add(key)
                unique.append(r)

        # Calculer le score composite
        for item in unique:
            item.score = self._calculate_score(item, context)

        # Trier par score décroissant
        unique.sort(key=lambda x: getattr(x, 'score', 0), reverse=True)

        # Retourner le top N
        return unique[:20]

    def _calculate_score(self, item: Any, context: dict[str, Any]) -> float:
        """Calcule le score de pertinence.

        Facteurs :
        - Similarité sémantique (40%)
        - Fraîcheur (20%)
        - Importance (20%)
        - Fréquence d'accès (10%)
        - Contexte (10%)

        Args:
            item: Item à évaluer
            context: Contexte

        Returns:
            Score de 0.0 à 1.0
        """
        score = 0.0

        # Similarité sémantique (40%)
        similarity = getattr(item, 'score', 0.0)
        score += similarity * 0.4

        # Fraîcheur (20%)
        created_at = getattr(item, 'created_at', datetime.utcnow())
        if isinstance(created_at, datetime):
            age_days = (datetime.utcnow() - created_at).days
            freshness = max(0.0, 1.0 - (age_days / 90.0))
            score += freshness * 0.2

        # Importance (20%)
        importance = getattr(item, 'importance', 0.5)
        score += importance * 0.2

        # Fréquence d'accès (10%)
        access_count = getattr(item, 'access_count', 0)
        access_score = min(1.0, access_count / 10.0)
        score += access_score * 0.1

        # Contexte (10%)
        metadata = getattr(item, 'metadata', {})
        if metadata.get('session_id') == context.get('session_id'):
            score += 0.1

        return min(1.0, score)

    async def recall_by_type(
        self,
        query: str,
        memory_type: Any,
        limit: int = 10,
    ) -> list[Any]:
        """Récupère des souvenirs d'un type spécifique.

        Args:
            query: Requête
            memory_type: Type de mémoire
            limit: Limite

        Returns:
            Résultats
        """
        type_map = {
            'working': self._memory.working,
            'short_term': self._memory.short_term,
            'episodic': self._memory.episodic,
            'semantic': self._memory.semantic,
            'procedural': self._memory.procedural,
            'vector': self._memory.vector,
            'event_log': self._memory.event_log,
            'history': self._memory.history,
        }

        store = type_map.get(memory_type)
        if not store:
            return []

        try:
            namespace = f"memory:{memory_type}"
            return await store.search(namespace, query, limit=limit)
        except Exception as e:
            logger.error(f"Recall by type failed: {e}")
            return []