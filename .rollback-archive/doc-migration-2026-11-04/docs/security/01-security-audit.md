# ETHAN — Phase 01 · Audit Sécurité & Gouvernance

> **Statut** : Analyse uniquement — aucun code modifié.
> **Objectif** : comprendre l'architecture de sécurité actuelle pour concevoir la future Constitution ETHAN.
> **Périmètre** : Core, Runtime, Services, Interfaces (WebUI, CLI) — chemins réels vérifiés dans le code.

---

## 1. Cartographie — comment une demande traverse ETHAN

### 1.1 Chemin chatbot moderne (réel, utilisé par la WebUI)

```
User (browser)
  ↓ POST /api/v1/chat/completions  (proxy Next.js → cookie HttpOnly → Bearer)
interfaces/api/main.py               (middleware JWT — auth uniquement)
  ↓ POST /v1/chat/completions        (router v1 — AUCUN require_permission)
Core ChatPipeline.run()              (core/chat/pipeline.py)
  ├─ ChatStore (conversation, arbre de messages)
  ├─ _resolve_agent()                (agent → provider/model/skills)
  ├─ _build_llm_messages()           (persona agent + skills + tools + mémoire + RAG + fichiers)
  ├─ _generate()                     → ProviderManager → provider LLM externe
  └─ loop <tool>                     → execute_tool_call() → ToolManager → ToolExecutor
                                                          └─ SecurityGateway  ← COMMENTÉ (skip)
```

### 1.2 Chemin événementiel (legacy, CLI)

```
CLI  →  /v1/message  →  NATS ethan.intent.user  →  modules (kernel, scheduler, autonomy…)
```

NATS n'impose **aucune authentification ni ACL** : tout émetteur du réseau Docker `ethan-core`
peut publier un événement d'intention utilisateur.

### 1.3 Chemin agent autonome

```
POST /v1/agents/{id}/execute  (require_permission EXECUTE) → AgentManager → Core AgentExecutor
  → ProviderManager (LLM) — pas de boucle d'outils, pas d'approbation, pas de limite de coût
```

### 1.4 Composants présents

| Couche | Composants |
|---|---|
| Interfaces | WebUI (Next.js 15, proxy `/api/*`), CLI (`./ethan`), API Gateway (FastAPI 8000) |
| Core | `chat/pipeline.py`, `llm/provider_manager.py`, `tools/`, `skills/`, `agents/`, `memory/`, `rag/`, `knowledge/`, `config/secrets.py`, `auth/`, `security/`, `approval/`, `audit/`, `capabilities/`, `modules/` |
| Bus | NATS (event-driven), middleware bus (enrichissement/traçage uniquement) |
| Services | Postgres 16, Redis 7, NATS 2.10, pg_backup — bindés **127.0.0.1** |
| Conteneurs | api (8000), kernel (8080), modules, ui (3001) — réseau interne `ethan-core` |

---

## 2. Points d'autorité — qui peut faire quoi **aujourd'hui**

| Action | Droit déclaré | Effectif (chemin réel) |
|---|---|---|
| Lire des fichiers | Rôle `user` (RBAC `file:read`) | Pipeline injecte `file_ids` **sans vérif. de propriété** |
| Écrire des fichiers | Rôle `user` (RBAC `file:write`) | TerminalPlugin écrit `/workspace` ; skills via tools (non vérifié) |
| Supprimer | Rôle admin (wildcard) | Non implémenté de façon contrôlée |
| Exécuter des commandes | Rôle `user` (RBAC `command:execute`) | **RBAC non appliqué** ; TerminalPlugin liste blanche ; MCP stdio lance des processus |
| Utiliser Docker | — | **Aucun socket Docker monté** (positif) ; `host.docker.internal` ouvre l'hôte |
| Accéder au réseau | Rôle `user` (`network:request`) | MCP, web_search, providers LLM — aucune restriction effective |
| Utiliser MCP | — | Serveurs MCP `command` local / URL ; auth bearer en mémoire |
| Modifier la config | Rôle admin ; `config_change` | Routes protégées JWT ; pas de politique de changement |
| Modifier les règles | — | Aucun mécanisme d'édition de politiques (PolicyEngine = code) |
| Accéder à la mémoire | Rôle `llm` (`memory:read`) | Pipeline lit **tous** les faits (`list_facts()` sans filtre user) |
| Transmettre des données | — | AuditStore + logs ; **pas de classification des sorties** |

### Constat central

**Deux mondes ne se parlent pas** :
1. le monde **API** (middleware JWT + `require_permission` sur une partie des routes),
2. le monde **Core** (SecurityGateway, PermissionChecker, PolicyEngine, RateLimiter, ApprovalEngine)
   défini, documenté, mais **déconnecté du chemin d'exécution réel**.

---

## 3. Capacités existantes

| Brique | Fichier | État |
|---|---|---|
| SecurityGateway | `core/security/gateway.py` | **Déconnecté** — non importé, import interne cassé (`core.security.audit` absent), exécution `TODO` |
| PermissionChecker | `core/security/validation/permissions.py` | Rôles **hardcodés**, jamais appelé |
| PolicyEngine | `core/security/validation/policy.py` | Règles Python, `rate_limit` = TODO, jamais appelé |
| SignatureValidator | `core/security/validation/signature.py` | **Non cryptographique** (signature auto-générée) |
| RateLimiter | `core/security/validation/rate_limiter.py` | Jamais appelé |
| ApprovalEngine | `core/approval/engine.py` | **Sous-utilisé** : seule `/v1/internal` l'expose |
| AuditStore | `core/audit/store.py` | Append-only PG/JSONL — câblage partiel, pas d'audit chat |
| RBAC API | `core/auth/__init__.py` + `interfaces/api/auth.py` | Actif sur routes décorées ; `user` n'a pas EXECUTE (bien) |
| Auth JWT | `interfaces/api/auth.py` | Actif ; **`JWT_SECRET` défaut insécure hardcodé** |
| TOTP 2FA | `core/auth/totp.py` | Existe, optionnel |
| API Keys | `core/auth/api_keys.py` | Existe (SHA-256) — usage à confirmer |
| LDAP / OAuth / SCIM | `core/auth/{ldap,oauth,scim}.py` | Définis — câblage à vérifier |
| Secrets (Vault → env) | `core/config/secrets.py` | Bonne base ; `.env` gitignored |
| Permissions modules | `core/modules/permissions.py` | **Défini mais inappliqué** |
| Sandbox plugins | `plugins/sandbox/core.py` | Existe (RLIMIT, builtins restreints) |
| TerminalPlugin | `plugins/terminal/main.py` | Liste blanche de commandes, blocage de métacaractères |
| Scanner secrets/PII | `src/openjarvis/security/scanner.py` | Existe, testé — application à confirmer |
| Runner WASM | `src/openjarvis/sandbox/wasm_runner.py` | Existe, testé |
| CapabilityRegistry | `core/capabilities/registry.py` | Découverte uniquement — **pas d'autorisation** |

---

## 4. Hiérarchie actuelle (gouvernance)

| Sphère | État |
|---|---|
| System policies | Ébauche Python (PolicyEngine) — déconnectée, non évolutive, pas de versioning |
| Agent rules | Aucune règle contraignante : persona + `skill_ids`, rien ne limite les effets de bord |
| LLM instructions | **Aucun system prompt de sûreté global** — injections contextuelles uniquement |
| Permissions | API RBAC actif mais partiel ; RBAC Core inappliqué ; Permissions modules inappliquées |
| Capability system | Registre de découverte uniquement (pas de gate) |
| Confirmation | ApprovalEngine existe — **aucun appelant du chemin chat** ne requiert d'approbation |
| Audit logs | AuditStore création/approbations (internal) ; **pas d'audit des actions du pipeline** |

---

## 5. Failles potentielles

1. **SecurityGateway déconnecté et import cassé** — exécution d'outils sans validation ;
   `core/security/audit.py` absent → `SecurityGateway.initialize()` planterait.
2. **JWT_SECRET par défaut insécure** — `change-me-in-prod-…` hardcodé : sans variable
   d'env, n'importe qui peut forger des tokens valides (HS256).
3. **SignatureValidator non cryptographique** — signature auto-générée `sig-{uuid}`,
   seul un champ non vide est vérifié → bypass trivial.
4. **Rôles hardcodés** — modifiables uniquement par code (« en dur, production: depuis DB »).
5. **Rate limiting inactif** — `_policy_rate_limit` TODO ; RateLimiter jamais appelé ;
   slowapi **sans aucun décorateur** `@limiter.limit` sur les routes.
6. **Register public auto-role `user`** — self-signup ouvert (spam, resource exhaustion) ;
   pas de premier-admin/fermeture beta ; login non rate-limité.
7. **IDOR chat/history** — `user_id` fourni par le client ; `/v1/chat/history` liste toutes
   les conversations ; pas de vérification de propriété de `chat_id`.
8. **Mémoire globale inter-utilisateurs** — `list_facts()` sans scope user → fuite dans le prompt.
9. **Prompt injection** — skills, fichiers, RAG et mémoire injectés **tels quels** dans le prompt
   système ; le LLM est invité à émettre des `<tool>` ; aucun contenu malveillant ne peut
   déclencher d'outil **non sélectionné** par l'utilisateur (le payload définit `tool_ids`),
   mais il peut en abuser de ceux sélectionnés.
10. **ApprovalEngine jamais sollicité sur le chemin chat** — actions à risque (write,
    exec, réseau) sans confirmation humaine ; publisher par défaut = log seulement.
11. **NATS sans auth** — n'importe quel conteneur du réseau peut publier `ethan.intent.user`.
12. **CLI sans token** — client `/v1/message` sans Authorization ; dépend du middleware JWT.
13. **`host.docker.internal`** — les conteneurs accèdent aux services locaux de l'hôte.
14. **MCP stdio** — peut lancer des processus locaux ; à restreindre (qui crée un serveur MCP ?).
15. **Outils builtin simulés** — `execute_python_code` (HIGH + sandbox_required) n'exécute
    réellement rien → faux sentiment de sécurité sur les contrôles de risque.
16. **Fallback echo** — si aucun provider n'est initialisé, le chat répond `[ECHO]` : le
    système fonctionne en mode dégradé non signalé à l'utilisateur.
17. **Plugin security vide** — `plugins/builtin/security/` est un dossier vide.
18. **Audit incomplet** — les actions du pipeline (tools, LLM, skills, agents) ne sont pas
    journalisées ; pas de traçabilité bout-en-bout.

---

## 6. Duplications

- **3 systèmes de permissions** : RBAC API (`core/auth`), Permissions modules
  (`core/modules/permissions.py`, inappliquées), PermissionSet plugins (`sandbox`).
- **2 rate limiters** : `core/security/validation/rate_limiter.py` (jamais appelé) et
  slowapi `interfaces/api/rate_limit.py` (sans décorateurs).
- **2 chemins de chat** : `/v1/message` (NATS legacy, CLI) et `/v1/chat/completions`
  (ChatPipeline moderne) — protégés différemment, comportements divergents.
- **2 loaders de secrets** : `get_secrets()` (legacy) et `SecretManager` (convention
  `ETHAN_<NAME>`) — documentés comme tels, mais deux points de vérité.
- **3 couches de sécurité non articulées** : `core/security`, `plugins/sandbox`,
  `plugins/terminal`.
- **2 registres de capabilities** : `core/capabilities/registry.py` et
  `core/registry/registry.py`.

---

## 7. Éléments manquants (pour la Constitution)

1. **Deny-by-default** : aucune définition de « capacité permise par défaut » — le rôle
   `user` est allow par défaut (file read/write, network, command).
2. **Confirmation obligatoire** pour une classe d'actions à risque (write, delete,
   command, network, email, export) — le pipeline chat n'appelle jamais l'ApprovalEngine.
3. **Classification des données** — rien ne distingue données publiques / internes /
   sensibles / secrètes avant transmission aux LLM externes.
4. **Instructions de priorité & refus** — aucun system prompt de sûreté global.
5. **Isolation des secrets par provider / par utilisateur** — clés API globales partagées.
6. **Vérification d'identité forte** — `verification_level` toujours 0.5 (simulation).
7. **Journal des modifications de règles/politiques** — aucune trace de gouvernance.
8. **Propriété des données** — pas de filtre user sur mémoire, fichiers, chats.
9. **Limites de consommation** — pas de plafond de coût/tokens par utilisateur effectif
   sur le pipeline chat (le router internal expose des budgets mais pas le chat).
10. **Non-répudiation des décisions d'approbation** — résolutions non signées.

---

## 8. Recommandations (pour la phase de conception)

1. **Rebrancher le SecurityGateway** sur `ToolExecutor` (retirer le « MVP: skip ») et
   corriger l'import `core.security.audit` (implémenter l'AuditLogger ou brancher
   l'AuditStore existant).
2. **Rendre le boot de l'API réfractaire sans secrets forts** : refuser de démarrer si
   `JWT_SECRET` vaut le défaut ou est absent en production.
3. **Définir des politiques déclaratives** (OPA/Rego ou fichiers versionnés) avec
   deny-by-default, et une API de gestion réservée admin.
4. **Appliquer l'approbation humaine** sur toute action classée à risque, avec
   publisher NATS/WebSocket réel (et non log) et gestion explicite du TIMEOUT (fail-closed).
5. **Fermer ou restreindre le register** (invitation, premier admin, captcha, rate limit).
6. **Imposer l'identité côté serveur** : ignorer `user_id` du payload, filtrer
   `chat/history` par utilisateur, scoper mémoire/fichiers par owner.
7. **Protéger contre la prompt injection** : délimiteurs stricts, instructions de
   priorité, vérification que les outils appelés appartiennent à la sélection, refus
   de suivre le « contenu » pour déclencher des actions.
8. **Activer l'authentification NATS** (token/user) + ACL par sujet.
9. **Retirer ou restreindre `host.docker.internal`** aux URLs nécessaires.
10. **Appliquer réellement le rate limiting** (décorateurs slowapi sur login/message/
    chat) en tenant compte du proxy (derrière 127.0.0.1 commun).
11. **Durcir le cookie** : `Secure` systématique en prod, `SameSite=strict`.
12. **Auditer la boucle d'outils du LLM** : pas de tool non sélectionné, limite de tours,
    coût, et journalisation de chaque invocation dans l'AuditStore.

---

## 9. Verdict

**PASS** — l'architecture de sécurité actuelle est suffisamment comprise pour concevoir
la Constitution ETHAN. Les points majeurs (gateway déconnecté, approbation sous-utilisée,
absence de système policies effectif, IDOR, prompt injection) sont identifiés avec leur
localisation exacte dans le code. La Constitution devra :

- définir un **modèle d'autorité unique** (qui peut faire quoi, deny-by-default),
- **rebrancher les briques existantes** (gateway, approval, audit, rate limit),
- ajouter **l'approbation humaine** comme porte obligatoire des actions à risque,
- garantir **l'isolation des données** par utilisateur,
- instaurer **l'audit complet** des décisions et actions.

Prochaine étape : Phase 02 — rédaction de la Constitution (principes, hiérarchie
fonctions/politiques/instructions, matrice de permissions, procédure d'approbation).
