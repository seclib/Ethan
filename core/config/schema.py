"""Configuration Schema — Validation et types pour toute la configuration ETHAN.

Source de vérité unique pour la configuration. Toutes les interfaces
(Runtime, Core, CLI, WebUI, Desktop) utilisent ce schéma.

Domaines gérés :
- providers  : configuration des fournisseurs LLM
- models     : routage et sélection des modèles
- rag        : ingestion, embeddings, retrieval, contexte
- memory     : gestion de la mémoire / faits
- agents     : configuration des agents cognitifs
- planner    : planification de tâches
- plugins    : gestion des plugins
- authentication : JWT, RBAC, OAuth
- runtime    : bus, stockage, mode d'exécution
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RuntimeMode(str, Enum):
    """Mode d'exécution du runtime."""
    AUTO = "auto"           # Détection : NATS si dispo, sinon in-memory
    STANDALONE = "standalone"  # InMemoryBus, mono-processus
    DISTRIBUTED = "distributed" # NATS, kernel + workers


# ─────────────────────────────────────────────────────────────────────────────
# Runtime (infrastructure)
# ─────────────────────────────────────────────────────────────────────────────

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
class RuntimeConfig:
    """Configuration du runtime (infrastructure)."""
    mode: RuntimeMode = RuntimeMode.AUTO
    bus: BusConfig = field(default_factory=BusConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    log_level: str = "INFO"
    debug: bool = False
    plugins_dir: str = "~/.ethan/plugins"
    data_dir: str = "~/.ethan/data"
    metadata: dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Providers LLM
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ProviderConfig:
    """Configuration d'un fournisseur LLM individuel.

    Les clés API ne sont JAMAIS stockées ici — elles proviennent de
    ``core/config/secrets.py`` (env / Vault / Docker secrets).
    """
    name: str = ""
    type: str = ""
    enabled: bool = False
    base_url: str = ""
    default_model: str = ""
    display_name: str = ""
    api_key_env: str = ""
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProvidersConfig:
    """Configuration globale des providers LLM."""
    active: str = "ollama"
    providers: dict[str, ProviderConfig] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Seed les providers par défaut si le dict est vide."""
        if not self.providers:
            self.providers = {
                "ollama": ProviderConfig(
                    name="ollama",
                    type="ollama",
                    enabled=True,
                    base_url="http://localhost:11434",
                    default_model="llama3.1",
                    display_name="Ollama (local)",
                ),
                "openai": ProviderConfig(
                    name="openai",
                    type="openai",
                    enabled=False,
                    base_url="https://api.openai.com/v1",
                    default_model="gpt-4o-mini",
                    display_name="OpenAI",
                    api_key_env="OPENAI_API_KEY",
                ),
                "anthropic": ProviderConfig(
                    name="anthropic",
                    type="anthropic",
                    enabled=False,
                    default_model="claude-3-5-sonnet-20241022",
                    display_name="Anthropic Claude",
                    api_key_env="ANTHROPIC_API_KEY",
                ),
                "vllm": ProviderConfig(
                    name="vllm",
                    type="vllm",
                    enabled=False,
                    base_url="http://vllm:8000",
                    display_name="vLLM (local)",
                ),
                "gemini": ProviderConfig(
                    name="gemini",
                    type="gemini",
                    enabled=False,
                    default_model="gemini-1.5-flash",
                    display_name="Google Gemini",
                    api_key_env="GEMINI_API_KEY",
                ),
            }


# ─────────────────────────────────────────────────────────────────────────────
# Models / Routage
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ModelRoutingConfig:
    """Routage des modèles par type de tâche."""
    reasoning: str = "claude-sonnet-4-20250514"
    code: str = "claude-3-5-sonnet-20241022"
    fast: str = "llama3.1"
    local: str = "llama3.1"
    embedding: str = "nomic-embed-text"


@dataclass
class ModelsConfig:
    """Configuration des modèles et du routage."""
    default: str = "llama3.1"
    routing: ModelRoutingConfig = field(default_factory=ModelRoutingConfig)
    fallback: str = "llama3.1"


# ─────────────────────────────────────────────────────────────────────────────
# RAG
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RAGConfig:
    """Configuration du pipeline RAG."""
    enabled: bool = True
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    embedding_model: str = "nomic-embed-text"
    embedding_dimensions: int = 768
    similarity_threshold: float = 0.7
    rerank: bool = False
    rerank_model: str = ""
    persist_directory: str = "~/.ethan/rag"


# ─────────────────────────────────────────────────────────────────────────────
# Memory
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MemoryConfig:
    """Configuration de la mémoire / faits."""
    enabled: bool = True
    max_facts: int = 10000
    ttl_days: int = 30
    auto_archive: bool = True
    archive_after_days: int = 7
    max_context_tokens: int = 4000
    memory_scope: str = "default"


# ─────────────────────────────────────────────────────────────────────────────
# Agents
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentsConfig:
    """Configuration globale des agents cognitifs."""
    max_concurrent: int = 4
    default_timeout_seconds: int = 300
    auto_restart: bool = True
    default_model: str = ""
    default_provider: str = ""
    memory_scope: str = "default"
    max_iterations: int = 10
    temperature: float = 0.7


# Alias de compatibilité — anciennement ``AgentConfig`` (singulier).
# Les modules legacy (core.agents.base, core.executive, core.cognition)
# importent ``AgentConfig`` depuis ce schéma.  ``AgentsConfig`` est la
# configuration globale des agents ; l'alias préserve la compatibilité
# sans dupliquer de logique.
AgentConfig = AgentsConfig


# ─────────────────────────────────────────────────────────────────────────────
# Planner
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PlannerConfig:
    """Configuration du planificateur de tâches."""
    max_depth: int = 5
    max_steps: int = 50
    timeout_seconds: int = 600
    auto_approve: bool = False
    require_confirmation: bool = True
    default_agent: str = "orchestrator"


# ─────────────────────────────────────────────────────────────────────────────
# Plugins
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PluginsConfig:
    """Configuration de la gestion des plugins."""
    auto_load: bool = True
    allowed_paths: list[str] = field(default_factory=list)
    sandbox_enabled: bool = True
    auto_update: bool = False
    update_interval_hours: int = 24


# ─────────────────────────────────────────────────────────────────────────────
# Authentication
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AuthenticationConfig:
    """Configuration de l'authentification et de l'autorisation."""
    enabled: bool = True
    jwt_secret_env: str = "JWT_SECRET"
    jwt_expiry_hours: int = 24
    rbac_enabled: bool = True
    oauth_enabled: bool = False
    oauth_providers: dict[str, Any] = field(default_factory=dict)
    password_min_length: int = 8
    session_timeout_minutes: int = 60


# ─────────────────────────────────────────────────────────────────────────────
# Point d'entrée
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ConfigSchema:
    """Point d'entrée de la configuration — source de vérité unique.

    Toutes les interfaces (Runtime, Core, CLI, WebUI, Desktop) accèdent
    à la configuration via ce schéma.
    """
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    providers: ProvidersConfig = field(default_factory=ProvidersConfig)
    models: ModelsConfig = field(default_factory=ModelsConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    agents: AgentsConfig = field(default_factory=AgentsConfig)
    planner: PlannerConfig = field(default_factory=PlannerConfig)
    plugins: PluginsConfig = field(default_factory=PluginsConfig)
    authentication: AuthenticationConfig = field(default_factory=AuthenticationConfig)
    metadata: dict[str, Any] = field(default_factory=dict)

    # ── Helpers de conversion ──────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Sérialise la configuration complète en dict."""
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConfigSchema":
        """Désérialise depuis un dict (avec fusion des defaults)."""
        defaults = cls()
        result = cls()

        for domain_name in (
            "runtime", "providers", "models", "rag", "memory",
            "agents", "planner", "plugins", "authentication",
        ):
            domain_data = data.get(domain_name, {})
            if not isinstance(domain_data, dict):
                continue
            default_domain = getattr(defaults, domain_name)
            merged = _merge_dataclass(default_domain, domain_data)
            setattr(result, domain_name, merged)

        if "metadata" in data and isinstance(data["metadata"], dict):
            result.metadata = dict(data["metadata"])

        return result


def _merge_dataclass(default_obj: Any, override: dict[str, Any]) -> Any:
    """Fusionne un dict de surcharge dans une instance de dataclass.

    Crée une nouvelle instance de la même classe avec les valeurs
    par défaut, puis applique les overrides récursivement.
    """
    from dataclasses import fields, is_dataclass

    if not is_dataclass(default_obj):
        return override

    cls = type(default_obj)
    kwargs: dict[str, Any] = {}

    for f in fields(default_obj):
        if f.name in override:
            value = override[f.name]
            default_value = getattr(default_obj, f.name)
            if is_dataclass(default_value) and isinstance(value, dict):
                kwargs[f.name] = _merge_dataclass(default_value, value)
            elif isinstance(default_value, dict) and isinstance(value, dict):
                kwargs[f.name] = {**default_value, **value}
            elif isinstance(default_value, list) and isinstance(value, list):
                kwargs[f.name] = value
            else:
                kwargs[f.name] = value
        else:
            kwargs[f.name] = getattr(default_obj, f.name)

    return cls(**kwargs)
