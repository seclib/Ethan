"""Tests des routes /v1/plugins — passerelle HTTP sur le PluginRegistry Core.

Les fonctions du routeur sont appelées directement avec l'injection
`set_plugin_registry` (même pattern que les tests folders/dedup).
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from core.plugins import PluginRegistry
from core.state import CoreRecordStore
from core.tools.registry import ToolRegistry
from interfaces.api.routers import v1


@pytest.fixture()
def wired():
    store = CoreRecordStore()
    v1.set_plugin_registry(PluginRegistry(store=store, tool_registry=ToolRegistry()))
    yield store
    v1.set_plugin_registry(None)


def test_routes_sans_registry_503():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.list_plugins())
    assert exc.value.status_code == 503


def test_list_plugins(wired):
    plugins = asyncio.run(v1.list_plugins())
    assert isinstance(plugins, list)
    ids = {p["id"] for p in plugins}
    assert "github" in ids and "web-search" in ids
    # compat : champs historiques présents
    gh = {p["id"]: p for p in plugins}["github"]
    assert {"id", "name", "status", "version"} <= set(gh.keys())


def test_plugin_categories(wired):
    resp = asyncio.run(v1.list_plugin_categories())
    assert "categories" in resp
    assert any(c["id"] == "development" for c in resp["categories"])


def test_get_plugin_detail(wired):
    plugin = asyncio.run(v1.get_plugin("code-interpreter"))
    assert plugin["id"] == "code-interpreter"
    assert plugin["tools"] == ["builtin_code_interpreter"]
    with pytest.raises(HTTPException) as exc:
        asyncio.run(v1.get_plugin("ghost"))
    assert exc.value.status_code == 404


def test_permissions_route(wired):
    perms = asyncio.run(v1.get_plugin_permissions("github"))
    assert perms["plugin_id"] == "github"
    assert "external_network" in perms["declared"]
    assert "authentication" in perms
    with pytest.raises(HTTPException):
        asyncio.run(v1.get_plugin_permissions("ghost"))


def test_capabilities_route(wired):
    caps = asyncio.run(v1.get_plugin_capabilities("knowledge"))
    assert caps["plugin_id"] == "knowledge"
    assert "search" in caps["capabilities"]


def test_lifecycle_routes(wired):
    installed = asyncio.run(v1.install_plugin_by_id("slack"))
    assert installed["status"] == "inactive"
    enabled = asyncio.run(v1.enable_plugin("slack"))
    assert enabled["status"] == "active"
    disabled = asyncio.run(v1.disable_plugin("slack"))
    assert disabled["status"] == "inactive"
    toggled = asyncio.run(v1.toggle_plugin("slack"))
    assert toggled["status"] == "active"
    with pytest.raises(HTTPException):
        asyncio.run(v1.install_plugin_by_id("ghost"))


def test_connect_disconnect_routes(wired):
    asyncio.run(v1.install_plugin_by_id("email"))
    connected = asyncio.run(
        v1.connect_plugin("email", {"config": {"mailbox": "ops@ethan.dev"}})
    )
    assert connected["connected"] is True
    assert connected["configuration"]["mailbox"] == "ops@ethan.dev"
    disconnected = asyncio.run(v1.disconnect_plugin("email"))
    assert disconnected["connected"] is False
    # connect sur plugin non installé → 404
    with pytest.raises(HTTPException):
        asyncio.run(v1.connect_plugin("projects", None))


def test_install_compat_body_nom(wired):
    custom = asyncio.run(v1.install_plugin({"name": "Plugin Custom"}))
    assert custom["source"] == "custom"
    assert custom["installed"] is True
    # compat avec id catalogue
    gh = asyncio.run(v1.install_plugin({"id": "github"}))
    assert gh["id"] == "github"
    assert gh["installed"] is True
