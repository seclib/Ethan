"""Tests réels des routes /v1/plugins (interfaces/api/routers/v1.py).

Exécute le vrai CoreWebUIStore du Core (core/state/webui_store.py) sur un
CoreRecordStore en mémoire (aucun mock du domaine) et appelle directement les
fonctions de route — les éventuels gates auth sont hors périmètre ici
(couverts par la couche auth).

Capacités réellement exposées (périmètre du contrat testé) :
    GET  /v1/plugins              — liste (seed 2 plugins par défaut si vide)
    GET  /v1/plugins/{id}         — informations
    POST /v1/plugins/install      — installation ({id?, name})
    PUT  /v1/plugins/{id}/toggle  — activation/désactivation
Pas de delete/update côté Core : le WebUI ne doit pas les exposer non plus.
"""

import asyncio

import pytest
from core.plugins import PluginRegistry
from core.state.record_store import CoreRecordStore
from core.state.webui_store import CoreWebUIStore
from fastapi import HTTPException
from routers import v1


@pytest.fixture(autouse=True)
def real_plugin_store():
    """Vrai CoreWebUIStore + PluginRegistry (CoreRecordStore mémoire) injectés.

    Le router est ainsi câblé sur le catalogue Core réel (plugins github, slack…).
    """
    store = CoreRecordStore()
    webui_store = CoreWebUIStore(store)
    plugin_registry = PluginRegistry(store)
    v1.set_webui_store(webui_store)
    v1.set_plugin_registry(plugin_registry)
    yield
    v1.set_webui_store(None)
    v1.set_plugin_registry(None)


def test_list_seeds_default_plugins():
    """Première liste : le Core amorce tous les plugins du catalogue."""
    plugins = asyncio.run(v1.list_plugins())
    by_id = {p["id"]: p for p in plugins}
    # Le catalogue Core contient github + slack au minimum.
    assert "github" in by_id
    assert "slack" in by_id
    # Tous les seed sont en statut « available » (non installés) initialement.
    assert by_id["github"]["status"] == "available"
    assert by_id["github"]["version"] == "1.0.0"


def test_install_custom_then_listed():
    """Installation custom → enregistré en statut « inactive »."""
    installed = asyncio.run(v1.install_plugin({"id": "my-plugin", "name": "Mon Plugin"}))
    assert installed["id"] == "my-plugin"
    assert installed["name"] == "Mon Plugin"
    assert installed["status"] == "inactive"
    assert installed["version"] == "0.1.0"

    listed = asyncio.run(v1.list_plugins())
    ids = [p["id"] for p in listed if p["source"] == "custom"]
    assert ids == ["my-plugin"]


def test_install_after_first_list_keeps_defaults():
    """Séquence WebUI : list d'abord, puis install — coexistence catalogue + custom."""
    asyncio.run(v1.list_plugins())  # seed du catalogue
    asyncio.run(v1.install_plugin({"id": "my-plugin", "name": "Mon Plugin"}))

    listed = asyncio.run(v1.list_plugins())
    ids = {p["id"] for p in listed}
    assert "github" in ids
    assert "slack" in ids
    assert "my-plugin" in ids


def test_install_generates_id_when_missing():
    """Le Core génère un id (uuid4) si non fourni."""
    installed = asyncio.run(v1.install_plugin({"name": "Sans Id"}))
    assert installed["id"]
    assert installed["name"] == "Sans Id"
    assert installed["status"] == "inactive"


def test_toggle_roundtrip():
    """Enable sur un builtin seedé (available→active), puis disable (→inactive)."""
    first = asyncio.run(v1.enable_plugin("github"))
    assert first["status"] == "active"

    fetched = asyncio.run(v1.get_plugin("github"))
    assert fetched["status"] == "active"

    second = asyncio.run(v1.disable_plugin("github"))
    assert second["status"] == "inactive"


def test_toggle_unknown_404():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.toggle_plugin("nope"))
    assert exc.value.status_code == 404


def test_get_detail_known_and_unknown():
    plugin = asyncio.run(v1.get_plugin("slack"))
    assert plugin["id"] == "slack"
    assert plugin["name"] == "Slack Notifier"

    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.get_plugin("nope"))
    assert exc.value.status_code == 404


def test_uninitialized_store_503():
    """Sans store ni registry injecté (API non bootstrapée) → HTTP 503."""
    v1.set_webui_store(None)
    v1.set_plugin_registry(None)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.list_plugins())
    assert exc.value.status_code == 503
