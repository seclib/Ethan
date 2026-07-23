"""Tests du système de plugins."""

import pytest

from core.plugins.interface import EthanPlugin, PluginManifest
from core.plugins.loader import PluginLoader


class MockPlugin(EthanPlugin):
    """Plugin de test."""

    manifest = PluginManifest(
        name="mock-plugin",
        version="1.0.0",
        description="A mock plugin for testing",
        capabilities=[],
    )

    async def init(self, bus, config):
        self.config = config

    async def close(self):
        pass


class TestPluginManifest:
    def test_manifest_creation(self):
        manifest = PluginManifest(
            name="test-plugin",
            version="2.0.0",
            description="Test plugin",
            author="Test Author",
            api_version="1",
        )
        assert manifest.name == "test-plugin"
        assert manifest.version == "2.0.0"
        assert manifest.description == "Test plugin"
        assert manifest.author == "Test Author"
        assert manifest.api_version == "1"

    def test_manifest_with_capabilities(self):
        from core.ethan_types.capability import Capability

        cap = Capability(name="test.action", version="1.0.0")
        manifest = PluginManifest(
            name="test-plugin",
            capabilities=[cap],
        )
        assert len(manifest.capabilities) == 1
        assert manifest.capabilities[0].name == "test.action"


class TestPluginLoader:
    def test_discover_empty(self, tmp_path):
        loader = PluginLoader(extra_paths=[tmp_path])
        manifests = loader.discover()
        assert manifests == []

    def test_discover_plugin_dir(self, tmp_path):
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "__init__.py").write_text("""
MANIFEST = {
    "name": "test-plugin",
    "version": "1.0.0",
    "description": "Test",
}
""")

        loader = PluginLoader(extra_paths=[tmp_path])
        manifests = loader.discover()

        assert len(manifests) == 1
        assert manifests[0].name == "test-plugin"
        assert manifests[0].version == "1.0.0"

    def test_discover_plugin_file(self, tmp_path):
        plugin_file = tmp_path / "simple_plugin.py"
        plugin_file.write_text("""
MANIFEST = {
    "name": "simple-plugin",
    "version": "2.0.0",
}
""")

        loader = PluginLoader(extra_paths=[tmp_path])
        manifests = loader.discover()

        assert len(manifests) == 1
        assert manifests[0].name == "simple-plugin"
        assert manifests[0].version == "2.0.0"

    @pytest.mark.asyncio
    async def test_load_plugin(self, tmp_path):
        plugin_dir = tmp_path / "loadable-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "__init__.py").write_text("""
from core.plugins.interface import EthanPlugin, PluginManifest

MANIFEST = {
    "name": "loadable-plugin",
    "version": "1.0.0",
}

class LoadablePlugin(EthanPlugin):
    manifest = PluginManifest(**MANIFEST)
    
    async def init(self, bus, config):
        self.bus = bus
        self.config = config
    
    async def close(self):
        pass
""")

        loader = PluginLoader(extra_paths=[tmp_path])
        plugin = await loader.load("loadable-plugin", config={"key": "value"})

        assert plugin is not None
        assert plugin.name == "loadable-plugin"
        assert plugin.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_load_all(self, tmp_path):
        # Créer deux plugins
        for name in ["plugin-a", "plugin-b"]:
            plugin_dir = tmp_path / name
            plugin_dir.mkdir()
            (plugin_dir / "__init__.py").write_text(f"""
MANIFEST = {{"name": "{name}", "version": "1.0.0"}}
class Plugin(EthanPlugin):
    manifest = PluginManifest(name="{name}", version="1.0.0")
    async def init(self, bus, config): pass
    async def close(self): pass
""")

        loader = PluginLoader(extra_paths=[tmp_path])
        plugins = await loader.load_all()

        assert len(plugins) == 2
        names = {p.name for p in plugins}
        assert names == {"plugin-a", "plugin-b"}

    @pytest.mark.asyncio
    async def test_load_plugin_not_found(self, tmp_path):
        loader = PluginLoader(extra_paths=[tmp_path])
        plugin = await loader.load("nonexistent")
        assert plugin is None

    def test_get_loaded(self, tmp_path):
        loader = PluginLoader(extra_paths=[tmp_path])
        assert loader.get_loaded("anything") is None
        assert loader.list_loaded() == []


class TestEthanPlugin:
    def test_plugin_interface(self):
        plugin = MockPlugin()
        assert plugin.name == "mock-plugin"
        assert plugin.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_plugin_lifecycle(self):
        plugin = MockPlugin()
        await plugin.init(bus=None, config={"test": True})
        assert plugin.config == {"test": True}
        await plugin.close()