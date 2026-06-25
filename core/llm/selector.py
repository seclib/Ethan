"""LLM Selector — Sélectionne le meilleur modèle LLM.

Score composite sur 6 critères :
- Qualité (25%)
- Coût (20%)
- Vitesse (20%)
- Confidentialité (15%)
- Contexte (10%)
- Disponibilité (10%)
"""

from __future__ import annotations

import logging
from typing import Any

from core.llm.types import LLMRequirements, ModelInfo, ScoredModel

logger = logging.getLogger(__name__)


class LLMSelector:
    """Sélectionne le meilleur modèle LLM."""

    def select(self, requirements: LLMRequirements, available_models: list[ModelInfo]) -> list[ScoredModel]:
        """Sélectionne le meilleur modèle.

        Args:
            requirements: Besoins
            available_models: Modèles disponibles

        Returns:
            Top 3 modèles scorés
        """
        # Filtrer par requirements
        candidates = self._filter_by_requirements(available_models, requirements)

        if not candidates:
            return []

        # Scorer chaque candidat
        scored = []
        for model in candidates:
            score, reasoning = self._calculate_score(model, requirements)
            scored.append(ScoredModel(model=model, score=score, reasoning=reasoning))

        # Trier par score décroissant
        scored.sort(key=lambda x: x.score, reverse=True)

        # Retourner le top 3
        return scored[:3]

    def _filter_by_requirements(self, models: list[ModelInfo], req: LLMRequirements) -> list[ModelInfo]:
        """Filtre les modèles selon les requirements.

        Args:
            models: Modèles disponibles
            req: Requirements

        Returns:
            Modèles filtrés
        """
        filtered = []

        for model in models:
            # Exclure les providers exclus
            if model.provider in req.excluded_providers:
                continue

            # Préférer les providers préférés
            if req.preferred_providers and model.provider not in req.preferred_providers:
                continue

            # Modèle local requis
            if req.require_local and not model.is_local:
                continue

            # Confidentialité requise
            if req.require_private and not model.is_private:
                continue

            # Contexte suffisant
            if req.context_length and model.context_length < req.context_length:
                continue

            # Qualité minimale
            if req.min_quality and model.quality_score < req.min_quality:
                continue

            filtered.append(model)

        return filtered

    def _calculate_score(self, model: ModelInfo, req: LLMRequirements) -> tuple[float, str]:
        """Calcule le score composite.

        Returns:
            (score, reasoning)
        """
        score = 0.0
        reasons = []

        # 1. Qualité (25%)
        quality_score = model.quality_score * 0.25
        score += quality_score
        reasons.append(f"quality={model.quality_score:.2f}")

        # 2. Coût (20%) - inverse
        cost_score = self._get_cost_score(model, req) * 0.2
        score += cost_score
        reasons.append(f"cost={cost_score:.2f}")

        # 3. Vitesse (20%)
        speed_score = self._get_speed_score(model) * 0.2
        score += speed_score
        reasons.append(f"speed={speed_score:.2f}")

        # 4. Confidentialité (15%)
        privacy_score = self._get_privacy_score(model) * 0.15
        score += privacy_score
        reasons.append(f"privacy={privacy_score:.2f}")

        # 5. Contexte (10%)
        context_score = self._get_context_score(model, req) * 0.1
        score += context_score
        reasons.append(f"context={context_score:.2f}")

        # 6. Disponibilité (10%)
        availability_score = 0.1 if model.is_available else 0.0
        score += availability_score
        reasons.append(f"available={model.is_available}")

        # Pénalités
        penalties = self._calculate_penalties(model, req)
        score -= penalties
        if penalties > 0:
            reasons.append(f"penalties=-{penalties:.2f}")

        # Normaliser entre 0.0 et 1.0
        score = max(0.0, min(1.0, score))

        reasoning = f"score={score:.3f} ({', '.join(reasons)})"
        return score, reasoning

    def _get_cost_score(self, model: ModelInfo, req: LLMRequirements) -> float:
        """Calcule le score de coût (inverse).

        Args:
            model: Modèle
            req: Requirements

        Returns:
            Score (0.0 à 1.0)
        """
        # Modèle local = gratuit
        if model.is_local:
            return 1.0

        # Sans pricing = inconnu
        if not model.pricing:
            return 0.5

        # Coût pour 1K tokens (moyenne input/output)
        input_cost = model.pricing.get("input", 0.0)
        output_cost = model.pricing.get("output", 0.0)
        avg_cost = (input_cost + output_cost) / 2

        # Normaliser sur 10 USD
        cost_score = max(0.0, 1.0 - (avg_cost / 10.0))
        return cost_score

    def _get_speed_score(self, model: ModelInfo) -> float:
        """Calcule le score de vitesse.

        Args:
            model: Modèle

        Returns:
            Score (0.0 à 1.0)
        """
        # Normaliser sur 10 secondes
        speed_score = max(0.0, 1.0 - (model.avg_latency_ms / 10000.0))
        return speed_score

    def _get_privacy_score(self, model: ModelInfo) -> float:
        """Calcule le score de confidentialité.

        Args:
            model: Modèle

        Returns:
            Score (0.0 à 1.0)
        """
        if model.is_private:
            return 1.0
        elif model.is_local:
            return 0.9
        else:
            # Cloud = moins privé
            return 0.3

    def _get_context_score(self, model: ModelInfo, req: LLMRequirements) -> float:
        """Calcule le score de contexte.

        Args:
            model: Modèle
            req: Requirements

        Returns:
            Score (0.0 à 1.0)
        """
        if not req.context_length:
            return 1.0

        # Ratio contexte disponible / contexte requis
        if model.context_length >= req.context_length:
            return 1.0
        else:
            # Pénalité si contexte insuffisant
            return model.context_length / req.context_length

    def _calculate_penalties(self, model: ModelInfo, req: LLMRequirements) -> float:
        """Calcule les pénalités.

        Args:
            model: Modèle
            req: Requirements

        Returns:
            Pénalité totale
        """
        penalty = 0.0

        # Pénalité: coût > budget
        if req.max_cost is not None and not model.is_local:
            if model.pricing:
                avg_cost = (model.pricing.get("input", 0.0) + model.pricing.get("output", 0.0)) / 2
                if avg_cost > req.max_cost:
                    penalty += 0.4

        # Pénalité: latence > max
        if req.max_latency_ms and model.avg_latency_ms > req.max_latency_ms:
            penalty += 0.3

        return penalty

    def explain_selection(self, scored_models: list[ScoredModel]) -> str:
        """Explique la sélection.

        Args:
            scored_models: Modèles scorés

        Returns:
            Explication textuelle
        """
        if not scored_models:
            return "No models available"

        lines = ["Model selection:"]
        for i, sm in enumerate(scored_models, 1):
            lines.append(f"  {i}. {sm.model.name} ({sm.model.provider})")
            lines.append(f"     Score: {sm.score:.3f} — {sm.reasoning}")

        return "\n".join(lines)