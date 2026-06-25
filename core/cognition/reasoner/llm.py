"""Reasoner — Raisonne avec un LLM."""

from __future__ import annotations

import logging
from typing import Any

from core.cognition.types import Reasoning

logger = logging.getLogger(__name__)


class Reasoner:
    """Raisonneur LLM pour le module Cognition.

    Responsabilités :
    - Construire le prompt
    - Appeler le LLM
    - Parser la réponse
    - Gérer le streaming
    """

    def __init__(self, llm_client=None):
        self._llm = llm_client

    async def reason(
        self,
        query: str,
        intent: Any,
        context: dict[str, Any],
        constraints: dict[str, Any] | None = None,
    ) -> Reasoning:
        """Raisonne sur une requête.

        Args:
            query: Requête utilisateur
            intent: Intent analysé
            context: Contexte assemblé
            constraints: Contraintes (temps, ressources)

        Returns:
            Reasoning avec chain_of_thought, goal, capabilities
        """
        # Construire le prompt
        prompt = self._build_prompt(query, intent, context)

        # Appeler le LLM (MVP : simulation)
        if self._llm:
            response = await self._call_llm(prompt, constraints)
        else:
            response = self._simulate_reasoning(query, intent, context)

        # Parser la réponse
        reasoning = self._parse_response(response, query)

        return reasoning

    def _build_prompt(self, query: str, intent: Any, context: dict[str, Any]) -> str:
        """Construit le prompt pour le LLM."""
        intent_type = intent.type.value if hasattr(intent, 'type') else "unknown"

        prompt = f"""You are ETHAN, a cognitive AI assistant.

Intent: {intent_type}
Query: {query}

Context:
{self._format_context(context)}

Instructions:
1. Analyze the query
2. Determine the goal
3. Identify required capabilities
4. Provide reasoning chain

Respond in JSON format:
{{
  "chain_of_thought": "...",
  "goal": "...",
  "required_capabilities": ["..."],
  "confidence": 0.0-1.0
}}
"""
        return prompt

    def _format_context(self, context: dict[str, Any]) -> str:
        """Formate le contexte pour le prompt."""
        parts = []

        if context.get("messages"):
            parts.append("History:")
            for msg in context["messages"][:3]:
                parts.append(f"  - {msg.get('role', '?')}: {msg.get('content', '')[:100]}")

        if context.get("memory_items"):
            parts.append("Memory:")
            for item in context["memory_items"][:3]:
                parts.append(f"  - {item.get('content', '')[:100]}")

        return "\n".join(parts) if parts else "No context"

    async def _call_llm(self, prompt: str, constraints: dict[str, Any] | None) -> dict[str, Any]:
        """Appelle le LLM (production)."""
        # TODO: Intégrer le LLM provider
        raise NotImplementedError("LLM client not configured")

    def _simulate_reasoning(self, query: str, intent: Any, context: dict[str, Any]) -> dict[str, Any]:
        """Simule un raisonnement (MVP)."""
        return {
            "chain_of_thought": f"Analyzing query: {query}\nIntent: {intent.type.value if hasattr(intent, 'type') else 'unknown'}\nContext items: {len(context.get('messages', []))}",
            "goal": query,
            "required_capabilities": [],
            "confidence": 0.8,
        }

    def _parse_response(self, response: dict[str, Any], query: str) -> Reasoning:
        """Parse la réponse du LLM."""
        return Reasoning(
            chain_of_thought=response.get("chain_of_thought", ""),
            goal=response.get("goal", query),
            required_capabilities=response.get("required_capabilities", []),
            tokens_used=len(response.get("chain_of_thought", "")) // 4,  # Approximation
            model="simulated",
            latency_ms=50.0,
        )