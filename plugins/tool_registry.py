"""Tool Registry — enregistrement et découverte des outils."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolParameter:
    """Paramètre d'un outil."""
    name: str
    type: str = "string"  # string, number, boolean, object
    required: bool = False
    description: str = ""
    default: Any = None


@dataclass
class ToolDefinition:
    """Définition complète d'un outil."""
    name: str
    plugin: str
    description: str
    parameters: dict[str, ToolParameter] = field(default_factory=dict)
    permissions: list[str] = field(default_factory=list)
    version: str = "1.0.0"


@dataclass
class ToolResult:
    """Résultat d'exécution d'un outil."""
    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, str] | None = None


class ToolRegistry:
    """Registre des outils disponibles."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Enregistre un outil."""
        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """Désenregistre un outil."""
        self._tools.pop(tool_name, None)

    def get(self, tool_name: str) -> ToolDefinition | None:
        """Récupère un outil par nom."""
        return self._tools.get(tool_name)

    def list_all(self) -> list[ToolDefinition]:
        """Liste tous les outils."""
        return list(self._tools.values())

    def list_by_plugin(self, plugin_name: str) -> list[ToolDefinition]:
        """Liste les outils d'un plugin spécifique."""
        return [t for t in self._tools.values() if t.plugin == plugin_name]

    def search(self, query: str) -> list[ToolDefinition]:
        """Recherche des outils par nom ou description."""
        q = query.lower()
        return [
            t for t in self._tools.values()
            if q in t.name.lower() or q in t.description.lower()
        ]

    def clear(self) -> None:
        """Vide le registre."""
        self._tools.clear()