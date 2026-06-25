"""Security Gateway — Point d'entrée unique pour toutes les actions.

Flux : Action → Signatures → Permissions → Politiques → Rate Limit → Exécution
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from core.security.types import (
    Action,
    ActionResult,
    ActionType,
    Identity,
    SecurityContext,
    TrustLevel,
    ValidationResult,
)

logger = logging.getLogger(__name__)


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
            SignatureValidator,
            PermissionChecker,
            PolicyEngine,
            RateLimiter,
        )
        from core.security.audit import AuditLogger

        self._validators = [
            SignatureValidator(),
            PermissionChecker(),
            PolicyEngine(),
            RateLimiter(),
        ]

        self._audit_logger = AuditLogger()

        logger.info("Security Gateway initialized")

    async def execute(self, action_type: str, params: dict[str, Any], source: str = "llm") -> ActionResult:
        """Point d'entrée pour exécuter une action.

        Args:
            action_type: Type d'action
            params: Paramètres de l'action
            source: Source ("llm", "user", "system")

        Returns:
            Résultat de l'action (validée ou rejetée)
        """
        # Créer l'action
        action = Action(
            id=str(uuid.uuid4()),
            type=ActionType(action_type),
            source=source,
            signature=f"sig-{uuid.uuid4().hex[:8]}",
            params=params,
        )

        # Créer le contexte de sécurité
        context = SecurityContext(
            identity=Identity(id=source, type=source, name=source),
            trust_level=self._get_default_trust(source),
            session_id=params.get("session_id", "default"),
            correlation_id=str(uuid.uuid4()),
        )

        # Valider l'action
        valid, result = await self._validate(action, context)

        if not valid:
            # Logger le rejet
            if self._audit_logger:
                await self._audit_logger.log_action(action, result, context)

            return result

        # Logger le succès
        if self._audit_logger:
            await self._audit_logger.log_action(action, result, context)

        return result

    async def _validate(self, action: Action, context: SecurityContext) -> tuple[bool, ActionResult]:
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
                logger.warning(f"Validation failed: {validator.__class__.__name__}: {result.reason}")

                return False, ActionResult(
                    action_id=action.id,
                    valid=False,
                    status="rejected",
                    error=result.reason,
                    violations=violations,
                )

            validators_passed.append(validator.__class__.__name__)

        # Validation réussie
        logger.info(f"Validation passed: {', '.join(validators_passed)}")

        # TODO: Exécuter l'action via Executor
        return True, ActionResult(
            action_id=action.id,
            valid=True,
            status="executed",
            sandbox_used="docker",  # TODO: Sélectionner sandbox
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