"""Security Gateway — Point d'entrée unique pour toutes les actions.

Flux : Action → Signatures → Permissions → Politiques → Rate Limit → Audit

Contrat (CTO P0-1) : le gateway **valide** les actions des routes API
sensibles (rate limiting par acteur, permissions, politiques, audit) ;
l'exécution est **déléguée** au handler de route puis, pour les outils, au
``ToolExecutor`` sous ``SecureToolEnforcer``. Le gateway ne contourne jamais
cette chaîne — il la précède.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

from core.security.types import (
    Action,
    ActionResult,
    ActionType,
    Identity,
    SecurityContext,
    TrustLevel,
)

logger = logging.getLogger(__name__)

# Rate limit par défaut : 100 actions / 60 s et par acteur (surchargeable
# via ETHAN_GATEWAY_RATE_LIMIT pour l'observabilité et les environnements
# chargeés).
ENV_RATE_LIMIT = "ETHAN_GATEWAY_RATE_LIMIT"
ENV_RATE_WINDOW = "ETHAN_GATEWAY_RATE_WINDOW"


class SecurityGateway:
    """Point d'entrée unique pour toutes les actions.

    Le LLM ne peut PAS exécuter directement une commande.
    Le LLM propose → ETHAN décide via SecurityGateway.
    """

    def __init__(self):
        # Initialisation paresseuse des validators
        self._validators: list[Any] | None = None
        self._audit_logger: Any = None

    async def initialize(self) -> None:
        """Initialise les composants de sécurité."""
        from core.security.validation import (
            PermissionChecker,
            PolicyEngine,
            RateLimiter,
            SignatureValidator,
        )

        max_actions = int(os.getenv(ENV_RATE_LIMIT, "100"))
        window = int(os.getenv(ENV_RATE_WINDOW, "60"))

        self._validators = [
            SignatureValidator(),
            PermissionChecker(),
            PolicyEngine(),
            RateLimiter(max_actions=max_actions, window_seconds=window),
        ]

        # Audit append-only du Core (JSONL/PostgreSQL) — remplace l'ancien
        # import `core.security.audit` inexistant qui rendait ce module
        # inutilisable (ModuleNotFoundError à l'initialisation).
        try:
            from core.audit import AuditStore

            self._audit_logger = AuditStore()
        except Exception as exc:  # pragma: no cover — dégradation non bloquante
            logger.warning("Security Gateway: audit store unavailable (%s)", exc)
            self._audit_logger = None

        logger.info("Security Gateway initialized")

    async def execute(
        self,
        action_type: str,
        params: dict[str, Any],
        source: str = "llm",
        actor: str | None = None,
    ) -> ActionResult:
        """Point d'entrée pour **valider** une action.

        Args:
            action_type: Type d'action (valeur d'``ActionType``)
            params: Paramètres de l'action
            source: Source (``llm``, ``user``, ``system``…)
            actor: Identifiant de l'acteur réel (rate limit par acteur).
                Par défaut, ``source`` fait foi.

        Returns:
            ActionResult — ``valid=True`` signifie que l'action est
            **autorisée à être exécutée** par le handler appelant (le
            gateway n'exécute pas lui-même : séparation validation /
            exécution).
        """
        # Créer l'action
        action = Action(
            id=str(uuid.uuid4()),
            type=ActionType(action_type),
            source=source,
            signature=f"sig-{uuid.uuid4().hex[:8]}",
            params=params,
        )

        # Créer le contexte de sécurité (identity.id = acteur réel → le
        # RateLimiter isole chaque utilisateur).
        context = SecurityContext(
            identity=Identity(id=actor or source, type=source, name=actor or source),
            trust_level=self._get_default_trust(source),
            session_id=params.get("session_id", "default"),
            correlation_id=str(uuid.uuid4()),
        )

        # Valider l'action
        valid, result = await self._validate(action, context)

        # Journalisation append-only (succès ET rejets).
        await self._log_action(action, result, context)

        return result

    async def _log_action(
        self, action: Action, result: ActionResult, context: SecurityContext
    ) -> None:
        """Journalise la décision dans l'audit Core (append-only)."""
        if not self._audit_logger:
            return
        try:
            from core.audit import AuditCategory, AuditDecision

            decision = AuditDecision.ALLOWED if result.valid else AuditDecision.DENIED
            details: dict[str, Any] = {
                "action_id": action.id,
                "correlation_id": context.correlation_id,
            }
            if not result.valid:
                details["error"] = result.error
                details["violations"] = list(result.violations or [])
            self._audit_logger.log(
                category=AuditCategory.SECURITY,
                decision=decision,
                action=action.type.value,
                actor=context.identity.id,
                source=action.source,
                details=details,
                correlation_id=context.correlation_id,
            )
        except Exception as exc:  # pragma: no cover — l'audit ne casse jamais l'API
            logger.warning("Security Gateway: audit log failed (%s)", exc)

    async def _validate(
        self, action: Action, context: SecurityContext
    ) -> tuple[bool, ActionResult]:
        """Valide une action via la chaîne de validation.

        Args:
            action: Action à valider
            context: Contexte de sécurité

        Returns:
            (valid, result)
        """
        if not self._validators:
            await self.initialize()

        validators_passed = []
        violations = []

        for validator in self._validators:
            result = await validator.validate(action, context)

            if not result.valid:
                violations.extend(result.violations)
                logger.warning(
                    f"Validation failed: {validator.__class__.__name__}: {result.reason}"
                )

                return False, ActionResult(
                    action_id=action.id,
                    valid=False,
                    status="rejected",
                    error=result.reason,
                    violations=violations,
                )

            validators_passed.append(validator.__class__.__name__)

        # Validation réussie : l'action est autorisée — l'exécution revient au
        # handler de route (puis au ToolExecutor sous SecureToolEnforcer).
        # Le statut n'est plus "executed" : le gateway valide, il n'exécute
        # pas (ancien TODO « Exécuter l'action via Executor » clarifié).
        logger.info(f"Validation passed: {', '.join(validators_passed)}")
        return True, ActionResult(
            action_id=action.id,
            valid=True,
            status="validated",
            validators_passed=validators_passed,
        )

    def _get_default_trust(self, source: str) -> TrustLevel:
        """Niveau de confiance par défaut selon la source."""
        trust_map = {
            "system": TrustLevel.CRITICAL,
            "admin": TrustLevel.HIGH,
            "user": TrustLevel.MEDIUM,
            "plugin": TrustLevel.LOW,
            "llm": TrustLevel.UNTRUSTED,
        }
        return trust_map.get(source, TrustLevel.UNTRUSTED)
