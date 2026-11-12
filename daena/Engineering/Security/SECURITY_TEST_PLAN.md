# Security Test Plan — ETHAN

> Classification : Test Plan
> Audience : Security Engineering, QA, Red Team
> Status : Pre-Implementation
> Date : 2026-03-09

---

## 1. Attack Surface Map

```
ENTREE                     COMPOSANT                 SORTIE
========================   =====================     ========================
Git Repository (clone)  →  Runtime Sandbox (Docker) →  Filesystem (sandbox)
MCP Server (stdio)      →  MCPClient → Sandbox       →  Process (sandbox)
MCP Server (HTTP)       →  MCPClient HTTP             →  Network (audit)
Plugin (Python)         →  PluginLoader/Validator     →  Filesystem (sandbox)
Skill (Content)         →  SkillExecutor              →  Tool execution
Agent Prompt            →  AgentExecutor              →  LLM API
WebUI/CLI Request       →  API Router                 →  Tool execution
.env / Vault            →  SecretManager              →  API keys
```

### Surfaces critiques

1. Git clone + hooks + config + submodules + payloads
2. MCP stdio (command injection, process creation)
3. TerminalPlugin (subprocess_shell sur l'hote)
4. ToolExecutor (policy_enforcer optionnel)
5. AgentExecutor (pas de boucle d'outils, injection skills)
6. PluginValidator (AST surface-level)
7. NATS (pas d'authentification)

---

## 2. Trust Boundary Map

```
[TRUSTED] Core Security (Policy, Capabilities, ExfilGuard)
   |
   | decision
   |
[UNTRUSTED] Runtime Sandbox (Docker, gVisor, Firecracker)
   |
   | execution
   |
[UNTRUSTED] Atreus / MCP / Plugins / Git Repos / Skills
```

### Boundaries a verifier

- Toute action passe par PolicyEngine AVANT execution.
- CapabilityManager valide le resource AVANT acces.
- ExfilGuard scanne la sortie APRES execution.
- Security Kernel est le SEUL point d'autorite.

---

## 3. Top 20 attaques (resume)

| # | Attaque | Risk | Mitigation clé |
|---|---------|------|----------------|
| 1 | Prompt injection README | CRITICAL | Content classifier + data-only mode |
| 2 | Git hooks malveillants | CRITICAL | core.hooksPath=/dev/null + scan |
| 3 | .git/config malveillant | HIGH | GIT_CONFIG_GLOBAL=/dev/null |
| 4 | Symlink escape | HIGH | resolve_safe_path + nocopy |
| 5 | MCP stdio malveillant | CRITICAL | Docker sandbox + validation |
| 6 | Plugin malveillant | CRITICAL | Bloquer importlib + sandbox |
| 7 | Skill injecte comme texte | HIGH | Execution via ToolManager |
| 8 | Env heritees | HIGH | --read-only + env isolation |
| 9 | TOCTOU capability | MEDIUM | check+execute atomique |
| 10 | Confusion MIME | MEDIUM | Type checking + data-only |
| 11 | Archive path traversal | HIGH | safe_extract() |
| 12 | Docker socket | CRITICAL | Pas --network=host, --cap-drop=ALL |
| 13 | Escalade setuid | CRITICAL | --security-opt=no-new-privs |
| 14 | Contournement ExfilGuard | HIGH | DLP + content inspection |
| 15 | Confusion donnees/instructions | CRITICAL | <data> tags + data-only |
| 16 | Contournement Policy Engine | MEDIUM | Resource validation post-check |
| 17 | Submodule malveillant | HIGH | Scan + isolation |
| 18 | npm scripts injection | HIGH | --ignore-scripts + scan |
| 19 | Makefile target | MEDIUM | Autorisation explicite |
| 20 | Bypass Security Kernel | CRITICAL | Enforcer obligatoire |

---

## 4. Top 20 mitigations

### P0 — Immédiat

1. Security Kernel obligatoire (core/security/kernel.py)
2. ToolExecutor: policy_enforcer non optionnel
3. NATS: authentification requise
4. TerminalPlugin: resolve_safe_path() + sandbox
5. MCP stdio: Docker sandbox

### P1 — Court terme

6. Skills: ne plus injecter comme texte
7. Plugin: bloquer importlib, getattr, eval, exec
8. Runtime: creer runtime/sandbox.py
9. Capability: check+execute atomique
10. Git: GIT_CONFIG_GLOBAL=/dev/null

### P2 — Moyen terme

11. Archive: safe_extract()
12. Content: data-only mode + <data> tags
13. Docker: --cap-drop=ALL + --security-opt
14. ExfilGuard: DLP + content inspection binaire
15. Submodule: scan avant init
16. npm: --ignore-scripts
17. Makefile: autorisation explicite
18. Signature d'actions (anti-repudiation)
19. Network egress control (firewall par container)
20. Plugin: dataflow analysis (au-dela de AST surface)

---

## 5. Security invariants

1. **LLM n'autorise jamais** — toujours demande au Security Kernel.
2. **PolicyEngine est immuable** — aucune instruction LLM ne peut modifier.
3. **ExfilGuard est dechainable** — toutes sorties sont scannées.
4. **Capabilities sont fail-closed** — aucune capability = DENY.
5. **Contenu externe = donnees** — jamais des instructions.
6. **Sandbox obligatoire** — aucun code externe sur l'hote.
7. **Secrets jamais persistes** — env/Vault/Docker only.
8. **Audit append-only** — toutes actions journalisées.
9. **TTL des capabilities** — expiration automatique.
10. **NATS auth requise** — pas d'event spoofing.
11. **Git config isole** — GIT_CONFIG_GLOBAL=/dev/null.
12. **Docker capabilities drop** — --cap-drop=ALL.
13. **No new privileges** — --security-opt=no-new-privileges.
14. **Plugin imports bloqués** — os, subprocess, importlib.
15. **Skill content non injecte** — execution via tools seulement.

---

## 6. Tests indispensables

### test_untrusted_git_config_cannot_escape_policy()

- Clone un depot avec .gitconfig malveillant (insteadOf, credential.helper).
- Verifie que GIT_CONFIG_GLOBAL=/dev/null est applique.
- Verifie que les credentiels ne fuient pas.

### test_repository_cannot_access_host_secrets()

- Cree un depot avec symlink vers /etc/passwd.
- Verifie que resolve_safe_path() bloque l'acces.
- Verifie que le conteneur Docker n'a pas /var/run/docker.sock.

### test_agent_cannot_bypass_capability_broker()

- Atreus tente d'executer une commande shell sans capability.
- Verifie que SecureToolEnforcer rejette (deny-by-default).
- Verifie que Security Kernel est le SEUL point d'autorite.

### test_untrusted_skill_cannot_gain_network_access()

- Skill malveillant tente de faire un appel HTTP.
- Verifie qu'ExfilGuard bloque la transmission.
- Verifie que le skill n'a pas de capability network.

### test_mcp_cannot_access_unapproved_filesystem()

- MCP stdio tente de lire /etc/passwd.
- Verifie que le sandbox Docker bloque l'acces.
- Verifie que la capability filesystem n'est pas accordee.

### test_terminal_plugin_path_traversal_blocked()

- Path absolu /etc/passwd passe a read_file().
- Verifie que PathSecurityError est levee.

### test_plugin_cannot_import_forbidden_modules()

- Plugin avec `import importlib; importlib.import_module("os")`.
- Verifie que validate_imports() rejette.

### test_skill_content_cannot_inject_prompt()

- Skill avec content contenant "system: override".
- Verifie que le content est encadre dans <data> tags.
- Verifie que sanitize_external_content() retire les blocs.

### test_capability_ttl_respected()

- Capability avec TTL=1s.
- Wait 2s, tente d'utiliser la capability.
- Verifie DENY (expired).

### test_exfil_guard_blocks_secret_in_output()

- Output contenant une API key.
- Verifie que le secret est redige (REDACTED).

### test_nats_auth_required()

- Connexion sans token.
- Verifie que la connexion est refusee.

### test_builtin_execution_requires_enforcer()

- ToolExecutor() sans policy_enforcer.
- Verifie qu'une exception est levee (fail-closed).

### test_git_hooks_disabled_in_sandbox()

- Clone un depot avec hooks.
- Verifie core.hooksPath=/dev/null.
- Verifie que les hooks ne s'executent pas.

### test_archive_extraction_safe()

- Archive zip avec path traversal (../../../etc/cron.d/backdoor).
- Verifie safe_extract() bloque.

### test_docker_container_hardened()

- Sandbox Docker avec --cap-drop=ALL.
- Verifie qu'aucune capability privilegiee.
- Verifie --security-opt=no-new-privileges.

---

## 7. Architecture a revoir

### 7.1 — Le modèle "demande → policy → capability → sandbox" est INCOMPLET

Le rapport CTO suppose que la **demande** de l'agent peut etre fiable. MAIS :

1. La demande provient d'un LLM qui a lu du contenu externe.
2. Si le LLM est manipule (prompt injection), la demande est malveillante.
3. La policy/cabability evaluent la demande, mais pas la **provenance** de la demande.

**Problem** : un LLM manipule peut demander legitimes capabilities, mais pour
des fins malveillantes. La chaine de confiance est brisee a la source.

**Solution** : 
- Le LLM doit operer en **data-only mode** — contenu lu = donnees, jamais instructions.
- Un "intent classifier" doit valider que la demande est coherente avec le but.
- L'approbation humaine est obligatoire pour les actions a risque eleve.

### 7.2 — Le Security Kernel comme point unique d'autorite est une BONNE IDEE mais RisQUE

- Si le kernel est compromis → tout le systeme est compromis.
- Le kernel doit etre **minime** — code review exhaustif.
- Le kernel doit etre **immuable** — pas de modification a chaud.

### 7.3 — L'approche "sandbox tout" peut etre contournere

- Docker sandbox peut etre contournre via runc CVE, container escape.
- gVisor/Firecracker sont mieux mais plus lents.
- La defense en profondeur (sandbox + policy + capability + exfil) est essentielle.

### 7.4 — Le LLM comme composant central est le point faible

- Le LLM est la source de toutes les demandes.
- Si le LLM est manipule → toutes les protections en aval sont contournables.
- **Le LLM doit etre isole** — ne peut pas lire de fichiers hors sandbox.
- **Le LLM doit etre audit** — toute decision justifiee.

---

## 8. GO / NO-GO pour l'implementation

### GO conditionnel — 5 correctifs P0 obligatoires

| # | Correctif | Status actuel | Deadline |
|---|-----------|---------------|----------|
| 1 | Security Kernel implemente | ❌ N'existe pas | Phase 0 |
| 2 | ToolExecutor policy_enforcer obligatoire | ⚠️ Optionnel | Phase 0 |
| 3 | NATS authentifie | ❌ Pas d'auth | Phase 0 |
| 4 | TerminalPlugin path traversal fixe | ❌ Path traversal | Phase 0 |
| 5 | MCP stdio en Docker sandbox | ❌ Host execution | Phase 1 |

### Risques bloquants (NO-GO si non corriges)

1. **AgentExecutor sans boucle d'outils** — Atreus ne peut pas fonctionner.
2. **TerminalPlugin sur l'hote** — accès host complet dès le premier read.
3. **NATS sans auth** — spoofing d'evenements systemiques.
4. **Security Kernel absent** — aucune autorite centrale.
5. **Skills injectes comme texte** — prompt injection a chaque agent.
6. **Plugin imports non bloque** — code arbitraire possible.
7. **CapabilityManager vide** — deny-by-default mais jamais de allow.
8. **Builtins simules** — la securite n'est pas testee en conditions réelles.

### Recommendation

**NO-GO pour Atreus tant que Phase 0 n'est pas complete.**

Atreus, etant un agent de codage autonome qui interagit avec des depôts Git,
multiplie les surfaces d'attaque (filesystem, Git, commandes, réseau). Sans
Security Kernel, sans sandbox obligatoire, sans boucle d'outils securisee,
Atreus est un vecteur d'attaque majeur.

### Priorite absolue

1. Security Kernel (core/security/kernel.py)
2. TerminalPlugin isolation (Docker sandbox)
3. NATS authentication
4. ToolExecutor enforcer mandatory
5. AgentExecutor tool loop + security integration

Le reste peut suivre progressivement, mais ces 5 éléments sont **bloqueants**.
