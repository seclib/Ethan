"""ETHAN CLI — Configuration Manager.

Source unique de vérité : `docs/specs/CLI_CONTRACT.md` §6 (configuration,
fichiers XDG, profils, variables d'environnement, gestion stricte des secrets).

Délègue au ConfigurationService centralisé (core/config/service.py) pour les
domaines métier et gère les profils et les credentials locaux (0600).

Priority chain :
  1. CLI argument / explicit override
  2. Environment variable
  3. User config file (~/.config/ethan/* ou ETHAN_CONFIG_DIR)
  4. Default value
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from core.config import ConfigurationService, ConfigStore


def get_config_dir() -> Path:
    """Return the active configuration directory following XDG and ETHAN_CONFIG_DIR."""
    if "ETHAN_CONFIG_DIR" in os.environ:
        return Path(os.environ["ETHAN_CONFIG_DIR"]).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg).expanduser() / "ethan"
    return Path.home() / ".config" / "ethan"


CONFIG_DIR = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.json"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
CONFIG_LOCAL_FILE = CONFIG_DIR / "config.local.json"

# Default configuration (CLI-specific, not business logic)
DEFAULTS: dict[str, Any] = {
    "current_profile": "default",
    "profiles": {
        "default": {
            "api_url": "http://localhost:8000",
            "timeout": 5.0,
            "output": "human",
        }
    },
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

# Instance globale du service de configuration centralisé
_service: ConfigurationService | None = None


def _get_service() -> ConfigurationService:
    """Retourne le ConfigurationService global (lazy init)."""
    global _service
    if _service is None:
        _service = ConfigurationService(store=ConfigStore())
    return _service


def _ensure():
    Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)
    if not Path(CONFIG_FILE).exists():
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
    env_config: dict[str, Any] = {}
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
    """Get a dot-separated config value, e.g. 'api.base_url'.

    Délègue au ConfigurationService centralisé pour les domaines métier
    (providers, models, rag, memory, agents, planner, plugins, authentication).
    Pour les clés CLI-spécifiques, utilise le fichier local.
    """
    business_domains = (
        "providers",
        "models",
        "rag",
        "memory",
        "agents",
        "planner",
        "plugins",
        "authentication",
        "runtime",
    )
    first = key.split(".")[0]
    if first in business_domains:
        try:
            service = _get_service()
            return service.get(key, default)
        except Exception:
            pass

    # CLI-specific → fichier local
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
    if Path(CONFIG_LOCAL_FILE).exists():
        Path(CONFIG_LOCAL_FILE).unlink()


# ── Profile Management (CLI_CONTRACT §6.3) ─────────────────────────


def get_active_profile_name() -> str:
    """Return the active profile name."""
    if "ETHAN_PROFILE" in os.environ:
        return os.environ["ETHAN_PROFILE"]
    cfg = load()
    return cfg.get("current_profile", "default")


def set_active_profile(name: str) -> None:
    """Set the current profile in config.json."""
    set_value("current_profile", name)


def get_profile(name: str | None = None) -> dict[str, Any]:
    """Retrieve profile configuration (endpoint, timeout, output format)."""
    cfg = load()
    p_name = name or get_active_profile_name()
    profiles = cfg.get("profiles", {})
    profile_data = dict(profiles.get(p_name, {}))
    if not profile_data and p_name == "default":
        profile_data = {
            "api_url": cfg.get("api", {}).get("base_url", "http://localhost:8000"),
            "timeout": cfg.get("api", {}).get("timeout", 5.0),
            "output": "human",
        }
    return profile_data


def set_profile(name: str, values: dict[str, Any]) -> None:
    """Create or update a profile in config.json."""
    _ensure()
    config = _load_json(CONFIG_FILE)
    if "profiles" not in config:
        config["profiles"] = {}
    config["profiles"][name] = values
    tmp = str(CONFIG_FILE) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(config, f, indent=2)
    os.replace(tmp, CONFIG_FILE)


def list_profiles() -> dict[str, dict[str, Any]]:
    """List all configured profiles."""
    cfg = load()
    return cfg.get("profiles", {"default": get_profile("default")})


# ── Credentials & Secrets Management (CLI_CONTRACT §6.1, §6.4, 0600) ──


def _get_credentials_path() -> Path:
    if hasattr(CONFIG_DIR, "mkdir"):
        return Path(CONFIG_DIR) / "credentials.json"
    return Path(CREDENTIALS_FILE)


def _read_credentials_file() -> dict[str, Any]:
    cred_file = _get_credentials_path()
    if not cred_file.exists():
        return {}
    try:
        # Enforce 0600 permissions
        mode = cred_file.stat().st_mode & 0o777
        if mode != 0o600:
            try:
                os.chmod(str(cred_file), 0o600)
            except OSError:
                pass
        with open(cred_file) as f:
            return json.load(f)
    except Exception:
        return {}


def _write_credentials_file(data: dict[str, Any]) -> None:
    cred_file = _get_credentials_path()
    cred_file.parent.mkdir(parents=True, exist_ok=True)
    raw_bytes = json.dumps(data, indent=2).encode("utf-8")
    fd = os.open(str(cred_file), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, raw_bytes)
    finally:
        os.close(fd)
    os.chmod(str(cred_file), 0o600)


def get_token_from_credentials(profile: str | None = None) -> str | None:
    """Retrieve stored JWT token for a given profile from credentials.json."""
    creds = _read_credentials_file()
    p_name = profile or get_active_profile_name()
    profiles = creds.get("profiles", {})
    if isinstance(profiles, dict) and p_name in profiles:
        p_val = profiles[p_name]
        if isinstance(p_val, dict):
            return p_val.get("token")
        if isinstance(p_val, str):
            return p_val
    # Top-level token is only fallback for default profile
    if p_name == "default" and "token" in creds and isinstance(creds["token"], str):
        return creds["token"]
    return None


def set_credentials_token(
    token: str,
    profile: str | None = None,
    expires_at: str | None = None,
) -> None:
    """Store JWT token in credentials.json with 0600 permissions."""
    p_name = profile or get_active_profile_name()
    creds = _read_credentials_file()
    if "profiles" not in creds or not isinstance(creds["profiles"], dict):
        creds["profiles"] = {}
    entry: dict[str, Any] = {"token": token}
    if expires_at:
        entry["expires_at"] = expires_at
    creds["profiles"][p_name] = entry
    if p_name == "default":
        creds["token"] = token
    _write_credentials_file(creds)


def clear_credentials(profile: str | None = None) -> None:
    """Remove stored credentials for a profile (or all if profile=None)."""
    p_name = profile or get_active_profile_name()
    creds = _read_credentials_file()
    if profile is None:
        creds = {}
    else:
        if "profiles" in creds and p_name in creds["profiles"]:
            del creds["profiles"][p_name]
        if p_name == "default":
            creds.pop("token", None)
    _write_credentials_file(creds)
