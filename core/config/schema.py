"""Configuration Schema — Validation Pydantic des configurations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RuntimeMode(str, Enum):
    """Mode d'exécution du runtime."""
    AUTO = "auto"           # Détection : NATS si dispo, sinon in-memory
    STANDALONE = "standalone"  # InMemoryBus, mono-processus
    DISTRIBUTED = "distributed" # NATS, kernel + workers


@dataclass
class BusConfig:
    """Configuration du bus d'événements."""
    type: str = "auto"  # "inmemory", "nats", "auto"
    servers: str = "nats://localhost:4222"
    record_history: bool = True
    max_history: int = 10000


@dataclass
class StorageConfig:
    """Configuration du stockage."""
    redis_url: str = "redis://localhost:6379/0"
    redis_prefix: str = "ethan:"
    postgres_url: str = "postgresql://ethan:ethan@localhost:5432/ethan"
    pgvector_enabled: bool = False
    pgvector_dimension: int = 768


@dataclass
class AgentConfig:
    """Configuration d'un agent."""
    name: str = ""
    enabled: bool = True
    model: str | None = None
    provider: str | None = None
    temperature: float = 0.7
    max_iterations: int = 10
    timeout: int = 300
    auto_start: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeConfig:
    """Configuration complète du runtime."""
    mode: RuntimeMode = RuntimeMode.AUTO
    bus: BusConfig = field(default_factory=BusConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    agents: dict[str, AgentConfig] = field(default_factory=dict)
    log_level: str = "INFO"
    debug: bool = False
    plugins_dir: str = "~/.ethan/plugins"
    data_dir: str = "~/.ethan/data"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigSchema:
    """Point d'entrée de la configuration."""
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)