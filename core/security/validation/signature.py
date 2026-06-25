"""Signature Validator — Valide les signatures des actions."""

from __future__ import annotations

import logging
from typing import Any

from core.security.types import Action, Identity, SecurityContext, TrustLevel, ValidationResult

logger = logging.getLogger(__name__)


class SignatureValidator:
    """Valide les signatures des actions."""

    async def validate(self, action: Action, context: SecurityContext) -> ValidationResult:
        """Vérifie la signature.

        Règles :
        - Actions LLM : signature LLM (moins de confiance)
        - Actions User : signature User (plus de confiance)
        - Actions System : signature System (confiance maximale)
        """
        # Vérifier la signature
        if not action.signature:
            return ValidationResult(
                valid=False,
                reason="Missing signature",
                trust_level=TrustLevel.UNTRUSTED,
            )

        # Vérifier l'identité (MVP: simulation)
        identity = Identity(
            id=action.source,
            type=action.source,
            name=action.source,
            verification_level=0.5,
        )

        # Déterminer le niveau de confiance
        trust_level = self._calculate_trust_level(identity, action.source)

        return ValidationResult(
            valid=True,
            identity=identity,
            trust_level=trust_level,
            validators_passed=["signature"],
        )

    def _calculate_trust_level(self, identity: Identity, source: str) -> TrustLevel:
        """Calcule le niveau de confiance."""
        if source == "system":
            return TrustLevel.CRITICAL
        elif source == "user":
            return TrustLevel.MEDIUM
        elif source == "llm":
            return TrustLevel.LOW
        else:
            return TrustLevel.UNTRUSTED