from __future__ import annotations

"""ETHAN Plugin Loader — full plugin lifecycle management.

Handles manifest.json parsing, entry point loading, capability registration,
command registration, permission validation, memory hooks binding,
and event subscription binding.

Usage:
    loader = PluginLoader()
    loader.load_all()   # scan + load all plugins
    loader.load(name)   # load single plugin
"""

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

ETHAN_PLUGIN_API = "2"

# Discovery paths
BUILTIN_DIR = Path(__file__).parent.parent / "cli" / "plugins"
USER_DIR = Path.home() / ".local" / "share" / "ethan" / "plugins"
SYSTEM_DIR = Path("/etc/ethan/plugins")


# ---- Permission model ----


class Permission:
    """Permission pattern validator."""

    LEVELS = {"none": 0, "read": 1, "write": 2, "execute": 3, "admin": 4}

    @staticmethod
    def validate(pattern: str) -> bool:
        parts = pattern.split(":")
        if len(parts) < 2:
            return False
        resource = parts[0]
        action = parts[1]
        return resource in ("state", "filesystem", "network", "execute") and action in Permission.LEVELS

    @staticmethod
    def check(required: list[str], granted: list[str]) -> bool:
        for req in required:
            # Exact match or glob: check granted patterns
            if not any(Permission._matches(req, g) for g in granted):
                return False
        return True

    @staticmethod
    def _matches(pattern: str, granted: str) -> bool:
        # Simple glob: * matches any segment, ** matches any depth
        import fnmatch
        return fnmatch.fnmatch(pattern, granted)


# ---- Plugin metadata ----


class PluginMeta:
    """Parsed and validated plugin metadata."""

    def __init__(self, manifest: dict, module: Any):
        self.name: str = manifest.get("name", "")
        self.version: str = manifest.get("version", "0.0.0")
        self.api_version: str = manifest.get("api_version", "")
        self.description: str = manifest.get("description", "")
        self.author: str = manifest.get("author", "")
        self.license: str = manifest.get("license", "")
        self.capabilities: list[dict] = manifest.get("capabilities", [])
        self.commands: dict = manifest.get("commands", {})
        self.memory_hooks: dict = manifest.get("memory_hooks", {})
        self.subscriptions: dict = manifest.get("subscriptions", {})
        self.permissions: list[str] = manifest.get("permissions", [])
        self.dependencies: dict = manifest.get("dependencies", {})
        self.module = module  # python module object

    def validate(self) -> list[str]:
        errors = []
        if not self.name:
            errors.append("missing name")
        if not self.version:
            errors.append("missing version")
        if self.api_version != ETHAN_PLUGIN_API:
            errors.append(f"api_version mismatch: {self.api_version} != {ETHAN_PLUGIN_API}")
        for perm in self.permissions:
            if not Permission.validate(perm):
                errors.append(f"invalid permission pattern: {perm}")
        for cap in self.capabilities:
            if not cap.get("name"):
                errors.append(f"capability missing name: {cap}")
        for cmd_name, cmd in self.commands.items():
            if not cmd.get("handler"):
                errors.append(f"command '{cmd_name}' missing handler")
            elif not hasattr(self.module, cmd["handler"]):
                errors.append(f"command '{cmd_name}' handler '{cmd['handler']}' not found in plugin.py")
        for subj, handler in self.subscriptions.items():
            if not hasattr(self.module, handler):
                errors.append(f"subscription '{subj}' handler '{handler}' not found in plugin.py")
        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0


# ---- Plugin Loader ----


class PluginLoader:
    """Scans, loads, and validates plugins."""

    def __init__(self):
        self._plugins: dict[str, PluginMeta] = {}

    def _search_paths(self) -> list[Path]:
        paths = []
        if BUILTIN_DIR.exists():
            paths.append(BUILTIN_DIR)
        if USER_DIR.exists():
            paths.append(USER_DIR)
        if SYSTEM_DIR.exists():
            paths.append(SYSTEM_DIR)
        return paths

    def _load_manifest(self, plugin_dir: Path) -> dict | None:
        manifest_path = plugin_dir / "manifest.json"
        if not manifest_path.exists():
            return None
        try:
            with open(manifest_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def _load_entry_point(self, plugin_dir: Path, manifest: dict) -> Any | None:
        # Try plugin.py first, then fallback to inline ETHAN_PLUGIN
        entry = plugin_dir / "plugin.py"
        if not entry.exists():
            return None

        spec = importlib.util.spec_from_file_location(manifest.get("name", plugin_dir.name), entry)
        if spec is None or spec.loader is None:
            return None

        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception:
            return None
        return mod

    def _resolve_version(self, name: str, version: str, existing: PluginMeta | None) -> bool:
        """Returns True if this version should replace existing."""
        if existing is None:
            return True
        # Higher version wins
        return version > existing.version

    def load(self, name: str) -> PluginMeta | None:
        """Load a single plugin by name from any discovery path."""
        for base in self._search_paths():
            plugin_dir = base / name
            if not plugin_dir.is_dir():
                continue
            manifest = self._load_manifest(plugin_dir)
            if manifest is None:
                continue
            module = self._load_entry_point(plugin_dir, manifest)
            if module is None:
                continue
            meta = PluginMeta(manifest, module)
            if not meta.is_valid():
                continue
            if not self._resolve_version(meta.name, meta.version, self._plugins.get(meta.name)):
                continue
            self._plugins[meta.name] = meta
            return meta
        return None

    def load_all(self) -> list[PluginMeta]:
        """Scan all paths and load all valid plugins."""
        loaded = []
        for base in self._search_paths():
            for entry in sorted(base.iterdir()):
                if not entry.is_dir():
                    continue
                meta = self.load(entry.name)
                if meta:
                    loaded.append(meta)
        return loaded

    def get(self, name: str) -> PluginMeta | None:
        return self._plugins.get(name)

    def list(self) -> list[PluginMeta]:
        return list(self._plugins.values())

    def extract_capabilities(self, meta: PluginMeta) -> list[dict]:
        """Return capability declarations for registry registration."""
        return meta.capabilities

    def extract_commands(self, meta: PluginMeta) -> dict:
        """Return CLI command declarations."""
        return meta.commands

    def extract_subscriptions(self, meta: PluginMeta) -> dict:
        """Return NATS subscription declarations."""
        return meta.subscriptions

    def extract_memory_hooks(self, meta: PluginMeta) -> dict:
        """Return memory hook declarations."""
        return meta.memory_hooks

    def check_permissions(self, meta: PluginMeta, granted: list[str]) -> bool:
        """Check if plugin's required permissions are satisfied."""
        return Permission.check(meta.permissions, granted)