"""Types du système d'extensions unifié — ETHAN.

Ce module est la VOCABULAIRE commun à Capabilities, Plugins et Cookbook. Il ne
contient aucune logique : uniquement des types, des états et les règles de
transition qui garantissent qu'une extension ne peut pas se trouver dans un
état incohérent.

Unicité (Première Loi, AGENTS.md) : il existe UN seul vocabulaire d'état pour
les trois types. Le type (`ExtensionKind`) reste explicite et discrimine le
comportement — un Cookbook n'est jamais déguisé en Plugin.

Le Core reste la source de vérité : `ExtensionManager` dérive ces états de
l'état réel persisté du système sous-jacent, il ne les invente jamais.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Types d'extension ────────────────────────────────────────────────────────


class ExtensionKind:
    """Le type explicite d'une extension.

    - `capability` : composant d'infrastructure réel (backend docker / pip /
      npm / exécutable). A un runtime.
    - `plugin` : manifeste déclaratif qui RÉFÉRENCE des outils / skills / MCP
      existants. N'a pas de runtime.
    - `cookbook` : recette qui instancie des records (prompts, skills,
      automations). N'a pas de runtime.
    """

    CAPABILITY = "capability"
    PLUGIN = "plugin"
    COOKBOOK = "cookbook"

    ALL = frozenset({CAPABILITY, PLUGIN, COOKBOOK})


# ── États unifiés ────────────────────────────────────────────────────────────


class ExtensionState:
    """États standardisés, communs aux trois types.

    Ils remplacent les trois vocabulaires historiques (`CapabilityState`,
    `STATUS_ACTIVE/INACTIVE`, présence/absence Cookbook) par UN seul, afin que
    l'interface n'ait pas à connaître le système d'origine.
    """

    AVAILABLE = "AVAILABLE"
    INSTALLING = "INSTALLING"
    INSTALLED = "INSTALLED"
    ENABLING = "ENABLING"
    ENABLED = "ENABLED"
    DISABLING = "DISABLING"
    DISABLED = "DISABLED"
    UPDATING = "UPDATING"
    ERROR = "ERROR"
    UNINSTALLING = "UNINSTALLING"

    ALL = frozenset(
        {
            AVAILABLE,
            INSTALLING,
            INSTALLED,
            ENABLING,
            ENABLED,
            DISABLING,
            DISABLED,
            UPDATING,
            ERROR,
            UNINSTALLING,
        }
    )

    # Un état « en cours » : l'interface montre une progression et ne présente
    # JAMAIS une installation comme aboutie (seul le Core décide).
    BUSY = frozenset({INSTALLING, ENABLING, DISABLING, UPDATING, UNINSTALLING})

    # Un état « posé » : l'extension existe et n'est pas en mouvement.
    SETTLED = frozenset({AVAILABLE, INSTALLED, ENABLED, DISABLED, ERROR})

    # Transitions légales. Clé = état courant → états atteignables.
    TRANSITIONS: dict[str, frozenset[str]] = {
        AVAILABLE: frozenset({INSTALLING}),
        INSTALLING: frozenset({INSTALLED, ERROR, AVAILABLE}),  # rollback
        INSTALLED: frozenset({ENABLING, UPDATING, UNINSTALLING, ERROR, DISABLED}),
        ENABLING: frozenset({ENABLED, ERROR, INSTALLED}),
        ENABLED: frozenset({DISABLING, UPDATING, UNINSTALLING, ERROR}),
        DISABLING: frozenset({DISABLED, ERROR, ENABLED}),
        DISABLED: frozenset({ENABLING, UNINSTALLING, UPDATING, INSTALLING, ERROR}),
        UPDATING: frozenset({INSTALLED, ENABLED, ERROR}),
        UNINSTALLING: frozenset({AVAILABLE, ERROR}),
        ERROR: frozenset({INSTALLING, AVAILABLE, UNINSTALLING, UPDATING}),
    }

    @classmethod
    def can_transition(cls, current: str, target: str) -> bool:
        return target in cls.TRANSITIONS.get(current, frozenset())


class TransitionError(ValueError):
    """Transition d'état illégale — protège la machine à états.

    L'API la traduit en HTTP 409 : une extension ne peut jamais être
    désinstallée pendant qu'elle est en cours d'installation.
    """


# ── Opérations de cycle de vie ───────────────────────────────────────────────


# ── Spécification d'une extension ────────────────────────────────────────────


@dataclass
class ExtensionSpec:
    """Ce que le catalogue sait d'une extension, indépendamment de son état.

    `payload` contient la spécification DU SYSTÈME D'ORIGINE (`CapabilitySpec`,
    `PluginManifest`, manifeste Cookbook) : le gestionnaire unifié ne
    réinterprète jamais la sémantique d'un type, il délègue au handler
    correspondant. C'est ce qui permet de mutualiser le cycle de vie sans
    dissoudre les différences entre types.
    """

    id: str
    kind: str
    name: str
    version: str = "0.0.0"
    description: str = ""
    source: str = "builtin"
    icon: str = "Package"
    categories: tuple[str, ...] = ()
    # `True` si le type sait réaliser une mise à jour. Sans runtime, un update
    # consiste à ré-appliquer l'installation (idempotent).
    updatable: bool = False
    # `True` si le type possède un plan d'exécution à montrer avant mutation.
    plannable: bool = False
    payload: Any = None

    def validate(self) -> None:
        if not self.id or not self.id.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"invalid extension id: {self.id!r}")
        if self.kind not in ExtensionKind.ALL:
            raise ValueError(f"unknown extension kind: {self.kind!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "source": self.source,
            "icon": self.icon,
            "categories": list(self.categories),
            "updatable": self.updatable,
            "plannable": self.plannable,
        }


# ── État runtime persisté ────────────────────────────────────────────────────


@dataclass
class ExtensionRuntimeState:
    """État persisté d'une extension (source de vérité du Core).

    `last_error` porte TOUJOURS le message réel de l'échec — une installation
    échouée n'est jamais représentée comme réussie.
    """

    id: str
    kind: str = ExtensionKind.CAPABILITY
    state: str = ExtensionState.AVAILABLE
    enabled: bool = False
    config: dict[str, Any] = field(default_factory=dict)
    installed_version: str | None = None
    last_error: str | None = None
    updated_at: str | None = None
    # Métadonnées propres au type (ex: container_id, ids de records créés).
    runtime_meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "state": self.state,
            "enabled": self.enabled,
            "config": dict(self.config),
            "installed_version": self.installed_version,
            "last_error": self.last_error,
            "updated_at": self.updated_at,
            "runtime_meta": dict(self.runtime_meta),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExtensionRuntimeState:
        return cls(
            id=data["id"],
            kind=data.get("kind", ExtensionKind.CAPABILITY),
            state=data.get("state", ExtensionState.AVAILABLE),
            enabled=bool(data.get("enabled", False)),
            config=dict(data.get("config", {})),
            installed_version=data.get("installed_version"),
            last_error=data.get("last_error"),
            updated_at=data.get("updated_at"),
            runtime_meta=dict(data.get("runtime_meta", {})),
        )


@dataclass
class ExtensionStatus:
    """Vue destinée à l'interface : spec + état réel + actions possibles.

    `actions` est calculé par le Core à partir de l'état ET du type — le
    frontend ne devine jamais ce qui est faisable.
    """

    spec: ExtensionSpec
    state: ExtensionRuntimeState
    actions: tuple[str, ...] = ()
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.spec.to_dict(),
            "state": self.state.state,
            "enabled": self.state.enabled,
            "config": dict(self.state.config),
            "installed_version": self.state.installed_version,
            "last_error": self.state.last_error,
            "updated_at": self.state.updated_at,
            "runtime_meta": dict(self.state.runtime_meta),
            "actions": list(self.actions),
            "detail": dict(self.detail),
        }


__all__ = [
    "ExtensionKind",
    "ExtensionOperation",
    "ExtensionRuntimeState",
    "ExtensionSpec",
    "ExtensionState",
    "ExtensionStatus",
    "OperationStatus",
    "TransitionError",
]
class OperationStatus:
    """États d'une opération (install / uninstall / update / toggle).

    `RUNNING` n'est jamais terminal : il existe toujours un chemin vers un état
    terminal, y compris après un redémarrage (réconciliation au démarrage),
    pour qu'aucune opération ne reste bloquée indéfiniment.
    """

    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"

    ALL = frozenset({RUNNING, SUCCESS, ERROR, TIMEOUT, CANCELLED})
    TERMINAL = frozenset({SUCCESS, ERROR, TIMEOUT, CANCELLED})


class ExtensionOperation:
    """Opérations de cycle de vie : install | uninstall | update | enable | disable."""

    INSTALL = "install"
    UNINSTALL = "uninstall"
    UPDATE = "update"
    ENABLE = "enable"
    DISABLE = "disable"

    ALL = frozenset({INSTALL, UNINSTALL, UPDATE, ENABLE, DISABLE})
