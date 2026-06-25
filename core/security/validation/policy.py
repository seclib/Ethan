"""Policy Engine — Moteur de politiques de sécurité.

Utilise OPA/Rego pour évaluer les politiques.
Simulation MVP : règles Python.
Production : OPA avec policies/*.rego.
"""

from __future__ import annotations

import logging
from typing import Any

from core.security.types import Action, SecurityContext, ValidationResult

logger = logging.getLogger(__name__)


class PolicyEngine:
    """Moteur de politiques de sécurité.

    Politiques :
    - Interdiction de commandes dangereuses
    - Limitation de ressources
    - Contrôle de conformité
    """

    def __init__(self):
        self._policies = self._load_default_policies()

    async def validate(self, action: Action, context: SecurityContext) -> ValidationResult:
        """Vérifie les politiques.

        Args:
            action: Action à valider
            context: Contexte de sécurité

        Returns:
            Résultat de validation
        """
        violations = []

        for policy in self._policies:
            result = policy(action, context)
            if result:
                violations.append(result)

        if violations:
            return ValidationResult(
                valid=False,
                reason="Policy violations detected",
                violations=violations,
            )

        return ValidationResult(
            valid=True,
            validators_passed=["policy"],
        )

    def _load_default_policies(self) -> list[callable]:
        """Charge les politiques par défaut."""
        return [
            self._policy_no_dangerous_commands,
            self._policy_no_sudo,
            self._policy_no_system_files,
            self._policy_rate_limit,
        ]

    def _policy_no_dangerous_commands(self, action: Action, context: SecurityContext) -> str | None:
        """Interdit les commandes destructives."""
        if action.type == "command":
            cmd = action.params.get("command", "")
            if cmd in ["rm", "dd", "mkfs", "format"]:
                args = action.params.get("args", [])
                if "-rf" in args or "-r" in args:
                    return f"Dangerous command: {cmd} with recursive flag"
                if cmd == "dd":
                    return f"Dangerous command: {cmd} is forbidden"
        return None

    def _policy_no_sudo(self, action: Action, context: SecurityContext) -> str | None:
        """Interdit sudo pour les sources non autorisées."""
        if action.type == "command":
            cmd = action.params.get("command", "")
            if cmd == "sudo":
                if context.trust_level.value not in ["high", "critical"]:
                    return "Sudo requires HIGH or CRITICAL trust level"
        return None

    def _policy_no_system_files(self, action: Action, context: SecurityContext) -> str | None:
        """Interdit l'accès aux fichiers système."""
        if action.type in ["file_write", "file_read"]:
            path = action.params.get("path", "")
            system_paths = ["/etc/", "/usr/", "/boot/", "/sys/", "/proc/"]
            for sys_path in system_paths:
                if path.startswith(sys_path):
                    if context.trust_level.value not in ["high", "critical"]:
                        return f"System file access requires HIGH trust: {path}"
        return None

    def _policy_rate_limit(self, action: Action, context: SecurityContext) -> str | None:
        """Limite le taux d'actions."""
        # TODO: Implémenter avec compteur Redis
        return None