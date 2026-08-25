"""Tests for the unified Core tool catalogue and persistent definitions."""

import pytest

from core.state.record_store import CoreRecordStore
from core.tools.manager import ToolManager
from core.tools.registry import ToolRegistry
from core.tools.types import Tool


def test_registry_registering_a_tool_twice_does_not_duplicate_indexes():
    registry = ToolRegistry()
    tool = Tool(
        id="custom-search",
        name="custom_search",
        description="Search custom data",
        category="search",
        capabilities=["search"],
        provider="custom",
    )

    registry.register(tool)
    registry.register(tool)

    assert [item.id for item in registry.get_by_category("search")].count(tool.id) == 1
    assert [item.id for item in registry.get_by_capability("search")].count(tool.id) == 1


@pytest.mark.asyncio
async def test_custom_tools_and_pipelines_persist_in_core_store():
    store = CoreRecordStore()
    manager = ToolManager(store=store)

    tool = await manager.create_tool(
        "greet",
        "Say hello",
        {"type": "object", "properties": {"name": {"type": "string"}}},
        code="return f'Hello {name}'",
        capabilities=["greeting"],
    )
    pipeline = await manager.create_pipeline(
        "Greeting pipeline",
        [{"tool_id": tool.id, "args": {"name": "ETHAN"}}],
    )

    restarted_manager = ToolManager(store=store)
    await restarted_manager.initialize()

    restored = restarted_manager.get_tool(tool.id)
    assert restored is not None
    assert restored.name == "greet"
    assert restored.metadata["code"] == "return f'Hello {name}'"
    assert restored.provider == "custom"
    assert await restarted_manager.get_pipeline(pipeline["id"]) == pipeline


@pytest.mark.asyncio
async def test_builtin_tools_are_not_deletable():
    manager = ToolManager()
    builtin = next(tool for tool in manager.list_tools() if tool.provider == "builtin")

    with pytest.raises(ValueError, match="Only custom tools"):
        await manager.delete_tool(builtin.id)
