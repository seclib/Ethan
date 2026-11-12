"""LLM Types — Types de données pour le moteur LLM multi-provider."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class TaskType(str, Enum):
    """Types de tâches LLM."""

    CHAT = "chat"
    CODE = "code"
    EMBEDDING = "embedding"
    REASONING = "reasoning"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"


class ProviderCapability(str, Enum):
    """Capacités normalisées d'un provider unifié.

    ETHAN distingue cinq capacités sur le modèle unifié ``LLMProvider`` :

    - ``LLM``              : chat + streaming (tous les providers)
    - ``VISION``           : analyse d'images (``vision_analyze``)
    - ``EMBEDDING``        : vecteurs sémantiques (``embed``)
    - ``SPEECH_TO_TEXT``   : audio → texte (``transcribe``)
    - ``TRANSCRIPTION``    : transcription de parole (alias STT, même méthode)

    Les flags ``supports_*`` du provider racontent la même histoire en
    booléens ; la liste canonique ci-dessous est la forme sérialisable
    exposée à l'API et à la WebUI.
    """

    LLM = "llm"
    VISION = "vision"
    EMBEDDING = "embedding"
    SPEECH_TO_TEXT = "speech_to_text"
    TRANSCRIPTION = "transcription"

    @classmethod
    def from_flags(
        cls,
        *,
        supports_vision: bool = False,
        supports_embedding: bool = True,
        supports_transcription: bool = False,
        supports_speech_to_text: bool | None = None,
    ) -> list[str]:
        """Construit la liste canonique des capacités depuis les flags.

        Args:
            supports_vision: Provider capable de vision.
            supports_embedding: Provider capable d'embedding (majorité).
            supports_transcription: Provider capable de STT/transcription.
            supports_speech_to_text: Alias explicite STT — si fourni, prime
                sur ``supports_transcription`` pour ``speech_to_text``.

        Returns:
            Liste ordonnée et canonique : llm, vision, embedding,
            speech_to_text | transcription selon les flags.
        """
        caps: list[str] = [cls.LLM.value]  # le chat est toujours supporté
        if supports_vision:
            caps.append(cls.VISION.value)
        if supports_embedding:
            caps.append(cls.EMBEDDING.value)
        stt = (
            supports_speech_to_text
            if supports_speech_to_text is not None
            else supports_transcription
        )
        if stt:
            caps.append(cls.SPEECH_TO_TEXT.value)
            caps.append(cls.TRANSCRIPTION.value)
        return caps


@dataclass
class LLMRequirements:
    """Besoins pour la sélection d'un modèle."""

    task_type: str = "chat"
    max_cost: float | None = None
    max_latency_ms: float | None = None
    min_quality: float | None = None
    require_local: bool = False
    require_private: bool = False
    context_length: int | None = None
    preferred_providers: list[str] = field(default_factory=list)
    excluded_providers: list[str] = field(default_factory=list)


@dataclass
class ModelInfo:
    """Informations sur un modèle LLM."""

    id: str
    provider: str
    name: str
    model: str = ""
    context_length: int = 4096
    pricing: dict | None = None
    quality_score: float = 0.8
    avg_latency_ms: float = 1000.0
    is_local: bool = False
    is_private: bool = False
    capabilities: list[str] = field(default_factory=list)
    is_available: bool = True
    metadata: dict = field(default_factory=dict)


@dataclass
class ScoredModel:
    """Modèle avec son score."""

    model: ModelInfo
    score: float
    reasoning: str = ""


# ── Capacités de tâche d'un modèle ─────────────────────────────────────────
#
# ``ModelInfo.capabilities`` utilise le vocabulaire « chat », « code »,
# « reasoning », « vision », « embedding » — celui qu'écrivent les providers.
# Les helpers ci-dessous traduisent un ``task_type`` de ``LLMRequirements`` en
# capacité requise, afin qu'un modèle d'embedding ne soit jamais sélectionné
# pour une complétion de chat (Ollama renvoie alors une erreur, le circuit
# breaker s'ouvre et l'API répond 502).

# Marqueurs de nom identifiant une famille de modèles d'embedding dédiés.
# Les runtimes locaux (Ollama, llama.cpp, LM Studio, vLLM) n'exposent aucune
# métadonnée de tâche dans leur endpoint de listing : la convention de nommage
# est la seule information disponible.
#
# ``_EMBEDDING_TOKENS`` : le token doit être EXACTEMENT le marqueur
# (``bge-m3`` → « bge »). ``_EMBEDDING_PREFIXES`` : le token doit COMMENCER par
# le marqueur — « embed » couvre ``qwen3-embedding``, ``embeddinggemma``,
# ``text-embedding-3-small``…
_EMBEDDING_TOKENS: frozenset[str] = frozenset({"bge", "gte", "e5", "nomic", "mxbai", "minilm"})
_EMBEDDING_PREFIXES: tuple[str, ...] = ("embed",)

# Séparateurs de tokens d'un identifiant de modèle ou d'un chemin HF.
_MODEL_TOKEN_SPLIT_RE = re.compile(r"[-_/.\s]+")

# Tâches qui exigent un modèle génératif (chat) et non un encodeur.
_CHAT_TASKS: frozenset[str] = frozenset(
    {
        "chat",
        "code",
        "reasoning",
        "summarize",
        "summarization",
        "translation",
    }
)


def is_embedding_model(model_id: str) -> bool:
    """Indique si ``model_id`` désigne un modèle d'embedding dédié.

    La détection se fait sur le nom du modèle (tag exclu), token par token :
    ``qwen3-embedding:8b``, ``nomic-embed-text``, ``mxbai-embed-large``,
    ``bge-m3``, ``all-minilm:l6-v2``, ``intfloat/e5-mistral-7b-instruct``.

    Args:
        model_id: Identifiant du modèle (``nom:tag`` accepté).

    Returns:
        True si le modèle est un encodeur d'embedding.
    """
    name = (model_id or "").split(":", 1)[0].lower()
    for token in _MODEL_TOKEN_SPLIT_RE.split(name):
        if not token:
            continue
        if token in _EMBEDDING_TOKENS or token.startswith(_EMBEDDING_PREFIXES):
            return True
    return False


def model_supports_task(model: ModelInfo, task_type: str | None) -> bool:
    """Indique si ``model`` peut honorer ``task_type``.

    Un modèle dont ``capabilities`` est vide est réputé compatible : les
    providers qui ne renseignent pas la métadonnée conservent le comportement
    historique de sélection.

    Args:
        model: Modèle candidat.
        task_type: Type de tâche (``None`` = chat).

    Returns:
        True si le modèle peut exécuter la tâche.
    """
    task = (task_type or "chat").strip().lower()
    requires_chat = task in _CHAT_TASKS
    if not model.capabilities:
        # Aucune métadonnée : seul le nom permet de détecter un encodeur.
        return not requires_chat or not is_embedding_model(model.id)
    if requires_chat:
        return "chat" in model.capabilities
    return "embedding" in model.capabilities


@dataclass
class ChatMessage:
    """Message de chat standardisé."""

    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: str | None = None
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None


@dataclass
class ChatResponse:
    """Réponse de chat standardisée."""

    content: str
    model: str
    provider: str
    usage: dict | None = None
    finish_reason: str | None = None


@dataclass
class UsageStats:
    """Statistiques d'utilisation."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0


# ── Vision Types ──────────────────────────────────────────────────────────


@dataclass
class VisionImage:
    """Image reference for vision analysis.

    Supports either a base64 payload or a URL. Providers that only accept
    one form should raise NotImplementedError for the other.
    """

    data: str  # base64-encoded bytes OR URL
    mime_type: str = "image/png"
    is_url: bool = False


@dataclass
class VisionRequest:
    """Request to analyze an image with a vision-capable model."""

    images: list[VisionImage]
    prompt: str = "Describe this image in detail."
    model: str | None = None
    max_tokens: int | None = None


@dataclass
class VisionResponse:
    """Response from a vision analysis."""

    content: str
    model: str
    provider: str
    usage: dict | None = None


# ── Transcription Types ───────────────────────────────────────────────────


@dataclass
class TranscriptionRequest:
    """Request to transcribe audio to text."""

    audio_data: bytes
    mime_type: str = "audio/wav"
    model: str | None = None
    language: str | None = None  # ISO-639-1 (e.g., "en", "fr")


@dataclass
class TranscriptionResponse:
    """Response from audio transcription."""

    text: str
    model: str
    provider: str
    language: str | None = None
    duration_seconds: float | None = None
