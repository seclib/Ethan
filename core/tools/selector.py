"""Tool Selector — Sélectionne le meilleur outil avec scoring.

Score composite :
- Précision (30%)
- Vitesse (20%)
- Coût inverse (20%)
- Fiabilité (20%)
- Disponibilité (10%)
"""

from __future__ import annotations

import logging
from typing import Any

from core.tools.types import ScoredTool, Tool, ToolContext

logger = logging.getLogger(__name__)


class ToolSelector:
    """Sélectionne le meilleur outil."""

    def select(self, candidates: list[Tool], context: ToolContext) -> list[ScoredTool]:
        """Score et rank les outils.

        Args:
            candidates: Liste d'outils candidats
            context: Contexte de sélection

        Returns:
            Top 3 outils scorés
        """
        scored = []

        for tool in candidates:
            score, reasoning = self._calculate_score(tool, context)
            scored.append(ScoredTool(tool=tool, score=score, reasoning=reasoning))

        # Trier par score décroissant
        scored.sort(key=lambda x: x.score, reverse=True)

        # Retourner le top 3
        return scored[:3]

    def _calculate_score(self, tool: Tool, context: ToolContext) -> tuple[float, str]:
        """Calcule le score composite.

        Returns:
            (score, reasoning)
        """
        score = 0.0
        reasons = []

        # 1. Précision (30%)
        precision_score = tool.accuracy * 0.3
        score += precision_score
        reasons.append(f"accuracy={tool.accuracy:.2f}")

        # 2. Vitesse (20%)
        # Normaliser sur 60 secondes
        speed_score = max(0.0, 1.0 - (tool.avg_duration_ms / 60000.0)) * 0.2
        score += speed_score
        reasons.append(f"speed={speed_score:.2f}")

        # 3. Coût inverse (20%)
        # Normaliser sur 10 USD
        cost_score = max(0.0, 1.0 - (tool.cost_per_call / 10.0)) * 0.2
        score += cost_score
        reasons.append(f"cost={cost_score:.2f}")

        # 4. Fiabilité (20%)
        reliability_score = tool.success_rate * 0.2
        score += reliability_score
        reasons.append(f"reliability={tool.success_rate:.2f}")

        # 5. Disponibilité (10%)
        availability_score = 0.1 if tool.is_available else 0.0
        score += availability_score
        reasons.append(f"available={tool.is_available}")

        # Pénalités
        penalties = self._calculate_penalties(tool, context)
        score -= penalties
        if penalties > 0:
            reasons.append(f"penalties=-{penalties:.2f}")

        # Normaliser entre 0.0 et 1.0
        score = max(0.0, min(1.0, score))

        reasoning = f"score={score:.3f} ({', '.join(reasons)})"
        return score, reasoning

    def _calculate_penalties(self, tool: Tool, context: ToolContext) -> float:
        """Calcule les pénalités.

        Args:
            tool: Outil
            context: Contexte

        Returns:
            Pénalité totale
        """
        penalty = 0.0

        # Pénalité: Dépendance manquante
        # (MVP: pas de vérification)

        # Pénalité: Conflit détecté
        # (MVP: pas de vérification)

        # Pénalité: Risque élevé
        risk_penalties = {
            "low": 0.0,
            "medium": 0.05,
            "high": 0.15,
            "critical": 0.3,
        }
        penalty += risk_penalties.get(tool.risk_level.value, 0.0)

        # Pénalité: Coût > budget
        if context.max_cost is not None and tool.cost_per_call > context.max_cost:
            penalty += 0.4

        # Pénalité: Temps > deadline
        if context.max_duration_ms is not None and tool.avg_duration_ms > context.max_duration_ms:
            penalty += 0.3

        return penalty

    def explain_selection(self, scored_tools: list[ScoredTool]) -> str:
        """Explique la sélection.

        Args:
            scored_tools: Outils scorés

        Returns:
            Explication textuelle
        """
        if not scored_tools:
            return "No tools available"

        lines = ["Tool selection:"]
        for i, st in enumerate(scored_tools, 1):
            lines.append(f"  {i}. {st.tool.name} (score: {st.score:.3f})")
            lines.append(f"     {st.reasoning}")

        return "\n".join(lines)