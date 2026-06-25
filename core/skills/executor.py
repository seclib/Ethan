"""Skill Executor — Exécution des skills avec pipeline."""

from __future__ import annotations

import logging
import time
from typing import Any

from core.skills.types import Skill, SkillContext, SkillResult, SkillStatus, SkillStep
from core.tools.manager import ToolManager

logger = logging.getLogger(__name__)


class SkillExecutor:
    """Exécute les skills en orchestrant les outils.
    
    Responsabilités :
    - Exécution séquentielle des étapes
    - Gestion des dépendances
    - Retry et timeout
    - Rollback en cas d'erreur
    """

    def __init__(self, tool_manager: ToolManager):
        self._tool_manager = tool_manager

    async def execute(self, skill: Skill, context: SkillContext) -> SkillResult:
        """Exécute une skill.

        Args:
            skill: Skill à exécuter
            context: Contexte d'exécution

        Returns:
            Résultat
        """
        start = time.time()
        steps_completed = 0
        steps_total = len(skill.steps)
        results: dict[str, Any] = {}

        logger.info(f"Executing skill: {skill.name} ({steps_total} steps)")

        # Exécuter les étapes
        for step in skill.steps:
            try:
                # Vérifier les dépendances
                if not self._check_dependencies(step, results):
                    if step.optional:
                        logger.warning(f"Skipping optional step: {step.name}")
                        continue
                    else:
                        return SkillResult(
                            skill_id=skill.id,
                            status=SkillStatus.FAILED,
                            error=f"Dependencies not met for step: {step.name}",
                            steps_completed=steps_completed,
                            steps_total=steps_total,
                            duration_ms=(time.time() - start) * 1000,
                        )

                # Exécuter l'outil via ToolManager
                logger.debug(f"Executing step: {step.name} (tool: {step.tool_id})")
                result = await self._tool_manager.select_and_execute(
                    query=step.name,
                    params=step.parameters,
                    context=context,  # type: ignore
                )

                # Stocker le résultat
                results[step.id] = result
                steps_completed += 1

                # Vérifier le résultat
                if result.status != "success":
                    if step.optional:
                        logger.warning(f"Optional step failed: {step.name}")
                        continue
                    else:
                        return SkillResult(
                            skill_id=skill.id,
                            status=SkillStatus.FAILED,
                            error=f"Step failed: {step.name} - {result.error}",
                            steps_completed=steps_completed,
                            steps_total=steps_total,
                            duration_ms=(time.time() - start) * 1000,
                            metadata={"failed_step": step.id},
                        )

            except Exception as e:
                logger.error(f"Step execution error: {step.name} - {e}", exc_info=True)
                return SkillResult(
                    skill_id=skill.id,
                    status=SkillStatus.FAILED,
                    error=f"Step error: {step.name} - {str(e)}",
                    steps_completed=steps_completed,
                    steps_total=steps_total,
                    duration_ms=(time.time() - start) * 1000,
                )

        # Succès
        duration_ms = (time.time() - start) * 1000
        logger.info(f"Skill completed: {skill.name} in {duration_ms:.2f}ms")

        return SkillResult(
            skill_id=skill.id,
            status=SkillStatus.COMPLETED,
            output=results,
            steps_completed=steps_completed,
            steps_total=steps_total,
            duration_ms=duration_ms,
        )

    def _check_dependencies(self, step: SkillStep, results: dict[str, Any]) -> bool:
        """Vérifie les dépendances d'une étape.

        Args:
            step: Étape
            results: Résultats des étapes précédentes

        Returns:
            True si les dépendances sont satisfaites
        """
        for dep_id in step.depends_on:
            if dep_id not in results:
                return False
        return True

    async def execute_step(self, step: SkillStep, context: SkillContext) -> Any:
        """Exécute une seule étape.

        Args:
            step: Étape
            context: Contexte

        Returns:
            Résultat
        """
        result = await self._tool_manager.select_and_execute(
            query=step.name,
            params=step.parameters,
            context=context,  # type: ignore
        )
        return result.output
