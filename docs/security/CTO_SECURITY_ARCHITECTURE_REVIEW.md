# CTO Security Architecture Review — ETHAN

> **Classification** : Architecture Review (Audit)  
> **Audience** : CTO, CISO, Security Architects, Core Team  
> **Status** : Pre-Implementation — Foundation for Atreus  
> **Date** : 2026-03-09  
> **Author** : Chief Security Officer  

---

## Executive Summary

ETHAN possède une base de sécurité **structurelle** (`core/security/`) partiellement câblée : PolicyEngine (8 niveaux, fail-closed), CapabilityManager, ExfilGuard, SecureToolEnforcer. Ces briques sont **indépendantes du LLM** et ne peuvent être modifiées par prompt ou contenu externe.

Cependant, **l'intégration est incomplète** et plusieurs surfaces critiques restent **non protégées** ou **simulées** :

- SecurityGateway déconnecté (TODO)
- ToolExecutor en a un `policy_enforcer` **optionnel** — outils builtin **simulés**
- AgentExecutor sans boucle d'outils, sans approbation, sans enforcer
- TerminalPlugin exécute sur l'hôte avec vulnérabilité path traversal
- MCP stdio lance des processus locaux non sandboxés
- NATS sans authentification
- Skills injectés comme texte dans le prompt système (prompt injection)
- `runtime/` n'existe pas

**GO conditionnel** — correctifs P0 obligatoires avant Atreus. Voir §30.

---

## 1. État actuel de l'architecture ETHAN

```
ethan/
├── core/
│   ├── security/
│   │   ├── types.py              ← ActionType, Identity, SecurityContext
│   │   ├── gateway.py            ← SecurityGateway (DÉCONNECTÉ — TODO)
│   │   ├── integration.py        ← SecureToolEnforcer (branché sur ToolExecutor)
│   │   ├── data_protection.py    ← Secret patterns, SensitiveDataClassifier
│   │   ├── data/exfiltration.py  ← ExfilGuard (4 flux indépendants)
│   │   └── policy/
│   │       ├── engine.py         ← PolicyEngine (8 niveaux, fail-closed)
│   │       ├── guard.py          ← PolicyGuard (point d'entrée obligatoire)
│   │       ├── types.py          ← PolicyRequest/Decision/Result
│   │       ├── rules.py          ← Règles CORE/SECURITY (default_rules)
│   │       └── capabilities.py   ← CapabilityManager, resolve_safe_path
│   ├── tools/
│   │   ├── executor.py           ← ToolExecutor (enforcer optionnel)
│   │   ├── manager.py            ← ToolManager (orchestration)
│   │   ├── mcp_client.py         ← MCPClient (stdio + HTTP)
│   │   └── builtin.py            ← Outils builtin (SIMULÉS)
│   ├── skills/
│   │   ├── executor.py           ← SkillExecutor (pipeline d'étapes)
│   │   ├── lab.py                ← SkillLab (sandbox Docker)
│   │   └── builtin.py            ← Skills injectés comme TEXTE (RISQUÉ)
│   ├── agents/
│   │   └── executor.py           ← AgentExecutor (AUCUNE boucle d'outils)
│   ├── audit/store.py            ← AuditStore (append-only)
│   ├── approval/                 ← ApprovalEngine (asynchrone)
│   └── isolation.py              ← FORBIDDEN_IMPORTS/FORBIDDEN_FUNCTIONS
├── runtime/                      ← N'EXISTE PAS (manque critique)
├── plugins/
│   ├── loader.py                 ← PluginLoader
│   ├── validator.py              ← PluginValidator (AST)
│   ├── sandbox/core.py           ← PluginSandbox
│   └── terminal/                  ← TerminalPlugin (HOST EXECUTION!)
├── interfaces/api/main.py       ← Composition root (build_secure_enforcer branché)
├── interfaces/webui/             ← Interface passive
├── docker-compose.yml            ← NATS sans auth, secrets dans env
└── infrastructure/systemd/       ← ethan-core.service
```

### Niveau de maturité

| Composant | Status | Commentaire |
|-----------|--------|-------------|
| PolicyEngine | ✅ Opérationnel | 8 niveaux, fail-closed, A1-A6 |
| CapabilityManager | ✅ Opérationnel | Path traversal / symlink / mount blocked |
| ExfilGuard | ✅ Opérationnel | 4 flux, sanitize_external_content |
| SecureToolEnforcer | ✅ Branché | Dans main.py → ToolExecutor |
| SecurityGateway | ❌ Déconnecté | TODO: exécuter l'action |
| ToolExecutor builtins | ⚠️ Simulé | sleep(0.1) + return dict |
| AgentExecutor | ❌ Critique | Pas de tool loop, pas d'approbation |
| TerminalPlugin | ❌ Critique | Host execution, path traversal |
| MCP stdio | ❌ Critique | Processus locaux non sandboxés |
| NATS | ❌ Critique | Aucune authentification |
| Skills injection | ⚠️ Risqué | Texte injecté dans system prompt |
| runtime/ | ❌ Critique | N'existe pas |

---

## 2. Points d'entrée permettant l'exécution de code

### 2.1 TerminalPlugin (plugins/terminal/main.py)

**Risque** : CRITIQUE — Exécution directe sur l'hôte.

- `execute()` : `asyncio.create_subprocess_shell()` directement sur l'hôte.
- **Path traversal** : `self._workdir / path` avec path absolu contourne le workdir.
- Commandes autorisées : `ls, cat, head, tail, grep, find, ps, df, du, echo, pwd`.
- Liste blanche contournable via pipes/redirects.

### 2.2 MCP stdio (core/tools/mcp_client.py)

**Risque** : CRITIQUE — Lancement de processus locaux.

- `connect()` accepte `command` + `args` depuis métadonnées du tool.
- Processus lancé via `stdio_client()` : aucune sandbox, aucune restriction.

### 2.3 Builtins tools (core/tools/builtin.py)

**Risque** : MOYEN — Exécution simulée.

- `_run_tool()` : `asyncio.sleep(0.1); return {"status": "ok"}` — mock.
- Infrastructure prête pour brancher l'exécution réelle.

### 2.4 SkillLab (core/skills/lab.py)

**Risque** : MOYEN — Sandbox Docker.

- Conteneur éphémère, copie code du skill, exécute.
- Aucune analyse statique préalable du code Python.

### 2.5 SkillExecutor (core/skills/executor.py)

- Exécute des steps via `ToolManager.select_and_execute()`.
- Aucun enforcer direct — dépend de `ToolExecutor._policy_enforcer`.

### 2.6 AgentExecutor (core/agents/executor.py)

**Risque** : CRITIQUE — Pas de boucle d'outils, pas d'approbation.

- `execute()` : résout provider → construit system_prompt → appelle `provider.chat()`.
- Aucune boucle d'outils (no tool calling).
- Aucune vérification de sécurité (no enforcer).
- Skills injectés comme **texte** dans `system_prompt`.

---

## 3. Points d'accès au filesystem

### 3.1 TerminalPlugin `read_file()` / `write_file()` / `list_directory()`

- `target = self._workdir / path` — **path traversal** via chemins absolus.
- Aucun contrôle hors `_workdir`.
- `write_file()` crée répertoires parents sans vérification.

### 3.2 CapabilityManager `resolve_safe_path()` (capabilities.py)

- ✅ Path traversal / symlink / mount escape bloqués.
- ✅ `allowed_roots = ["/workspace"]` par défaut.
- ❌ **Non appliqué** dans TerminalPlugin ni MCP stdio.

### 3.3 Builtins tools filesystem

- Simulés — aucun accès réel pour l'instant.

---

## 4. Points d'accès Git

| Composant | Type | Sécurité |
|-----------|------|----------|
| TerminalPlugin | `git` en shell | ⚠️ Sur l'hôte via subprocess_shell |
| Core | Aucun natif | N/A |

**Observation** : Git n'est pas utilisé nativement par ETHAN Core. Les accès Git potentiels passent par TerminalPlugin (shell) ou future intégration de dépôts (attracteur pour Atreus).

---

## 5. Points d'accès Docker

### 5.1 SkillLab (core/skills/lab.py)

- SDK Docker, conteneurs éphémères.
- `docker.from_env()` — aucune restriction de resource limits autre que timeout.
- Conteneur `python:3.11-slim` — privilegié, peut monter volumes.

### 5.2 ToolExecutor `_select_sandbox()`

- Retourne `"docker"/"gvisor"/"firecracker"` — **mais jamais utilisé**.

### 5.3 docker-compose.yml

- Services : nats, redis, postgres, api, kernel, modules, pg_backup, ui.
- Réseau `ethan-core` (bridge, 172.20.0.0/16).
- `host.docker.internal:host-gateway` pour API/Kernel/Modules.
- Aucun volume utilisateur hôte monté.

---

## 6. Points d'accès réseau

### 6.1 NATS

- **AUCUNE AUTHENTIFICATION** (`nats:4222`).
- `authorization`, `token`, `auth` absents du docker-compose.yml.
- Surface critique — toute entité peut publier/s'abonner.

### 6.2 API (interfaces/api/main.py)

- Écoute `0.0.0.0:8000` → mappé à `127.0.0.1:8000`.
- Routes `/v1/` nécessitent inspection individuelle.

### 6.3 MCP HTTP

- `streamable_http_client` — connexion sortante.
- `verify=True` par défaut (SSL vérifié).
- Token OAuth en mémoire (InMemoryTokenStorage).

---

## 7. Gestion actuelle des secrets

### 7.1 SecretManager (core/config/secrets.py)

- Résout via : cache → `ETHAN_<NAME>` → `<NAME>` → Vault.
- Vault : `_load_from_vault()` lit `VAULT_ADDR` + `VAULT_TOKEN` (env).
- Tokens jamais persistés.

### 7.2 docker-compose.yml

- `REDIS_PASSWORD`, `POSTGRES_PASSWORD` : variables env (non versionnées).
- API keys (OpenAI, Anthropic, Gemini) : variables env.
- **Problème** : mappées dans l'environnement des conteneurs — si compromis,
  récupérables via `/proc/<pid>/environ`.

### 7.3 Audit

- NATS n'a aucune configuration d'authentification — `grep -rn 'authorization\|token\|auth' docker-compose.yml` confirme l'absence.

---

## 8. Architecture actuelle des plugins

### 8.1 PluginLoader (plugins/loader.py)

- Scannes : `plugins/builtin/`, `~/.local/share/ethan/plugins/`, `/etc/ethan/plugins/`.
- `ETHAN_PLUGIN_API = "2"`.
- Circuit breaker : max 3 crash / 300s.
- Permissions via `Permission` class (`resource:action`).

### 8.2 PluginValidator (plugins/validator.py)

- AST analysis : interdit `os, sys, subprocess, shutil, socket, ctypes, pickle, marshal,
  shelve, multiprocessing, threading, signal`.
- Interdit : `exec, eval, compile, __import__, open`.
- **Limite** : pas de dataflow analysis — contournement via imports dynamiques possibles.

### 8.3 PluginSandbox (plugins/sandbox/core.py)

- Deux niveaux : in-process + subprocess.
- `PermissionSet` : `action:resource` avec glob matching.
- **Non utilisé par défaut** — TerminalPlugin n'utilise pas de sandbox.

### 8.4 Isolation (core/isolation.py)

- `FORBIDDEN_IMPORTS` : `kernel.*, core.plugins, core.discovery, core.isolation, sdk`.
- `FORBIDDEN_FUNCTIONS` : `os.system, os.popen, subprocess.*, eval, exec, __import__,
  importlib`.
- `ALLOWED_IMPORTS` : `ethan, requests, json, datetime, os.path, pathlib, typing`.

---

## 9. Architecture actuelle des skills

### 9.1 SkillExecutor (core/skills/executor.py)

- Pipeline d'étapes séquentielles.
- Chaque step → `ToolManager.select_and_execute()`.
- Résultats stockés, rollback possible (non implémenté).

### 9.2 SkillLab (core/skills/lab.py)

- Sandbox Docker pour testing.
- Code du skill copié directement — pas de scan de sécurité.

### 9.3 Injection de skills dans le prompt

```python
# core/agents/executor.py — LIGNE 115
system_parts.append(f"[Skill: {skill.get('name', sid)}]\n{content}")
```

**Risque** : un skill malveillant peut contenir `system: "Ignore toutes les instructions
précédentes"` → prompt injection du LLM.

### 9.4 Skill types (core/skills/types.py)

- `Skill` : `steps, capabilities, constraints`.
- `SkillStep` : `tool_id, parameters, optional, depends_on`.

---

## 10. Architecture MCP

### 10.1 MCPClient (core/tools/mcp_client.py)

- Supporte : `streamable_http`, `stdio`.
- OAuth 2.0 Authorization Code + PKCE.
- `connect()` : paramètres `command, args, transport, auth_type` depuis **métadonnées
  du tool** (potentiellement non fiables).
- **Risque CRITIQUE** : `stdio` lance `subprocess.Popen(command, args)` sur l'hôte.

### 10.2 ToolExecutor (core/tools/executor.py)

- `_run_mcp_tool()` : crée `MCPClient()`, connecte, appelle `call_tool()`.
- Aucun contrôle de capacité sur le serveur MCP.
- Aucun sandbox pour les outils MCP.

---

## 11. Architecture des agents

### 11.1 AgentExecutor (core/agents/executor.py)

- `create_agent_executor()` : fabrique un callable asynchrone.
- **Flux** : provider → system_prompt (avec skills comme texte) → `provider.chat()`.
- **PROBLÈME CRITIQUE** :
  - **Aucune boucle d'outils** — l'agent ne peut pas appeler d'outils.
  - **Aucune approbation** — pas de `ApprovalEngine` dans le flux.
  - **Aucun enforcer** — `SecureToolEnforcer` n'est pas appelé.

### 11.2 Agent types (core/agents/types.py)

- `Agent` : `capabilities, model, provider, skill_ids, knowledge_collection_ids,
  folder_ids`.
- `AgentExecution` : suivi (status, task, result).

### 11.3 AgentManager ?

- Types définis mais **manque `manager.py`** pour l'orchestration complète.

---

## 12. Risques identifiés

| # | Risque | Risque | Impact |
|---|--------|--------|--------|
| R1 | AgentExecutor sans tool loop/approval | CRITIQUE | Atreus ne peut être construit |
| R2 | TerminalPlugin path traversal | CRITIQUE | Accès hôte complet |
| R3 | MCP stdio processus locaux | CRITIQUE | Code arbitraire sur l'hôte |
| R4 | NATS sans auth | CRITIQUE | Spoofing d'événements |
| R5 | Skills injectés comme texte | ÉLEVÉ | Prompt injection |
| R6 | SecurityGateway déconnecté | MOYEN | Contournement de policy |
| R7 | Builtins simulés | MOYEN | Sécurité pas testée en vrai |
| R8 | Secrets dans env conteneurs | MOYEN | Fuite via /proc |
| R9 | PluginValidator AST surface | MOYEN | Import indirect possible |
| R10 | runtime/ absent | MOYEN | Pas d'isolation d'orchestration |

---

## 13. Architecture de sécurité cible

### Principe fondamental

```
                    AGENT (Atreus, agents existants)
                          │ demande
                          ▼
              ┌─────────────────────────┐
              │  Security Kernel         │
              │  (Core/Security)         │
              └──────────┬──────────────┘
                          │ décide
                          ▼
              ┌─────────────────────────┐
              │  Capability Broker      │
              │  (Core/Capabilities)     │
              └──────────┬──────────────┘
                          │ autorise
                          ▼
              ┌─────────────────────────┐
              │  Approval Engine        │
              │  (Core/Approval)         │
              └──────────┬──────────────┘
                          │ valide
                          ▼
              ┌─────────────────────────┐
              │  Secure Execution       │
              │  Runtime (runtime/)      │
              └──────────┬──────────────┘
                          │ exécute
                          ▼
              ┌─────────────────────────┐
              │  Exfiltration Guard     │
              │  (Core/Security)         │
              └──────────┬──────────────┘
                          │ audit
                          ▼
              ┌─────────────────────────┐
              │  Audit Store            │
              │  (Core/Audit)            │
              └─────────────────────────┘
```

### Nouveaux composants à créer

| Composant | Localisation | Responsabilité |
|-----------|-------------|----------------|
| Security Kernel | `core/security/kernel.py` | Point d'autorité unique |
| Capability Broker | `core/security/capability_broker.py` | Gestion capabilities utilisateur |
| Approval Gate | `core/security/approval_gate.py` | Interface PolicyEngine ↔ ApprovalEngine |
| Runtime Sandbox Manager | `runtime/sandbox.py` | Orchestration sandboxes |
| Trust Manager | `core/security/trust_manager.py` | Niveaux de confiance par source |

---

## 14. Trust Model

### Niveaux de confiance

```
UNTRUSTED     (0.0-0.3)  LLM, contenu externe, dépôts non fiables
LOW           (0.3-0.5)  Plugins non vérifiés, MCP externes
MEDIUM        (0.5-0.7)  Utilisateur, skills Core
HIGH          (0.7-0.9)  Admin, système, skills signés
CRITICAL      (0.9-1.0)  Kernel, Security Kernel, règles CORE
```

### Frontières de confiance

1. **Contenu vs Instructions** : tout contenu (fichiers, MCP, mémoire, web) est
   traité comme **donnée non fiable** — jamais comme instruction.
   `sanitize_external_content()` retire `system:`, `instruction:`.

2. **Agent vs Autorité** : un agent/LLM peut **proposer** mais **jamais autoriser**.
   L'autorité est dans le Security Kernel + PolicyEngine + Capability Broker.

3. **Dépôt vs Host** : dépôt non fiable monté dans un sandbox Docker — jamais sur l'hôte.

4. **Plugin vs Core** : plugins en privilèges limités, jamais au-delà du manifeste.

---

## 15. Capability Model

### Structure d'une Capability

```python
@dataclass(frozen=True)
class Capability:
    id: str                     # UUID
    subject: str                # "agent:atreus", "user:h4ck3r", "*"
    category: str               # filesystem, shell, docker, network, mcp, ...
    operation: str              # read, write, execute, send, delete
    resource: str               # "/repos/myproject/**", "github.com/**"
    scope: str                  # "repo:myproject", "session:abc123"
    ttl_seconds: int | None     # Expiration
    risk_level: str             # low, medium, high, critical
    origin: str                 # "user", "admin", "system"
    granted_at: float           # Timestamp Unix
    granted_by: str             # Qui a accordé
    granted_reason: str         # Pourquoi
    usage_limit: int | None     # Nombre max d'utilisations
    usage_count: int            # Nombre d'utilisations effectuées
    revoked: bool = False
```

### Hiérarchie des opérations

```
filesystem:  read → write → delete → execute
shell:       execute (interdit par défaut)
docker:      execute (interdit par défaut)
network:     read → write (REQUIERT ExfilGuard)
mcp:         execute (confirmation)
external:    send (INTERDIT sans TransmissionPolicy)
```

---

## 16. Security Policy Model

### Hiérarchie à 8 niveaux

```
1 — CORE         (inviolable, immutable)
2 — SECURITY    (deny/confirm par défaut)
3 — SYSTEM       (changement d'infrastructure)
4 — PROJECT       (politiques projet/dépôt)
5 — AGENT         (capabilities assignées)
6 — TASK           (capabilities temporaires)
7 — USER           (préférences utilisateur)
8 — LLM            (suggestions — jamais autorité)
```

### Axiomes (A1-A6)

| Axio | Description |
|------|-------------|
| A1 | Niveau le plus fort → décision |
| A2 | Non-annulation |
| A3 | Conflit intra-niveau — plus restrictif gagne |
| A4 | Fail-closed — aucune règle → DENY |
| A5 | Pas d'inférence — read ≠ write |
| A6 | Neutralité du demandeur |

### Effets (PolicyEffect)

- ALLOW — autorise
- DENY — refuse (irréversible)
- REQUIRE_CONFIRMATION — demande approbation humaine

---

## 17. Sandbox Model

| Tier | Isolation | Usage |
|------|-----------|-------|
| 1 | In-Process | Plugins légers, builtins trusted |
| 2 | Subprocess | TerminalPlugin, sandbox restrictions |
| 3 | Docker | SkillLab, dépôts non fiables, MCP stdio |
| 4 | gVisor/Firecracker | Code de dépôts, MCP haut risque |

---

## 18. Audit / Logging Model

### AuditStore (core/audit/store.py)

- Append-only — entrées jamais modifiées.
- PostgreSQL (table audit_log) + JSONL fallback.
- Publie sur EventBus.
- Champs : id, timestamp, category, decision, action, actor, source, details,
  correlation_id, tags.

### Catégories d'audit

| Catégorie | Décision | Description |
|-----------|----------|-------------|
| SECURITY | ALLOW/DENY | Évaluation policy |
| TOOL | ALLOW/DENY | Exécution d'outil |
| CAPABILITY | GRANT/REVOKE | Gestion de capabilities |
| APPROVAL | APPROVED/REJECTED | Confirmation humaine |
| SENSITIVE | BLOCKED/REDACTED | Détection de secrets |

---

## 19. Threat Model (STRIDE)

| Threat | Description | Mitigation actuelle | Gap |
|--------|-------------|---------------------|-----|
| Spoofing | Usurpation NATS | Aucune | NATS pas d'auth |
| Tampering | Policy modifiée | PolicyEngine immuable | SecurityGateway déconnecté |
| Repudiation | Agent nie action | AuditStore | Pas de signature |
| Disclosure | Exfiltration secrets | ExfilGuard | Builtins simulés |
| DoS | Consommation CPU/RAM | Resource limits | TerminalPlugin host |
| Privilege | Escalade | Capabilities | PluginLoader sandbox non utilisé |

---

## 20. Flux de sécurité d'une commande

```
1. Utilisateur → WebUI/CLI: action
2. WebUI/CLI → HTTP API /v1/tools/execute
3. API → ToolManager.select_and_execute()
4. ToolManager → ToolExecutor.execute()
5. ToolExecutor → SecureToolEnforcer.check()
   a. PolicyEngine.evaluate() → ALLOW / DENY / CONFIRMATION
   b. CapabilityManager.check() → capability match
   c. ExfilGuard.check() → exfiltration check
   d. AuditStore.log() → append-only
6. Si DENY → rejeter, logger
7. Si CONFIRMATION → ApprovalEngine.request() → attente humaine
8. Si ALLOW → sandbox sélectionné → exécution isolée
9. ExfilGuard.sanitize_external_content() → nettoyage sortie
10. AuditStore.log() → résultat final
11. Retour à l'utilisateur
```

**Problème actuel** : SecureToolEnforcer est optionnel dans ToolExecutor.
Si policy_enforcer=None → exécution directe.

---

## 21. Flux de sécurité d'un dépôt Git non fiable

```
FLUX CIBLE :
1. Clone → sandbox Docker (Tier 3)
2. Scan AST du code
3. Git exécuté dans le sandbox
4. Sorties → ExfilGuard
5. Writes → PolicyEngine + Capability
6. Aucun accès filesystem hôte

FLUX ACTUEL :
1. TerminalPlugin → subprocess_shell sur l'hôte
2. Path traversal → /etc/passwd accessible
3. Aucun scan de code
4. Aucun confinement réseau
```

---

## 22. Flux de sécurité d'un skill externe

```
FLUX ACTUEL :
1. Skill stocké dans Core
2. Au runtime → content injecté comme TEXTE dans system_prompt
3. Prompt injection possible

FLUX CIBLE :
1. Skill → SkillLab (sandbox Docker) → test isolation
2. AST scan du code
3. Stockage comme définition structurée
4. Exécution → ToolManager → SecureToolEnforcer
```

---

## 23. Flux de sécurité d'un MCP externe

```
FLUX ACTUEL :
1. MCPClient.connect(command, args)
2. stdio → subprocess.Popen sur l'hôte
3. Exécution arbitraire

FLUX CIBLE :
1. MCP → SecurityKernel.check(category=MCP)
2. PolicyEngine → DENY / CONFIRMATION
3. stdio → Docker sandbox (Tier 3)
4. Réponses → ExfilGuard
```

---

## 24. Flux de sécurité d'un plugin externe

```
FLUX ACTUEL :
1. PluginValidator (AST surface-level)
2. PluginLoader → PluginSandbox (optionnel)

FLUX CIBLE :
1. Plugin → PluginValidator (AST + dataflow)
2. Plugin → SkillLab → test isolation
3. Activation → subprocess sandbox (Tier 2)
4. Permissions → CapabilityManager
5. Actions → SecurityKernel
```

---

## 25. Flux de sécurité d'Atreus

Atreus est un agent de codage autonome. Contraintes :

- Aucun accès filesystem hôte hors /workspace/repos/
- Aucune commande sur l'hôte
- Aucune connexion réseau sortante non auditée
- Aucun plugin/MCP auto-installable
- Aucune capability auto-accordée

```
Atreus demande → SecurityKernel → PolicyEngine → CapabilityBroker → Sandbox → Audit
```

---

## 26. Frontières de confiance

```
┌────────────────────────────────────────┐
│  TRUSTED ZONE                          │
│  ┌─────┐ ┌─────┐ ┌──────┐              │
│  │User │ │Admin│ │System│              │
│  └─────┘ └─────┘ └──────┘              │
│  ┌──────────────────────────────────┐  │
│  │     Security Kernel              │  │
│  │  - Capability Broker             │  │
│  │  - Approval Gate                 │  │
│  │  - Trust Manager                 │  │
│  └──────────────────────────────────┘  │
└──────────────┬─────────────────────────┘
               │ authorization
┌──────────────┴─────────────────────────┐
│  UNTRUSTED ZONE                         │
│  ┌──────────────────────────────────┐  │
│  │  Sandbox Layer                   │  │
│  │  Tier 2: Subprocess               │  │
│  │  Tier 3: Docker                   │  │
│  │  Tier 4: Firecracker              │  │
│  └──────────────────────────────────┘  │
│  ┌──────────────────────────────────┐  │
│  │  Execution Agents                 │  │
│  │  Atreus | Agents | Skills | MCP  │  │
│  └──────────────────────────────────┘  │
│  ┌──────────────────────────────────┐  │
│  │  Untrusted Sources                │  │
│  │  Git Repo | MCP | Plugins | Web  │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## 27. Principes architecturaux imposés

1. Zero Trust par défaut — fail-closed.
2. Séparation Agent / Autorité — LLM ne peut jamais autoriser.
3. Séparation Données / Instructions — contenu externe = données.
4. Non-exfiltration structurelle — LOCAL_READ ≠ EXTERNAL_TRANSMISSION.
5. Isolation des dépôts — sandbox Docker obligatoire.
6. Protection du host — aucun code externe sur l'hôte.
7. Secrets — env/Vault/Docker secrets uniquement.
8. Auditabilité — append-only, correlation_id.
9. Révocation — capabilities/plugins/MCP révocables.
10. Absence de privilège implicite — pas de policy_enforcer=None.

---

## 28. Ce qui doit être INTERDIT

| Action | Motif |
|--------|-------|
| Executer tool sans SecureToolEnforcer | Contournement sécurité |
| LLM/agent modifier policy > son niveau | Violation A1/A2 |
| Injecter skill comme texte dans prompt | Prompt injection |
| Lancer processus stdio hors sandbox | Code arbitraire hôte |
| NATS sans authentification | Spoofing événements |
| Plugin contredire FORBIDDEN_IMPORTS | Violation isolation |
| MCP écrire filesystem hôte | Violation sandbox |
| Exfiltrer secrets HTTP/MCP/shell | Violation CR-4 |
| Path traversal TerminalPlugin | Violation sécurité |
| Builtins sans SecureToolEnforcer | Fail-open |

---

## 29. Ce qui nécessite une approbation utilisateur

| Action | Risque | Approbation |
|--------|--------|-------------|
| Supprimer fichier | Medium | Confirmation simple |
| Écrire/éditer fichier | Medium | Confirmation simple |
| Commande shell | High | Confirmation explicite |
| Tool Docker | High | Confirmation explicite |
| Plugin externe | High | Confirmation + review |
| MCP externe | High | Confirmation + review |
| Envoi données externes | Medium | Confirmation ExfilGuard |
| MCP stdio | Critical | Confirmation renforcée |
| Clone dépôt Git | Medium | Confirmation simple |
| Skill externe | Medium | Confirmation + test |
| Modifier capability | High | Confirmation + log |

---

## 30. Plan d'implémentation par phases

### Phase 0 — Security Foundation (1 semaine)

1. SecurityGateway → brancher sur routes API sensibles.
2. ToolExecutor → policy_enforcer non optionnel.
3. AgentExecutor → SecureToolEnforcer dans le flux.
4. NATS auth → authorization token dans docker-compose.yml.
5. TerminalPlugin → resolve_safe_path().

### Phase 1 — Runtime Isolation (2 semaines)

1. Créer runtime/ : sandbox.py + isolation.py
2. TerminalPlugin → subprocess sandbox (Tier 2).
3. MCP stdio → Docker sandbox (Tier 3).
4. Security Kernel → core/security/kernel.py.

### Phase 2 — Capability Broker (1 semaine)

1. core/security/capability_broker.py
2. API /v1/capabilities → CRUD.
3. PostgreSQL persistence.
4. TTL + usage limits + révocation.

### Phase 3 — Atreus Framework (3 semaines)

1. AgentExecutor → boucle d'outils complète.
2. Skills → ne plus injecter comme texte.
3. SkillLab → AST scan + test.
4. Audit → signatures d'actions.
5. Trust Model → Security Kernel.

---

## 31. Résumé CTO

### GO / NO-GO

**GO conditionnel** — 5 correctifs P0 obligatoires avant Atreus :

1. SecurityGateway branché sur routes API.
2. SecureToolEnforcer obligatoire.
3. NATS authentifié.
4. TerminalPlugin → path traversal corrigé.
5. MCP stdio → execution en sandbox Docker.

### Top 10 risques

1. AgentExecutor sans tool loop — Atreus ne peut être construit.
2. TerminalPlugin path traversal — accès hôte complet.
3. MCP stdio — exécution arbitraire.
4. NATS sans auth — spoofing d'événements.
5. Skills comme texte — prompt injection.
6. SecurityGateway déconnecté — contournement.
7. Builtins simulés — sécurité pas testée.
8. Secrets dans env conteneurs — fuite /proc.
9. PluginValidator AST surface — import indirect.
10. runtime/ absent — pas isolation orchestration.

### Top 10 composants à créer

1. core/security/kernel.py — Security Kernel.
2. core/security/capability_broker.py — capabilities utilisateur.
3. core/security/approval_gate.py — interface Policy ↔ Approval.
4. runtime/sandbox.py — orchestrateur sandboxes.
5. core/agents/loop.py — boucle d'outils (Atreus-ready).
6. core/tools/sandbox_runner.py — execution isolée.
7. core/security/trust_manager.py — trust levels.
8. API /v1/capabilities — CRUD capabilities.
9. API /v1/approvals — gestion approbations.
10. core/security/signatures.py — signature actions.

### Top 10 règles non négociables

1. LLM/agent ne peut jamais autoriser.
2. SecureToolEnforcer obligatoire sur toute action sensible.
3. fail-closed — erreur sécurité → DENY.
4. Aucun code externe sur l'hôte — sandbox obligatoire.
5. Aucune donnée sort sans TransmissionPolicy (ExfilGuard).
6. Aucun secret dans code/git/logs/env.
7. Skills jamais injectés comme texte.
8. NATS requiert authentification.
9. Capability TTL-bornée + révocable.
10. Audit append-only + correlation_id.

### Dépendances entre phases

```
Phase 0 → Phase 1 → Phase 2 → Phase 3
Atreus ne peut être implémenté qu'après Phase 0 complétée.
Phase 1-2 nécessaires pour sécurité opérationnelle.
Phase 3 peut commencer une fois Phase 0 validée.
