"""Tool Registry — Catalogue central de tous les outils."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from core.tools.types import Tool, ToolContext

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Catalogue central de tous les outils."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._categories: dict[str, list[str]] = defaultdict(list)
        self._capabilities: dict[str, list[str]] = defaultdict(list)
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Enregistre les outils natifs."""
        try:
            from core.tools.builtin import get_builtin_tools
            for tool in get_builtin_tools():
                self.register(tool)
        except ImportError as e:
            logger.warning(f"Could not load builtin tools: {e}")

    def register(self, tool: Tool) -> None:
        """Enregistre un outil.

        Args:
            tool: Outil à enregistrer
        """
        existing = self._tools.get(tool.id)
        if existing is not None:
            self._unindex(existing)

        self._tools[tool.id] = tool
        self._categories[tool.category].append(tool.id)

        for capability in tool.capabilities:
            self._capabilities[capability].append(tool.id)

        logger.info(f"Tool registered: {tool.id} ({tool.name})")

    def unregister(self, tool_id: str) -> None:
        """Supprime un outil.

        Args:
            tool_id: ID de l'outil
        """
        if tool_id not in self._tools:
            return

        tool = self._tools.pop(tool_id)
        self._unindex(tool)

        logger.info(f"Tool unregistered: {tool_id}")

    def _unindex(self, tool: Tool) -> None:
        """Remove a tool from secondary indexes before replacing it."""
        category_tools = self._categories.get(tool.category, [])
        if tool.id in category_tools:
            category_tools.remove(tool.id)
        if not category_tools:
            self._categories.pop(tool.category, None)

        for capability in tool.capabilities:
            capability_tools = self._capabilities.get(capability, [])
            if tool.id in capability_tools:
                capability_tools.remove(tool.id)
            if not capability_tools:
                self._capabilities.pop(capability, None)

    def get(self, tool_id: str) -> Tool | None:
        """Récupère un outil par ID.

        Args:
            tool_id: ID de l'outil

        Returns:
            Outil ou None
        """
        return self._tools.get(tool_id)

    def get_by_capability(self, capability: str) -> list[Tool]:
        """Trouve les outils pour une capability.

        Args:
            capability: Capability recherchée

        Returns:
            Liste d'outils
        """
        tool_ids = self._capabilities.get(capability, [])
        return [self._tools[tid] for tid in tool_ids if tid in self._tools]

    def get_by_category(self, category: str) -> list[Tool]:
        """Trouve les outils par catégorie.

        Args:
            category: Catégorie

        Returns:
            Liste d'outils
        """
        tool_ids = self._categories.get(category, [])
        return [self._tools[tid] for tid in tool_ids if tid in self._tools]

    def search(self, query: str, context: ToolContext | None = None) -> list[Tool]:
        """Recherche des outils par requête.

        Args:
            query: Requête de recherche
            context: Contexte (optionnel)

        Returns:
            Liste d'outils correspondants
        """
        query_lower = query.lower()
        results = []

        for tool in self._tools.values():
            # Recherche dans le nom, description, tags
            if (query_lower in tool.name.lower() or
                query_lower in tool.description.lower() or
                any(query_lower in tag.lower() for tag in tool.tags)):
                results.append(tool)

        return results

    def get_available_tools(self, context: ToolContext) -> list[Tool]:
        """Récupère les outils disponibles pour un contexte.

        Args:
            context: Contexte de sélection

        Returns:
            Liste d'outils disponibles
        """
        available = []

        for tool in self._tools.values():
            if not tool.is_available:
                continue

            # Vérifier les permissions (MVP: pas de vérification)
            # Vérifier les dépendances (MVP: pas de vérification)
            available.append(tool)

        return available

    def list_all(self) -> list[Tool]:
        """Liste tous les outils.

        Returns:
            Liste de tous les outils
        """
        return list(self._tools.values())

    def list_categories(self) -> list[str]:
        """Liste toutes les catégories.

        Returns:
            Liste de catégories
        """
        return list(self._categories.keys())

    def get_stats(self) -> dict[str, Any]:
        """Récupère les statistiques.

        Returns:
            Statistiques du registry
        """
        return {
            "total_tools": len(self._tools),
            "categories": len(self._categories),
            "capabilities": len(self._capabilities),
            "available_tools": sum(1 for t in self._tools.values() if t.is_available),
        }
