# Capability & Permission System — Phase 05

## Objectif

Permettre à ETHAN d'accorder des **capacités contrôlées et granulaires** sans
donner d'accès système illimité de façon implicite.

## Modèle de capability

Chaque capability définit :

| Attribut | Description |
|---|---|
| `subject` | Sujet (ex. `agent:atreus`, `user:alice`, `task:scan-42`) |
| `category` | Catégorie d'action : `filesystem`, `shell`, `docker`, `systemd`, `network`, `mcp`, `memory`, `configuration` |
| `operation` | Opération précise : `read`, `write`, `delete`, `list`, `execute` |
| `resource` | Ressource ciblée (pattern glob, ex. `/workspace/**`) |
| `scope` | Portée : `self` ou `shared` |
| `ttl_seconds` | Durée de vie (None = éternelle, interdit sauf exception CORE) |
| `risk_level` | Niveau de risque : `low`, `medium`, `high`, `critical` |
| `origin` | Provenance (ex. `core:bootstrap`, `user:consent`) |
| `revoked` | Si la capability a été révoquée |

## Exemple conceptuel

```
Agent:    agent:atreus
Resource: filesystem:/workspace/projects/ethan
Operation: READ
Duration: task
```

```python
from core.security.policy.capabilities import CapabilityManager, RiskLevel

cm = CapabilityManager(allowed_roots=["/workspace"])
cap = cm.grant(
    subject="agent:atreus",
    category="filesystem",
    operation="read",
    resource="/workspace/projects/ethan/**",
    scope="self",
    ttl_seconds=3600,
    risk_level=RiskLevel.LOW,
    origin="user:consent",
)

result, reason, _ = cm.check("agent:atreus", "filesystem", "read", "/workspace/projects/ethan/README.md")
assert result == "allow"
```

## Règle fondamentale : ne jamais dépasser la portée

Une capability accordée ne peut **jamais** permettre de dépasser sa portée.

```python
# Permission: READ /workspace/projects/ethan
# → ne permet PAS: READ ~/.ssh/id_rsa
result, _, _ = cm.check("agent:atreus", "filesystem", "read", "/root/.ssh/id_rsa")
assert result == "deny"  # hors portée
```

## Path Security

Le résolveur `resolve_safe_path()` protège contre :

- **Path traversal** : `../` est résolu et vérifié contre les racines autorisées → DENY si sortie.
- **Symlink escape** : `Path.resolve()` suit les symlinks ; le chemin résolu final est vérifié → DENY si sortie.
- **Mount escape** : `os.path.commonpath()` garantit que le chemin reste dans une racine autorisée → DENY sinon.

```python
from core.security.policy.capabilities import resolve_safe_path, PathSecurityError

# Bloquer un traversal
try:
    resolve_safe_path("/workspace/../../../etc/passwd", ["/workspace"])
except PathSecurityError:
    pass  # refusé

# Autorisé si dans les racines
resolve_safe_path("/workspace/file.txt", ["/workspace"])  # OK
```

## Hiérarchie & interaction avec le Policy Engine

Le CapabilityManager est **indépendant** mais **complémentaire** au
PolicyEngine (`Phase 04`) :

```
Request
  ↓
PolicyEngine.check()  ← SecurityGateway (Phase 03)
  ↓ DENY
  → refus
  ↓ ALLOW / REQUIRE_CONFIRMATION
CapabilityManager.check()  ← granularité runtime
  ↓ DENY
  → refus (fail-closed)
  ↓ ALLOW
  → exécution
```

## Révocation

Les capabilities sont **révocables** à tout moment :

```python
cm.revoke(cap.id)  # marque comme révoquée (conservation audit)
```

La révocation est un **marquage immuable** — l'entrée reste dans le gestionnaire
mais est ignorée par `check()` et `list_capabilities()`.

## Audit

Chaque utilisation est **traçée** (append-only) :

```python
entries = cm.audit_log  # list[AuditEntry]
summary = cm.audit_summary()
# {
#   "total_evaluations": 42,
#   "allowed": 38,
#   "denied": 4,
#   "active_capabilities": 3,
# }
```

## Catégories d'actions

| Category | Opérations |
|---|---|
| `filesystem` | `read`, `write`, `delete`, `list` |
| `shell` | `execute` |
| `docker` | `execute` |
| `systemd` | `execute` |
| `network` | `read`, `write` |
| `mcp` | `execute` |
| `memory` | `read`, `write` |
| `configuration` | `read`, `write` |

## Tests

```bash
pytest tests/security/test_policy_engine.py tests/security/test_capabilities.py \
       tests/security/test_api_wiring.py tests/security/test_ecosystem_integration.py -v
```

**21 tests** (`test_capabilities.py`) couvrant : allow/deny/fail-closed, TTL/expiration, conflit de
règles, priorité, path security (traversal/smlink/mount escape), révocation, audit
append-only, validation des catégories/opérations/scopes, et la règle
*fail-closed* (aucune capability = DENY).

**5 tests** (`test_api_wiring.py`) de câblage production, dont 3 ajoutés en Phase 05 :

| Test | Ce qui est prouvé |
|---|---|
| `test_toolmanager_with_secure_enforcer_rejects_forbidden_tool` | docker rejeté (policy CORE) — fail-closed |
| `test_toolmanager_with_secure_enforcer_rejects_uncategorized` | silence = DENY |
| `test_toolmanager_with_secure_enforcer_allows_workspace_read` | policy ALLOW + capability active → exécution |
| `test_toolmanager_capability_scope_cannot_exceed` ⭐ | capability `/workspace/**` ≠ lecture `~/.ssh` → DENY |
| `test_toolmanager_capability_lower_than_constitution_deny` ⭐ | capability rm ≠ annulation d'une règle CORE(1) |

⭐ = cas de validation de la Phase 05 : **une capability ne peut jamais permettre de
dépasser sa portée**, et **ne peut jamais annuler une règle supérieure**.

## Intégration production (Phase 05)

`core/security/integration.py` → `build_secure_enforcer()` instancie désormais par défaut
un `CapabilityManager(allowed_roots=["/workspace"])` **sans capabilities** → fail-closed :
aucune action sensible n'est autorisée tant qu'une capability explicite n'est pas accordée.
Câblage dans `interfaces/api/main.py` :

```python
from core.security.integration import build_secure_enforcer
secure_enforcer = build_secure_enforcer()                       # PolicyEngine + CapabilityManager
tool_manager = ToolManager(store=domain_store, policy_enforcer=secure_enforcer)
```

→ Tous les chemins d'exécution (routeur `/tools`, skills) transitent par
`SecureToolEnforcer.check` → `PolicyEngine` → `CapabilityManager` → `ExfilGuard` → `AuditStore`.
**Non-contournable** : le callback d'exécution n'est jamais invoqué si DENY.