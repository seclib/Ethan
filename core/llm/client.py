"""LLM Client — Interface unifiée pour tous les providers.

Intègre un circuit breaker par provider pour la résilience:
- 5 échecs consécutifs → OPEN (fail fast pendant 60s)
- Après 60s → HALF_OPEN (test avec un appel)
- Succès → CLOSED (opération normale)
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from core.llm.registry import LLMProviderRegistry
from core.llm.selector import LLMSelector
from core.llm.types import ChatMessage, ChatResponse, LLMRequirements, ModelInfo
from core.safety.circuit_breaker import CircuitBreaker, CircuitState

logger = logging.getLogger(__name__)


class LLMClient:
    """Client LLM unifié avec circuit breaker par provider."""

    def __init__(self, registry: LLMProviderRegistry, selector: LLMSelector):
        self.registry = registry
        self.selector = selector
        self._cost_tracker = None
        self._breakers: dict[str, CircuitBreaker] = {}

    def _get_breaker(self, provider_name: str) -> CircuitBreaker:
        """Get or create a circuit breaker for a provider."""
        if provider_name not in self._breakers:
            self._breakers[provider_name] = CircuitBreaker(
                name=f"llm-{provider_name}",
                fail_threshold=5,
                timeout=60.0,
            )
        return self._breakers[provider_name]

    async def initialize(self) -> None:
        """Initialise le client."""
        from core.llm.tracker import CostTracker
        self._cost_tracker = CostTracker()
        logger.info("LLM Client initialized with circuit breakers")

    async def chat(
        self,
        messages: list[ChatMessage],
        requirements: LLMRequirements | None = None,
    ) -> ChatResponse:
        """Chat completion avec sélection automatique et circuit breaker."""
        model, provider = self._select_model(requirements)
        provider_name = model.provider if model else "default"
        breaker = self._get_breaker(provider_name)

        if breaker.state == CircuitState.OPEN:
            logger.warning("Circuit breaker OPEN for provider %s, trying fallback", provider_name)
            alt_model, alt_provider = self._select_fallback_provider(provider_name, requirements)
            if alt_provider:
                provider_name = alt_model.provider if alt_model else "default"
                breaker = self._get_breaker(provider_name)
                model, provider = alt_model, alt_provider
            else:
                raise RuntimeError(f"All LLM providers unavailable (circuit breaker OPEN for {provider_name})")

        response = await breaker.call(
            provider.chat,
            messages=messages,
            model=model.id if model else None,
        )

        if response is None:
            raise RuntimeError(f"LLM provider {provider_name} failed (circuit breaker)")

        if self._cost_tracker and response.usage:
            self._cost_tracker.track(model.provider, model.id, response.usage)

        return response

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        requirements: LLMRequirements | None = None,
    ) -> AsyncIterator[str]:
        """Chat completion avec streaming."""
        model, provider = self._select_model(requirements)
        async for chunk in provider.chat_stream(
            messages=messages,
            model=model.id if model else None,
        ):
            yield chunk

    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
        provider_name: str | None = None,
    ) -> list[list[float]]:
        """Génère des embeddings."""
        if provider_name:
            provider = self.registry.get_provider(provider_name)
        else:
            providers = self.registry.list_providers()
            if not providers:
                raise ValueError("No LLM providers registered")
            provider = self.registry.get_provider(providers[0])
        return await provider.embed(texts, model=model)

    def _select_fallback_provider(
        self, excluded: str, requirements: LLMRequirements | None
    ) -> tuple[ModelInfo | None, Any]:
        """Select an alternative provider when the primary is unavailable."""
        all_providers = self.registry.list_providers()
        for name in all_providers:
            if name == excluded:
                continue
            breaker = self._get_breaker(name)
            if breaker.state == CircuitState.OPEN:
                continue
            try:
                provider = self.registry.get_provider(name)
                default_model_id = provider.default_model
                model = self.registry.get_model(default_model_id)
                return model, provider
            except Exception:
                continue
        return None, None

    def _select_model(self, requirements: LLMRequirements | None) -> tuple[ModelInfo | None, Any]:
        """Sélectionne un modèle."""
        if not requirements:
            provider_name = self.registry.list_providers()[0]
            provider = self.registry.get_provider(provider_name)
            default_model_id = provider.default_model
            model = self.registry.get_model(default_model_id)
            return model, provider

        all_models = self.registry.list_models()
        scored = self.selector.select(requirements, all_models)

        if not scored:
            logger.warning("No model matched requirements, using default")
            provider_name = self.registry.list_providers()[0]
            provider = self.registry.get_provider(provider_name)
            default_model_id = provider.default_model
            model = self.registry.get_model(default_model_id)
            return model, provider

        best = scored[0]
        logger.info(f"Selected model: {best.model.name} (score: {best.score:.3f})")
        logger.info(f"Reasoning: {best.reasoning}")

        provider = self.registry.get_provider(best.model.provider)
        return best.model, provider
