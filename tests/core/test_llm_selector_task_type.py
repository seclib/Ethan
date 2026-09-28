"""Non-régression : sélection de modèle par ``task_type``.

Bug observé en production : ``qwen3-embedding:8b`` (encodeur) était sélectionné
pour une complétion de chat — les providers locaux déclaraient
``capabilities=["chat", "embedding"]`` pour TOUS leurs modèles et
``LLMRequirements.task_type`` était ignoré par ``LLMSelector``. Ollama renvoyait
alors une erreur, le circuit breaker s'ouvrait et l'API répondait 502.
"""

from __future__ import annotations

import asyncio

import pytest
from core.llm.providers.ollama import OllamaProvider
from core.llm.selector import LLMSelector
from core.llm.types import (
    LLMRequirements,
    ModelInfo,
    is_embedding_model,
    model_supports_task,
)

CHAT_TASKS = ["chat", "code", "reasoning", "summarize", "summarization", "translation"]


def _model(model_id: str, capabilities: list[str] | None = None) -> ModelInfo:
    return ModelInfo(
        id=model_id,
        provider="ollama",
        name=model_id,
        is_local=True,
        is_private=True,
        capabilities=capabilities if capabilities is not None else ["chat", "embedding"],
        quality_score=0.80,
        avg_latency_ms=100.0,
    )


# ── Détection des encodeurs d'embedding ────────────────────────────────────

ENCODERS = [
    "qwen3-embedding:8b",
    "nomic-embed-text:latest",
    "mxbai-embed-large",
    "bge-m3",
    "all-minilm:l6-v2",
    "intfloat/e5-mistral-7b-instruct",
    "snowflake-arctic-embed:latest",
    "embeddinggemma:300m",
    "text-embedding-3-small",
    "hf.co/mixedbread-ai/mxbai-embed-large-v1-GGUF:Q4_K_M",
]

CHAT_MODELS = [
    "llama3.1:latest",
    "qwen2.5:7b",
    "mistral:7b",
    "deepseek-coder:6.7b",
    "codegemma:7b",
    "llava:13b",
    "gemma2:9b",
    "phi3.5:latest",
    "gpt-4o",
    "claude-3-opus",
]


@pytest.mark.parametrize("model_id", ENCODERS)
def test_embedding_models_are_detected(model_id: str):
    assert is_embedding_model(model_id) is True


@pytest.mark.parametrize("model_id", CHAT_MODELS)
def test_chat_models_are_not_flagged_as_embedding(model_id: str):
    assert is_embedding_model(model_id) is False


def test_is_embedding_model_handles_empty_id():
    assert is_embedding_model("") is False


# ── Filtre par tâche ───────────────────────────────────────────────────────


@pytest.mark.parametrize("task", CHAT_TASKS)
def test_encoder_is_rejected_for_chat_tasks(task: str):
    assert model_supports_task(_model("qwen3-embedding:8b", ["embedding"]), task) is False


def test_encoder_is_eligible_for_embedding_task():
    assert model_supports_task(_model("qwen3-embedding:8b", ["embedding"]), "embedding") is True


def test_chat_model_is_rejected_for_embedding_only_task():
    """Un modèle purement génératif n'est pas un encodeur."""
    assert model_supports_task(_model("llama3.1:latest", ["chat"]), "embedding") is False


def test_undeclared_capabilities_keep_legacy_behaviour():
    """``capabilities=[]`` → modèle réputé compatible (aucune régression)."""
    assert model_supports_task(_model("legacy-model", []), "chat") is True


def test_undeclared_capabilities_with_encoder_name_is_rejected():
    """Sans métadonnée, le nom du modèle reste discriminant."""
    assert model_supports_task(_model("bge-m3", []), "chat") is False


def test_none_task_type_defaults_to_chat():
    assert model_supports_task(_model("qwen3-embedding:8b", ["embedding"]), None) is False


# ── Sélection effective ────────────────────────────────────────────────────


def test_selector_never_returns_an_encoder_for_chat():
    models = [_model("llama3.1:latest"), _model("qwen3-embedding:8b", ["embedding"])]

    scored = LLMSelector().select(LLMRequirements(task_type="chat"), models)

    assert scored, "a chat model must remain selectable"
    assert scored[0].model.id == "llama3.1:latest"
    assert all(s.model.id != "qwen3-embedding:8b" for s in scored)


def test_selector_keeps_encoder_for_embedding_task():
    models = [_model("llama3.1:latest", ["chat"]), _model("qwen3-embedding:8b", ["embedding"])]

    scored = LLMSelector().select(LLMRequirements(task_type="embedding"), models)

    assert [s.model.id for s in scored] == ["qwen3-embedding:8b"]


def test_selector_returns_empty_when_only_encoders_available():
    """Aucun modèle génératif : la sélection ne doit pas mentir."""
    models = [_model("nomic-embed-text:latest", ["embedding"])]

    scored = LLMSelector().select(LLMRequirements(task_type="chat"), models)

    assert scored == []


# ── Capacités déclarées par le provider Ollama ─────────────────────────────


class _FakeTagsResponse:
    """Réponse simulée de ``GET /api/tags`` (aucun réseau)."""

    def __init__(self, names: list[str]) -> None:
        self._names = names

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"models": [{"name": name} for name in self._names]}


class _FakeOllamaClient:
    def __init__(self, names: list[str]) -> None:
        self._names = names

    async def get(self, url: str) -> _FakeTagsResponse:
        return _FakeTagsResponse(self._names)


def _ollama_with_models(names: list[str]) -> OllamaProvider:
    provider = OllamaProvider(base_url="http://ollama.test")
    provider._client = _FakeOllamaClient(names)
    return provider


def test_ollama_list_models_marks_encoders_as_embedding_only():
    """Un encodeur ne doit pas être déclaré « chat » par Ollama."""
    provider = _ollama_with_models(
        ["llama3.1:latest", "qwen3-embedding:8b", "nomic-embed-text:latest", "qwen2.5:7b"]
    )

    models = asyncio.run(provider.list_models())
    caps = {m.id: m.capabilities for m in models}

    assert caps["llama3.1:latest"] == ["chat", "embedding"]
    assert caps["qwen2.5:7b"] == ["chat", "embedding"]
    assert caps["qwen3-embedding:8b"] == ["embedding"]
    assert caps["nomic-embed-text:latest"] == ["embedding"]


def test_ollama_encoders_are_not_selectable_for_chat():
    """Bout en bout : listing Ollama → sélection chat."""
    provider = _ollama_with_models(["qwen3-embedding:8b", "llama3.1:latest"])

    models = asyncio.run(provider.list_models())
    scored = LLMSelector().select(LLMRequirements(task_type="chat"), models)

    assert [s.model.id for s in scored] == ["llama3.1:latest"]
