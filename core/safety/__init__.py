"""Safety & Permission Model — ADR-1009

Système de garde-fous de sécurité unifié:
- RBAC (Role-Based Access Control)
- Permission checking
- Audit logging
- Risk assessment
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from core.events import Event, EventBus, EventHandler, EventType


logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Niveaux de risque."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Effect(str, Enum):
    """Effet d'une permission."""
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class Permission:
    """Permission atomique."""
    resource: str
    action: str
    effect: Effect = Effect.ALLOW


@dataclass
class Role:
    """Rôle avec permissions."""
    name: str
    permissions: List[Permission]
    inherits: List[str] = field(default_factory=list)


@dataclass
class SafetyContext:
    """Contexte de sécurité pour une requête."""
    user_id: str
    roles: List[str]
    risk_level: RiskLevel = RiskLevel.LOW
    metadata: Optional[dict] = None


@dataclass
class AuditEvent:
    """Événement d'audit."""
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    result: str
    risk_level: RiskLevel
    metadata: dict


class RoleRegistry(ABC):
    """Interface abstraite pour le registre des rôles."""

    @abstractmethod
    def get_role(self, name: str) -> Role:
        """Récupérer un rôle par nom."""
        pass

    @abstractmethod
    def list_roles(self) -> List[str]:
        """Lister tous les rôles."""
        pass

    @abstractmethod
    def register_role(self, role: Role) -> None:
        """Enregistrer un rôle."""
        pass


class SafetyChecker(ABC):
    """Interface abstraite pour le vérificateur de sécurité."""

    @abstractmethod
    async def check_permission(
        self, context: SafetyContext, resource: str, action: str
    ) -> bool:
        """Vérifier si l'utilisateur a la permission."""
        pass

    @abstractmethod
    async def assess_risk(self, context: SafetyContext, action: str) -> RiskLevel:
        """Évaluer le risque d'une action."""
        pass


class AuditLogger(ABC):
    """Interface abstraite pour le logger d'audit."""

    @abstractmethod
    async def log(
        self,
        user_id: str,
        action: str,
        resource: str,
        result: str,
        risk_level: RiskLevel = RiskLevel.LOW,
        metadata: Optional[dict] = None,
    ) -> None:
        """Logger un événement d'audit."""
        pass


class DefaultRoleRegistry(RoleRegistry):
    """Implémentation par défaut du registre des rôles."""

    def __init__(self):
        self._roles: dict[str, Role] = {}

    def register_role(self, role: Role) -> None:
        """Enregistrer un rôle."""
        self._roles[role.name] = role
        logger.info(f"Role registered: {role.name}")

    def get_role(self, name: str) -> Role:
        """Récupérer un rôle par nom."""
        if name not in self._roles:
            raise ValueError(f"Role '{name}' not found")
        return self._roles[name]

    def list_roles(self) -> List[str]:
        """Lister tous les rôles."""
        return list(self._roles.keys())


class DefaultSafetyChecker(SafetyChecker):
    """Implémentation par défaut du vérificateur de sécurité."""

    def __init__(self, role_registry: RoleRegistry):
        self.role_registry = role_registry

    async def check_permission(
        self, context: SafetyContext, resource: str, action: str
    ) -> bool:
        """Vérifier si l'utilisateur a la permission."""
        permissions = await self._get_user_permissions(context)

        # Chercher une permission explicite
        for perm in permissions:
            if perm.resource == resource and perm.action == action:
                return perm.effect == Effect.ALLOW

        # Deny by default
        return False

    async def _get_user_permissions(self, context: SafetyContext) -> List[Permission]:
        """Récupérer toutes les permissions d'un utilisateur."""
        permissions = []
        seen = set()

        for role_name in context.roles:
            try:
                role = self.role_registry.get_role(role_name)
                for perm in role.permissions:
                    perm_key = (perm.resource, perm.action, perm.effect)
                    if perm_key not in seen:
                        seen.add(perm_key)
                        permissions.append(perm)

                # Récupérer les permissions des rôles hérités
                if role.inherits:
                    for inherited_role_name in role.inherits:
                        try:
                            inherited_role = self.role_registry.get_role(inherited_role_name)
                            for perm in inherited_role.permissions:
                                perm_key = (perm.resource, perm.action, perm.effect)
                                if perm_key not in seen:
                                    seen.add(perm_key)
                                    permissions.append(perm)
                        except ValueError:
                            logger.warning(f"Inherited role '{inherited_role_name}' not found")
            except ValueError:
                logger.warning(f"Role '{role_name}' not found")

        return permissions

    async def assess_risk(self, context: SafetyContext, action: str) -> RiskLevel:
        """Évaluer le risque d'une action."""
        # Simplified risk assessment
        high_risk_actions = ["delete", "drop", "truncate", "shutdown", "admin"]
        
        if any(risk_action in action.lower() for risk_action in high_risk_actions):
            return RiskLevel.HIGH
        
        # Check user risk level
        if context.risk_level == RiskLevel.CRITICAL:
            return RiskLevel.CRITICAL
        
        return RiskLevel.LOW


class DefaultAuditLogger(AuditLogger, EventHandler):
    """Implémentation par défaut du logger d'audit avec EventBus."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        # S'abonner aux événements de sécurité
        # Note: L'abonnement se fait de manière asynchrone via subscribe()

    async def log(
        self,
        user_id: str,
        action: str,
        resource: str,
        result: str,
        risk_level: RiskLevel = RiskLevel.LOW,
        metadata: Optional[dict] = None,
    ) -> None:
        """Logger un événement d'audit."""
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            risk_level=risk_level,
            metadata=metadata or {},
        )

        # Publier sur l'event bus
        await self.event_bus.publish(
            Event(
                type=EventType.SECURITY_AUDIT,
                source="safety",
                data={
                    "user_id": event.user_id,
                    "action": event.action,
                    "resource": event.resource,
                    "result": event.result,
                    "risk_level": event.risk_level,
                    "metadata": event.metadata,
                },
            )
        )

        logger.info(
            f"AUDIT: {event.user_id} {event.action} {event.resource} -> {event.result} "
            f"(risk: {event.risk_level})"
        )

    async def handle(self, event: Event) -> None:
        """Traiter un événement (implémentation EventHandler)."""
        if event.type == EventType.SECURITY_AUDIT:
            # Already logged in log() method
            pass


# Global instances
role_registry = DefaultRoleRegistry()
safety_checker = DefaultSafetyChecker(role_registry)
audit_logger = None  # Initialisé avec EventBus après création