"""Skill Composer — Composition de skills."""

from __future__ import annotations

import logging
from typing import Any

from core.skills.registry import SkillRegistry
from core.skills.types import Skill, SkillContext, SkillResult, SkillStatus

logger = logging.getLogger(__name__)


class SkillComposer:
    """Compose plusieurs skills en un workflow.
    
    Responsabilités :
    - Composition séquentielle
    - Composition parallèle
    - Gestion des dépendances entre skills
    - Agrégation des résultats
    """

    def __init__(self, registry: SkillRegistry):
        self._registry = registry

    async def compose_sequential(self, skill_ids: list[str], context: SkillContext) -> SkillResult:
        """Compose des skills en séquence.

        Args:
            skill_ids: IDs des skills
            context: Contexte

        Returns:
            Résultat agrégé
        """
        results = []
        for skill_id in skill_ids:
            skill = self._registry.get(skill_id)
            if not skill:
                return SkillResult(
                    skill_id=skill_id,
                    status=SkillStatus.FAILED,
                    error=f"Skill not found: {skill_id}",
                )

            # TODO: Exécuter via SkillExecutor
            result = SkillResult(
                skill_id=skill.id,
                status=SkillStatus.COMPLETED,
            )
            results.append(result)

            if result.status == SkillStatus.FAILED:
                return SkillResult(
                    skill_id="composed",
                    status=SkillStatus.FAILED,
                    error=f"Skill {skill_id} failed",
                    metadata={"results": results},
                )

        return SkillResult(
            skill_id="composed",
            status=SkillStatus.COMPLETED,
            output={"results": results},
            metadata={"composed": len(results)},
        )

    async def compose_parallel(self, skill_ids: list[str], context: SkillContext) -> SkillResult:
        """Compose des skills en parallèle.

        Args:
            skill_ids: IDs des skills
            context: Contexte

        Returns:
            Résultat agrégé
        """
        # TODO: Implémenter l'exécution parallèle
        return await self.compose_sequential(skill_ids, context)

    def validate_composition(self, skill_ids: list[str]) -> bool:
        """Valide une composition.

        Args:
            skill_ids: IDs des skills

        Returns:
            True si valide
        """
        for skill_id in skill_ids:
            if not self._registry.get(skill_id):
                return False
        return True