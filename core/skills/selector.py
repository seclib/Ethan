"""Skill Selector — Sélection intelligente de skills."""

from __future__ import annotations

import logging
from typing import Any

from core.skills.registry import SkillRegistry
from core.skills.types import Skill, SkillContext

logger = logging.getLogger(__name__)


class SkillSelector:
    """Sélectionne la meilleure skill pour un contexte.
    
    Responsabilités :
    - Scoring des skills
    - Filtrage par contraintes
    - Sélection du meilleur candidat
    """

    def __init__(self):
        self._registry = SkillRegistry()

    def set_registry(self, registry: SkillRegistry) -> None:
        """Définit le registry.

        Args:
            registry: Registry de skills
        """
        self._registry = registry

    def select(self, context: SkillContext, max_results: int = 1) -> list[tuple[Skill, float, str]]:
        """Sélectionne les meilleures skills.

        Args:
            context: Contexte de sélection
            max_results: Nombre max de résultats

        Returns:
            Liste de (skill, score, reasoning)
        """
        candidates = self._registry.list_skills(enabled_only=True)

        if not candidates:
            return []

        # Scorer chaque skill
        scored = []
        for skill in candidates:
            score, reasoning = self._score_skill(skill, context)
            scored.append((skill, score, reasoning))

        # Trier par score décroissant
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[:max_results]

    def _score_skill(self, skill: Skill, context: SkillContext) -> tuple[float, str]:
        """Score une skill.

        Args:
            skill: Skill à scorer
            context: Contexte

        Returns:
            (score, reasoning)
        """
        score = 0.0
        reasons = []

        # 1. Correspondance sémantique (basique)
        query_lower = context.parameters.get("query", "").lower()
        if query_lower in skill.name.lower():
            score += 0.3
            reasons.append("name match")
        if query_lower in skill.description.lower():
            score += 0.2
            reasons.append("description match")

        # 2. Tags
        if context.parameters.get("tags"):
            required_tags = context.parameters["tags"]
            matching = sum(1 for tag in required_tags if tag in skill.tags)
            if matching > 0:
                score += 0.2 * (matching / len(required_tags))
                reasons.append(f"tags match ({matching})")

        # 3. Taux de succès historique
        if skill.total_executions > 0:
            success_rate = skill.success_count / skill.total_executions
            score += 0.2 * success_rate
            reasons.append(f"success rate {success_rate:.2f}")

        # 4. Catégorie
        if context.parameters.get("category"):
            if skill.category == context.parameters["category"]:
                score += 0.1
                reasons.append("category match")

        # 5. Pénalités
        # Coût
        if context.max_cost is not None:
            # TODO: Calculer le coût estimé
            pass

        # Durée
        if context.max_duration_ms is not None:
            if skill.estimated_duration_ms > context.max_duration_ms:
                score -= 0.3
                reasons.append("duration too long")

        reasoning = ", ".join(reasons) if reasons else "default"
        return score, reasoning

    def recommend_next(self, completed_skill_id: str, context: SkillContext) -> list[tuple[Skill, float, str]]:
        """Recommande des skills suivants.

        Args:
            completed_skill_id: ID de la skill complétée
            context: Contexte

        Returns:
            Liste de skills recommandées
        """
        # TODO: Implémenter la recommandation basée sur l'historique
        return self.select(context, max_results=3)