"""Configuration Loader — Chargement hiérarchique de la configuration.

Ordre de priorité (le plus haut gagne) :
1. Variables d'environnement ETHAN_*
2. ~/.config/ethan/config.local.yaml
3. ~/.config/ethan/config.yaml
4. ./ethan.yaml (projet local)
5. Valeurs par défaut (plus basse priorité)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from core.config.schema import (
    BusConfig,
    ConfigSchema,
    RuntimeConfig,
    RuntimeMode,
    StorageConfig,
)

logger = logging.getLogger(__name__)

# Chemins de configuration par ordre de priorité croissante
CONFIG_PATHS = [
    Path("./ethan.yaml"),
    Path.home() / ".config" / "ethan" / "config.yaml",
    Path.home() / ".config" / "ethan" / "config.local.yaml",
]

# Variables d'environnement mappées sur des clés de configuration
# Format: (env_var, (domain, *path_within_domain))
ENV_MAPPINGS: dict[str, tuple[str, ...]] = {
    "ETHAN_MODE": ("runtime", "mode"),
    "ETHAN_BUS_TYPE": ("runtime", "bus", "type"),
    "ETHAN_BUS_SERVERS": ("runtime", "bus", "servers"),
    "ETHAN_REDIS_URL": ("runtime", "storage", "redis_url"),
    "ETHAN_POSTGRES_URL": ("runtime", "storage", "postgres_url"),
    "ETHAN_LOG_LEVEL": ("runtime", "log_level"),
    "ETHAN_DEBUG": ("runtime", "debug"),
    "ETHAN_PLUGINS_DIR": ("runtime", "plugins_dir"),
    "ETHAN_DATA_DIR": ("runtime", "data_dir"),
    # Providers
    "ETHAN_PROVIDER_ACTIVE": ("providers", "active"),
    "ETHAN_OLLAMA_HOST": ("providers", "providers", "ollama", "base_url"),
    "ETHAN_OLLAMA_MODEL": ("providers", "providers", "ollama", "default_model"),
    "ETHAN_OPENAI_API_KEY": ("providers", "providers", "openai", "api_key_env"),
    "ETHAN_OPENAI_BASE_URL": ("providers", "providers", "openai", "base_url"),
    "ETHAN_ANTHROPIC_API_KEY": ("providers", "providers", "anthropic", "api_key_env"),
    # Models
    "ETHAN_MODEL_DEFAULT": ("models", "default"),
    "ETHAN_MODEL_ROUTING_REASONING": ("models", "routing", "reasoning"),
    "ETHAN_MODEL_ROUTING_CODE": ("models", "routing", "code"),
    "ETHAN_MODEL_ROUTING_FAST": ("models", "routing", "fast"),
    # RAG
    "ETHAN_RAG_ENABLED": ("rag", "enabled"),
    "ETHAN_RAG_CHUNK_SIZE": ("rag", "chunk_size"),
    "ETHAN_RAG_TOP_K": ("rag", "top_k"),
    "ETHAN_RAG_EMBEDDING_MODEL": ("rag", "embedding_model"),
    # Memory
    "ETHAN_MEMORY_ENABLED": ("memory", "enabled"),
    "ETHAN_MEMORY_MAX_FACTS": ("memory", "max_facts"),
    "ETHAN_MEMORY_TTL_DAYS": ("memory", "ttl_days"),
    # Agents
    "ETHAN_AGENTS_MAX_CONCURRENT": ("agents", "max_concurrent"),
    "ETHAN_AGENTS_TIMEOUT": ("agents", "default_timeout_seconds"),
    # Planner
    "ETHAN_PLANNER_MAX_DEPTH": ("planner", "max_depth"),
    "ETHAN_PLANNER_MAX_STEPS": ("planner", "max_steps"),
    # Plugins
    "ETHAN_PLUGINS_AUTO_LOAD": ("plugins", "auto_load"),
    "ETHAN_PLUGINS_SANDBOX": ("plugins", "sandbox_enabled"),
    # Authentication
    "ETHAN_AUTH_ENABLED": ("authentication", "enabled"),
    "ETHAN_AUTH_JWT_SECRET": ("authentication", "jwt_secret_env"),
    "ETHAN_AUTH_JWT_EXPIRY": ("authentication", "jwt_expiry_hours"),
    "ETHAN_AUTH_RBAC": ("authentication", "rbac_enabled"),
}


class ConfigLoader:
    """Chargeur de configuration avec surcharge hiérarchique.

    Args:
        paths: Liste de chemins YAML à charger (par défaut CONFIG_PATHS)
        overrides: Surcharges programmatiques (venant du CLI par exemple)
    """

    def __init__(
        self,
        paths: list[Path] | None = None,
        overrides: dict[str, Any] | None = None,
    ):
        self._paths = paths or CONFIG_PATHS
        self._overrides = overrides or {}

    def load(self) -> ConfigSchema:
        """Charge la configuration complète.

        Returns:
            ConfigSchema validée
        """
        config = self._default_config()

        # 1. Charger les fichiers YAML (du moins prioritaire au plus prioritaire)
        for path in reversed(self._paths):
            if path.exists():
                try:
                    self._merge_yaml(config, path)
                    logger.debug("Loaded config from %s", path)
                except Exception as e:
                    logger.warning("Failed to load %s: %s", path, e)

        # 2. Surcharger avec les variables d'environnement
        self._merge_env(config)

        # 3. Surcharger avec les overrides programmatiques
        if self._overrides:
            self._merge_dict(config, self._overrides)

        # 4. Appliquer le mode auto
        if config.runtime.mode == RuntimeMode.AUTO:
            config.runtime.mode = self._detect_mode()

        return config

    def _default_config(self) -> ConfigSchema:
        """Configuration par défaut."""
        return ConfigSchema()

    def _merge_yaml(self, config: ConfigSchema, path: Path) -> None:
        """Merge un fichier YAML dans la configuration."""
        try:
            import yaml
        except ImportError:
            logger.warning("PyYAML not installed, skipping YAML config")
            return

        with open(path) as f:
            data = yaml.safe_load(f)
            if data and isinstance(data, dict):
                self._merge_dict(config, data)

    def _merge_env(self, config: ConfigSchema) -> None:
        """Merge les variables d'environnement ETHAN_*."""
        for env_var, path_tuple in ENV_MAPPINGS.items():
            value = os.getenv(env_var)
            if value is None:
                continue

            # Naviguer dans le nested dataclass pour trouver l'endroit où écrire
            target: Any = config
            for key in path_tuple[:-1]:
                if hasattr(target, key):
                    target = getattr(target, key)
                else:
                    break
            else:
                last_key = path_tuple[-1]
                if hasattr(target, last_key):
                    setattr(target, last_key, self._cast(value, last_key, target))

    def _merge_dict(self, config: ConfigSchema, data: dict[str, Any], prefix: str = "") -> None:
        """Merge récursif d'un dict dans la config (dataclass)."""
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict) and hasattr(config, key):
                child = getattr(config, key)
                if child is not None and hasattr(child, "__dict__"):
                    self._merge_dict(child, value, full_key)
                    continue
            if hasattr(config, key):
                setattr(config, key, value)

    def _detect_mode(self) -> RuntimeMode:
        """Détecte le mode d'exécution.

        Si NATS est reachable → DISTRIBUTED
        Sinon → STANDALONE
        """
        import asyncio

        async def _probe():
            try:
                import nats
                nc = await asyncio.wait_for(
                    nats.connect(
                        "nats://localhost:4222",
                        timeout=2,
                        name="ethan-probe",
                    ),
                    timeout=2,
                )
                await asyncio.wait_for(nc.close(), timeout=2)
                return True
            except Exception as exc:
                logger.debug("NATS mode probe failed; using standalone mode: %s", exc, exc_info=True)
                return False

        try:
            reachable = asyncio.run(_probe())
            if reachable:
                logger.info("NATS reachable → distributed mode")
                return RuntimeMode.DISTRIBUTED
        except Exception as exc:
            logger.debug("NATS mode detection failed; using standalone mode: %s", exc, exc_info=True)

        logger.info("NATS not reachable → standalone mode")
        return RuntimeMode.STANDALONE

    def _cast(self, value: str, attr_name: str, target: Any) -> Any:
        """Convertit une string en type approprié."""
        # Booléens
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # RuntimeMode
        if "mode" in attr_name.lower():
            try:
                return RuntimeMode(value)
            except ValueError:
                return RuntimeMode.AUTO

        # Ints
        try:
            return int(value)
        except (ValueError, TypeError):
            pass

        # Floats
        try:
            return float(value)
        except (ValueError, TypeError):
            pass

        return value
