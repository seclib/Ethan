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

    def __init__(self):
        self._max_retries = 3
        self._retry_delay = 1.0  # secondes

    async def execute(self, tool: Tool, params: dict[str, Any], context: ToolContext) -> ToolResult:
        """Exécute un outil.

        Args:
            tool: Outil à exécuter
            params: Paramètres d'exécution
            context: Contexte d'exécution

        Returns:
            Résultat de l'exécution
        """
        start_time = time.time()

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
        """Exécute l'outil (MVP: simulation).

        Args:
            tool: Outil
            params: Paramètres

        Returns:
            Résultat
        """
        # MVP: simulation
        await asyncio.sleep(0.1)  # Simuler l'exécution
        return {"status": "ok", "params": params}

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