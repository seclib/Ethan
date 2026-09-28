"""Types du Capability Manager — états, spécification déclarative, plans.

La spec d'une capability est DEVELOPPEUR-DEFINIE (builtin ou plugin signé),
jamais construite depuis l'input utilisateur brut : c'est le rempart contre
l'injection d'arguments dans les backends (section 10 de la spec).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Types de composants ──────────────────────────────────────────────────────


class CapabilityType:
    """Types de composants optionnels gérés par ETHAN."""

    PROVIDER = "provider"
    MODEL = "model"
    VECTOR_DATABASE = "vector_database"
    RUNTIME = "runtime"
    SERVICE = "service"
    INTEGRATION = "integration"
    TOOL = "tool"
    EMBEDDING = "embedding"
    RERANKER = "reranker"
    STT_TTS = "stt_tts"
    MCP_SERVER = "mcp_server"
    PLUGIN = "plugin"
    SKILL = "skill"

    ALL = frozenset(
        {
            PROVIDER,
            MODEL,
            VECTOR_DATABASE,
            RUNTIME,
            SERVICE,
            INTEGRATION,
            TOOL,
            EMBEDDING,
            RERANKER,
            STT_TTS,
            MCP_SERVER,
            PLUGIN,
            SKILL,
        }
    )


# Backends d'exécution connus (allowlist structurelle) : une spec ne peut
# déclarer que l'un d'eux, et l'utilisateur n'en fournit jamais. Chaque
# backend listé ici DOIT avoir une implémentation dans `backends.py` —
# sinon `get_backend` échoue explicitement à l'usage (jamais de composant
# silencieusement inerte).
BACKENDS = frozenset({"docker", "python_package", "node_package", "executable", "builtin"})


# ── États ────────────────────────────────────────────────────────────────────


class CapabilityState:
    """États explicites du cycle de vie — jamais un simple booléen `installed`."""

    SUPPORTED = "SUPPORTED"
    NOT_INSTALLED = "NOT_INSTALLED"
    INSTALLING = "INSTALLING"
    INSTALLED = "INSTALLED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    UNHEALTHY = "UNHEALTHY"
    CONFIGURATION_REQUIRED = "CONFIGURATION_REQUIRED"
    READY = "READY"
    UNINSTALLING = "UNINSTALLING"
    ERROR = "ERROR"

    ALL = frozenset(
        {
            SUPPORTED,
            NOT_INSTALLED,
            INSTALLING,
            INSTALLED,
            STARTING,
            RUNNING,
            STOPPED,
            UNHEALTHY,
            CONFIGURATION_REQUIRED,
            READY,
            UNINSTALLING,
            ERROR,
        }
    )

    # Transitions légales. Clé = état courant, valeurs = états atteignables.
    TRANSITIONS: dict[str, frozenset[str]] = {
        SUPPORTED: frozenset({NOT_INSTALLED, ERROR}),
        NOT_INSTALLED: frozenset({INSTALLING}),
        INSTALLING: frozenset({INSTALLED, ERROR, NOT_INSTALLED}),  # rollback
        INSTALLED: frozenset({STARTING, CONFIGURATION_REQUIRED, UNINSTALLING, ERROR}),
        CONFIGURATION_REQUIRED: frozenset({STARTING, INSTALLED, UNINSTALLING, ERROR}),
        STARTING: frozenset({RUNNING, UNHEALTHY, ERROR, STOPPED}),
        RUNNING: frozenset({READY, UNHEALTHY, STOPPED, ERROR}),
        UNHEALTHY: frozenset({STARTING, STOPPED, UNINSTALLING, ERROR, READY}),
        READY: frozenset({RUNNING, UNHEALTHY, STOPPED, ERROR, UNINSTALLING}),
        STOPPED: frozenset({STARTING, UNINSTALLING, ERROR}),
        UNINSTALLING: frozenset({SUPPORTED, ERROR}),
        ERROR: frozenset({NOT_INSTALLED, SUPPORTED, INSTALLING, UNINSTALLING, ERROR}),
    }

    # États intermédiaires : une opération longue est en cours.
    BUSY = frozenset({INSTALLING, STARTING, UNINSTALLING})

    # États terminaux stables (alias, évite l'ombre du string READY ci-dessus).
    READY_STATES = frozenset({READY, RUNNING, STOPPED})

    @classmethod
    def can_transition(cls, current: str, target: str) -> bool:
        if current == target:
            return True
        return target in cls.TRANSITIONS.get(current, frozenset())


# ── Spécification déclarative (développeur-définie) ─────────────────────────


@dataclass(frozen=True)
class ConfigField:
    """Champ de configuration utilisateur, typé et borné.

    Les valeurs utilisateur sont validées contre cette définition avant
    persistance ; elles n'atteignent jamais une argv (les backends ne
    consomment que la spec développeur + des paramètres typés).
    """

    name: str
    type: str = "string"  # "string" | "int" | "bool" | "port"
    required: bool = False
    default: Any = None
    description: str = ""
    min_value: int | None = None
    max_value: int | None = None
    choices: tuple[str, ...] | None = None


@dataclass(frozen=True)
class HealthCheck:
    """Un palier de vérification fonctionnelle.

    kind:
      - "endpoint" : HTTP GET sur `url` — attend un statut < 500.
      - "tcp"      : connexion TCP host:port.
      - "exec"     : commande du BACKEND (figée dans la spec, jamais un input
                     utilisateur).
      - "builtin"  : composant intégré au process Core (présent par
                     construction).
    `level` : "basic" (le composant tourne) ou "functional" (requis pour READY).
    """

    kind: str  # "endpoint" | "tcp" | "exec" | "builtin"
    level: str = "functional"  # "basic" | "functional"
    host: str = ""
    port: str = ""  # nom du champ de config (ex: "http_port")
    url: str = ""  # peut référencer {config.<field>} via format
    command: tuple[str, ...] = ()  # pour kind="exec" — figé côté spec


@dataclass(frozen=True)
class Dependency:
    """Dépendance d'une capability : executable système, autre capability, port."""

    id: str  # "docker", "qdrant", "storage"…
    kind: str = "system"  # "system" (executable) | "capability" | "port"
    command: tuple[str, ...] = ()  # pour kind="system" — probe shutil.which
    optional: bool = False
    description: str = ""


@dataclass(frozen=True)
class Provenance:
    """Provenance d'un composant — traçabilité de l'origine.

    Chaque composant géré par ETHAN doit pouvoir répondre : d'où vient-il ?
    Qui l'a produit ? Peut-on le vérifier ?
    """

    source: str = "builtin"  # "builtin" | "official" | "community" | "custom"
    author: str = "ETHAN"
    url: str = ""
    license: str = ""
    checksum: str = ""  # SHA256 quand disponible
    signature: str = ""  # signature PGP/cosign quand disponible


@dataclass(frozen=True)
class Requirements:
    """Prérequis de compatibilité et de ressources déclarés par la spec.

    Vérifiés AVANT toute mutation (section « PRÉREQUIS » de la spec) :
    dépendances = `Dependency`, compatibilité et ressources = ce type.
    Vide = aucune exigence déclarée — rien n'est jamais inventé :

      - `os` / `arch`   : valeurs normalisées minuscules (``platform``) ;
      - `min_ram_mb`    : RAM *disponible* minimale, en Mio ;
      - `min_disk_mb`   : espace libre minimal, en Mio.

    Une mesure indisponible (psutil absent) n'est jamais bloquante : elle
    est rapportée honnêtement comme « non vérifiable » — comme partout
    dans ce module, un verdict non fondé est refusé.
    """

    os: tuple[str, ...] = ()
    arch: tuple[str, ...] = ()
    min_ram_mb: int | None = None
    min_disk_mb: int | None = None

    def is_empty(self) -> bool:
        return not (self.os or self.arch or self.min_ram_mb or self.min_disk_mb)

    def to_dict(self) -> dict[str, Any]:
        return {
            "os": list(self.os),
            "arch": list(self.arch),
            "min_ram_mb": self.min_ram_mb,
            "min_disk_mb": self.min_disk_mb,
        }


@dataclass
class CapabilitySpec:
    """Spécification déclarative d'un composant optionnel.

    `install_actions` / `uninstall_actions` / `start_actions` /
    `stop_actions` sont la SEULE source des opérations backends (étapes
    déclaratives : {"action": "pull", "image": ...}, {"action": "run", ...}).
    L'input utilisateur (config) ne fait que remplir des champs typés
    référencés par la spec — il ne compose jamais une commande.
    """

    id: str
    name: str
    description: str
    type: str  # CapabilityType.*
    version: str = "0.0.0"
    backend: str = "docker"  # "docker" | "python_package" | "executable" | "builtin"
    install_actions: tuple[dict[str, Any], ...] = ()
    uninstall_actions: tuple[dict[str, Any], ...] = ()
    start_actions: tuple[dict[str, Any], ...] = ()
    stop_actions: tuple[dict[str, Any], ...] = ()
    data_resources: tuple[dict[str, Any], ...] = ()  # volumes/dirs persistants
    dependencies: tuple[Dependency, ...] = ()
    config_schema: tuple[ConfigField, ...] = ()
    health_checks: tuple[HealthCheck, ...] = ()
    requirements: Requirements = field(default_factory=Requirements)
    requires_confirmation: bool = True  # opérations mutatrices à confirmer
    provenance: Provenance = field(default_factory=Provenance)

    def validate(self) -> None:
        if not self.id or not self.id.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"invalid capability id: {self.id!r}")
        if self.type not in CapabilityType.ALL:
            raise ValueError(f"unknown capability type: {self.type!r}")
        if self.backend not in BACKENDS:
            raise ValueError(f"unknown backend: {self.backend!r}")
        if self.provenance.source not in {"builtin", "official", "community", "custom"}:
            raise ValueError(f"unknown provenance source: {self.provenance.source!r}")
        for name in ("os", "arch"):
            entries = getattr(self.requirements, name)
            if any(not isinstance(entry, str) or not entry.strip() for entry in entries):
                raise ValueError(f"invalid requirements.{name}: {entries!r}")
        for name in ("min_ram_mb", "min_disk_mb"):
            value = getattr(self.requirements, name)
            if value is not None and (not isinstance(value, int) or value <= 0):
                raise ValueError(f"invalid requirements.{name}: {value!r}")


# ── Runtime (état persisté + vivant) ────────────────────────────────────────


@dataclass
class CapabilityRuntimeState:
    """État runtime persisté d'une capability (CoreRecordStore, domaine
    `capability_manager`). `state` est la source de vérité ; `config` ne
    contient JAMAIS de secret (règle secrets : write-only, non stocké ici)."""

    id: str
    state: str = CapabilityState.SUPPORTED
    enabled: bool = False
    config: dict[str, Any] = field(default_factory=dict)
    installed_version: str | None = None
    last_error: str | None = None
    updated_at: str | None = None
    runtime_meta: dict[str, Any] = field(default_factory=dict)  # ex: container_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "state": self.state,
            "enabled": self.enabled,
            "config": dict(self.config),
            "installed_version": self.installed_version,
            "last_error": self.last_error,
            "updated_at": self.updated_at,
            "runtime_meta": dict(self.runtime_meta),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CapabilityRuntimeState":
        return cls(
            id=data["id"],
            state=data.get("state", CapabilityState.SUPPORTED),
            enabled=bool(data.get("enabled", False)),
            config=dict(data.get("config", {})),
            installed_version=data.get("installed_version"),
            last_error=data.get("last_error"),
            updated_at=data.get("updated_at"),
            runtime_meta=dict(data.get("runtime_meta", {})),
        )


# ── Plans d'exécution ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class PlanStep:
    """Une opération qui sera effectuée — affichée à l'utilisateur AVANT
    confirmation lorsque l'opération modifie l'environnement."""

    description: str
    kind: str  # "install" | "start" | "stop" | "remove" | "verify" | "data"
    destructive: bool = False  # touche des données persistantes


@dataclass(frozen=True)
class MutationPlan:
    """Plan d'une opération mutatrice (install/start/stop/uninstall)."""

    capability_id: str
    operation: str  # "install" | "uninstall" | "start" | "stop"
    steps: tuple[PlanStep, ...] = ()
    requires_confirmation: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "operation": self.operation,
            "requires_confirmation": self.requires_confirmation,
            "steps": [
                {
                    "description": s.description,
                    "kind": s.kind,
                    "destructive": s.destructive,
                }
                for s in self.steps
            ],
        }


class TransitionError(Exception):
    """Transition d'état illégale — protège la machine à états."""
