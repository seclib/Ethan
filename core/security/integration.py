"""Écosystème — Intégration de la sécurité au Core (Phase 07).

Relie les briques des phases 04/05/06 aux composants réels d'ETHAN :

    Agent / LLM ──propose──> Tool ──▶ SecureToolEnforcer.check ──▶ exécution
                                     │
                                     ├─ PolicyEngine      (hiérarchie CORE→LLM)
                                     ├─ CapabilityManager (sujet × ressource × op)
                                     ├─ ExfilGuard        (transmission externe)
                                     └─ AuditStore        (observabilité, append-only)

Invariants (Constitution) :
- La décision d'un LLM/agent n'est **jamais** une autorisation (A6 + Loi Fondamentale).
- Un agent **propose / demande / agit selon ses capacités** ; il ne peut pas
  modifier une règle supérieure (le PolicyEngine est immuable depuis le flux LLM).
- Un tool sensible est évalué **avant** toute exécution (non contournable).

Rétro-compatibilité : `ToolExecutor()` sans enforcer conserve le comportement
historique ; la sécurité est activée en fournissant un `SecureToolEnforcer`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from core.audit.types import AuditCategory, AuditDecision
from core.security.data.exfiltration import ExfilGuard
from core.security.policy import ActionCategory, PolicyEngine, PolicyResult
from core.tools.types import Tool, ToolContext

logger = logging.getLogger(__name__)

# Alias de catégorie de tool vers les catégories du Policy Engine.
_CATEGORY_ALIASES: dict[str, str] = {
    "shell": ActionCategory.SHELL,
    "command": ActionCategory.SHELL,
    "bash": ActionCategory.SHELL,
    "terminal": ActionCategory.SHELL,
    "docker": ActionCategory.DOCKER,
    "filesystem": ActionCategory.FILESYSTEM,
    "file": ActionCategory.FILESYSTEM,
    "fs": ActionCategory.FILESYSTEM,
    "network": ActionCategory.NETWORK,
    "http": ActionCategory.NETWORK,
    "web": ActionCategory.NETWORK,
    "url": ActionCategory.NETWORK,
    "mcp": ActionCategory.MCP,
    "memory": ActionCategory.MEMORY,
    "config": ActionCategory.CONFIGURATION,
    "configuration": ActionCategory.CONFIGURATION,
    "send": ActionCategory.EXTERNAL_TRANSMISSION,
    "transmission": ActionCategory.EXTERNAL_TRANSMISSION,
    "exfil": ActionCategory.EXTERNAL_TRANSMISSION,
}

_KNOWN_CATEGORIES = {c.value for c in ActionCategory}


def classify_tool_call(
    tool: Tool, params: dict[str, Any]
) -> tuple[str, str, str]:
    """Mappe un appel de tool vers une requête Policy (catégorie, action, ressource).

    Le mapping est **structurel** (métadonnées du tool + paramètres), jamais
    influencé par le contenu du prompt ou une sortie de LLM.
    """
    raw_category = (tool.category or "generic").lower()
    category = _CATEGORY_ALIASES.get(
        raw_category,
        raw_category if raw_category in _KNOWN_CATEGORIES else "generic",
    )

    # Action
    action = "execute"
    if category == ActionCategory.FILESYSTEM:
        explicit = str(params.get("action", "")).lower()
        if explicit in ("read", "write", "delete", "list"):
            action = explicit
        else:
            action = "write" if ("content" in params or "data" in params) else "read"
    elif category == ActionCategory.MEMORY:
        action = (
            "write"
            if str(params.get("action", "")).lower() in ("write", "store", "remember")
            else "read"
        )
    elif category == ActionCategory.EXTERNAL_TRANSMISSION:
        # Toute transmission externe est une action "send" (CR-4 : refusée
        # par défaut, autorisée uniquement par une politique supérieure).
        action = "send"

    # Ressource cible (chemin / URL / commande / destination)
    resource = (
        params.get("path")
        or params.get("file")
        or params.get("url")
        or params.get("destination")
        or params.get("command")
        or params.get("resource")
        or "*"
    )
    return category, action, str(resource)


class ToolRejectedError(Exception):
    """L'exécution du tool a été refusée par le système de sécurité."""

    def __init__(self, reason: str, decision: Any = None) -> None:
        self.reason = reason
        self.decision = decision
        super().__init__(reason)


@dataclass(frozen=True)
class _CheckOutcome:
    """Traçabilité d'un contrôle : statut + identifiants pour l'audit."""

    decision: str
    category: str
    action: str
    resource: str
    policy_id: str | None = None


class SecureToolEnforcer:
    """Point d'entrée d'intégration : évalue un tool avant son exécution.

    Ordre d'évaluation (non contournable — toute exécution passe par ``check``) :
    1. PolicyEngine  — hiérarchie constitutionnelle (CORE → LLM).
    2. CapabilityManager — droit granulaire du sujet (si fourni).
    3. ExfilGuard    — toute transmission externe (si fourni).
    4. AuditStore    — enregistre la décision (si fourni).

    Si une étape refuse, ``ToolRejectedError`` est levée **avant** l'exécution
    et l'événement est audité.
    """

    def __init__(
        self,
        engine: PolicyEngine | None = None,
        capabilities: Any | None = None,
        exfil: ExfilGuard | None = None,
        audit: Any | None = None,
    ) -> None:
        self._engine = engine or PolicyEngine()
        self._capabilities = capabilities  # CapabilityManager | None
        self._exfil = exfil  # ExfilGuard | None
        self._audit = audit  # AuditStore | None
        self._subject_resolver: Callable[[ToolContext], str] | None = None

    # ── Configuration ────────────────────────────────────────────────────

    def set_subject_resolver(
        self, resolver: Callable[[ToolContext], str]
    ) -> "SecureToolEnforcer":
        """Définit comment dériver le sujet (agent/user) depuis le contexte."""
        self._subject_resolver = resolver
        return self

    @property
    def engine(self) -> PolicyEngine:
        return self._engine

    # ── Évaluation ───────────────────────────────────────────────────────

    async def check(
        self, tool: Tool, params: dict[str, Any], context: ToolContext
    ) -> _CheckOutcome:
        """Évalue un appel de tool ; lève ``ToolRejectedError`` si refusé.

        Ne **jamais** exécuter le tool si cette méthode lève.
        """
        category, action, resource = classify_tool_call(tool, params)
        subject = self._subject(tool, context)
        source = getattr(context, "source", "unknown") or "unknown"
        actor = f"{subject}"

        # 1. Policy Engine (hiérarchie, fail-closed, neutralité A6)
        decision = self._engine.check(
            category, action, resource, source=source
        )
        if decision.result is PolicyResult.DENY:
            self._record(
                AuditDecision.DENIED, actor, category, action, resource,
                f"policy:{decision.policy_id or 'silence'}",
                decision.reason,
            )
            raise ToolRejectedError(decision.reason, decision=decision)
        if decision.result is PolicyResult.REQUIRE_CONFIRMATION:
            self._record(
                AuditDecision.REJECTED, actor, category, action, resource,
                f"policy:{decision.policy_id}",
                "Confirmation humaine requise (fail-closed).",
            )
            raise ToolRejectedError(
                "Confirmation humaine requise (fail-closed).", decision=decision
            )

        # 2. Capability System (droit du sujet, phase 05)
        if self._capabilities is not None:
            result, reason, _cap = self._capabilities.check(
                subject, category, action, resource
            )
            if result is not PolicyResult.ALLOW:
                self._record(
                    AuditDecision.DENIED, actor, category, action, resource,
                    "capability", reason,
                )
                raise ToolRejectedError(reason)


        # 3. ExfilGuard (transmission externe, phase 06)
        if category == ActionCategory.EXTERNAL_TRANSMISSION and self._exfil is not None:
            content = params.get("content") or params.get("payload") or ""
            exfil_decision = self._exfil.evaluate(
                resource, str(content), source=source
            )
            if not exfil_decision.allowed:
                self._record(
                    AuditDecision.DENIED, actor, category, action, resource,
                    f"exfil:{exfil_decision.result.value}", exfil_decision.reason,
                )
                raise ToolRejectedError(exfil_decision.reason)

        # 4. Audit ALLOWED
        self._record(
            AuditDecision.ALLOWED, actor, category, action, resource,
            f"policy:{decision.policy_id or 'base'}",
            decision.reason,
        )
        return _CheckOutcome(
            decision="allowed", category=category, action=action, resource=resource
        )

    # ── Audit / observabilité ────────────────────────────────────────────

    def _record(
        self,
        decision: AuditDecision,
        actor: str,
        category: str,
        action: str,
        resource: str,
        policy_id: str,
        reason: str,
    ) -> None:
        """Enregistre la décision dans l'AuditStore (append-only)."""
        if self._audit is None:
            return
        try:
            self._audit.log(
                category=AuditCategory.SECURITY,
                decision=decision,
                action=f"{category}:{action}",
                actor=actor,
                source="policy",
                details={
                    "category": category,
                    "action": action,
                    "resource": resource,
                    "policy_id": policy_id,
                    "reason": reason,
                },
                tags=["policy", "tool", decision.value],
            )
        except Exception as exc:  # l'audit ne doit jamais bloquer l'exécution
            logger.error("SecureToolEnforcer: audit failed: %s", exc)

    def _subject(self, tool: Tool, context: ToolContext) -> str:
        if self._subject_resolver is not None:
            try:
                return self._subject_resolver(context)
            except Exception:
                pass
        user = getattr(context, "user_id", "default") or "default"
        return f"user:{user}"


def build_secure_enforcer(
    capabilities: Any | None = None,
    exfil: ExfilGuard | None = None,
    audit: Any | None = None,
    engine: PolicyEngine | None = None,
) -> SecureToolEnforcer:
    """Fabrique un enforcer avec les briques par défaut du Core.

    ``audit`` : une instance d'``AuditStore`` (ou None pour désactiver l'audit).
    ``capabilities`` : un ``CapabilityManager`` (ou None pour ne pas exiger de
    capability — l'évaluation Policy reste toujours active).

    Par défaut (Phase 05), un ``CapabilityManager`` fail-closed est instancié sans
    aucune capability accordée : aucune action sensible n'est donc autorisée tant
    qu'aucune capability explicite n'a été accordée. Cela préserve le deny-by-default
    tout en activant le contrôle granulaire du sujet × ressource × opération × portée.
    """
    if capabilities is None:
        from core.security.policy.capabilities import CapabilityManager as _CM
        capabilities = _CM(allowed_roots=["/workspace"])
    return SecureToolEnforcer(
        engine=engine,
        capabilities=capabilities,
        exfil=exfil,
        audit=audit,
    )

