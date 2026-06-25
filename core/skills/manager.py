"""Skill Manager — Orchestrateur principal des skills."""

from __future__ import annotations

import logging
from typing import Any

from core.skills.registry import SkillRegistry
from core.skills.types import Skill, SkillContext, SkillResult, SkillStatus
from core.tools.manager import ToolManager

logger = logging.getLogger(__name__)


class SkillManager:
    """Orchestrateur principal des skills.
    
    Responsabilités :
    - Gestion du cycle de vie des skills
    - Coordination avec le Tool Manager
    - Exécution et monitoring
    """

    def __init__(self, tool_manager: ToolManager):
        self._registry = SkillRegistry()
        self._tool_manager = tool_manager
        self._executions: dict[str, SkillResult] = {}

    def register_skill(self, skill: Skill) -> None:
        """Enregistre une skill.

        Args:
            skill: Skill à enregistrer
        """
        self._registry.register(skill)

    def unregister_skill(self, skill_id: str) -> None:
        """Désenregistre une skill.

        Args:
            skill_id: ID de la skill
        """
        self._registry.unregister(skill_id)

    def get_skill(self, skill_id: str) -> Skill | None:
        """Récupère une skill.

        Args:
            skill_id: ID de la skill

        Returns:
            Skill ou None
        """
        return self._registry.get(skill_id)

    def list_skills(self, **kwargs: Any) -> list[Skill]:
        """Liste les skills.

        Returns:
            Liste de skills
        """
        return self._registry.list_skills(**kwargs)

    def search_skills(self, query: str) -> list[Skill]:
        """Recherche des skills.

        Args:
            query: Requête

        Returns:
            Liste de skills
        """
        return self._registry.search(query)

    async def execute(self, context: SkillContext) -> SkillResult:
        """Exécute une skill.

        Args:
            context: Contexte d'exécution

        Returns:
            Résultat
        """
        skill = self._registry.get(context.skill_id)
        if not skill:
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                error=f"Skill not found: {context.skill_id}",
            )

        # Valider les dépendances
        if not self._registry.validate_dependencies(context.skill_id):
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                error="Dependencies not met",
            )

        logger.info(f"Executing skill: {skill.name} ({skill.id})")

        # TODO: Implémenter l'exécution via SkillExecutor
        result = SkillResult(
            skill_id=skill.id,
            status=SkillStatus.COMPLETED,
            steps_completed=len(skill.steps),
            steps_total=len(skill.steps),
        )

        self._executions[skill.id] = result
        return result

    def get_execution_result(self, skill_id: str) -> SkillResult | None:
        """Récupère le résultat d'une exécution.

        Args:
            skill_id: ID de la skill

        Returns:
            Résultat ou None
        """
        return self._executions.get(skill_id)

    def get_stats(self) -> dict[str, Any]:
        """Récupère les statistiques.

        Returns:
            Statistiques
        """
        return {
            "registry": self._registry.get_stats(),
            "executions": len(self._executions),
        }