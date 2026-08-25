"""Tests unitaires pour core/llm/model_store.py (ModelStore)."""

from __future__ import annotations

import pytest

from core.llm.model_store import ModelStore


@pytest.fixture
def store() -> ModelStore:
    """ModelStore en mode mémoire (pas de PG/Redis)."""
    return ModelStore()


@pytest.mark.asyncio
async def test_create_and_get_model(store: ModelStore):
    """Création puis récupération d'une fiche modèle."""
    created = await store.create_model({
        "name": "My Custom Llama",
        "model": "llama3.1:70b-instruct-q4_K_M",
        "base_model_id": "llama3.1",
        "params": {"temperature": 0.7, "max_tokens": 4096},
        "meta": {"tags": ["local", "test"]},
        "is_active": True,
        "acl": ["user:admin"],
    })

    assert created["id"] is not None
    assert created["name"] == "My Custom Llama"
    assert created["model"] == "llama3.1:70b-instruct-q4_K_M"
    assert created["base_model_id"] == "llama3.1"
    assert created["params"]["temperature"] == 0.7
    assert created["is_active"] is True
    assert created["acl"] == ["user:admin"]
    assert created["created_at"] is not None
    assert created["updated_at"] is not None

    fetched = await store.get_model(created["id"])
    assert fetched is not None
    assert fetched["name"] == "My Custom Llama"


@pytest.mark.asyncio
async def test_list_models(store: ModelStore):
    """list_models retourne tous les modèles créés."""
    await store.create_model({"name": "Model A"})
    await store.create_model({"name": "Model B"})

    models = await store.list_models()
    assert len(models) == 2
    names = [m["name"] for m in models]
    assert "Model A" in names
    assert "Model B" in names


@pytest.mark.asyncio
async def test_update_model(store: ModelStore):
    """update_model modifie les champs et met à jour updated_at."""
    created = await store.create_model({"name": "Original", "is_active": True})
    original_updated = created["updated_at"]

    updated = await store.update_model(created["id"], {
        "name": "Updated",
        "is_active": False,
        "params": {"temperature": 0.1},
    })

    assert updated is not None
    assert updated["name"] == "Updated"
    assert updated["is_active"] is False
    assert updated["params"]["temperature"] == 0.1
    assert updated["updated_at"] != original_updated


@pytest.mark.asyncio
async def test_update_model_not_found(store: ModelStore):
    """update_model retourne None si le modèle n'existe pas."""
    result = await store.update_model("nonexistent", {"name": "X"})
    assert result is None


@pytest.mark.asyncio
async def test_delete_model(store: ModelStore):
    """delete_model supprime et retourne True."""
    created = await store.create_model({"name": "To Delete"})
    existed = await store.delete_model(created["id"])
    assert existed is True

    fetched = await store.get_model(created["id"])
    assert fetched is None


@pytest.mark.asyncio
async def test_delete_model_not_found(store: ModelStore):
    """delete_model retourne False si le modèle n'existe pas."""
    existed = await store.delete_model("nonexistent")
    assert existed is False


@pytest.mark.asyncio
async def test_toggle_model(store: ModelStore):
    """toggle_model inverse is_active."""
    created = await store.create_model({"name": "Toggle", "is_active": True})
    assert created["is_active"] is True

    toggled = await store.toggle_model(created["id"])
    assert toggled is not None
    assert toggled["is_active"] is False

    toggled_again = await store.toggle_model(created["id"])
    assert toggled_again is not None
    assert toggled_again["is_active"] is True


@pytest.mark.asyncio
async def test_toggle_model_not_found(store: ModelStore):
    """toggle_model retourne None si le modèle n'existe pas."""
    result = await store.toggle_model("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_search_models(store: ModelStore):
    """search_models filtre par nom, base_model_id et tags."""
    await store.create_model({
        "name": "Llama 3.1 Custom",
        "base_model_id": "llama3.1",
        "meta": {"tags": ["local", "coding"]},
    })
    await store.create_model({
        "name": "GPT-4 Custom",
        "base_model_id": "gpt-4",
        "meta": {"tags": ["cloud", "reasoning"]},
    })

    # Recherche par nom
    results = await store.search_models("llama")
    assert len(results) == 1
    assert results[0]["name"] == "Llama 3.1 Custom"

    # Recherche par base_model_id
    results = await store.search_models("gpt-4")
    assert len(results) == 1
    assert results[0]["name"] == "GPT-4 Custom"

    # Recherche par tag
    results = await store.search_models("coding")
    assert len(results) == 1
    assert results[0]["name"] == "Llama 3.1 Custom"

    # Recherche sans résultat
    results = await store.search_models("nonexistent")
    assert len(results) == 0


@pytest.mark.asyncio
async def test_create_model_defaults(store: ModelStore):
    """Les valeurs par défaut sont appliquées quand les champs sont absents."""
    created = await store.create_model({"name": "Minimal"})

    assert created["name"] == "Minimal"
    assert created["base_model_id"] == ""
    assert created["model"] == ""
    assert created["params"] == {}
    assert created["meta"] == {}
    assert created["is_active"] is True
    assert created["acl"] == []


@pytest.mark.asyncio
async def test_create_model_default_name(store: ModelStore):
    """Si name est absent, utilise 'unnamed'."""
    created = await store.create_model({})
    assert created["name"] == "unnamed"
