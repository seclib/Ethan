"""Router API — Gestion centralisée des providers LLM.

Routes :
    GET    /api/providers                    → liste des providers
    POST   /api/providers                    → enregistrer un provider
    PUT    /api/providers/{id}               → mettre à jour un provider
    DELETE /api/providers/{id}               → supprimer un provider
    GET    /api/providers/{id}/models        → modèles disponibles
    POST   /api/providers/{id}/test          → tester la connexion
    PUT    /api/providers/{id}/default       → définir comme provider par défaut
    GET    /api/providers/{id}/capabilities  → capacités du provider
    POST   /api/providers/vision             → analyser une image
    POST   /api/providers/transcribe         → transcrire un audio
"""

from __future__ import annotations

import base64
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from core.auth import Permission
from interfaces.api.auth import require_permission
from core.llm.provider_manager import ProviderManager
from core.llm.types import TranscriptionRequest, VisionImage, VisionRequest
from interfaces.api.models.provider_schemas import (
    ProviderCreate,
    ProviderUpdate,
    ProviderResponse,
    TestConnectionResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/providers", tags=["providers"])

# Instance globale du ProviderManager — injectée au démarrage via set_manager()
_manager: ProviderManager | None = None


def set_provider_manager(manager: ProviderManager) -> None:
    """Injecte le ProviderManager dans le router (appelé au startup)."""
    global _manager
    _manager = manager


def get_manager() -> ProviderManager:
    """Retourne le ProviderManager global.

    Raises:
        HTTPException 503 si le manager n'est pas initialisé.
    """
    if _manager is None:
        raise HTTPException(status_code=503, detail="Provider manager not initialized")
    return _manager


# ── GET /providers ─────────────────────────────────────────────────────────

@router.get("", response_model=list[ProviderResponse])
async def list_providers():
    """Liste tous les providers enregistrés avec leur état."""
    manager = get_manager()
    providers = await manager.list_providers()
    return [ProviderResponse(**p) for p in providers]


# ── GET /providers/{id} ────────────────────────────────────────────────────

@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(provider_id: str):
    """Détail d'un provider (statut de connexion rafraîchi)."""
    manager = get_manager()

    try:
        provider = await manager.describe_provider(provider_id)
        return ProviderResponse(**provider)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to get provider %s: %s", provider_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to get provider: {e}")


# ── POST /providers ────────────────────────────────────────────────────────

@router.post("", response_model=ProviderResponse, status_code=201)
async def create_provider(data: ProviderCreate):
    """Enregistre un nouveau provider.

    Le provider est instancié via la factory, testé si activé,
    puis persisté (config sans clé API).
    """
    manager = get_manager()

    config = {
        "name": data.name,
        "type": data.type,
        "base_url": data.base_url,
        "api_key": data.api_key or "",
        "default_model": data.default_model,
        "display_name": data.display_name or data.name,
        "enabled": data.enabled,
        "options": data.options,
    }

    try:
        result = await manager.register_provider(config=config)
        return ProviderResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to create provider %s: %s", data.name, e)
        raise HTTPException(status_code=500, detail=f"Failed to create provider: {e}")


# ── PUT /providers/{id} ────────────────────────────────────────────────────

@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(provider_id: str, data: ProviderUpdate):
    """Met à jour un provider existant.

    - active/désactive via ``enabled``
    - met à jour base_url, default_model, display_name
    - une nouvelle clé API peut être fournie (jamais renvoyée)

    Lève 404 si le provider n'existe pas.
    """
    manager = get_manager()

    # Récupérer la config actuelle
    config = await manager._store.get(provider_id)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")

    # Appliquer les mises à jour
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            config[key] = value

    # Si on change la clé API, la stocker séparément (jamais dans le store public)
    api_key = config.pop("api_key", None)

    try:
        # Sauvegarder la nouvelle config
        await manager._store.save(provider_id, config)
        manager._providers_config[provider_id] = config

        # Ré-instancier / ré-enregistrer si activé
        if config.get("enabled", False):
            from core.llm.provider_factory import create_provider_from_config
            provider = create_provider_from_config({**config, "name": provider_id, "api_key": api_key or ""})
            await manager._register(provider, provider_id)
            await provider.initialize()
        else:
            manager._registry._providers.pop(provider_id, None)

        result = await manager.describe_provider(provider_id)
        return ProviderResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to update provider %s: %s", provider_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to update provider: {e}")


# ── DELETE /providers/{id} ─────────────────────────────────────────────────

@router.delete("/{provider_id}")
async def delete_provider(provider_id: str):
    """Supprime un provider de la config et du registry."""
    manager = get_manager()

    try:
        existed = await manager.unregister_provider(provider_id)
        if not existed:
            raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")
        return {"status": "deleted", "provider_id": provider_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete provider %s: %s", provider_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to delete provider: {e}")


# ── GET /providers/{id}/models ─────────────────────────────────────────────

@router.get("/{provider_id}/models", response_model=list[dict])
async def list_provider_models(provider_id: str):
    """Liste les modèles disponibles chez un provider."""
    manager = get_manager()

    try:
        models = await manager.list_models(provider_id)
        return [
            {
                "id": m.id,
                "name": m.name,
                "context_length": m.context_length,
                "is_local": m.is_local,
                "is_private": m.is_private,
                "quality_score": m.quality_score,
                "capabilities": m.capabilities,
            }
            for m in models
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to list models for %s: %s", provider_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to list models: {e}")


# ── POST /providers/{id}/test ──────────────────────────────────────────────

@router.post("/{provider_id}/test", response_model=TestConnectionResult)
async def test_provider_connection(provider_id: str):
    """Teste la connexion à un provider (vrai healthcheck)."""
    manager = get_manager()

    try:
        result = await manager.test_connection(provider_id)
        return TestConnectionResult(
            provider_id=provider_id,
            connected=result["connected"],
            status=result["status"],
            message=result["message"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to test connection for %s: %s", provider_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to test connection: {e}")


# ── PUT /providers/{id}/default ────────────────────────────────────────────

@router.put("/{provider_id}/default", response_model=ProviderResponse)
async def set_default_provider(provider_id: str):
    """Définit le provider par défaut."""
    manager = get_manager()

    try:
        result = await manager.set_default_provider(provider_id)
        return ProviderResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to set default provider %s: %s", provider_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to set default provider: {e}")


# ── GET /providers/{id}/capabilities ──────────────────────────────────────

@router.get("/{provider_id}/capabilities")
async def get_provider_capabilities(provider_id: str):
    """Retourne les capacités d'un provider (vision, transcription, embedding)."""
    manager = get_manager()

    provider = manager._registry.get_provider(provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")

    return {
        "provider_id": provider_id,
        "name": provider.name,
        "supports_vision": getattr(provider, "supports_vision", False),
        "supports_transcription": getattr(provider, "supports_transcription", False),
        "supports_embedding": getattr(provider, "supports_embedding", True),
    }


# ── POST /providers/vision ────────────────────────────────────────────────

@router.post("/vision")
async def vision_analyze(
    file: UploadFile = File(...),
    prompt: str = Form("Describe this image in detail."),
    model: str | None = Form(None),
    provider_id: str | None = Form(None),
):
    """Analyse une image via un provider capable de vision.

    Le fichier image est lu en mémoire et envoyé au provider.
    Les secrets ne sont jamais exposés — le provider utilise sa clé API
    injectée en mémoire au démarrage.
    """
    manager = get_manager()

    try:
        raw = await file.read()
        b64 = base64.b64encode(raw).decode("ascii")

        # Determine MIME type (default to png)
        mime = file.content_type or "image/png"

        request = VisionRequest(
            images=[VisionImage(data=b64, mime_type=mime, is_url=False)],
            prompt=prompt,
            model=model,
        )
        result = await manager.vision_analyze(
            request, provider_name=provider_id
        )
        return {
            "content": result.content,
            "model": result.model,
            "provider": result.provider,
            "usage": result.usage,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.exception("Vision analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Vision analysis failed: {e}")


# ── POST /providers/transcribe ────────────────────────────────────────────

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    model: str | None = Form(None),
    language: str | None = Form(None),
    provider_id: str | None = Form(None),
):
    """Transcrit un fichier audio via un provider capable (ex: OpenAI Whisper).

    Le fichier audio est lu en mémoire et envoyé au provider.
    """
    manager = get_manager()

    try:
        raw = await file.read()
        mime = file.content_type or "audio/wav"

        request = TranscriptionRequest(
            audio_data=raw,
            mime_type=mime,
            model=model,
            language=language,
        )
        result = await manager.transcribe(
            request, provider_name=provider_id
        )
        return {
            "text": result.text,
            "model": result.model,
            "provider": result.provider,
            "language": result.language,
            "duration_seconds": result.duration_seconds,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.exception("Transcription failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")