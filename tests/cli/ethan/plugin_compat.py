"""Plugin compatibility checker — ensure plugins load correctly."""
import importlib.util
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PluginCheckResult:
    """Result of plugin compatibility check."""
    plugin: str
    loaded: bool
    version: str = "?"
    commands: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class PluginCompatibilityChecker:
    """Check plugin loading and compatibility."""

    def __init__(self):
        self.results: List[PluginCheckResult] = []

    def check_all(self) -> List[PluginCheckResult]:
        """Check all discoverable plugins.

        Returns:
            List of PluginCheckResult
        """
        self.results = []

        # Check builtin plugins
        self._check_directory(Path("cli/plugins"))

        # Check user plugins
        user_dir = Path.home() / ".local" / "share" / "ethan" / "plugins"
        if user_dir.exists():
            self._check_directory(user_dir)

        return self.results

    def _check_directory(self, directory: Path):
        """Check all plugins in a directory."""
        if not directory.exists():
            return

        for plugin_dir in sorted(directory.iterdir()):
            if not plugin_dir.is_dir():
                continue

            result = self._check_plugin(plugin_dir)
            self.results.append(result)

    def _check_plugin(self, plugin_dir: Path) -> PluginCheckResult:
        """Check single plugin."""
        plugin_file = plugin_dir / "plugin.py"
        plugin_name = plugin_dir.name

        # Check 1: plugin.py exists
        if not plugin_file.exists():
            return PluginCheckResult(
                plugin=plugin_name,
                loaded=False,
                errors=["plugin.py not found"],
            )

        # Check 2: Can import
        try:
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for {plugin_name}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            return PluginCheckResult(
                plugin=plugin_name,
                loaded=False,
                errors=[f"Import error: {e}"],
            )

        # Check 3: Has ETHAN_PLUGIN dict
        if not hasattr(module, "ETHAN_PLUGIN"):
            return PluginCheckResult(
                plugin=plugin_name,
                loaded=False,
                errors=["Missing ETHAN_PLUGIN dict"],
            )

        plugin_info = module.ETHAN_PLUGIN

        # Check 4: Valid version
        version = plugin_info.get("version", "?")

        # Check 5: Commands are callable
        commands = []
        errors = []
        for cmd_name, cmd_info in plugin_info.get("commands", {}).items():
            handler = cmd_info.get("handler")
            if not callable(handler):
                errors.append(f"Command '{cmd_name}' handler not callable")
            else:
                commands.append(cmd_name)

        return PluginCheckResult(
            plugin=plugin_name,
            loaded=True,
            version=version,
            commands=commands,
            errors=errors,
        )

    def get_summary(self) -> str:
        """Get summary of plugin check results."""
        total = len(self.results)
        loaded = sum(1 for r in self.results if r.loaded)
        failed = total - loaded

        lines = [
            f"Plugin Compatibility Summary",
            f"  Total: {total}",
            f"  Loaded: {loaded}",
            f"  Failed: {failed}",
        ]

        if failed > 0:
            lines.append("")
            lines.append("Failed plugins:")
            for result in self.results:
                if not result.loaded:
                    errors = ", ".join(result.errors)
                    lines.append(f"  {result.plugin}: {errors}")

        return "\n".join(lines)