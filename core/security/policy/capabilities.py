"""Capability System — Gestion granulaire des capacités ETHAN.

Une capability est un **droit d'action temporellement et spatialement borné** :
sujet × ressource × opération × portée × durée × origine × niveau de risque.

Contraintes (Phase 05) :
- Une capability accordée **ne peut jamais dépasser sa portée**.
- Path traversal / symlink escape / mount escape sont bloqués par le résolveur
  de chemin (`resolve_safe_path`).
- Durée contrôlée par un TTL absolu : expirée -> DENY (fail-closed).
- Chaque utilisation est **audité** (append-only).
- Révocable à tout moment.

Ce module est **indépendant du LLM** : aucune instruction de modèle ne peut
créer, modifier ou contourner une capability.
"""

from __future__ import annotations

import fnmatch
import hashlib
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from core.security.policy.types import PolicyRequest, PolicyResult

logger = logging.getLogger(__name__)

# ── Catégories de ressources supportées ──────────────────────────────────────

FILESYSTEM = "filesystem"
SHELL = "shell"
DOCKER = "docker"
SYSTEMD = "systemd"
NETWORK = "network"
MCP = "mcp"
MEMORY = "memory"
CONFIGURATION = "configuration"
EXTERNAL_TRANSMISSION = "external_transmission"

RESOURCE_CATEGORIES = {
    FILESYSTEM, SHELL, DOCKER, SYSTEMD, NETWORK, MCP, MEMORY, CONFIGURATION,
    EXTERNAL_TRANSMISSION,
}

# Opérations par catégorie.
FILESYSTEM_OPS = {"read", "write", "delete", "list"}
SHELL_OPS = {"execute"}
DOCKER_OPS = {"execute"}
SYSTEMD_OPS = {"execute"}
NETWORK_OPS = {"read", "write"}
MCP_OPS = {"execute"}
MEMORY_OPS = {"read", "write"}
CONFIGURATION_OPS = {"read", "write"}
EXTERNAL_TRANSMISSION_OPS = {"send"}

_OPERATION_MAP: dict[str, set[str]] = {
    FILESYSTEM: FILESYSTEM_OPS,
    SHELL: SHELL_OPS,
    DOCKER: DOCKER_OPS,
    SYSTEMD: SYSTEMD_OPS,
    NETWORK: NETWORK_OPS,
    MCP: MCP_OPS,
    MEMORY: MEMORY_OPS,
    CONFIGURATION: CONFIGURATION_OPS,
    EXTERNAL_TRANSMISSION: EXTERNAL_TRANSMISSION_OPS,
}


class RiskLevel:
    """Niveau de risque d'une capability (aligné sur le Core existant)."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CapabilityState:
    """État de vie d'une capability."""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


# ── Path Security — traversal / symlink / mount escape ───────────────────────

@dataclass(frozen=True)
class PathSecurityError(Exception):
    """Chemin refusé par le résolveur de sécurité."""
    resource: str
    reason: str


def resolve_safe_path(resource: str, allowed_roots: list[str]) -> str:
    """Résout un chemin de ressource en chemin absolu sécurisé.

    Garantit :
    - Pas de path traversal (../)
    - Pas de symlink escape (le chemin résolu reste dans allowed_roots)
    - Pas de mount escape (le chemin reste dans les racines autorisées)

    Raises:
        PathSecurityError: si le chemin sort du périmètre autorisé.
    """
    if not resource or not resource.strip():
        raise PathSecurityError(resource, "resource path is empty")

    raw = Path(resource)
    if not raw.is_absolute():
        raw = Path("/workspace") / raw

    resolved = raw.resolve(strict=False)
    resolved_str = str(resolved)

    for root in allowed_roots:
        root_str = str(Path(root).resolve(strict=False))
        try:
            common = os.path.commonpath([resolved_str, root_str])
        except ValueError:
            continue
        if common == root_str:
            return resolved_str

    raise PathSecurityError(
        resource,
        f"path '{resolved_str}' escapes allowed roots {allowed_roots}",
    )


# ── Capability granulaire ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class Capability:
    """Une capability accordée — immuable."""

    id: str
    subject: str
    category: str
    operation: str
    resource: str
    scope: str
    ttl_seconds: int | None
    risk_level: str
    origin: str
    granted_at: float
    revoked: bool = False

    def is_expired(self, now: float | None = None) -> bool:
        """True si la capability a expiré (TTL écoulé)."""
        now = now or time.time()
        if self.ttl_seconds is None:
            return False
        return now > self.granted_at + self.ttl_seconds

    def matches(
        self,
        subject: str,
        category: str,
        operation: str,
        resolved_resource: str,
        allowed_roots: list[str],
    ) -> bool:
        """Vérifie si la capability couvre une requête concrète.

        Contraintes :
        - sujet exact ou wildcard
        - catégorie exacte ou wildcard
        - opération exacte ou wildcard (lire != ecrire — A5 no-inference)
        - le resource résolu reste dans la portée définie
        """
        if self.revoked or self.is_expired():
            return False
        if self.subject != subject and self.subject != "*":
            return False
        if self.category != category and self.category != "*":
            return False
        if self.operation != operation and self.operation != "*":
            return False

        # Path security : uniquement pour les ressources filesystem. Pour les
        # autres catégories (shell, docker, réseau, mcp...), la ressource est
        # une commande/URL — matching glob simple sur la valeur brute.
        if category != FILESYSTEM:
            return fnmatch.fnmatch(resolved_resource, self.resource)

        if self.resource == "*":
            # Wildcard total : autoriser (path security déjà faite en amont).
            try:
                resolve_safe_path(resolved_resource, allowed_roots)
            except PathSecurityError:
                return False
            return True

        try:
            cap_resource = resolve_safe_path(self.resource, allowed_roots)
            req_resource = resolve_safe_path(resolved_resource, allowed_roots)
        except PathSecurityError:
            return False

        # Le "**" dans la capability est un wildcard de répertoire.
        # On le retire du chemin résolu pour faire le prefix-matching.
        if cap_resource.endswith(os.sep + "**") or cap_resource.endswith("/**"):
            cap_base = cap_resource[:-3]  # retire le "**"
            if cap_base.endswith(os.sep):
                cap_base = cap_base[:-1]
        else:
            cap_base = cap_resource

        if cap_base == req_resource:
            return True
        if req_resource.startswith(cap_base + os.sep):
            return True
        return False

    def to_audit_dict(self) -> dict[str, Any]:
        """Sérialisation pour l'audit (sans secrets)."""
        return {
            "id": self.id,
            "subject": self.subject,
            "category": self.category,
            "operation": self.operation,
            "resource": self.resource,
            "scope": self.scope,
            "ttl_seconds": self.ttl_seconds,
            "risk_level": self.risk_level,
            "origin": self.origin,
            "granted_at": datetime.utcfromtimestamp(self.granted_at).isoformat(),
            "revoked": self.revoked,
        }


# ── Génération d'ID ──────────────────────────────────────────────────────────

def capability_id(*parts: str) -> str:
    """Génère un ID de capability déterministe SHA-256."""
    h = hashlib.sha256(":".join(parts).encode()).hexdigest()
    return f"cap_{h[:16]}"


# ── Entrée d'audit ────────────────────────────────────────────────────────────

@dataclass
class AuditEntry:
    """Entrée d'audit d'une utilisation de capability."""
    capability_id: str
    subject: str
    category: str
    operation: str
    resource: str
    granted: bool
    decision: PolicyResult
    reason: str
    timestamp: float = field(default_factory=time.time)
    matched_policy: str | None = None


# ── Gestionnaire de capabilities ─────────────────────────────────────────────

class CapabilityManager:
    """Gestionnaire central des capabilities.

    Granularité : sujet x ressource x opération x portée x durée, avec :
    - sécurité de chemin (traversal / symlink / mount escape)
    - audit append-only de chaque utilisation
    - révocation dynamique
    - fail-closed (aucune capability = DENY)
    """

    def __init__(self, allowed_roots: list[str] | None = None) -> None:
        self.allowed_roots: list[str] = (
            allowed_roots or [str(Path.cwd().resolve())]
        )
        self._capabilities: dict[str, Capability] = {}
        self._audit_log: list[AuditEntry] = []

    # ── Administration ─────────────────────────────────────────────────

    def grant(
        self,
        subject: str,
        category: str,
        operation: str,
        resource: str,
        scope: str = "self",
        ttl_seconds: int | None = None,
        risk_level: str = RiskLevel.MEDIUM,
        origin: str = "runtime",
    ) -> Capability:
        """Accorde une capability granulaire.

        Valide la catégorie/opération avant l'octroi (fail-closed).
        """
        if category not in RESOURCE_CATEGORIES:
            raise ValueError(f"unknown resource category: {category}")
        allowed_ops = _OPERATION_MAP.get(category, set())
        if operation not in allowed_ops and operation != "*":
            raise ValueError(
                f"operation '{operation}' not allowed for category '{category}'"
            )
        if scope not in ("self", "shared"):
            raise ValueError(f"invalid scope: {scope}")

        cap = Capability(
            id=capability_id(
                subject, category, operation, resource, str(ttl_seconds)
            ),
            subject=subject,
            category=category,
            operation=operation,
            resource=resource,
            scope=scope,
            ttl_seconds=ttl_seconds,
            risk_level=risk_level,
            origin=origin,
            granted_at=time.time(),
        )
        self._capabilities[cap.id] = cap
        logger.info(
            "Capability granted: %s (%s:%s:%s:%s)",
            cap.id, subject, category, operation, resource,
        )
        return cap

    def revoke(self, capability_id: str) -> bool:
        """Révoque une capability (marquage, conservation audit)."""
        cap = self._capabilities.get(capability_id)
        if cap is None:
            return False
        self._capabilities[capability_id] = _revoke(cap)
        logger.info("Capability revoked: %s", capability_id)
        return True

    def list_capabilities(
        self, subject: str | None = None
    ) -> list[Capability]:
        """Liste les capabilities actives (non révoquées, non expirées)."""
        now = time.time()
        result = []
        for cap in self._capabilities.values():
            if cap.revoked or cap.is_expired(now):
                continue
            if subject is not None and cap.subject != subject and cap.subject != "*":
                continue
            result.append(cap)
        return result

    # ── Évaluation ─────────────────────────────────────────────────────

    def check(
        self,
        subject: str,
        category: str,
        operation: str,
        resource: str,
        *,
        request: PolicyRequest | None = None,  # noqa: ARG002
    ) -> tuple[PolicyResult, str, Capability | None]:
        """Évalue une action contre les capabilities.

        Returns:
            (result, reason, matched_capability)
        """
        for cap in self._capabilities.values():
            if not cap.matches(
                subject, category, operation, resource, self.allowed_roots
            ):
                continue
            entry = AuditEntry(
                capability_id=cap.id,
                subject=subject,
                category=category,
                operation=operation,
                resource=resource,
                granted=True,
                decision=PolicyResult.ALLOW,
                reason=f"capability {cap.id} matched",
                matched_policy=cap.id,
            )
            self._audit_log.append(entry)
            return (
                PolicyResult.ALLOW,
                f"capability {cap.id} matched",
                cap,
            )

        entry = AuditEntry(
            capability_id="none",
            subject=subject,
            category=category,
            operation=operation,
            resource=resource,
            granted=False,
            decision=PolicyResult.DENY,
            reason="No matching active capability (fail-closed).",
        )
        self._audit_log.append(entry)
        return (
            PolicyResult.DENY,
            "No matching active capability (fail-closed).",
            None,
        )

    # ── Audit ──────────────────────────────────────────────────────────

    @property
    def audit_log(self) -> list[AuditEntry]:
        """Journal d'audit append-only (lecture seule)."""
        return list(self._audit_log)

    def audit_summary(self) -> dict[str, Any]:
        """Résumé statistique de l'audit."""
        total = len(self._audit_log)
        allowed = sum(1 for e in self._audit_log if e.granted)
        return {
            "total_evaluations": total,
            "allowed": allowed,
            "denied": total - allowed,
            "active_capabilities": len(self.list_capabilities()),
        }


def _revoke(cap: Capability) -> Capability:
    """Marque une capability comme révoquée (immuable)."""
    return Capability(
        id=cap.id,
        subject=cap.subject,
        category=cap.category,
        operation=cap.operation,
        resource=cap.resource,
        scope=cap.scope,
        ttl_seconds=cap.ttl_seconds,
        risk_level=cap.risk_level,
        origin=cap.origin,
        granted_at=cap.granted_at,
        revoked=True,
    )
