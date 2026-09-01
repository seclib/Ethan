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
from fastapi import HTTPException

from routers import v1
from core.state.webui_store import CoreWebUIStore
from core.state.record_store import CoreRecordStore


@pytest.fixture(autouse=True)
def real_plugin_store():
    """Vrai CoreWebUIStore (CoreRecordStore mémoire) injecté dans le router."""
    v1.set_webui_store(CoreWebUIStore(CoreRecordStore()))
    yield
    v1.set_webui_store(None)


def test_list_seeds_default_plugins():
    """Première liste : le Core amorce ses 2 plugins par défaut."""
    plugins = asyncio.run(v1.list_plugins())
    by_id = {p["id"]: p for p in plugins}
    assert set(by_id) == {"github", "slack"}
    assert by_id["github"]["status"] == "active"
    assert by_id["slack"]["status"] == "inactive"
    assert by_id["github"]["version"] == "1.0.0"


def test_install_then_listed_inactive():
    """Installation → enregistré en statut « inactive » (activation séparée).

    Contrat réel du Core : les plugins par défaut ne sont seedés que par
    list_plugins() sur un store VIDE. Une installation sur store vide fait
    donc disparaître les défauts de la liste (quirk documenté, assumé —
    le WebUI n'a pas à le compenser).
    """
    installed = asyncio.run(v1.install_plugin({"id": "my-plugin", "name": "Mon Plugin"}))
    assert installed == {
        "id": "my-plugin",
        "name": "Mon Plugin",
        "status": "inactive",
        "version": "0.1.0",
    }

    listed = asyncio.run(v1.list_plugins())
    ids = [p["id"] for p in listed]
    assert ids == ["my-plugin"]


def test_install_after_first_list_keeps_defaults():
    """Séquence normale (WebUI) : list d'abord (seed des défauts), puis install —
    les défauts et le plugin installé coexistent."""
    asyncio.run(v1.list_plugins())  # seed github + slack
    asyncio.run(v1.install_plugin({"id": "my-plugin", "name": "Mon Plugin"}))

    listed = asyncio.run(v1.list_plugins())
    ids = {p["id"] for p in listed}
    assert ids == {"github", "slack", "my-plugin"}


def test_install_generates_id_when_missing():
    """Le Core génère un id (uuid4) si non fourni."""
    installed = asyncio.run(v1.install_plugin({"name": "Sans Id"}))
    assert installed["id"]
    assert installed["name"] == "Sans Id"
    assert installed["status"] == "inactive"


def test_toggle_roundtrip():
    """Toggle = bascule active ↔ inactive, persistée dans le store."""
    first = asyncio.run(v1.toggle_plugin("github"))
    assert first["status"] == "inactive"

    # L'état basculé est bien persisté (relecture via get_plugin).
    fetched = asyncio.run(v1.get_plugin("github"))
    assert fetched["status"] == "inactive"

    second = asyncio.run(v1.toggle_plugin("github"))
    assert second["status"] == "active"


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
    """Sans store injecté (API non bootstrapée) → HTTP 503 explicite."""
    v1.set_webui_store(None)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.list_plugins())
    assert exc.value.status_code == 503
