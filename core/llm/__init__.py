# Jarvis OS — LLM Provider Interface (unified)
#
# This module is a backward-compatibility re-export layer.
# The authoritative definitions live in:
#   - core/llm/providers/base.py  → LLMProvider (ABC)
#   - core/llm/registry.py        → LLMProviderRegistry
#   - core/llm/provider_manager.py → ProviderManager
#
# Do NOT add new definitions here — extend the authoritative modules.

from __future__ import annotations

# ── Re-exports from authoritative modules ─────────────────────────────────

from core.llm.providers.base import LLMProvider
from core.llm.types import (
    ChatMessage,
    ChatResponse,
    ModelInfo,
    TranscriptionRequest,
    TranscriptionResponse,
    VisionRequest,
    VisionResponse,
)

# ── Provider Manager (système centralisé — authoritative) ────────────────

try:
    from core.llm.provider_manager import ProviderManager
    from core.llm.provider_factory import create_provider_from_config, create_default_providers
    from core.llm.store import ProviderStore
    from core.llm.registry import LLMProviderRegistry

    __all__ = [
        # Types
        "ChatMessage",
        "ChatResponse",
        "ModelInfo",
        "VisionRequest",
        "VisionResponse",
        "TranscriptionRequest",
        "TranscriptionResponse",
        # Core interfaces
        "LLMProvider",
        "LLMProviderRegistry",
        # Manager & factory
        "ProviderManager",
        "create_provider_from_config",
        "create_default_providers",
        "ProviderStore",
    ]
except ImportError:  # pragma: no cover - partial environment
    __all__ = [
        "ChatMessage",
        "ChatResponse",
        "ModelInfo",
        "VisionRequest",
        "VisionResponse",
        "TranscriptionRequest",
        "TranscriptionResponse",
        "LLMProvider",
    ]


# ── Legacy compatibility aliases (deprecated) ─────────────────────────────
# These will be removed in a future release. Use ProviderManager directly.

from core.llm.registry import LLMProviderRegistry as _LLMProviderRegistry

ProviderRegistry = _LLMProviderRegistry  # type: ignore[assignment]
