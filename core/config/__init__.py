"""ETHAN Core — Configuration système.

Source de vérité unique pour toute la configuration ETHAN.
Toutes les interfaces (Runtime, Core, CLI, WebUI, Desktop) utilisent
le même service de configuration.

Chargement hiérarchique :
1. Arguments CLI (plus haute priorité)
2. Variables d'environnement (ETHAN_*)
3. Fichier de config local (~/.config/ethan/config.local.yaml)
4. Fichier de config utilisateur (~/.config/ethan/config.yaml)
5. Fichier de config projet (./ethan.yaml)
6. Valeurs par défaut (plus basse priorité)

Domaines gérés :
- providers
- models
- rag
- memory
- agents
- planner
- plugins
- authentication
- runtime
"""

from .loader import ConfigLoader, ENV_MAPPINGS
from .schema import (
    ConfigSchema,
    RuntimeConfig,
    RuntimeMode,
    BusConfig,
    StorageConfig,
    ProviderConfig,
    ProvidersConfig,
    ModelRoutingConfig,
    ModelsConfig,
    RAGConfig,
    MemoryConfig,
    AgentsConfig,
    AgentConfig,
    PlannerConfig,
    PluginsConfig,
    AuthenticationConfig,
)
from .service import ConfigurationService, DOMAINS
from .store import ConfigStore
from .secrets import Secrets, get_secrets
from .prompts import PromptManager
from .jsonschema import config_to_json_schema, get_domains

__all__ = [
    # Loader
    "ConfigLoader",
    "ENV_MAPPINGS",
    # Schema
    "ConfigSchema",
    "RuntimeConfig",
    "RuntimeMode",
    "BusConfig",
    "StorageConfig",
    "ProviderConfig",
    "ProvidersConfig",
    "ModelRoutingConfig",
    "ModelsConfig",
    "RAGConfig",
    "MemoryConfig",
    "AgentsConfig",
    "AgentConfig",
    "PlannerConfig",
    "PluginsConfig",
    "AuthenticationConfig",
    # Service
    "ConfigurationService",
    "DOMAINS",
    # Store
    "ConfigStore",
    # Secrets
    "Secrets",
    "get_secrets",
    # Prompts
    "PromptManager",
    # JSON Schema
    "config_to_json_schema",
    "get_domains",
]
