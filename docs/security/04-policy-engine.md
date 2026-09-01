# Policy Engine — Phase 04

> **Statut** : ✅ IMPLEMENTED & VERIFIED.
> **Objectif de la phase** : toute action sensible peut être évaluée avant exécution via
> `Request → PolicyEngine → ALLOW | DENY | REQUIRE_CONFIRMATION`, le moteur étant
> **indépendant du LLM** et **non contournable**.
> Implémentation réelle : `core/security/policy/` et `core/security/integration.py`.
> Aucun accès système plus large n'est accordé à ETHAN (deny-by-default).

---

## 1. Architecture du moteur

```
   Request (category, action, resource, params, source)
        │  source = INFORMATIONNEL (A6 : pas d'influence sur la décision)
        ▼
   PolicyEngine.evaluate()        ← core/security/policy/engine.py
        │ 1. collecte des règles matchantes (glob category/action/resource)  A5
        │ 2. silence = DENY                                          A4
        │ 3. niveau le plus fort (1..8)                             A1
        │ 4. effet le plus restrictif à ce niveau (DENY>CONFIRM>ALLOW)  A3
        │ 5. on ne redescend pas (niveau inférieur ne contredit jamais)  A2
        ▼
   PolicyDecision { result, reason, policy_id, level, matched[] }
        ├─ DENY            → PolicyDeniedError   (bloquant)
        ├─ REQUIRE_CONFIRMATION → approver ? ALLOW : DENY (fail-closed CR-7)
        └─ ALLOW           → exécution
```

Indépendance du LLM : aucune instruction textuelle, prompt, skill ou sortie de LLM ne peut
modifier une règle (immuable en lecture) ni influencer une décision (A6 : `source` est
informationnel). Les mappages catégorie/action/ressource sont structuraux (métadonnées
+ params), jamais dérivés du contenu d'un prompt.

## 2. Hiérarchie (8 niveaux) — appliquée

| Niveau | Catégorie | Source | Classe |
|---|---|---|---|
| 1 | CORE CONSTITUTION | Constitution | CORE (inviolable) |
| 2 | SECURITY POLICIES | Core security module | PROTECTED |
| 3 | SYSTEM POLICIES | opérationnel | PROTECTED |
| 4 | PROJECT POLICIES | projet/domaine | PROTECTED ou USER |
| 5 | AGENT POLICIES | agent | USER |
| 6 | TASK POLICIES | tâche/session | USER |
| 7 | USER PREFERENCES | utilisateur | USER |
| 8 | LLM INSTRUCTIONS | prompts/skills/RAG | **aucun pouvoir normatif** |

## 3. Catégories & règles

`ActionCategory` : filesystem, process, shell, docker, network, mcp, memory,
configuration, external_transmission (`core/security/policy/types.py`).
Règles par défaut (`rules.py`) : DENY sur tout effet de bord, REQUIRE_CONFIRMATION sur
suppressions/transmissions/MCP/config, ALLOW limité à lecture workspace + mémoire user.

---

## 4. Non-contourgabilité (le point critique)

`PolicyGuard` (`core/security/policy/guard.py`) : point d'entrée obligatoire.

- `guard.execute(...)` **n'appelle jamais** le callback en cas de DENY ou de confirmation refusée.
- `REQUIRE_CONFIRMATION` sans `approver` → **refus fail-closed** (CR-7).
- `SecureToolEnforcer` (`core/security/integration.py`) orchestre, dans l'ordre,
  `PolicyEngine` + `CapabilityManager` + `ExfilGuard` (transmission) + `AuditStore`.

### Câblage production (correction Phase 04)

Avant la phase, `interfaces/api/main.py` instanciait `ToolManager(store=...)` **sans enforcer** →
les tools pouvaient s'exécuter sans évaluation. Correction appliquée :

```python
from core.security.integration import build_secure_enforcer
secure_enforcer = build_secure_enforcer()
tool_manager = ToolManager(store=domain_store, policy_enforcer=secure_enforcer)
```

Le `SkillManager` réutilise ce même `ToolManager` → les skills passent par le moteur.

---

## 5. Tests (preuve)

`pytest tests/security/test_policy_engine.py` → **25 tests passants** (ALLOW, DENY, CONFIRM,
conflit intra-niveau, priorité, fail-closed, no-inference, source neutre, déterminisme,
8 catégories).

`tests/security/test_api_wiring.py` → **3 tests passants** : docker rejeté, uncategorized
rejeté (fail-closed), lecture `/workspace/**` autorisée et exécutée.

`tests/security/test_ecosystem_integration.py` → un tool refusé par la politique n'est jamais
exécuté (`status == "rejected"`).

**Total Phase 04 : 57 tests passants.**

### Exemples de conflits résolus par les tests

- `rm -rf /tmp` demandé par LLM/user/agent/tool/MCP → **DENY** (CORE), décision identique (A6).
- Docker demandé par un agent → **DENY** (SECURITY) même si l'AGENT POLICY le suggérait.
- Transmission externe de données sensibles → **DENY** (CR-4) ou REQUIRE_CONFIRMATION ; l'agent
  ne peut pas auto-autoriser.
- Silence de règle → **DENY** (fail-closed).

---

## 6. Limites (hors Phase 04)

- OPA/Rego non intégré (MVP Python).
- 22 fichiers de `tests/security/` héritant de l'ancien nom `openjarvis` (ex.
  `test_security_profiles.py`) sont une **suite legacy** (migration), non liée au Policy Engine —
  `test_policy_engine.py`, `test_ecosystem_integration.py` et `test_api_wiring.py` eux sont au
  format ETHAN actuel.
- L'API `/v1/policy` d'administration des règles niveaux 2–4 n'est pas exposée (Phase 05).

---

## 7. VERDICT — Phase 04 : **PASS**

- Demande `Request → Engine → ALLOW/DENY/REQUIRE_CONFIRMATION` avec raison explicite → ✅
- Moteur **indépendant du LLM** (aucune source normative textuelle) → ✅
- Toute action sensible **peut** être évaluée avant exécution → ✅
- Le chemin de production (`interfaces/api/main.py` → `ToolManager` → `ToolExecutor`) passe
  **obligatoirement** par `PolicyGuard` (non-contournable : callback jamais appelé si DENY) → ✅
- **Les actions interdites sont réellement bloquées** — prouvé par 57 tests, dont
  `test_toolmanager_with_secure_enforcer_rejects_forbidden_tool` (docker rejeté, fail-closed) → ✅
- Aucun accès système plus large n'est accordé (deny-by-default) → ✅

*Spécification v1.1 — moteur implémenté & validé. Prochaine étape : Phase 05
(capabilités structurées & éditeur d'USER RULES).*
