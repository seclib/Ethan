"""Tests API Tools — catalogue et CRUD custom avec le ToolManager RÉEL.

Les handlers sont appelés directement (pattern du repo). Aucun mock :
ToolManager = ToolRegistry + CoreRecordStore réels, et les tools builtin
sont de vrais objets Tool enregistrés dans le registre.

Couverture :
  - création custom persistante (name, parameters, code → metadata)
  - validation 422 (name vide, parameters non-objet)
  - suppression custom, refus builtin (422), 404 inconnu
  - list_tools expose les records (builtin + custom)
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from routers.capabilities import (
    CapabilityManagers,
    set_capability_managers,
    create_tool,
    delete_tool,
    list_tools,
)
from core.tools.manager import ToolManager
from core.tools.types import Tool


def _install_real_manager() -> ToolManager:
    manager = ToolManager()
    set_capability_managers(CapabilityManagers(tools=manager))
    return manager


def _register_builtin(manager: ToolManager) -> None:
    manager.registry.register(
        Tool(
            id="builtin_web_search",
            name="web_search",
            description="Recherche web réelle du registre",
            provider="builtin",
            category="search",
        )
    )


def test_create_custom_tool_persists_and_lists():
    async def scenario():
        manager = _install_real_manager()
        created = await create_tool(
            {
                "name": "summarize_text",
                "description": "Résume un texte",
                "parameters": {"text": {"type": "string"}},
                "code": "def run(text): ...",
                "capabilities": ["chat"],
                "tags": ["nlp"],
            }
        )
        assert created.provider == "custom"
        assert created.metadata["code"] == "def run(text): ..."

        listed = await list_tools()
        ids = {t.id for t in listed}
        assert created.id in ids

        # Le record custom est restaurable (persistance CoreRecordStore)
        record = await manager._store.get(manager._CUSTOM_TOOLS_DOMAIN, created.id)
        assert record is not None
        assert record["name"] == "summarize_text"

    asyncio.run(scenario())


def test_create_tool_empty_name_422():
    async def scenario():
        _install_real_manager()
        with pytest.raises(HTTPException) as exc:
            await create_tool({"name": "   "})
        assert exc.value.status_code == 422
        assert "name" in str(exc.value.detail).lower()

    asyncio.run(scenario())


def test_create_tool_non_object_parameters_422():
    async def scenario():
        _install_real_manager()
        with pytest.raises(HTTPException) as exc:
            await create_tool({"name": "bad_params", "parameters": ["not", "a", "dict"]})
        assert exc.value.status_code == 422
        assert "JSON object" in str(exc.value.detail)

    asyncio.run(scenario())


def test_delete_custom_tool_removes_it():
    async def scenario():
        manager = _install_real_manager()
        created = await create_tool({"name": "temp_tool"})
        result = await delete_tool(created.id)
        assert result == {"status": "deleted"}
        assert all(t.id != created.id for t in await list_tools())
        assert manager.registry.get(created.id) is None

    asyncio.run(scenario())


def test_delete_builtin_tool_is_refused_422():
    async def scenario():
        manager = _install_real_manager()
        _register_builtin(manager)
        with pytest.raises(HTTPException) as exc:
            await delete_tool("builtin_web_search")
        assert exc.value.status_code == 422
        assert "custom" in str(exc.value.detail)
        # Le builtin est toujours là
        assert manager.registry.get("builtin_web_search") is not None

    asyncio.run(scenario())


def test_delete_unknown_tool_404():
    async def scenario():
        _install_real_manager()
        with pytest.raises(HTTPException) as exc:
            await delete_tool("ghost_tool")
        assert exc.value.status_code == 404

    asyncio.run(scenario())
