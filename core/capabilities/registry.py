"""Capability Registry — Registre central des capacités ETHAN.

ETHAN doit pouvoir se décrire lui-même.
Le registre découvre les capacités du Core et les expose via une API.

Les interfaces ne découvrent plus ETHAN via le code.
Elles interrogent ce registre.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CapabilityInfo:
    """Information sur une capacité découverte."""
    name: str
    description: str
    available: bool
    source: str  # "core" ou "plugins"
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "available": self.available,
            "source": self.source,
            "details": self.details,
        }


class CapabilityRegistry:
    """Registre central des capacités ETHAN.

    Découvre les capacités disponibles dans le Core et les expose
    sous forme de métadonnées consultables par les interfaces.
    """

    def __init__(self):
        self._capabilities: dict[str, CapabilityInfo] = {}

    def register(self, name: str, info: CapabilityInfo) -> None:
        """Enregistre une capacité."""
        self._capabilities[name] = info

    def get(self, name: str) -> CapabilityInfo | None:
        """Récupère une capacité par son nom."""
        return self._capabilities.get(name)

    def list(self) -> list[CapabilityInfo]:
        """Liste toutes les capacités."""
        return list(self._capabilities.values())

    def to_dict(self) -> dict[str, Any]:
        """Sérialise le registre en dict."""
        return {
            name: info.to_dict() for name, info in self._capabilities.items()
        }

    # ── Découverte automatique ──────────────────────────────────────────

    def discover(self) -> dict[str, Any]:
        """Découvre automatiquement toutes les capacités ETHAN.

        Returns:
            Dict {category: [...]} — format API
        """
        self._capabilities.clear()

        # 1. Providers LLM
        self._discover_providers()

        # 2. Models
        self._discover_models()

        # 3. RAG
        self._discover_rag()

        # 4. Memory
        self._discover_memory()

        # 5. Planner
        self._discover_planner()

        # 6. Goals
        self._discover_goals()

        # 7. Missions
        self._discover_missions()

        # 8. Agents
        self._discover_agents()

        # 9. Skills
        self._discover_skills()

        # 10. Plugins
        self._discover_plugins()

        # Formater pour l'API
        return self._format_for_api()

    def _discover_providers(self) -> None:
        """Découvre les providers LLM."""
        try:
            from core.llm.provider_manager import ProviderManager
            # ProviderManager nécessite une initialisation
            # On vérifie simplement que le module est disponible
            self._capabilities["providers"] = CapabilityInfo(
                name="providers",
                description="LLM provider management (Ollama, OpenAI, Anthropic, etc.)",
                available=True,
                source="core",
                details={"module": "core.llm.provider_manager"},
            )
        except ImportError:
            self._capabilities["providers"] = CapabilityInfo(
                name="providers",
                description="LLM provider management",
                available=False,
                source="core",
            )

    def _discover_models(self) -> None:
        """Découvre les modèles disponibles."""
        try:
            from core.llm.provider_manager import ProviderManager
            self._capabilities["models"] = CapabilityInfo(
                name="models",
                description="AI model registry and status",
                available=True,
                source="core",
                details={"module": "core.llm.provider_manager"},
            )
        except ImportError:
            self._capabilities["models"] = CapabilityInfo(
                name="models",
                description="AI model registry",
                available=False,
                source="core",
            )

    def _discover_rag(self) -> None:
        """Découvre le module RAG."""
        try:
            from core.rag import RAGIngestion, RAGRetrieval, RAGContext
            self._capabilities["rag"] = CapabilityInfo(
                name="rag",
                description="Retrieval Augmented Generation (ingestion, embeddings, retrieval, context)",
                available=True,
                source="core",
                details={
                    "module": "core.rag",
                    "components": ["ingestion", "embeddings", "retrieval", "context"],
                },
            )
        except ImportError:
            self._capabilities["rag"] = CapabilityInfo(
                name="rag",
                description="Retrieval Augmented Generation",
                available=False,
                source="core",
            )

    def _discover_memory(self) -> None:
        """Découvre le module Memory."""
        try:
            from core.memory import MemoryManager
            self._capabilities["memory"] = CapabilityInfo(
                name="memory",
                description="Long-term cognitive memory (facts, events, search)",
                available=True,
                source="core",
                details={"module": "core.memory"},
            )
        except ImportError:
            self._capabilities["memory"] = CapabilityInfo(
                name="memory",
                description="Cognitive memory",
                available=False,
                source="core",
            )

    def _discover_planner(self) -> None:
        """Découvre le module Planner."""
        try:
            from core.planner import Planner
            self._capabilities["planner"] = CapabilityInfo(
                name="planner",
                description="Task orchestration DAG (planning, decomposition, optimization)",
                available=True,
                source="core",
                details={"module": "core.planner"},
            )
        except ImportError:
            self._capabilities["planner"] = CapabilityInfo(
                name="planner",
                description="Task orchestration",
                available=False,
                source="core",
            )

    def _discover_goals(self) -> None:
        """Découvre le module Goals."""
        try:
            from core.goals import GoalManager
            self._capabilities["goals"] = CapabilityInfo(
                name="goals",
                description="Cognitive goal management (create, track, complete)",
                available=True,
                source="core",
                details={"module": "core.goals"},
            )
        except ImportError:
            self._capabilities["goals"] = CapabilityInfo(
                name="goals",
                description="Goal management",
                available=False,
                source="core",
            )

    def _discover_missions(self) -> None:
        """Découvre le module Missions."""
        try:
            from core.missions import MissionManager
            self._capabilities["missions"] = CapabilityInfo(
                name="missions",
                description="Long-term objectives with tasks and progression",
                available=True,
                source="core",
                details={"module": "core.missions"},
            )
        except ImportError:
            self._capabilities["missions"] = CapabilityInfo(
                name="missions",
                description="Mission management",
                available=False,
                source="core",
            )

    def _discover_agents(self) -> None:
        """Découvre le module Agents."""
        try:
            from core.agents import AgentManager
            self._capabilities["agents"] = CapabilityInfo(
                name="agents",
                description="Autonomous agent lifecycle (deploy, monitor, control)",
                available=True,
                source="core",
                details={"module": "core.agents"},
            )
        except ImportError:
            self._capabilities["agents"] = CapabilityInfo(
                name="agents",
                description="Agent management",
                available=False,
                source="core",
            )

    def _discover_skills(self) -> None:
        """Découvre le module Skills."""
        try:
            from core.skills import SkillManager
            self._capabilities["skills"] = CapabilityInfo(
                name="skills",
                description="Cognitive skills registry and execution",
                available=True,
                source="core",
                details={"module": "core.skills"},
            )
        except ImportError:
            self._capabilities["skills"] = CapabilityInfo(
                name="skills",
                description="Skill management",
                available=False,
                source="core",
            )

    def _discover_plugins(self) -> None:
        """Découvre le module Plugins."""
        try:
            from plugins.manager import PluginManager
            self._capabilities["plugins"] = CapabilityInfo(
                name="plugins",
                description="Plugin marketplace and management",
                available=True,
                source="plugins",
                details={"module": "plugins.manager"},
            )
        except ImportError:
            self._capabilities["plugins"] = CapabilityInfo(
                name="plugins",
                description="Plugin management",
                available=False,
                source="plugins",
            )

    def _format_for_api(self) -> dict[str, Any]:
        """Formate le registre pour l'API.

        Retourne :
        {
            "providers": [...],
            "agents": [...],
            "skills": [...],
            "rag": true,
            "memory": true,
            ...
        }
        """
        result: dict[str, Any] = {}

        for name, info in self._capabilities.items():
            if name in ("rag", "memory", "planner", "goals", "missions", "agents", "plugins"):
                # Booléen simple pour les capacités binaires
                result[name] = info.available
            else:
                # Liste pour les capacités avec des éléments
                result[name] = [info.to_dict()]

        return result
