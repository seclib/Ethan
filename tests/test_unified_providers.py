"""tests/test_unified_providers.py — Unified provider capability tests.

Validates the unified LLMProvider interface:
- Capability flags (supports_vision, supports_transcription, supports_embedding)
- vision_analyze() raises NotImplementedError for non-vision providers
- transcribe() raises NotImplementedError for non-transcription providers
- ProviderManager routes to the right provider based on capabilities
- Secrets are never exposed in provider descriptions
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
import pytest_asyncio

from core.llm.providers.base import LLMProvider
from core.llm.providers.openai import OpenAIProvider
from core.llm.providers.anthropic import AnthropicProvider
from core.llm.providers.ollama import OllamaProvider
from core.llm.store import ProviderStore
from core.llm.provider_manager import ProviderManager
from core.llm.types import (
    ChatMessage,
    ChatResponse,
    ModelInfo,
    TranscriptionRequest,
    VisionImage,
    VisionRequest,
)


# ── Helpers ────────────────────────────────────────────────────────────────


class StubVisionProvider(LLMProvider):
    """Minimal provider that supports only vision."""

    name = "stub-vision"
    default_model = "stub-v1"
    supports_vision = True
    supports_transcription = False
    supports_embedding = False

    async def chat(self, messages, model=None, temperature=0.7, max_tokens=None, stream=False):
        raise NotImplementedError

    async def chat_stream(self, messages, model=None, temperature=0.7, max_tokens=None):
        raise NotImplementedError

    async def embed(self, texts, model=None):
        raise NotImplementedError

    async def list_models(self):
        return [ModelInfo(id="stub-v1", provider=self.name, name="Stub V1", capabilities=["vision"])]

    async def vision_analyze(self, request):
        from core.llm.types import VisionResponse
        return VisionResponse(
            content="analyzed: " + request.prompt,
            model=request.model or self.default_model,
            provider=self.name,
        )


class StubTranscribeProvider(LLMProvider):
    """Minimal provider that supports only transcription."""

    name = "stub-transcribe"
    default_model = "stub-t1"
    supports_vision = False
    supports_transcription = True
    supports_embedding = False

    async def chat(self, messages, model=None, temperature=0.7, max_tokens=None, stream=False):
        raise NotImplementedError

    async def chat_stream(self, messages, model=None, temperature=0.7, max_tokens=None):
        raise NotImplementedError

    async def embed(self, texts, model=None):
        raise NotImplementedError

    async def list_models(self):
        return [ModelInfo(id="stub-t1", provider=self.name, name="Stub T1", capabilities=["transcription"])]

    async def transcribe(self, request):
        from core.llm.types import TranscriptionResponse
        return TranscriptionResponse(
            text="transcribed text",
            model=request.model or self.default_model,
            provider=self.name,
            language=request.language,
        )


class StubPlainProvider(LLMProvider):
    """Minimal provider that supports neither vision nor transcription."""

    name = "stub-plain"
    default_model = "stub-p1"
    supports_vision = False
    supports_transcription = False
    supports_embedding = True

    async def chat(self, messages, model=None, temperature=0.7, max_tokens=None, stream=False):
        return ChatResponse(content="hi", model=self.default_model, provider=self.name)

    async def chat_stream(self, messages, model=None, temperature=0.7, max_tokens=None):
        yield "hi"

    async def embed(self, texts, model=None):
        return [[0.1, 0.2, 0.3]]

    async def list_models(self):
        return [ModelInfo(id="stub-p1", provider=self.name, name="Stub P1", capabilities=["chat"])]


# ── Tests: Capability Flags ────────────────────────────────────────────────


class TestCapabilityFlags:
    """Providers declare their capabilities correctly."""

    def test_openai_flags(self):
        assert OpenAIProvider.supports_vision is True
        assert OpenAIProvider.supports_transcription is True
        assert OpenAIProvider.supports_embedding is True

    def test_anthropic_flags(self):
        assert AnthropicProvider.supports_vision is True
        assert AnthropicProvider.supports_transcription is False
        assert AnthropicProvider.supports_embedding is False

    def test_ollama_flags(self):
        assert OllamaProvider.supports_vision is True
        assert OllamaProvider.supports_transcription is False
        assert OllamaProvider.supports_embedding is True

    def test_base_defaults(self):
        """Base LLMProvider defaults: no vision/transcription, yes embedding."""
        assert LLMProvider.supports_vision is False
        assert LLMProvider.supports_transcription is False
        assert LLMProvider.supports_embedding is True


# ── Tests: NotImplementedError for unsupported capabilities ─────────────────


class TestNotImplemented:
    """Providers raise NotImplementedError for unsupported capabilities."""

    @pytest.mark.asyncio
    async def test_base_vision_raises(self):
        provider = StubPlainProvider()
        with pytest.raises(NotImplementedError, match="vision"):
            await provider.vision_analyze(VisionRequest(images=[]))

    @pytest.mark.asyncio
    async def test_base_transcribe_raises(self):
        provider = StubPlainProvider()
        with pytest.raises(NotImplementedError, match="transcription"):
            await provider.transcribe(TranscriptionRequest(audio_data=b""))

    @pytest.mark.asyncio
    async def test_anthropic_transcribe_raises(self):
        provider = AnthropicProvider(api_key="test-key")
        with pytest.raises(NotImplementedError, match="transcription"):
            await provider.transcribe(TranscriptionRequest(audio_data=b""))


# ── Tests: ProviderManager routing ─────────────────────────────────────────


class TestProviderManagerRouting:
    """ProviderManager routes vision/transcription to the right provider."""

    @pytest_asyncio.fixture()
    async def manager(self):
        """Create a ProviderManager with stub providers registered."""
        mgr = ProviderManager(store=ProviderStore())
        mgr._registry._providers["stub-vision"] = StubVisionProvider()
        mgr._providers_config["stub-vision"] = {"name": "stub-vision", "type": "custom", "enabled": True}
        mgr._registry._providers["stub-transcribe"] = StubTranscribeProvider()
        mgr._providers_config["stub-transcribe"] = {"name": "stub-transcribe", "type": "custom", "enabled": True}
        mgr._registry._providers["stub-plain"] = StubPlainProvider()
        mgr._providers_config["stub-plain"] = {"name": "stub-plain", "type": "custom", "enabled": True}
        return mgr

    @pytest.mark.asyncio
    async def test_vision_auto_routes_to_vision_provider(self, manager):
        request = VisionRequest(
            images=[VisionImage(data="b64fake", mime_type="image/png")],
            prompt="What is this?",
        )
        result = await manager.vision_analyze(request)
        assert result.provider == "stub-vision"
        assert "analyzed" in result.content

    @pytest.mark.asyncio
    async def test_transcribe_auto_routes_to_transcribe_provider(self, manager):
        request = TranscriptionRequest(audio_data=b"fake-audio", language="en")
        result = await manager.transcribe(request)
        assert result.provider == "stub-transcribe"
        assert result.text == "transcribed text"

    @pytest.mark.asyncio
    async def test_vision_specific_provider(self, manager):
        request = VisionRequest(images=[VisionImage(data="b64x")])
        result = await manager.vision_analyze(request, provider_name="stub-vision")
        assert result.provider == "stub-vision"

    @pytest.mark.asyncio
    async def test_vision_unsupported_provider_raises(self, manager):
        request = VisionRequest(images=[VisionImage(data="b64x")])
        with pytest.raises(ValueError, match="does not support vision"):
            await manager.vision_analyze(request, provider_name="stub-plain")

    @pytest.mark.asyncio
    async def test_no_vision_provider_raises(self):
        """When no provider supports vision, a clear error is raised."""
        mgr = ProviderManager(store=ProviderStore())
        mgr._registry._providers["plain"] = StubPlainProvider()
        mgr._providers_config["plain"] = {"name": "plain", "type": "custom", "enabled": True}
        with pytest.raises(ValueError, match="No provider with vision"):
            await mgr.vision_analyze(VisionRequest(images=[VisionImage(data="x")]))

    @pytest.mark.asyncio
    async def test_unknown_provider_raises(self):
        mgr = ProviderManager(store=ProviderStore())
        with pytest.raises(ValueError, match="not found"):
            await mgr.vision_analyze(VisionRequest(images=[]), provider_name="nonexistent")


# ── Tests: Canonical Capabilities ───────────────────────────────────────


class TestCanonicalCapabilities:
    """Le modèle unifié expose des capacités normalisées et sérialisables.

    Cinq capacités : llm, vision, embedding, speech_to_text, transcription.
    """

    def test_enum_values(self):
        from core.llm.types import ProviderCapability

        assert ProviderCapability.LLM.value == "llm"
        assert ProviderCapability.VISION.value == "vision"
        assert ProviderCapability.EMBEDDING.value == "embedding"
        assert ProviderCapability.SPEECH_TO_TEXT.value == "speech_to_text"
        assert ProviderCapability.TRANSCRIPTION.value == "transcription"

    def test_from_flags_bare(self):
        from core.llm.types import ProviderCapability

        caps = ProviderCapability.from_flags()
        assert caps == ["llm", "embedding"]

    def test_from_flags_all(self):
        from core.llm.types import ProviderCapability

        caps = ProviderCapability.from_flags(
            supports_vision=True,
            supports_embedding=True,
            supports_transcription=True,
        )
        assert caps == ["llm", "vision", "embedding", "speech_to_text", "transcription"]

    def test_from_flags_stt_alias_primes(self):
        from core.llm.types import ProviderCapability

        caps = ProviderCapability.from_flags(
            supports_transcription=True, supports_speech_to_text=False
        )
        # L'alias explicite prime sur le flag transcription.
        assert "speech_to_text" not in caps
        assert caps == ["llm", "embedding"]

    def test_base_provider_capabilities(self):
        assert StubPlainProvider().capabilities() == ["llm", "embedding"]

    def test_openai_capabilities(self):
        caps = OpenAIProvider(api_key="x").capabilities()
        assert caps == ["llm", "vision", "embedding", "speech_to_text", "transcription"]

    def test_anthropic_capabilities(self):
        caps = AnthropicProvider(api_key="x").capabilities()
        assert caps == ["llm", "vision"]

    def test_ollama_capabilities(self):
        caps = OllamaProvider().capabilities()
        assert caps == ["llm", "vision", "embedding"]


# ── Tests: describe_provider canonical capabilities + has_api_key ─────────


class TestDescribeProviderCapabilities:
    """describe_provider() expose capabilities + has_api_key, jamais la clé."""

    @pytest.mark.asyncio
    async def test_describe_contains_canonical_capabilities(self):
        mgr = ProviderManager(store=ProviderStore())
        mgr._registry._providers["stub-vision"] = StubVisionProvider()
        mgr._providers_config["stub-vision"] = {
            "name": "stub-vision", "type": "custom", "enabled": False,
        }
        desc = await mgr.describe_provider("stub-vision")
        assert desc["capabilities"] == ["llm", "vision"]

    @pytest.mark.asyncio
    async def test_describe_has_api_key_flag_not_value(self):
        mgr = ProviderManager(store=ProviderStore())
        mgr._registry._providers["stub-plain"] = StubPlainProvider()
        mgr._providers_config["stub-plain"] = {
            "name": "stub-plain", "type": "custom", "enabled": False,
            "api_key": "sk-super-secret",
        }
        desc = await mgr.describe_provider("stub-plain")
        # Booléen oui, valeur jamais.
        assert desc["has_api_key"] is True
        assert "api_key" not in desc
        assert "sk-super-secret" not in str(desc)

    @pytest.mark.asyncio
    async def test_describe_without_key_reports_false(self):
        mgr = ProviderManager(store=ProviderStore())
        mgr._registry._providers["stub-plain"] = StubPlainProvider()
        mgr._providers_config["stub-plain"] = {
            "name": "stub-plain", "type": "custom", "enabled": False,
        }
        desc = await mgr.describe_provider("stub-plain")
        assert desc["has_api_key"] is False

    @pytest.mark.asyncio
    async def test_get_provider_capabilities_central(self):
        mgr = ProviderManager(store=ProviderStore())
        mgr._registry._providers["stub-transcribe"] = StubTranscribeProvider()
        caps = mgr.get_provider_capabilities("stub-transcribe")
        assert caps["supports_speech_to_text"] is True
        assert caps["supports_transcription"] is True
        assert "speech_to_text" in caps["capabilities"]
        assert "transcription" in caps["capabilities"]

    def test_get_provider_capabilities_missing_raises(self):
        mgr = ProviderManager(store=ProviderStore())
        with pytest.raises(ValueError, match="not found"):
            mgr.get_provider_capabilities("nonexistent")


# ── Tests: Secret Safety ───────────────────────────────────────────────────


class TestSecretSafety:
    """API responses must never expose secrets in plaintext."""

    def test_describe_provider_no_api_key(self):
        """ProviderResponse schema excludes api_key."""
        from interfaces.api.models.provider_schemas import ProviderResponse
        resp = ProviderResponse(
            id="test-openai",
            name="test-openai",
            type="openai",
            enabled=True,
            status="unknown",
            default_model="gpt-4",
        )
        serialized = resp.model_dump()
        assert "api_key" not in serialized
        assert "sk-super-secret" not in str(serialized)

    @pytest.mark.asyncio
    async def test_list_models_no_secret_leak(self):
        """list_models endpoint must not expose api_key."""
        mgr = ProviderManager(store=ProviderStore())
        models = await mgr.list_models(provider_id=None)
        assert isinstance(models, list)

    # ── TTS / Images : les configs ne doivent jamais exposer la clé ──

    @pytest.mark.asyncio
    async def test_tts_get_config_never_exposes_api_key(self):
        """get_config() remplace la clé par un booléen has_api_key."""
        from core.llm.tts import TTSEngine

        engine = TTSEngine()
        await engine.configure("openai", voice="alloy", api_key="sk-tts-secret")
        cfg = await engine.get_config()
        assert cfg["has_api_key"] is True
        assert "api_key" not in cfg
        assert "sk-tts-secret" not in str(cfg)

    @pytest.mark.asyncio
    async def test_tts_key_not_persisted_in_store(self):
        """La clé n'est jamais persistée dans le record store — mémoire seule."""
        from core.llm.tts import TTSEngine
        from core.state.record_store import CoreRecordStore

        store = CoreRecordStore()
        engine = TTSEngine(store=store)
        await engine.configure("openai", voice="alloy", api_key="sk-tts-secret")
        raw = await store.get("tts-config", "default")
        assert "api_key" not in raw
        assert "sk-tts-secret" not in str(raw)

    @pytest.mark.asyncio
    async def test_images_get_config_never_exposes_api_key(self):
        """get_config() de l'ImageGenerator ne doit pas exposer la clé."""
        from core.llm.images import ImageGenerator

        gen = ImageGenerator()
        await gen.configure("openai", model="dall-e-3", api_key="sk-img-secret")
        cfg = await gen.get_config()
        assert cfg["has_api_key"] is True
        assert "api_key" not in cfg
        assert "sk-img-secret" not in str(cfg)


# ── Tests: New Types ───────────────────────────────────────────────────────


class TestNewTypes:
    """Vision and transcription types are well-formed."""

    def test_vision_image_defaults(self):
        img = VisionImage(data="abc123")
        assert img.mime_type == "image/png"
        assert img.is_url is False

    def test_vision_image_url(self):
        img = VisionImage(data="https://example.com/img.png", is_url=True)
        assert img.is_url is True

    def test_vision_request_defaults(self):
        req = VisionRequest(images=[VisionImage(data="x")])
        assert req.prompt == "Describe this image in detail."
        assert req.model is None

    def test_transcription_request_defaults(self):
        req = TranscriptionRequest(audio_data=b"data")
        assert req.mime_type == "audio/wav"
        assert req.language is None
        assert req.model is None

    def test_transcription_request_with_language(self):
        req = TranscriptionRequest(audio_data=b"data", language="fr", model="whisper-1")
        assert req.language == "fr"
        assert req.model == "whisper-1"


# ── Azure capabilities (GPT-4V / Whisper via SDK openai) ──────────────────


class TestAzureCapabilities:
    def test_azure_flags(self):
        from core.llm.providers.azure import AzureOpenAIProvider

        assert AzureOpenAIProvider.supports_vision is True
        assert AzureOpenAIProvider.supports_transcription is True

    @pytest.mark.asyncio
    async def test_azure_vision_requires_client(self):
        from core.llm.providers.azure import AzureOpenAIProvider

        provider = AzureOpenAIProvider(api_key="test")
        with pytest.raises(RuntimeError, match="not initialized"):
            await provider.vision_analyze(
                VisionRequest(images=[VisionImage(data="x")])
            )

    @pytest.mark.asyncio
    async def test_azure_transcribe_requires_client(self):
        from core.llm.providers.azure import AzureOpenAIProvider

        provider = AzureOpenAIProvider(api_key="test")
        with pytest.raises(RuntimeError, match="not initialized"):
            await provider.transcribe(TranscriptionRequest(audio_data=b"x"))
