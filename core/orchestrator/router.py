"""Request Router — Route les requêtes vers les bons modules."""

from __future__ import annotations

import logging
from typing import Any

from core.orchestrator.context import OrchestratorContext

logger = logging.getLogger(__name__)


class RequestRouter:
    """Route les requêtes vers les modules appropriés.
    
    Responsabilités :
    - Analyser la requête
    - Déterminer le module cible
    - Router vers cognition, planner, tools, etc.
    """

    def __init__(self):
        self._routes: dict[str, str] = {
            "intent": "cognition",
            "plan": "planner",
            "execute": "tools",
            "memory": "memory",
            "security": "security",
            "llm": "llm",
            "skill": "skills",
        }

    async def route(self, context: OrchestratorContext, request_type: str) -> str:
        """Route une requête.

        Args:
            context: Contexte
            request_type: Type de requête

        Returns:
            Module cible
        """
        module = self._routes.get(request_type, "cognition")
        logger.debug(f"Routing request {context.request_id} to {module}")
        return module

    def get_available_routes(self) -> list[str]:
        """Liste les routes disponibles.

        Returns:
            Liste de routes
        """
        return list(self._routes.keys())