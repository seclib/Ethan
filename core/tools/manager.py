"""Tool Manager — Module principal du Tool Manager.

Orchestre :
- ToolRegistry (catalogue)
- ToolSelector (sélection)
- ToolExecutor (exécution)
- ToolMonitor (surveillance)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from core.tools.registry import ToolRegistry
from core.tools.selector import ToolSelector
from core.tools.executor import ToolExecutor
from core.tools.monitor import ToolMonitor
from core.tools.types import Tool, ToolContext, ToolResult
from core.tools.types import RiskLevel
from core.state.record_store import CoreRecordStore

logger = logging.getLogger(__name__)


class ToolManager:
    """Module Tool Manager — gère les outils."""

    _CUSTOM_TOOLS_DOMAIN = "tools"
    _PIPELINES_DOMAIN = "tool-pipelines"

    def __init__(self, store: CoreRecordStore | None = None, policy_enforcer=None):
        self._store = store or CoreRecordStore()
        self.registry = ToolRegistry()
        self.selector = ToolSelector()
        # Intégration sécurité (Phase 07) : SecureToolEnforcer | None.
        self.executor = ToolExecutor(policy_enforcer=policy_enforcer)
        self.monitor = ToolMonitor()

    async def initialize(self) -> None:
        """Restore custom tool definitions into the Core registry.

        Built-ins are registered synchronously by :class:`ToolRegistry`.
        Custom tools are Core records and must be hydrated at startup so every
        gateway (HTTP, CLI, future desktop) observes the same catalogue.
        """
        for record in await self._store.list(self._CUSTOM_TOOLS_DOMAIN):
            self.registry.register(self._tool_from_record(record))

    async def create_tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        *,
        code: str = "",
        category: str = "custom",
        capabilities: list[str] | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Tool:
        """Create a persistent custom tool definition owned by the Core.

        ``code`` remains definition metadata. It is deliberately not executed
        here: custom execution must be routed through a reviewed executor or
        sandbox, rather than granting an HTTP client arbitrary code execution.
        """
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Tool name is required")
        if not isinstance(parameters, dict):
            raise ValueError("Tool parameters must be a JSON object")

        tool = Tool(
            id=str(uuid4()),
            name=normalized_name,
            description=description.strip(),
            parameters=dict(parameters),
            category=category.strip() or "custom",
            capabilities=list(capabilities or []),
            tags=list(tags or []),
            provider="custom",
            metadata={**dict(metadata or {}), "code": code},
        )
        await self._store.save(self._CUSTOM_TOOLS_DOMAIN, tool.id, self._tool_record(tool))
        self.registry.register(tool)
        return tool

    async def delete_tool(self, tool_id: str) -> bool:
        """Delete a custom tool definition; built-ins and MCP tools are read-only."""
        tool = self.registry.get(tool_id)
        if tool is not None and tool.provider != "custom":
            raise ValueError("Only custom tools can be deleted")
        deleted = await self._store.delete(self._CUSTOM_TOOLS_DOMAIN, tool_id)
        if deleted:
            self.registry.unregister(tool_id)
        return deleted

    async def create_pipeline(
        self,
        name: str,
        steps: list[dict[str, Any]],
        *,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist an ordered composition of Core tool calls.

        The pipeline is a definition only. Runtime orchestration remains
        responsible for scheduling, approvals and actual execution.
        """
        if not name.strip():
            raise ValueError("Pipeline name is required")
        if not isinstance(steps, list):
            raise ValueError("Pipeline steps must be a list")
        pipeline = {
            "id": str(uuid4()),
            "name": name.strip(),
            "description": description,
            "steps": list(steps),
            "metadata": dict(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._store.save(self._PIPELINES_DOMAIN, pipeline["id"], pipeline)
        return pipeline

    async def get_pipeline(self, pipeline_id: str) -> dict[str, Any] | None:
        """Retrieve a pipeline definition by identifier."""
        return await self._store.get(self._PIPELINES_DOMAIN, pipeline_id)

    async def list_pipelines(self) -> list[dict[str, Any]]:
        """List persistent pipeline definitions."""
        return await self._store.list(self._PIPELINES_DOMAIN)

    async def delete_pipeline(self, pipeline_id: str) -> bool:
        """Delete a pipeline definition."""
        return await self._store.delete(self._PIPELINES_DOMAIN, pipeline_id)

    @staticmethod
    def _tool_record(tool: Tool) -> dict[str, Any]:
        """Convert a Tool into a JSON-safe Core record."""
        return {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "version": tool.version,
            "category": tool.category,
            "capabilities": tool.capabilities,
            "cost_per_call": tool.cost_per_call,
            "avg_duration_ms": tool.avg_duration_ms,
            "timeout_seconds": tool.timeout_seconds,
            "accuracy": tool.accuracy,
            "success_rate": tool.success_rate,
            "risk_level": tool.risk_level.value,
            "required_permissions": tool.required_permissions,
            "sandbox_required": tool.sandbox_required,
            "dependencies": tool.dependencies,
            "conflicts": tool.conflicts,
            "is_available": tool.is_available,
            "total_calls": tool.total_calls,
            "success_count": tool.success_count,
            "tags": tool.tags,
            "provider": tool.provider,
            "metadata": tool.metadata,
            "created_at": tool.created_at.isoformat(),
        }

    @staticmethod
    def _tool_from_record(record: dict[str, Any]) -> Tool:
        """Restore a Tool from a JSON-safe Core record."""
        created_at = record.get("created_at")
        return Tool(
            id=record["id"],
            name=record["name"],
            description=record.get("description", ""),
            parameters=dict(record.get("parameters") or {}),
            version=record.get("version", "1.0.0"),
            category=record.get("category", "custom"),
            capabilities=list(record.get("capabilities") or []),
            cost_per_call=float(record.get("cost_per_call", 0.0)),
            avg_duration_ms=float(record.get("avg_duration_ms", 1000.0)),
            timeout_seconds=int(record.get("timeout_seconds", 30)),
            accuracy=float(record.get("accuracy", 0.9)),
            success_rate=float(record.get("success_rate", 0.95)),
            risk_level=RiskLevel(record.get("risk_level", RiskLevel.LOW.value)),
            required_permissions=list(record.get("required_permissions") or []),
            sandbox_required=bool(record.get("sandbox_required", False)),
            dependencies=list(record.get("dependencies") or []),
            conflicts=list(record.get("conflicts") or []),
            is_available=bool(record.get("is_available", True)),
            total_calls=int(record.get("total_calls", 0)),
            success_count=int(record.get("success_count", 0)),
            tags=list(record.get("tags") or []),
            provider=record.get("provider", "custom"),
            metadata=dict(record.get("metadata") or {}),
            created_at=datetime.fromisoformat(created_at) if created_at else datetime.utcnow(),
        )

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
