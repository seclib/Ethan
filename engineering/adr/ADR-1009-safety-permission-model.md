# ADR-1009 — Safety & Permission Model

> **Statut** : Proposed
> **Date** : 2026-06-23

---

## Context

Le système actuel n'a pas de garde-fous de sécurité unifiés. Pour un système production-grade, nous avons besoin de:

- **RBAC** — Role-Based Access Control
- **Permission checking** — Vérification avant exécution
- **Audit logging** — Traçabilité complète
- **Risk assessment** — Évaluation des risques
- **Compliance** — Conformité aux politiques

Sans sécurité unifiée:
- Risque d'escalade de privilèges
- Pas de traçabilité
- Difficile d'appliquer des politiques
- Non-conforme aux standards de sécurité

---

## Decision

Le système doit avoir un **Safety & Permission Model** unifié:

> **Safety Layer with RBAC + Audit + Risk Assessment**

---

## Safety Schema

```python
class Permission:
    """Permission atomique."""
    resource: str
    action: str
    effect: Literal["allow", "deny"]

class Role:
    """Rôle avec permissions."""
    name: str
    permissions: List[Permission]
    inherits: List[str]

class SafetyContext:
    """Contexte de sécurité pour une requête."""
    user_id: str
    roles: List[str]
    permissions: List[Permission]
    risk_level: RiskLevel

class SafetyChecker:
    """Vérificateur de sécurité."""
    
    async def check_permission(self, context: SafetyContext, resource: str, action: str) -> bool
    async def assess_risk(self, context: SafetyContext, action: str) -> RiskLevel
    async def audit(self, context: SafetyContext, action: str, result: str)

class AuditLogger:
    """Logger d'audit pour traçabilité."""
    
    async def log(self, event: AuditEvent)
    async def query(self, filters: AuditFilters) -> List[AuditEvent]
```

---

## Implementation

### Core Types

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Literal

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Effect(str, Enum):
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
    inherits: List[str] = None  # Role inheritance

@dataclass
class SafetyContext:
    """Contexte de sécurité."""
    user_id: str
    roles: List[str]
    risk_level: RiskLevel = RiskLevel.LOW
    metadata: dict = None
```

### Safety Checker

```python
class SafetyChecker:
    """Vérificateur de sécurité central."""
    
    def __init__(self, role_registry: RoleRegistry):
        self.role_registry = role_registry
    
    async def check_permission(
        self, 
        context: SafetyContext, 
        resource: str, 
        action: str
    ) -> bool:
        """Vérifier si l'utilisateur a la permission."""
        # Récupérer toutes les permissions de l'utilisateur
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
        
        for role_name in context.roles:
            role = self.role_registry.get_role(role_name)
            permissions.extend(role.permissions)
            
            # Récupérer les permissions des rôles hérités
            if role.inherits:
                for inherited_role in role.inherits:
                    inherited = self.role_registry.get_role(inherited_role)
                    permissions.extend(inherited.permissions)
        
        return permissions
```

### Audit Logger

```python
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

class AuditLogger:
    """Logger d'audit pour traçabilité."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
    
    async def log(
        self, 
        user_id: str, 
        action: str, 
        resource: str, 
        result: str,
        risk_level: RiskLevel = RiskLevel.LOW,
        metadata: dict = None
    ):
        """Logger un événement d'audit."""
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            risk_level=risk_level,
            metadata=metadata or {}
        )
        
        # Publier sur l'event bus
        await self.event_bus.publish(Event(
            type=EventType.SECURITY_AUDIT,
            source="safety",
            data=event.__dict__
        ))
```

---

## Consequences

* **Security** — Vérification systématique des permissions
* **Traceability** — Audit complet de toutes les actions
* **Compliance** — Conforme aux standards de sécurité
* **Risk management** — Évaluation et mitigation des risques
* **Accountability** — Responsabilité claire des actions

---

## Compliance

* Toute action sensible nécessite une vérification de permission
* Toutes les actions sont auditées
* RBAC avec héritage de rôles
* Deny by default
* Risk assessment avant actions critiques

## References

* [Constitution Architecturale](/engineering/architecture/constitution.md) — Principe 6 (Safety First)
* [ADR-1007](/engineering/adr/ADR-1007-event-driven-architecture.md) — Event-Driven Architecture
* [ADR-1005](/engineering/adr/ADR-1005-core-technology-independence.md) — Core Technology Independence