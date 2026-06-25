"""Intention Analyzer — Analyse l'intention des requêtes."""

from __future__ import annotations

import logging
from typing import Any

from core.cognition.types import Intent, IntentType

logger = logging.getLogger(__name__)


class IntentionAnalyzer:
    """Analyse l'intention d'une requête utilisateur."""

    def __init__(self):
        self._patterns = {
            IntentType.COMMAND: ["!", "executer", "exécuter", "run", "lancer"],
            IntentType.QUERY: ["?", "quoi", "qui", "où", "quand", "comment", "pourquoi", "explique"],
            IntentType.CONVERSATION: ["bonjour", "salut", "aide", "help", "merci"],
            IntentType.TASK: ["fait", "crée", "génère", "déploie", "build", "test"],
        }

    async def analyze(self, query: str) -> Intent:
        """Analyse une requête et extrait l'intention.

        Args:
            query: Requête utilisateur

        Returns:
            Intent avec type, entités et confiance
        """
        query_lower = query.lower().strip()

        # Détection par patterns
        scores = {}
        for intent_type, keywords in self._patterns.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            scores[intent_type] = score

        # Prendre le meilleur match
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]

        # Calculer la confiance
        if best_score == 0:
            # Aucun match → TASK par défaut avec faible confiance
            return Intent(
                type=IntentType.TASK,
                entities={"description": query},
                confidence=0.5,
                raw_query=query,
                ambiguity_score=0.5,
            )

        confidence = min(0.95, 0.6 + (best_score * 0.1))

        # Extraire les entités
        entities = self._extract_entities(query, best_intent)

        return Intent(
            type=best_intent,
            entities=entities,
            confidence=confidence,
            raw_query=query,
            ambiguity_score=1.0 - confidence,
        )

    def _extract_entities(self, query: str, intent_type: IntentType) -> dict[str, Any]:
        """Extrait les entités de la requête."""
        entities = {}

        if intent_type == IntentType.COMMAND:
            # Extraire la commande
            if query.startswith("!"):
                entities["command"] = query[1:].strip()

        elif intent_type == IntentType.TASK:
            # Extraire la description
            entities["description"] = query

        return entities

    async def generate_clarification(self, query: str) -> list[str]:
        """Génère des questions de clarification.

        Args:
            query: Requête ambiguë

        Returns:
            Liste de questions
        """
        return [
            "Pourriez-vous préciser ce que vous attendez ?",
            "S'agit-il d'une question ou d'une tâche à accomplir ?",
        ]