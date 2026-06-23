# ADR-1009 — Safety & Permission Model — Implementation Report

## Date
2026-06-23

## Statut
✅ **Implémenté**

---

## Résumé

Système de garde-fous de sécurité unifié implémenté avec:

- **RBAC** — Role-Based Access Control avec héritage
- **Permission checking** — Vérification avant exécution (deny by default)
- **Audit logging** — Traçabilité complète via EventBus
- **Risk assessment** — Évaluation automatique des risques

---

## Modifications

### 1. Core Model (`core/safety/__init__.py`)

**Ajouté:**
- `RiskLevel` (Enum) — LOW, MEDIUM, HIGH, CRITICAL
- `Effect` (Enum) — ALLOW, DENY
- `Permission` — Permission atomique (resource, action, effect)
- `Role` — Rôle avec permissions + héritage
- `SafetyContext` — Contexte de sécurité (user_id, roles, risk_level)
- `AuditEvent` — Événement d'audit
- `RoleRegistry` (ABC) — Interface abstraite
- `SafetyChecker` (ABC) — Interface abstraite
- `AuditLogger` (ABC) — Interface abstraite
- `DefaultRoleRegistry` — Implémentation avec stockage en mémoire
- `DefaultSafetyChecker` — Vérification + évaluation de risque
- `DefaultAuditLogger` — Logging via EventBus

### 2. Event Integration (`core/events/__init__.py`)

**Ajouté:**
- `EventType.SECURITY_AUDIT` — Type d'événement pour audits

### 3. Tests (`tests/core/test_safety.py`)

**Ajouté:**
- 23 tests unitaires couvrant:
  - Permission creation (allow/deny)
  - Role creation + inheritance
  - SafetyContext
  - RoleRegistry (CRUD)
  - SafetyChecker (permission check, deny by default, inheritance)
  - Risk assessment (low/high/critical)
  - AuditLogger (logging, metadata, high risk)
  - Integration tests (full flow, admin workflow)

**Résultat:** ✅ 23/23 tests passent

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Safety Layer (ADR-1009)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ RoleRegistry │  │SafetyChecker │  │ AuditLogger  │     │
│  │  - get_role  │  │ -check_perm  │  │  - log       │     │
│  │  - register  │  │ -assess_risk │  │  - query     │     │
│  │  - list      │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ utilise
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    EventBus (ADR-1007)                       │
│  Publie les événements SECURITY_AUDIT                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Exemples d'usage

### RBAC — Définir des rôles

```python
from core.safety import RoleRegistry, Role, Permission, Effect

registry = RoleRegistry()

# Créer un rôle utilisateur
user_role = Role(
    name="user",
    permissions=[
        Permission("file", "read"),
        Permission("file", "write"),
    ]
)

# Créer un rôle admin avec héritage
admin_role = Role(
    name="admin",
    permissions=[
        Permission("file", "read"),
        Permission("file", "write"),
        Permission("file", "delete"),
    ],
    inherits=["user"]  # Hérite des permissions de user
)

registry.register_role(user_role)
registry.register_role(admin_role)
```

### Permission Checking

```python
from core.safety import SafetyChecker, SafetyContext, RoleRegistry

checker = SafetyChecker(role_registry)

# Contexte utilisateur
user_context = SafetyContext(
    user_id="user_123",
    roles=["user"]
)

# Vérifier permission
allowed = await checker.check_permission(
    context=user_context,
    resource="file",
    action="read"
)
# allowed = True

# Vérifier action interdite
allowed = await checker.check_permission(
    context=user_context,
    resource="file",
    action="delete"
)
# allowed = False (deny by default)
```

### Risk Assessment

```python
from core.safety import RiskLevel

# Évaluer le risque
risk = await checker.assess_risk(
    context=user_context,
    action="read"
)
# risk = RiskLevel.LOW

risk = await checker.assess_risk(
    context=user_context,
    action="delete_data"
)
# risk = RiskLevel.HIGH
```

### Audit Logging

```python
from core.safety import AuditLogger, RiskLevel

audit = AuditLogger(event_bus)

# Logger une action
await audit.log(
    user_id="user_123",
    action="read",
    resource="file",
    result="success",
    risk_level=RiskLevel.LOW,
    metadata={"file_size": 1024}
)

# L'événement est publié sur EventBus
# Type: EventType.SECURITY_AUDIT
```

### Workflow complet

```python
from core.safety import (
    SafetyContext, SafetyChecker, AuditLogger, RiskLevel
)

# 1. Créer le contexte
context = SafetyContext(
    user_id="admin_123",
    roles=["admin"],
    risk_level=RiskLevel.LOW
)

# 2. Vérifier la permission
allowed = await checker.check_permission(
    context, "database", "delete"
)

if not allowed:
    await audit.log(
        user_id=context.user_id,
        action="delete",
        resource="database",
        result="denied",
        risk_level=RiskLevel.HIGH
    )
    raise PermissionError("Access denied")

# 3. Évaluer le risque
risk = await checker.assess_risk(context, "delete")

# 4. Exécuter l'action
# ... execute dangerous operation ...

# 5. Logger l'audit
await audit.log(
    user_id=context.user_id,
    action="delete",
    resource="database",
    result="success",
    risk_level=risk
)
```

---

## API Reference

### Core Types

```python
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
    resource: str
    action: str
    effect: Effect = Effect.ALLOW

@dataclass
class Role:
    name: str
    permissions: List[Permission]
    inherits: List[str] = []

@dataclass
class SafetyContext:
    user_id: str
    roles: List[str]
    risk_level: RiskLevel = RiskLevel.LOW
    metadata: Optional[dict] = None
```

### RoleRegistry

```python
class RoleRegistry(ABC):
    @abstractmethod
    def register_role(self, role: Role) -> None
    @abstractmethod
    def get_role(self, name: str) -> Role
    @abstractmethod
    def list_roles(self) -> List[str]
```

### SafetyChecker

```python
class SafetyChecker(ABC):
    @abstractmethod
    async def check_permission(
        self, context: SafetyContext, resource: str, action: str
    ) -> bool
    
    @abstractmethod
    async def assess_risk(
        self, context: SafetyContext, action: str
    ) -> RiskLevel
```

### AuditLogger

```python
class AuditLogger(ABC):
    @abstractmethod
    async def log(
        self,
        user_id: str,
        action: str,
        resource: str,
        result: str,
        risk_level: RiskLevel = RiskLevel.LOW,
        metadata: Optional[dict] = None
    ) -> None
```

---

## Conformité ADR-1009

| Règle ADR | Status | Preuve |
|-----------|--------|--------|
| RBAC | ✅ | RoleRegistry + Role avec permissions |
| Permission checking | ✅ | SafetyChecker.check_permission() |
| Deny by default | ✅ | Retourne False si permission non trouvée |
| Role inheritance | ✅ | Role.inherits + _get_user_permissions() |
| Audit logging | ✅ | AuditLogger + EventType.SECURITY_AUDIT |
| Risk assessment | ✅ | SafetyChecker.assess_risk() |
| Event-driven | ✅ | Intégré avec EventBus (ADR-1007) |
| Abstraction | ✅ | ABC pour RoleRegistry, SafetyChecker, AuditLogger |

---

## Impact

- ✅ **Security** — Vérification systématique des permissions
- ✅ **Traceability** — Audit complet via EventBus
- ✅ **Compliance** — RBAC + deny by default
- ✅ **Risk management** — Évaluation automatique des risques
- ✅ **Accountability** — Traçabilité complète des actions
- ✅ **Extensibility** — Abstractions pour implémentations custom
- ✅ **Integration** — Fonctionne avec EventBus (ADR-1007)
- ✅ **Testé** — 23 tests passent

---

## Références

- [ADR-1009](/engineering/adr/ADR-1009-safety-permission-model.md)
- [Constitution Architecturale](/engineering/architecture/constitution.md) — Principe 6 (Safety First)
- [ADR-1007](/engineering/adr/ADR-1007-event-driven-architecture.md) — Event-Driven Architecture
- [ADR-1005](/engineering/adr/ADR-1005-core-technology-independence.md) — Core Technology Independence