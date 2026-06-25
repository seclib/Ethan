"""Security Types — Types de données pour le module Security."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TrustLevel(str, Enum):
    """Niveaux de confiance."""
    UNTRUSTED = "untrusted"      # 0.0-0.3: LLM externe
    LOW = "low"                  # 0.3-0.5: Plugin non vérifié
    MEDIUM = "medium"            # 0.5-0.7: Utilisateur
    HIGH = "high"                # 0.7-0.9: Admin, Système
    CRITICAL = "critical"        # 0.9-1.0: Root, Kernel


class ActionType(str, Enum):
    """Types d'actions."""
    COMMAND = "command"              # Exécution de commande
    CAPABILITY = "capability"        # Invocation de capability
    FILE_READ = "file_read"          # Lecture de fichier
    FILE_WRITE = "file_write"        # Écriture de fichier
    NETWORK = "network"              # Accès réseau
    MEMORY_READ = "memory_read"      # Lecture mémoire
    MEMORY_WRITE = "memory_write"    # Écriture mémoire
    PLUGIN_INSTALL = "plugin_install" # Installation plugin
    CONFIG_CHANGE = "config_change"  # Modification config


@dataclass
class Action:
    """Action à valider."""
    id: str
    type: ActionType
    source: str  # "llm", "user", "system", "plugin"
    signature: str | None = None
    resource: str = ""
    operation: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Identity:
    """Identité d'un acteur."""
    id: str
    type: str  # "llm", "user", "system", "plugin"
    name: str
    verification_level: float = 0.0  # 0.0 à 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityContext:
    """Contexte de sécurité."""
    identity: Identity
    trust_level: TrustLevel
    session_id: str
    correlation_id: str
    ip_address: str | None = None
    user_agent: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Permission:
    """Permission."""
    resource: str      # "file", "network", "command", "capability"
    action: str        # "read", "write", "execute", "delete"
    scope: str         # "user", "system", "plugin"
    conditions: dict[str, Any] = field(default_factory=dict)


@dataclass
class Role:
    """Rôle."""
    name: str
    permissions: list[Permission]
    trust_level: TrustLevel


@dataclass
class ValidationResult:
    """Résultat de validation."""
    valid: bool
    reason: str = ""
    identity: Identity | None = None
    trust_level: TrustLevel | None = None
    violations: list[str] = field(default_factory=list)
    validators_passed: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionResult:
    """Résultat d'exécution."""
    action_id: str
    valid: bool
    status: str  # "executed", "rejected", "failed"
    sandbox_used: str | None = None
    result: Any = None
    error: str | None = None
    duration_ms: float = 0.0
    validators_passed: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)


@dataclass
class AuditEntry:
    """Entrée d'audit."""
    id: str
    timestamp: datetime
    action_id: str
    actor: dict[str, Any]
    action: dict[str, Any]
    validation: dict[str, Any]
    execution: dict[str, Any]
    context: dict[str, Any]