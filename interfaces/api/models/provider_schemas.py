"""Schémas Pydantic pour la gestion centralisée des providers LLM."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ProviderCreate(BaseModel):
    """Payload pour enregistrer un nouveau provider."""
    name: str = Field(..., description="Identifiant unique du provider (ex: my-ollama)")
    type: str = Field(..., description="Type de provider: ollama, openai, anthropic, vllm, llamacpp, lmstudio, gemini, openai-compatible, custom")
    base_url: str = Field("", description="URL de base du service")
    api_key: str | None = Field(None, description="Clé API (jamais renvoyée dans les réponses)")
    default_model: str = Field("", description="Modèle par défaut")
    display_name: str = Field("", description="Nom d'affichage")
    enabled: bool = Field(True, description="Activer immédiatement")
    options: dict[str, Any] = Field(default_factory=dict, description="Options spécifiques au provider")


class ProviderUpdate(BaseModel):
    """Payload pour mettre à jour un provider existant."""
    base_url: str | None = Field(None, description="URL de base du service")
    api_key: str | None = Field(None, description="Clé API (jamais renvoyée)")
    default_model: str | None = Field(None, description="Modèle par défaut")
    display_name: str | None = Field(None, description="Nom d'affichage")
    enabled: bool | None = Field(None, description="Activer/désactiver")
    options: dict[str, Any] | None = Field(None, description="Options spécifiques")


class ProviderResponse(BaseModel):
    """Réponse d'un provider (sans secrets)."""
    id: str = Field(..., description="Identifiant unique")
    name: str = Field(..., description="Nom d'affichage")
    type: str = Field(..., description="Type de provider")
    enabled: bool = Field(..., description="État d'activation")
    status: str = Field("unknown", description="État de connexion: connected, disconnected, error, unknown")
    default_model: str = Field("", description="Modèle par défaut")
    is_default: bool = Field(False, description="Est le provider par défaut")
    base_url: str = Field("", description="URL de base")
    models: list[str] = Field(default_factory=list, description="Modèles disponibles")
    # Capacités normalisées du modèle unifié (llm, vision, embedding,
    # speech_to_text, transcription).
    capabilities: list[str] = Field(default_factory=list, description="Capacités normalisées")
    # Méthodes d'authentification supportées par ce provider
    # ("api_key", "user_account"). Le WebUI conditionne sa section
    # « Connection method » (API Key / User Account) dessus.
    auth_methods: list[str] = Field(default_factory=list, description="Méthodes d'authentification supportées")
    # Booléen uniquement — la clé API elle-même n'est JAMAIS sérialisée.
    has_api_key: bool = Field(False, description="Une clé/token est configuré (secrets jamais exposés)")


class ModelInfoResponse(BaseModel):
    """Modèle disponible chez un provider."""
    id: str = Field(..., description="ID du modèle")
    name: str = Field(..., description="Nom du modèle")
    context_length: int = Field(4096, description="Longueur de contexte")
    is_local: bool = Field(False, description="Modèle local")
    is_private: bool = Field(False, description="Modèle privé")
    quality_score: float = Field(0.8, description="Score qualité")
    capabilities: list[str] = Field(default_factory=list, description="Capacités")


class TestConnectionResult(BaseModel):
    """Résultat du test de connexion."""
    provider_id: str = Field(..., description="ID du provider testé")
    connected: bool = Field(..., description="Connexion réussie")
    status: str = Field(..., description="connected, error")
    message: str = Field("", description="Message détaillé")