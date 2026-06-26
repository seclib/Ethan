"""ETHAN Plugin Manager — install, remove, list, validate plugins.

Plugin structure (~/.local/share/ethan/plugins/<name>/):
  plugin.py          # Must define ETHAN_PLUGIN
  requirements.txt   # Optional pip dependencies
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

USER_PLUGIN_DIR = Path.home() / ".local" / "share" / "ethan" / "plugins"
ETHAN_API_VERSION = "2"


def _discover_paths() -> list[Path]:
    """Return all plugin paths (built-in + user)."""
    paths = []
    # Built-in: cli/plugins/
    builtin = Path(__file__).parent / "plugins"
    if builtin.exists():
        for p in builtin.iterdir():
            if p.is_dir() and (p / "plugin.py").exists():
                paths.append(p)
    # User: ~/.local/share/ethan/plugins/<name>/
    if USER_PLUGIN_DIR.exists():
        for p in USER_PLUGIN_DIR.iterdir():
            if p.is_dir() and (p / "plugin.py").exists():
                paths.append(p)
    return paths


def _load_plugin(plugin_dir: Path):
    """Load a single plugin from its directory."""
    entry = plugin_dir / "plugin.py"
    if not entry.exists():
        return None
    spec = importlib.util.spec_from_file_location(plugin_dir.name, entry)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return None
    if not hasattr(mod, "ETHAN_PLUGIN"):
        return None
    meta = mod.ETHAN_PLUGIN
    # API version check
    if meta.get("api_version") != ETHAN_API_VERSION:
        print(f"Warning: plugin '{meta.get('name','?')}' requires API v{meta.get('api_version')}, CLI v{ETHAN_API_VERSION}")
        return None
    return meta


def discover() -> list[dict]:
    """Discover all valid plugins and return their metadata."""
    plugins = []
    for path in _discover_paths():
        meta = _load_plugin(path)
        if meta:
            plugins.append(meta)
    return plugins


def validate(plugin_dir: Path) -> dict | None:
    """Validate a single plugin directory. Returns meta or None."""
    return _load_plugin(plugin_dir)


def install(source: str) -> bool:
    """Install a plugin from a path or git URL."""
    dest = USER_PLUGIN_DIR / Path(source).name
    USER_PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

    if source.startswith(("http://", "https://", "git@")):
        # Git clone
        try:
            subprocess.run(["git", "clone", source, str(dest)], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"git clone failed: {e.stderr.decode()}")
            return False
    else:
        # Local path copy
        src = Path(source).expanduser().resolve()
        if not src.exists():
            print(f"Path not found: {src}")
            return False
        shutil.copytree(src, dest, dirs_exist_ok=True)

    # Validate
    meta = validate(dest)
    if meta is None:
        shutil.rmtree(dest)
        print("Plugin validation failed — removed invalid install")
        return False

    # Install pip dependencies
    req_file = dest / "requirements.txt"
    if req_file.exists():
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)], check=True)
        except subprocess.CalledProcessError:
            print("Warning: pip dependencies failed to install")

    print(f"Installed plugin: {meta.get('name','?')} v{meta.get('version','?')}")
    return True


def remove(name: str) -> bool:
    """Remove a user-installed plugin by name."""
    dest = USER_PLUGIN_DIR / name
    if not dest.exists():
        print(f"Plugin '{name}' not found")
        return False
    shutil.rmtree(dest)
    print(f"Removed plugin: {name}")
    return True


def list_installed() -> list[dict]:
    """List user-installed plugins only."""
    if not USER_PLUGIN_DIR.exists():
        return []
    plugins = []
    for p in USER_PLUGIN_DIR.iterdir():
        meta = validate(p)
        if meta:
            plugins.append(meta)
    return plugins