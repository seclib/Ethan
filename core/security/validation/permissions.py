"""Permission Checker — Vérifie les permissions RBAC + ABAC."""

from __future__ import annotations

import logging
from typing import Any

from core.security.types import Action, ActionType, Permission, SecurityContext, TrustLevel, ValidationResult

logger = logging.getLogger(__name__)


class PermissionChecker:
    """Vérifie les permissions."""

    def __init__(self):
        # Rôles prédéfinis (MVP: en dur, production: depuis DB)
        self._roles = {
            "llm": {
                "permissions": [
                    Permission(resource="memory", action="read", scope="user"),
                    Permission(resource="capability", action="invoke", scope="user", 
                              conditions={"trust_level": "medium"}),
                ],
                "trust_level": TrustLevel.LOW,
            },
            "user": {
                "permissions": [
                    Permission(resource="file", action="read", scope="user"),
                    Permission(resource="file", action="write", scope="user"),
                    Permission(resource="network", action="request", scope="user"),
                    Permission(resource="capability", action="invoke", scope="user"),
                    Permission(resource="command", action="execute", scope="user"),
                ],
                "trust_level": TrustLevel.MEDIUM,
            },
            "admin": {
                "permissions": [
                    Permission(resource="*", action="*", scope="*"),
                ],
                "trust_level": TrustLevel.HIGH,
            },
            "system": {
                "permissions": [
                    Permission(resource="*", action="*", scope="*"),
                ],
                "trust_level": TrustLevel.CRITICAL,
            },
        }

    async def validate(self, action: Action, context: SecurityContext) -> ValidationResult:
        """Vérifie les permissions.

        Modèle RBAC + ABAC.
        """
        # Récupérer le rôle
        role_data = self._roles.get(context.identity.type)
        if not role_data:
            return ValidationResult(
                valid=False,
                reason=f"No role for identity type: {context.identity.type}",
            )

        role_permissions = role_data["permissions"]

        # Vérifier la permission requise
        required_permission = self._get_required_permission(action)

        # Vérifier si le rôle a la permission
        has_permission = self._check_permission(role_permissions, required_permission, context)

        if not has_permission:
            return ValidationResult(
                valid=False,
                reason=f"Permission denied: {required_permission.resource}:{required_permission.action}",
                violations=[f"missing_permission:{required_permission.resource}:{required_permission.action}"],
            )

        return ValidationResult(
            valid=True,
            validators_passed=["permissions"],
        )

    def _get_required_permission(self, action: Action) -> Permission:
        """Détermine la permission requise."""
        # Mapper ActionType vers Permission
        resource_map = {
            ActionType.COMMAND: "command",
            ActionType.CAPABILITY: "capability",
            ActionType.FILE_READ: "file",
            ActionType.FILE_WRITE: "file",
            ActionType.NETWORK: "network",
            ActionType.MEMORY_READ: "memory",
            ActionType.MEMORY_WRITE: "memory",
            ActionType.PLUGIN_INSTALL: "plugin",
            ActionType.CONFIG_CHANGE: "config",
        }

        action_map = {
            ActionType.COMMAND: "execute",
            ActionType.CAPABILITY: "invoke",
            ActionType.FILE_READ: "read",
            ActionType.FILE_WRITE: "write",
            ActionType.NETWORK: "request",
            ActionType.MEMORY_READ: "read",
            ActionType.MEMORY_WRITE: "write",
            ActionType.PLUGIN_INSTALL: "install",
            ActionType.CONFIG_CHANGE: "change",
        }

        resource = resource_map.get(action.type, "*")
        operation = action_map.get(action.type, "*")

        return Permission(
            resource=resource,
            action=operation,
            scope=action.source,
        )

    def _check_permission(self, role_permissions: list[Permission], required: Permission, context: SecurityContext) -> bool:
        """Vérifie si le rôle a la permission.

        Args:
            role_permissions: Permissions du rôle
            required: Permission requise
            context: Contexte de sécurité

        Returns:
            True si autorisé
        """
        for perm in role_permissions:
            # Vérifier le resource (avec wildcard)
            if not self._matches(perm.resource, required.resource):
                continue

            # Vérifier l'action (avec wildcard)
            if not self._matches(perm.action, required.action):
                continue

            # Vérifier le scope (avec wildcard)
            if not self._matches(perm.scope, required.scope):
                continue

            # Vérifier les conditions (ABAC)
            if perm.conditions:
                if not self._check_conditions(perm.conditions, context):
                    continue

            # Permission accordée
            return True

        return False

    def _matches(self, pattern: str, value: str) -> bool:
        """Vérifie si value matche pattern (avec wildcard)."""
        if pattern == "*":
            return True
        return pattern == value

    def _check_conditions(self, conditions: dict[str, Any], context: SecurityContext) -> bool:
        """Vérifie les conditions ABAC.

        Conditions supportées :
        - trust_level: "low", "medium", "high", "critical"
        - time_range: {"start": "09:00", "end": "17:00"}
        - ip_whitelist: ["192.168.1.0/24"]
        """
        # Vérifier trust_level
        if "trust_level" in conditions:
            required_level = TrustLevel(conditions["trust_level"])
            if context.trust_level.value != required_level.value:
                # Vérifier hiérarchie
                level_order = [TrustLevel.UNTRUSTED, TrustLevel.LOW, TrustLevel.MEDIUM, 
                              TrustLevel.HIGH, TrustLevel.CRITICAL]
                required_idx = level_order.index(required_level)
                actual_idx = level_order.index(context.trust_level)
                if actual_idx < required_idx:
                    return False

        # Vérifier time_range
        if "time_range" in conditions:
            from datetime import datetime
            now = datetime.utcnow()
            start = datetime.strptime(conditions["time_range"]["start"], "%H:%M").time()
            end = datetime.strptime(conditions["time_range"]["end"], "%H:%M").time()
            if not (start <= now.time() <= end):
                return False

        # Vérifier ip_whitelist
        if "ip_whitelist" in conditions:
            if context.ip_address not in conditions["ip_whitelist"]:
                return False

        return True