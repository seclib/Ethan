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

    def register(self, tool: Tool) -> None:
        """Enregistre un outil.

        Args:
            tool: Outil à enregistrer
        """
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

        tool = self._tools[tool_id]
        del self._tools[tool_id]

        self._categories[tool.category].remove(tool_id)
        for capability in tool.capabilities:
            self._capabilities[capability].remove(tool_id)

        logger.info(f"Tool unregistered: {tool_id}")

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