# 11 — Runtime Isolation & Durcissements Red Team

> **Date** : 29/09/2026
> **Source** : `CTO_SECURITY_ARCHITECTURE_REVIEW.md` (§30 Phases 0-3) +
> `RED_TEAM_SECURITY_REVIEW.md` (Attaques 1, 2, 15, 17, 18, 20)
> **Statut** : Phase 0 **COMPLÈTE** ; Phase 1 démarrée (Tier 3) ; reste
> documenté en §4.

---

## 1. Phase 0 — Security Foundation : COMPLÉTÉE (5/5 + GO #5)

| # | Correctif P0 (CTO §31) | État | Où |
|---|---|---|---|
| 1 | SecurityGateway branché sur routes API | ✅ | `interfaces/api/gateway_guard.py` (P0-1) |
| 2 | SecureToolEnforcer obligatoire (fail-closed) | ✅ | `core/tools/executor.py` (P0-2) |
| 3 | **AgentExecutor → SecureToolEnforcer dans le flux** | ✅ **(ce lot)** | `core/agents/executor.py` — `run_agent_chat()` |
| 4 | NATS authentifié | ✅ | `core/bus/nats_auth.py` (P0-3) |
| 5 | **MCP stdio → sandbox Docker (Tier 3)** | ✅ **(ce lot)** | `core/tools/sandbox_runner.py` (P0-5) |
| — | TerminalPlugin → `resolve_safe_path()` | ✅ | `plugins/terminal/main.py` (P0-4) |

## 2. Implémentations de ce lot

### 2.1 Sandbox stdio MCP — `core/tools/sandbox_runner.py` (Tier 3)

Toute commande stdio est wrappée dans un conteneur éphémère **durci**
(immuable) : `--cap-drop=ALL`, `--security-opt=no-new-privileges:true`,
`--pids-limit=64`, `--read-only` + `--tmpfs /tmp`, `--network` par défaut
`none`, montages `-v path:path:ro` des chemins absolus existants.

- **Fail-closed** : mode `docker` par défaut ; sans CLI Docker ou sans
  `ETHAN_MCP_STDIO_SANDBOX_IMAGE` ⇒ `SandboxError` ⇒ **connexion refusée**
  (jamais de repli silencieux sur l'hôte — règle non négociable #4).
- `env`/`cwd` sur stdio : **refusés** en mode docker (un secret ne part
  jamais dans un conteneur par accident).
- Opt-out : `ETHAN_MCP_STDIO_SANDBOX=off` (tracé par warning). La suite de
  tests l'utilise (`tests/conftest.py` + test d'intégration stdio) — le
  wrap docker est couvert par des unit tests dédiés.
- Câblage : `core/tools/mcp_client.py` (branche stdio de `connect()`) ;
  env : `.env.example` + service `api` de `docker-compose.yml`
  (+ `ETHAN_MCP_STDIO_ALLOWLIST` enfin transmis).

### 2.2 Boucle d'outils agent — `core/agents/executor.py` (Phase 0.3 + base 3.1)

- `run_agent_chat()` : boucle bornée (`MAX_TOOL_ROUNDS = 3`) réutilisant le
  protocole balisé du chat ; chaque appel passe par
  `ToolManager → ToolExecutor → SecureToolEnforcer` (AUCUN contournement).
- **Refus fail-closed** : sans ToolManager ou sans enforcer ⇒ message de
  refus explicite (Attaque 20). Budget épuisé ⇒ blocs `<tool>` restants
  stripés (jamais de brut rendu).
- La section outils du prompt communique désormais le protocole d'appel.

### 2.3 Protocole `<tool>` migré dans Core — `core/tools/call_protocol.py`

Le parseur vivait dans `interfaces/api/routers/v1.py` (violation
AGENTS.md : logique métier dans une interface). `parse_tool_calls` /
`strip_tool_blocks` sont désormais la **source unique** importée par v1,
le pipeline et les agents — test d'identité d'import dans les tests.

### 2.4 Skills = données dans le chat (CT-4, Attaques 1/15)

`build_skill_system_block()` dans `core/chat/pipeline.py` : sanitisation
(`sanitize_external_content`) + enclos `<data source="skill:…">` avec
instruction sticky — identique au traitement déjà présent dans
`core/agents/executor.py`. Fin de l'injection brute `[Skill: …]\n{content}`.

### 2.5 Quick wins Red Team

- **Attaque 18** : `npm_install_command()` ajoute `--ignore-scripts`
  (pas de `postinstall` exécuté) — `core/capability_manager/backends.py`.
- **Attaques 2/17** : `git_clone_command()` avec
  `-c core.hooksPath=/dev/null` + `--no-recurse-submodules` —
  `interfaces/cli/plugin_manager.py`.

## 3. Tests

- `tests/security/test_runtime_isolation.py` : **36 tests** (modes/wrap
  sandbox, parseur partagé, boucle agent fail-closed, skills `<data>`,
  npm/git).
- Rejeux impactés : mcp servers + mcp client + cli plugin (20),
  chat pipeline + agents + prompt_guard (36), RBAC/guard/plugins API (55).

## 4. Reste à faire (Phases 1-3 — hors de ce lot, RFC dédié)

| Phase | Composant (CTO Top 10) | État | Effort estimé |
|---|---|---|---|
| 1 | `runtime/` (sandbox.py + isolation.py) | ❌ absent | 1 sem. |
| 1 | TerminalPlugin → subprocess sandbox (Tier 2) | ❌ (host + jail chemin actuel) | 2-3 j |
| 1 | `core/security/kernel.py` (autorité unique) | ❌ absent | 1 sem. |
| 2 | `core/security/capability_broker.py` + TTL/révocation | ❌ (CapabilityManager seul) | 1 sem. |
| 2 | API `/v1/capabilities` CRUD + persistance PG | partiel (exécution seule, gate EXECUTE) | 3-4 j |
| 2 | API `/v1/approvals` + `core/security/approval_gate.py` | ❌ absent | 3 j |
| 3 | Skills : protocole structuré (fin de tout injection texte) | partiel (data-only ce lot) | 3 j |
| 3 | SkillLab : AST scan du code avant exécution | partiel (requirements validés) | 2 j |
| 3 | `core/security/signatures.py` (audit signé) | ❌ absent | 3 j |
| 3 | `core/security/trust_manager.py` | ❌ absent | 3 j |
| 3 | Attaque 14 (DLP entropie/encodage binaire) | ❌ (ExfilGuard texte seul) | 3 j |
| 3 | Attaque 16 (resource résolue APRES policy) | à vérifier | 1 j |

**Changement de comportement à connaître** : un serveur MCP stdio exige
désormais `ETHAN_MCP_STDIO_SANDBOX_IMAGE` (+ CLI Docker) ou l'opt-out
explicite `ETHAN_MCP_STDIO_SANDBOX=off` — sans cela, connexion **refusée**
(fail-closed, volontaire).

**Note d'architecture** : la Phase 0.3 est satisfaite par
`run_agent_chat()` (enforcer dans le flux) ; la « boucle complète Atreus »
(Phase 3.1) restera à étoffer (streams, parallélisme, approvals) sur la
base de ce même chemin ToolExecutor.

