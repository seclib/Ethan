"""Tests de configuration Odin — lecture, sauvegarde, persistance, secrets.

Valide :
- get_odin_config / set_odin_config (IA)
- get_voice_config / update_voice_config (voix TTS/STT)
- get_api_config / update_api_config (API externe)
- Persistence via ConfigurationService (domaine preferences)
- Rechargement (valeurs conservees)
- Rejet des valeurs invalides
- Secrets jamais exposes dans les reponses
"""

from __future__ import annotations

import asyncio
import os

import pytest

from core.config import ConfigurationService, ConfigStore
from core.config.loader import ConfigLoader
from fastapi import HTTPException
from interfaces.api.routers import odin_ai as odin_ai_mod

os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-production")


def _make_service() -> ConfigurationService:
    store = ConfigStore()
    loader = ConfigLoader()
    return ConfigurationService(loader=loader, store=store)


@pytest.fixture
def svc():
    service = _make_service()
    odin_ai_mod.set_odin_config_service(service)
    yield service
    odin_ai_mod.set_odin_config_service(None)


def _run(coro):
    return asyncio.get_event_loop_policy().new_event_loop().run_until_complete(coro)


# ── Tests config IA ──────────────────────────────────────────────────────

def test_get_odin_ai_config_defaults(svc):
    """Config par defaut retournee quand rien n'est encore configure."""
    cfg = odin_ai_mod.get_odin_config()
    assert cfg["default_model"] is None
    assert cfg["default_provider"] is None
    assert cfg["context_limit"] == 8000
    assert cfg["timeout_seconds"] == 60
    text = str(cfg).lower()
    assert "api_key" not in text
    assert "secret" not in text
    assert "token" not in text


def test_set_odin_ai_config_and_persist(svc):
    """Sauvegarde config IA + persistence."""
    _run(odin_ai_mod.set_odin_config({
        "default_model": "llama3.2:3b",
        "default_provider": "ollama",
        "context_limit": 4096,
        "timeout_seconds": 30,
    }))
    cfg = odin_ai_mod.get_odin_config()
    assert cfg["default_model"] == "llama3.2:3b"
    assert cfg["default_provider"] == "ollama"
    assert cfg["context_limit"] == 4096
    assert cfg["timeout_seconds"] == 30
    cfg2 = odin_ai_mod.get_odin_config()
    assert cfg2["default_model"] == "llama3.2:3b"
    assert cfg2["context_limit"] == 4096


def test_set_odin_ai_config_partial(svc):
    """Mise a jour partielle."""
    _run(odin_ai_mod.set_odin_config({"default_model": "mistral:7b"}))
    cfg = odin_ai_mod.get_odin_config()
    assert cfg["default_model"] == "mistral:7b"
    assert cfg["context_limit"] == 8000
    assert cfg["timeout_seconds"] == 60


def test_set_odin_ai_config_invalid_context_limit(svc):
    """context_limit hors bornes est refuse."""
    with pytest.raises(HTTPException) as exc:
        _run(odin_ai_mod.set_odin_config({"context_limit": 100}))
    assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        _run(odin_ai_mod.set_odin_config({"context_limit": 200000}))
    assert exc.value.status_code == 422


def test_set_odin_ai_config_invalid_timeout(svc):
    """timeout_seconds hors bornes est refuse."""
    with pytest.raises(HTTPException) as exc:
        _run(odin_ai_mod.set_odin_config({"timeout_seconds": 1}))
    assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        _run(odin_ai_mod.set_odin_config({"timeout_seconds": 500}))
    assert exc.value.status_code == 422


# ── Tests config voix ────────────────────────────────────────────────────

def test_get_odin_voice_config_defaults(svc):
    """Config voix par defaut."""
    data = odin_ai_mod.get_voice_config()
    assert data["tts_provider"] == "builtin-tone"
    assert data["tts_voice"] == "default"
    assert data["tts_speed"] == 1.0
    assert data["stt_enabled"] is False


def test_update_voice_config(svc):
    """Sauvegarde config voix + persistence."""
    data = _run(odin_ai_mod.update_voice_config({
        "tts_provider": "openai",
        "tts_voice": "alloy",
        "tts_speed": 1.2,
        "stt_enabled": True,
    }))
    assert data["tts_provider"] == "openai"
    assert data["tts_voice"] == "alloy"
    assert data["tts_speed"] == 1.2
    assert data["stt_enabled"] is True
    data2 = odin_ai_mod.get_voice_config()
    assert data2["tts_speed"] == 1.2


def test_update_voice_config_invalid_speed(svc):
    """tts_speed hors bornes est refuse."""
    with pytest.raises(HTTPException) as exc:
        _run(odin_ai_mod.update_voice_config({"tts_speed": 0.05}))
    assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        _run(odin_ai_mod.update_voice_config({"tts_speed": 5.0}))
    assert exc.value.status_code == 422


# ── Tests config API externe ─────────────────────────────────────────────

def test_get_odin_api_config_defaults(svc):
    """Config API externe par defaut."""
    data = odin_ai_mod.get_api_config()
    assert data["api_base_url"] is None
    assert data["api_timeout_seconds"] == 30
    assert data["api_retry_count"] == 3


def test_update_api_config(svc):
    """Sauvegarde config API externe + persistence."""
    data = _run(odin_ai_mod.update_api_config({
        "api_base_url": "https://api.example.com",
        "api_timeout_seconds": 45,
        "api_retry_count": 5,
    }))
    assert data["api_base_url"] == "https://api.example.com"
    assert data["api_timeout_seconds"] == 45
    assert data["api_retry_count"] == 5
    data2 = odin_ai_mod.get_api_config()
    assert data2["api_timeout_seconds"] == 45


def test_update_api_config_invalid_timeout(svc):
    """api_timeout_seconds hors bornes est refuse."""
    with pytest.raises(HTTPException) as exc:
        _run(odin_ai_mod.update_api_config({"api_timeout_seconds": 0}))
    assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        _run(odin_ai_mod.update_api_config({"api_timeout_seconds": 400}))
    assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        _run(odin_ai_mod.update_api_config({"api_retry_count": 11}))
    assert exc.value.status_code == 422


# ── Tests secrets ────────────────────────────────────────────────────────

def test_no_secrets_in_config_responses(svc):
    """Aucune cle API / secret n'est expose dans les reponses de config."""
    _run(odin_ai_mod.set_odin_config({
        "default_model": "llama3.2:3b",
        "default_provider": "ollama",
    }))
    _run(odin_ai_mod.update_voice_config({
        "tts_provider": "openai",
        "tts_voice": "alloy",
    }))
    _run(odin_ai_mod.update_api_config({
        "api_base_url": "https://api.example.com",
    }))
    for getter in (odin_ai_mod.get_odin_config,
                   odin_ai_mod.get_voice_config,
                   odin_ai_mod.get_api_config):
        body = getter()
        text = str(body).lower()
        assert "api_key" not in text
        assert "secret" not in text
        assert "password" not in text
        assert "authorization" not in text
        assert "sk-" not in text
        assert "bearer" not in text


# ── Injection des services ───────────────────────────────────────────────

def test_set_get_config_service():
    """set_odin_config_service / get_config_service fonctionnent."""
    service = _make_service()
    odin_ai_mod.set_odin_config_service(service)
    assert odin_ai_mod.get_config_service() is service
    odin_ai_mod.set_odin_config_service(None)
    with pytest.raises(HTTPException):
        odin_ai_mod.get_config_service()
