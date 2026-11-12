"""Forgetting Engine — Moteur d'oubli intelligent.

Inspiré de la cognition humaine :
- Oubli naturel (courbe de l'oubli d'Ebbinghaus)
- Oubli par manque d'usage
- Oubli par redondance
- Consolidation des souvenirs importants
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class ForgettingEngine:
    """Moteur d'oubli intelligent."""

    def __init__(self, memory_manager):
        self._memory = memory_manager

    async def run(self) -> None:
        """Exécute le cycle d'oubli."""
        logger.info("Running forgetting cycle...")

        # Oublier dans Short-term Memory
        await self._forget_short_term()

        # Oublier dans Episodic Memory
        await self._forget_episodic()

        # Réduire l'importance des items anciens
        await self._decay_importance()

        logger.info("✅ Forgetting cycle complete")

    async def _forget_short_term(self) -> None:
        """Oublie les items expirés dans Short-term Memory."""
        if not self._memory.short_term:
            return

        try:
            # Lister toutes les clés
            keys = await self._memory.short_term.list_namespace("short_term")

            for key in keys:
                # Vérifier le TTL
                ttl = await self._memory.short_term.ttl("short_term", key)
                if ttl is None or ttl > 0:
                    continue

                # TTL expiré → supprimer
                await self._memory.short_term.delete("short_term", key)
                logger.debug(f"Forgot short-term item: {key}")

        except Exception as e:
            logger.error(f"Error forgetting short-term: {e}")

    async def _forget_episodic(self) -> None:
        """Oublie les items anciens non importants."""
        if not self._memory.episodic:
            return

        try:
            # TODO: Implémenter avec requête SQL
            # SELECT * FROM episodic_memory WHERE age > 90 AND importance < 0.3
            pass

        except Exception as e:
            logger.error(f"Error forgetting episodic: {e}")

    async def _decay_importance(self) -> None:
        """Réduit l'importance des items anciens."""
        # TODO: Implémenter
        pass

    async def should_forget(self, item: Any) -> bool:
        """Détermine si un item doit être oublié.

        Critères :
        1. TTL expiré
        2. Ancienneté d'accès > 30 jours
        3. Importance < 0.1
        4. Redondance (doublon trouvé)

        Args:
            item: Item à évaluer

        Returns:
            True si l'item doit être oublié
        """
        # 1. TTL expiré
        if item.ttl and item.age_seconds > item.ttl:
            return True

        # 2. Ancienneté d'accès
        if item.days_since_last_access > 30:
            # Réduire l'importance
            item.importance *= 0.9
            if item.importance < 0.1:
                return True

        # 3. Importance trop faible
        if item.importance < 0.05:
            return True

        return False

    async def is_redundant(self, item: Any, threshold: float = 0.95) -> bool:
        """Vérifie si l'item est redondant.

        Args:
            item: Item à vérifier
            threshold: Seuil de similarité

        Returns:
            True si un doublon existe
        """
        if not self._memory.vector:
            return False

        try:
            # Chercher des items similaires
            similar = await self._memory.vector.search_by_embedding(
                namespace="*",
                query_embedding=[],  # TODO: Générer embedding
                limit=5,
                min_similarity=threshold,
            )

            # Si plus d'un résultat → redondant
            return len(similar) > 1

        except Exception as e:
            logger.warning(f"Redundancy check failed: {e}")
            return False