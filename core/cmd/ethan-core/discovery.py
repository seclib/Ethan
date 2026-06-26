"""ETHAN Plugin Discovery System — centralized plugin scanning and registration.

Discovery paths (in order, lower wins):
  1. Built-in:     cli/plugins/<name>/
  2. User local:   ~/.local/share/ethan/plugins/<name>/
  3. System-wide:  /etc/ethan/plugins/<name>/          (if exists)

Lifecycle:
  scan() → for each valid plugin → register capabilities + commands + subscriptions

Versioning:
  - Plugin declares api_version (must match ETHAN_PLUGIN_API = "2")
  - Multiple versions of same plugin: latest wins
  - Version conflicts logged as warnings
  - Schema version evolves independently (backward-compatible changes only)
"""

import importlib.util
import os
import sys
from pathlib import Path

ETHAN_PLUGIN_API = "2"

# Search paths
BUILTIN_DIR = Path(__file__).parent.parent / "cli" / "plugins"
USER_DIR = Path.home() / ".local" / "share" / "ethan" / "plugins"
SYSTEM_DIR = Path("/etc/ethan/plugins")


def _search_paths() -> list[Path]:
    """Return all candidate plugin directories in priority order."""
    paths = []
    if BUILTIN_DIR.exists():
        paths.append(BUILTIN_DIR)
    if USER_DIR.exists():
        paths.append(USER_DIR)
    if SYSTEM_DIR.exists():
        paths.append(SYSTEM_DIR)
    return paths


def _load_module(plugin_dir: Path):
    """Load plugin.py and return parsed metadata or None."""
    entry = plugin_dir / "plugin.py"
    if not entry.exists():
        return None

    spec = importlib.util.spec_from_file_location(plugin_dir.name, entry)
    if spec is None or spec.loader is None:
        return None

    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        return None

    if not hasattr(mod, "ETHAN_PLUGIN"):
        return None

    return getattr(mod, "ETHAN_PLUGIN")


def _validate(meta: dict) -> bool:
    """Validate plugin metadata structure and version."""
    if not isinstance(meta, dict):
        return False
    if "name" not in meta or "version" not in meta:
        return False
    if meta.get("api_version") != ETHAN_PLUGIN_API:
        return False
    return True


# ---- Public API ----


def scan() -> list[dict]:
    """Scan all plugin directories and return validated metadata."""
    plugins = {}
    for base in _search_paths():
        for entry in sorted(base.iterdir()):
            if not entry.is_dir():
                continue
            meta = _load_module(entry)
            if meta is None:
                continue
            if not _validate(meta):
                continue
            name = meta["name"]
            existing = plugins.get(name)
            if existing:
                # Version compare: keep higher version
                if meta.get("version", "0") <= existing.get("version", "0"):
                    continue
            plugins[name] = meta
    return list(plugins.values())


def register_capabilities(meta: dict) -> list[dict]:
    """Extract capability declarations from plugin metadata."""
    return meta.get("capabilities", [])


def register_commands(meta: dict) -> dict:
    """Extract CLI command declarations."""
    return meta.get("commands", {})


def register_subscriptions(meta: dict) -> dict:
    """Extract NATS subscription declarations."""
    return meta.get("subscriptions", {})


def get_handlers(meta: dict) -> dict:
    """Extract memory hook declarations."""
    return meta.get("memory_hooks", {})


def version_info(meta: dict) -> tuple[str, str]:
    """Return (name, version) tuple for dedup."""
    return (meta.get("name", "?"), meta.get("version", "0.0.0"))