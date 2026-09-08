"""Tests API — Providers unifiés (routes /providers et /providers/{id}/capabilities).

Valide le modèle de provider unifié côté passerelle HTTP :
- Les capacités canoniques (llm, vision, embedding, speech_to_text, transcription)
  sont exposées sans logique métier dans le routeur.
- Les secrets ne sont JAMAIS renvoyés (has_api_key booléen uniquement).
- La réponse respecte le schéma ProviderResponse (Pydantic).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
import pytest_asyncio

from core.llm.provider_manager import ProviderManager
from core.llm.store import ProviderStore
from interfaces.api.models.provider_schemas import ProviderResponse
from interfaces.api.routers.providers import (
    get_provider_capabilities,
    set_provider_manager,
)


class _StubAllCaps:
    """Provider fictif avec toutes les capacités du modèle unifié."""

    name = "stub-all"
    default_model = "stub-all-1"
    supports_vision = True
    supports_transcription = True
    supports_embedding = True

    async def list_models(self):
        return []


@pytest_asyncio.fixture()
async def manager():
    mgr = ProviderManager(store=ProviderStore())
    mgr._registry._providers["stub-all"] = _StubAllCaps()
    config = {
        "name": "stub-all",
        "type": "custom",
        "enabled": False,
        "api_key": "sk-test-secret-123",
    }
    # Le store est la source de persistance lue par les routeurs (PUT/GET) ;
    # on doit le seed aussi, pas seulement la config mémoire du manager.
    await mgr._store.save("stub-all", dict(config))
    mgr._providers_config["stub-all"] = dict(config)
    set_provider_manager(mgr)
    return mgr


@pytest.mark.asyncio
async def test_capabilities_endpoint_canonical(manager):
    """L'endpoint /capabilities délègue au ProviderManager (modèle unifié)."""
    result = await get_provider_capabilities("stub-all")
    assert result["provider_id"] == "stub-all"
    assert result["capabilities"] == [
        "llm", "vision", "embedding", "speech_to_text", "transcription",
    ]
    assert result["supports_speech_to_text"] is True


@pytest.mark.asyncio
async def test_capabilities_endpoint_never_exposes_secrets(manager):
    """La réponse capabilities ne contient jamais la clé API."""
    result = await get_provider_capabilities("stub-all")
    assert "sk-test-secret-123" not in str(result)
    assert "api_key" not in result


@pytest.mark.asyncio
async def test_provider_response_schema_no_secrets(manager):
    """ProviderResponse sérialise capabilities/has_api_key, jamais la clé."""
    desc = await manager.describe_provider("stub-all")
    resp = ProviderResponse(**desc)
    payload = resp.model_dump()
    assert payload["has_api_key"] is True
    assert payload["capabilities"] == [
        "llm", "vision", "embedding", "speech_to_text", "transcription",
    ]
    assert "api_key" not in payload
    assert "sk-test-secret-123" not in str(payload)


@pytest.mark.asyncio
async def test_capabilities_unknown_provider_raises_404(manager):
    """Provider inconnu → ValueError (convertie en 404 par le routeur)."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await get_provider_capabilities("ghost")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_empty_api_key_never_persisted(manager):
    """PUT avec api_key='' → la clé vide n'est jamais persistée.

    Le formulaire WebUI laisse le champ vide pour « conserver la clé
    actuelle » ; le routeur ne doit ni persister ``api_key: ''`` ni créer
    une intention de wipe (les clés vivent dans env/secrets, jamais dans
    le store).
    """
    from interfaces.api.models.provider_schemas import ProviderUpdate
    from interfaces.api.routers.providers import update_provider

    await update_provider("stub-all", ProviderUpdate(api_key="", enabled=False))

    stored = await manager._store.get("stub-all")
    # La clé n'apparaît ni vide ni renseignée : elle n'est jamais persistée.
    assert "api_key" not in stored


@pytest.mark.asyncio
async def test_update_with_new_key_rotates_into_instance(manager):
    """PUT avec une clé non vide = rotation — propagée à l'instance.

    La clé n'est jamais persistée dans le store (retirée avant save) mais
    elle est injectée dans l'instance provider ré-enregistrée.
    """
    from interfaces.api.models.provider_schemas import ProviderUpdate
    from interfaces.api.routers.providers import update_provider

    await update_provider("stub-all", ProviderUpdate(api_key="sk-new-key", enabled=True))

    # Le store ne contient JAMAIS la clé.
    stored = await manager._store.get("stub-all")
    assert "api_key" not in stored
    assert "sk-new-key" not in str(stored)
    # L'instance ré-enregistrée a bien reçu la nouvelle clé.
    instance = manager._registry.get_provider("stub-all")
    assert getattr(instance, "_api_key", None) == "sk-new-key"