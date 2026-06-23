"""Tests — Plugin Discovery & Loading (ADR-1008)"""

import pytest
import asyncio
from pathlib import Path
import shutil
import tempfile
from unittest.mock import MagicMock, AsyncMock

from core.plugins import Plugin, PluginRegistry, PluginMetadata, PluginContext

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
            capabilities=["test.cap"]
        )

    async def initialize(self, context: PluginContext) -> None:
        pass

    async def shutdown(self) -> None:
        pass

class TestPluginRegistry:
    """Tests for PluginRegistry."""

    @pytest.fixture
    def registry(self):
        return PluginRegistry()

    @pytest.fixture
    def temp_plugin_dir(self):
        """Creates a temporary directory for plugins."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_registry_empty(self, registry):
        """Test registry is empty on initialization."""
        assert len(registry) == 0
        assert registry.list_plugins() == []

    @pytest.mark.asyncio
    async def test_discover_no_plugins(self, registry, temp_plugin_dir):
        """Test discovery with no plugins."""
        await registry.discover([temp_plugin_dir])
        assert len(registry) == 0

    @pytest.mark.asyncio
    async def test_discover_single_plugin(self, registry, temp_plugin_dir):
        """Test discovery of a single plugin file."""
        # Create a plugin file
        plugin_file = temp_plugin_dir / "my_plugin.py"
        plugin_file.write_text(
            "from core.plugins import Plugin, PluginMetadata\n"
            "class MyPlugin(Plugin):\n"
            "    def get_metadata(self):\n"
            "        return PluginMetadata('my-plugin', '1.0.0', 'Desc', 'Auth', ['cap1'])\n"
            "    async def initialize(self, ctx): pass\n"
            "    async def shutdown(self): pass\n"
        )

        await registry.discover([temp_plugin_dir])
        assert len(registry) == 1
        assert "my-plugin" in registry.list_plugins()
        assert registry.get_plugin("my-plugin") is not None

    @pytest.mark.asyncio
    async def test_discover_init_file_plugin(self, registry, temp_plugin_dir):
        """Test discovery of a plugin in a package (__init__.py)."""
        plugin_dir = temp_plugin_dir / "plugin_pkg"
        plugin_dir.mkdir()
        init_file = plugin_dir / "__init__.py"
        init_file.write_text(
            "from core.plugins import Plugin, PluginMetadata\n"
            "class PkgPlugin(Plugin):\n"
            "    def get_metadata(self):\n"
            "        return PluginMetadata('pkg-plugin', '1.0.0', 'Desc', 'Auth', ['cap1'])\n"
            "    async def initialize(self, ctx): pass\n"
            "    async def shutdown(self): pass\n"
        )

        await registry.discover([temp_plugin_dir])
        assert len(registry) == 1
        assert "pkg-plugin" in registry.list_plugins()

    @pytest.mark.asyncio
    async def test_discover_multiple_plugins(self, registry, temp_plugin_dir):
        """Test discovery of multiple plugins."""
        # Plugin 1
        (temp_plugin_dir / "p1.py").write_text(
            "from core.plugins import Plugin, PluginMetadata\n"
            "class P1(Plugin):\n"
            "    def get_metadata(self):\n"
            "        return PluginMetadata('p1', '1.0', 'D', 'A', [])\n"
            "    async def initialize(self, ctx): pass\n"
            "    async def shutdown(self): pass\n"
        )
        # Plugin 2
        (temp_plugin_dir / "p2.py").write_text(
            "from core.plugins import Plugin, PluginMetadata\n"
            "class P2(Plugin):\n"
            "    def get_metadata(self):\n"
            "        return PluginMetadata('p2', '1.0', 'D', 'A', [])\n"
            "    async def initialize(self, ctx): pass\n"
            "    async def shutdown(self): pass\n"
        )

        await registry.discover([temp_plugin_dir])
        assert len(registry) == 2
        assert set(registry.list_plugins()) == {"p1", "p2"}

    @pytest.mark.asyncio
    async def test_discover_invalid_plugin(self, registry, temp_plugin_dir):
        """Test discovery ignores invalid python files."""
        (temp_plugin_dir / "invalid.py").write_text("print('hello')")
        
        await registry.discover([temp_plugin_dir])
        assert len(registry) == 0

    def test_get_nonexistent_plugin(self, registry):
        """Test getting a plugin that doesn't exist."""
        assert registry.get_plugin("ghost") is None
        assert registry.get_metadata("ghost") is None