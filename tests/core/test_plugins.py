"""Tests — Plugin Discovery & Loading (ADR-1008)"""

import pytest
from core.plugins import Plugin, PluginContext, PluginMetadata, PluginRegistry


class MockPlugin(Plugin):
    """A simple plugin for testing."""

    def __init__(self, name="test-plugin", version="1.0.0"):
        self.name = name
        self.version = version

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name=self.name,
            version=self.version,
            description="Test plugin",
            author="Tester",
            capabilities=["test.cap"],
        )

    async def initialize(self, context: PluginContext) -> None:
        pass

    async def shutdown(self) -> None:
        pass


class TestPlugin:
    """Comportements du SDK Plugin / PluginMetadata / PluginContext."""

    def test_metadata(self):
        meta = MockPlugin("x", "1.0.0").get_metadata()
        assert meta.name == "x"
        assert meta.capabilities == ["test.cap"]
        assert meta.description == "Test plugin"

    @pytest.mark.asyncio
    async def test_lifecycle(self):
        plugin = MockPlugin()
        await plugin.initialize(PluginContext())
        await plugin.shutdown()


class TestPluginRegistry:
    """Tests du registre Core (source de vérité des plugins).

    Le registre Core est un gestionnaire de catalogue + état persistant :
    il ne scanne pas (cela relève du loader), il exporte et arbitre.
    """

    @pytest.fixture
    def store(self):
        class _Store:
            def __init__(self):
                self._data = {}

            async def list(self, domain):
                return list(self._data.values())

            async def get(self, domain, plugin_id):
                return self._data.get(plugin_id)

            async def save(self, domain, plugin_id, record):
                self._data[plugin_id] = record

        return _Store()

    @pytest.fixture
    def registry(self, store):
        return PluginRegistry(store)

    @pytest.mark.asyncio
    async def test_empty_store_has_no_installed_plugins(self, registry):
        assert await registry.get("ghost") is None

    @pytest.mark.asyncio
    async def test_save_and_list(self, registry, store):
        await store.save("webui_plugins", "my-plugin", {
            "id": "my-plugin",
            "name": "My Plugin",
            "status": "active",
            "version": "1.0.0",
            "installed": True,
            "capabilities": ["test.cap"],
        })
        view = await registry.list_plugins()
        assert {"my-plugin"} <= {v["id"] for v in view}
        assert (await registry.get("my-plugin"))["id"] == "my-plugin"

    @pytest.mark.asyncio
    async def test_get_nonexistent_plugin(self, registry):
        assert await registry.get("ghost") is None
        assert await registry.permissions("ghost") is None

    @pytest.mark.asyncio
    async def test_builtin_catalog_is_listed(self, registry):
        view = await registry.list_plugins()
        assert view
        assert all(isinstance(v.get("id"), str) for v in view)
