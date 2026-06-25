"""Configuration Loader — Chargement hiérarchique de la configuration.

Ordre de priorité (le plus haut gagne) :
1. Variables d'environnement ETHAN_*
2. ~/.config/ethan/config.local.yaml
3. ~/.config/ethan/config.yaml
4. ./ethan.yaml (projet local)
5. Défauts
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from core.config.schema import (
    AgentConfig,
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


class ConfigLoader:
    """Chargeur de configuration avec surcharge hiérarchique."""

    def __init__(self, paths: list[Path] | None = None):
        self._paths = paths or CONFIG_PATHS

    def load(self, overrides: dict[str, Any] | None = None) -> ConfigSchema:
        """Charge la configuration complète.

        Args:
            overrides: Surcharges programmatiques (venant du CLI par exemple)

        Returns:
            ConfigSchema validée
        """
        config = self._default_config()

        # 1. Charger les fichiers YAML (du plus prioritaire au moins)
        for path in reversed(self._paths):
            if path.exists():
                try:
                    self._merge_yaml(config, path)
                    logger.debug(f"Loaded config from {path}")
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

        # 2. Surcharger avec les variables d'environnement
        self._merge_env(config)

        # 3. Surcharger avec les overrides programmatiques
        if overrides:
            self._merge_dict(config, overrides)

        # 4. Appliquer le mode auto
        if config.runtime.mode == RuntimeMode.AUTO:
            config.runtime.mode = self._detect_mode()

        return config

    def _default_config(self) -> ConfigSchema:
        """Configuration par défaut."""
        return ConfigSchema(
            runtime=RuntimeConfig(
                mode=RuntimeMode.AUTO,
                bus=BusConfig(type="auto", servers="nats://localhost:4222"),
                storage=StorageConfig(
                    redis_url="redis://localhost:6379/0",
                    postgres_url="postgresql://ethan:ethan@localhost:5432/ethan",
                ),
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                debug=False,
            )
        )

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
        env = {
            "ETHAN_MODE": ("runtime", "mode"),
            "ETHAN_BUS_TYPE": ("runtime", "bus", "type"),
            "ETHAN_BUS_SERVERS": ("runtime", "bus", "servers"),
            "ETHAN_REDIS_URL": ("runtime", "storage", "redis_url"),
            "ETHAN_POSTGRES_URL": ("runtime", "storage", "postgres_url"),
            "ETHAN_LOG_LEVEL": ("runtime", "log_level"),
            "ETHAN_DEBUG": ("runtime", "debug"),
            "ETHAN_PLUGINS_DIR": ("runtime", "plugins_dir"),
            "ETHAN_DATA_DIR": ("runtime", "data_dir"),
        }

        for env_var, path in env.items():
            value = os.getenv(env_var)
            if value is None:
                continue

            # Naviguer dans le nested dict pour trouver l'endroit où écrire
            target = config
            for key in path[:-1]:
                target = getattr(target, key, {})
            setattr(target, path[-1], self._cast(value, path[-1], target))

    def _merge_dict(self, config: ConfigSchema, data: dict, prefix: str = "") -> None:
        """Merge récursif d'un dict dans la config."""
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict) and hasattr(config, key):
                child = getattr(config, key)
                if child is not None:
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
                nc = await nats.connect(
                    "nats://localhost:4222",
                    timeout=2,
                    name="ethan-probe",
                )
                await nc.close()
                return True
            except Exception:
                return False

        try:
            reachable = asyncio.run(_probe())
            if reachable:
                logger.info("NATS reachable → distributed mode")
                return RuntimeMode.DISTRIBUTED
        except Exception:
            pass

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

        return value