"""Policy Engine ETHAN — évaluation hiérarchique des actions sensibles.

Point d'entrée pour évaluer et protéger toute action à effet de bord
(filesystem, process, shell, docker, network, mcp, memory, configuration).

Usage rapide ::

    from core.security.policy import PolicyEngine, PolicyGuard

    engine = PolicyEngine()                 # règles par défaut (CORE+SECURITY)
    guard = PolicyGuard(engine)             # exécution protégée

    decision = engine.check("shell", "execute", "rm -rf /tmp")  # DENY
    await guard.execute("shell", "execute", "ls -la", fn, source="llm")
"""

from __future__ import annotations

from core.security.policy.engine import PolicyEngine
from core.security.policy.guard import PolicyGuard
from core.security.policy.rules import default_rules
from core.security.policy.types import (
    ActionCategory,
    Policy,
    PolicyConfirmationRequiredError,
    PolicyDecision,
    PolicyDeniedError,
    PolicyEffect,
    PolicyError,
    PolicyLevel,
    PolicyRequest,
    PolicyResult,
)

try:  # capabilities (Phase 05) — import optionnel, fail-closed si absent
    from core.security.policy.capabilities import (
        Capability,
        CapabilityManager,
        CapabilityState,
        PathSecurityError,
        RiskLevel,
        resolve_safe_path,
    )
except Exception:  # pragma: no cover - garde le package utilisable si capabilities.py est incomplet
    CapabilityManager = None

__all__ = [
    "ActionCategory",
    "Capability",
    "CapabilityManager",
    "CapabilityState",
    "PathSecurityError",
    "Policy",
    "PolicyConfirmationRequiredError",
    "PolicyDecision",
    "PolicyDeniedError",
    "PolicyEffect",
    "PolicyEngine",
    "PolicyError",
    "PolicyGuard",
    "PolicyLevel",
    "PolicyRequest",
    "PolicyResult",
    "RiskLevel",
    "default_rules",
    "resolve_safe_path",
]
