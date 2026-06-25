"""Cost Tracker — Suit les coûts d'utilisation des LLM."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


class CostTracker:
    """Suit les coûts d'utilisation des LLM."""

    def __init__(self):
        self._usage: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "calls": 0,
            "tokens": 0,
            "cost": 0.0,
        })
        self._budgets: dict[str, float] = {}

    def track(self, provider: str, model: str, usage: dict[str, Any]) -> None:
        """Enregistre une utilisation.

        Args:
            provider: Nom du provider
            model: ID du modèle
            usage: Statistiques d'usage
        """
        key = f"{provider}:{model}"

        self._usage[key]["calls"] += 1
        self._usage[key]["tokens"] += usage.get("total_tokens", 0)

        # Calculer le coût
        cost = self._calculate_cost(provider, model, usage)
        self._usage[key]["cost"] += cost

        # Vérifier le budget
        self._check_budget(key)

        logger.debug(f"Cost tracked: {key} — ${cost:.4f} (total: ${self._usage[key]['cost']:.4f})")

    def _calculate_cost(self, provider: str, model: str, usage: dict[str, Any]) -> float:
        """Calcule le coût.

        Args:
            provider: Provider
            model: Modèle
            usage: Usage

        Returns:
            Coût en USD
        """
        # Pricing par provider/model (MVP: en dur)
        pricing = {
            "openai:gpt-4": {"input": 0.03, "output": 0.06},
            "openai:gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "anthropic:claude-3-opus": {"input": 0.015, "output": 0.075},
            "anthropic:claude-3-sonnet": {"input": 0.003, "output": 0.015},
        }

        key = f"{provider}:{model}"
        if key not in pricing:
            return 0.0

        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        cost = (input_tokens * pricing[key]["input"] + 
                output_tokens * pricing[key]["output"]) / 1000

        return cost

    def _check_budget(self, key: str) -> None:
        """Vérifie le budget.

        Args:
            key: Clé (provider:model)
        """
        budget = self._budgets.get(key)
        if budget is None:
            return

        current_cost = self._usage[key]["cost"]
        if current_cost > budget:
            logger.warning(f"Budget exceeded for {key}: ${current_cost:.2f} > ${budget:.2f}")

    def set_budget(self, key: str, budget: float) -> None:
        """Définit un budget.

        Args:
            key: Clé (provider:model)
            budget: Budget en USD
        """
        self._budgets[key] = budget

    def get_usage(self, key: str | None = None) -> dict[str, Any]:
        """Récupère l'utilisation.

        Args:
            key: Clé (optionnel)

        Returns:
            Statistiques d'utilisation
        """
        if key:
            return dict(self._usage.get(key, {}))
        return {k: dict(v) for k, v in self._usage.items()}

    def get_total_cost(self) -> float:
        """Coût total.

        Returns:
            Coût total en USD
        """
        return sum(v["cost"] for v in self._usage.values())