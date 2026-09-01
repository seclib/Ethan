"""Tool Executor — Exécute les outils avec isolation.

Responsabilités :
- Vérifier les dépendances
- Valider via Security Gateway
- Exécuter dans un sandbox
- Gérer timeout et retry
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from core.tools.types import Tool, ToolContext, ToolResult

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Exécute les outils avec isolation."""

    def __init__(self, policy_enforcer=None):
        self._max_retries = 3
        self._retry_delay = 1.0  # secondes
        # Intégration sécurité (Phase 07) : SecureToolEnforcer | None.
        # None = comportement historique (aucune évaluation).
        self._policy_enforcer = policy_enforcer

    async def execute(
        self, tool: Tool, params: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        """Exécute un outil.

        Args:
            tool: Outil à exécuter
            params: Paramètres d'exécution
            context: Contexte d'exécution

        Returns:
            Résultat de l'exécution
        """
        start_time = time.time()

        # 0. Évaluation sécurité (PolicyEngine + Capability + ExfilGuard).
        #    Non contournable : toute exécution sensible passe par l'enforcer.
        if self._policy_enforcer is not None:
            try:
                await self._policy_enforcer.check(tool, params, context)
            except Exception as e:
                from core.security.integration import ToolRejectedError

                if isinstance(e, ToolRejectedError):
                    logger.warning(
                        "Tool %s rejected by security policy: %s", tool.id, e.reason
                    )
                    return ToolResult(
                        status="rejected",
                        error=e.reason,
                        duration_ms=(time.time() - start_time) * 1000,
                        metadata={"rejected": True, "reason": e.reason},
                    )
                # Erreur d'infrastructure de sécurité : fail-closed (on ne
                # contourne jamais la sécurité même en cas de panne).
                logger.error(
                    "Tool %s security check failed (%s) -> rejected", tool.id, e
                )
                return ToolResult(
                    status="rejected",
                    error="Security check unavailable (fail-closed).",
                    duration_ms=(time.time() - start_time) * 1000,
                    metadata={"rejected": True, "fail_closed": True},
                )

        # 1. Vérifier les dépendances (MVP: skip)
        # await self._check_dependencies(tool)

        # 2. Valider via Security Gateway (MVP: skip)
        # from core.security.gateway import SecurityGateway
        # gateway = SecurityGateway()
        # result = await gateway.execute(...)

        # 3. Exécuter avec retry
        for attempt in range(self._max_retries):
            try:
                # Timeout
                output = await asyncio.wait_for(
                    self._run_tool(tool, params),
                    timeout=tool.timeout_seconds,
                )

                duration_ms = (time.time() - start_time) * 1000

                return ToolResult(
                    status="success",
                    output=output,
                    duration_ms=duration_ms,
                    cost=tool.cost_per_call,
                )

            except asyncio.TimeoutError:
                logger.warning(f"Tool {tool.id} timed out (attempt {attempt + 1})")
                if attempt == self._max_retries - 1:
                    return ToolResult(
                        status="timeout",
                        error=f"Timeout after {tool.timeout_seconds}s",
                        duration_ms=(time.time() - start_time) * 1000,
                    )

            except Exception as e:
                logger.error(f"Tool {tool.id} failed (attempt {attempt + 1}): {e}")
                if attempt == self._max_retries - 1:
                    return ToolResult(
                        status="failed",
                        error=str(e),
                        duration_ms=(time.time() - start_time) * 1000,
                    )

            # Attendre avant retry
            if attempt < self._max_retries - 1:
                await asyncio.sleep(self._retry_delay * (attempt + 1))

        # Ne devrait jamais arriver
        return ToolResult(
            status="failed",
            error="Max retries exceeded",
            duration_ms=(time.time() - start_time) * 1000,
        )

    async def _run_tool(self, tool: Tool, params: dict[str, Any]) -> Any:
        """Exécute l'outil.

        Args:
            tool: Outil
            params: Paramètres

        Returns:
            Résultat
        """
        # Exécution MCP
        if tool.provider == "mcp":
            return await self._run_mcp_tool(tool, params)

        # MVP: simulation pour les outils builtin
        await asyncio.sleep(0.1)  # Simuler l'exécution
        return {"status": "ok", "params": params}

    async def _run_mcp_tool(self, tool: Tool, params: dict[str, Any]) -> Any:
        """Exécute un outil MCP via le client MCP.

        Args:
            tool: Outil MCP
            params: Paramètres

        Returns:
            Résultat de l'exécution MCP
        """
        from core.tools.mcp_client import MCPClient

        metadata = tool.metadata or {}
        server_url = metadata.get("mcp_server_url")
        transport = metadata.get("mcp_transport", "http")
        command = metadata.get("mcp_command")
        args = metadata.get("mcp_args")
        auth_type = metadata.get("mcp_auth_type", "none")

        if not server_url:
            raise ValueError(f"Tool {tool.id} has no MCP server URL in metadata")

        client = MCPClient()
        try:
            await client.connect(
                server_url,
                transport=transport,
                command=command,
                args=args,
                auth_type=auth_type,
            )
            return await client.call_tool(tool.name, params)
        finally:
            await client.disconnect()

    async def _check_dependencies(self, tool: Tool) -> None:
        """Vérifie les dépendances.

        Args:
            tool: Outil

        Raises:
            RuntimeError: Si une dépendance manque
        """
        # MVP: pas de vérification
        pass

    def _select_sandbox(self, risk_level: str) -> str:
        """Sélectionne le sandbox selon le risque.

        Args:
            risk_level: Niveau de risque

        Returns:
            Type de sandbox
        """
        sandbox_map = {
            "low": "none",
            "medium": "docker",
            "high": "gvisor",
            "critical": "firecracker",
        }
        return sandbox_map.get(risk_level, "docker")
