"""Tool Manager — Module principal du Tool Manager.

Orchestre :
- ToolRegistry (catalogue)
- ToolSelector (sélection)
- ToolExecutor (exécution)
- ToolMonitor (surveillance)
"""

from __future__ import annotations

import logging
from typing import Any

from core.tools.registry import ToolRegistry
from core.tools.selector import ToolSelector
from core.tools.executor import ToolExecutor
from core.tools.monitor import ToolMonitor
from core.tools.types import Tool, ToolContext, ToolResult

logger = logging.getLogger(__name__)


class ToolManager:
    """Module Tool Manager — gère les outils."""

    def __init__(self):
        self.registry = ToolRegistry()
        self.selector = ToolSelector()
        self.executor = ToolExecutor()
        self.monitor = ToolMonitor()

    def register_tool(self, tool: Tool) -> None:
        """Enregistre un outil.

        Args:
            tool: Outil à enregistrer
        """
        self.registry.register(tool)

    async def select_and_execute(self, query: str, params: dict[str, Any], context: ToolContext) -> ToolResult:
        """Sélectionne et exécute le meilleur outil.

        Args:
            query: Requête (ex: "build docker image")
            params: Paramètres d'exécution
            context: Contexte

        Returns:
            Résultat de l'exécution
        """
        # 1. Rechercher les candidats
        candidates = self.registry.search(query, context)

        if not candidates:
            return ToolResult(
                status="failed",
                error=f"No tools found for query: {query}",
            )

        # 2. Sélectionner le meilleur
        scored = self.selector.select(candidates, context)

        if not scored:
            return ToolResult(
                status="failed",
                error="No suitable tool found",
            )

        best = scored[0]
        logger.info(f"Selected tool: {best.tool.name} (score: {best.score:.3f})")
        logger.info(f"Reasoning: {best.reasoning}")

        # 3. Exécuter
        result = await self.executor.execute(best.tool, params, context)

        # 4. Enregistrer dans le monitor
        await self.monitor.record_execution(best.tool, result, params)

        return result

    async def execute_by_capability(self, capability: str, params: dict[str, Any], context: ToolContext) -> ToolResult:
        """Exécute une capability (trouve le meilleur outil).

        Args:
            capability: Capability requise
            params: Paramètres
            context: Contexte

        Returns:
            Résultat
        """
        # 1. Trouver les outils pour cette capability
        candidates = self.registry.get_by_capability(capability)

        if not candidates:
            return ToolResult(
                status="failed",
                error=f"No tools for capability: {capability}",
            )

        # 2. Sélectionner
        scored = self.selector.select(candidates, context)

        if not scored:
            return ToolResult(
                status="failed",
                error="No suitable tool found",
            )

        best = scored[0]

        # 3. Exécuter
        result = await self.executor.execute(best.tool, params, context)

        # 4. Monitor
        await self.monitor.record_execution(best.tool, result, params)

        return result

    def get_tool(self, tool_id: str) -> Tool | None:
        """Récupère un outil.

        Args:
            tool_id: ID de l'outil

        Returns:
            Outil ou None
        """
        return self.registry.get(tool_id)

    def list_tools(self) -> list[Tool]:
        """Liste tous les outils.

        Returns:
            Liste d'outils
        """
        return self.registry.list_all()

    def get_stats(self) -> dict[str, Any]:
        """Récupère les statistiques.

        Returns:
            Statistiques
        """
        return self.registry.get_stats()