"""ETHAN Configuration Manager.

Priority chain:
  1. CLI argument / explicit override
  2. Environment variable
  3. User config file (~/.config/ethan/*)
  4. Default value

Config sources (merged in order):
  ~/.config/ethan/config.json        # User config
  ~/.config/ethan/config.local.json  # Local override (never committed)
  env vars                           # ETHAN_ prefix
"""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "ethan"
CONFIG_FILE = CONFIG_DIR / "config.json"
CONFIG_LOCAL_FILE = CONFIG_DIR / "config.local.json"

# Default configuration
DEFAULTS = {
    "api": {
        "base_url": "http://localhost:8000",
        "timeout": 10,
    },
    "daemon": {
        "interval": 5,
        "enabled": False,
    },
    "memory": {
        "max_entries": 100,
        "max_text": 120,
    },
    "logging": {
        "max_entries": 500,
    },
    "plugins": {
        "user_dir": str(Path.home() / ".local" / "share" / "ethan" / "plugins"),
        "enabled": True,
    },
}


def _ensure():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULTS, f, indent=2)


def _load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _deep_merge(base, override):
    """Recursively merge override into base."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_env():
    """Load ETHAN_ prefixed env vars as config sections."""
    env_config = {}
    for key, value in sorted(os.environ.items()):
        if key.startswith("ETHAN_"):
            parts = key.replace("ETHAN_", "", 1).lower().split("_", 1)
            if len(parts) == 2:
                section, name = parts
                if section not in env_config:
                    env_config[section] = {}
                env_config[section][name] = value
            else:
                env_config[parts[0]] = value
    return env_config


def load():
    """Load and merge all config sources. Returns a dict."""
    _ensure()

    # Priority: defaults → user config → local config → env
    config = dict(DEFAULTS)
    user_cfg = _load_json(CONFIG_FILE)
    local_cfg = _load_json(CONFIG_LOCAL_FILE)
    env_cfg = _load_env()

    config = _deep_merge(config, user_cfg)
    config = _deep_merge(config, local_cfg)
    config = _deep_merge(config, env_cfg)

    return config


def get(key: str, default=None):
    """Get a dot-separated config value, e.g. 'api.base_url'."""
    config = load()
    parts = key.split(".")
    current = config
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
            if current is None:
                return default
        else:
            return default
    return current


def set_value(path: str, value):
    """Set a value in the user config file. path is dot-separated, e.g. 'api.base_url'."""
    _ensure()
    config = _load_json(CONFIG_FILE)
    parts = path.split(".")
    current = config
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value
    tmp = str(CONFIG_FILE) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(config, f, indent=2)
    os.replace(tmp, CONFIG_FILE)


def show():
    """Print the complete merged config."""
    config = load()
    print(json.dumps(config, indent=2))


def reset():
    """Reset user config to defaults."""
    _ensure()
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULTS, f, indent=2)
    if CONFIG_LOCAL_FILE.exists():
        CONFIG_LOCAL_FILE.unlink()