# Audit technique de JCode (source d'inspiration pour ETHAN / Atreus)

Date de l'audit : 9 novembre 2026
Dépôt audité : `/home/fatsio/AI/jcode` (upstream `https://github.com/1jehuang/jcode`)
Dépôt cible : `/home/fatsio/AI/Ethan`
Mode : **lecture seule** (aucun fichier modifié, aucune dépendance installée, aucune commande destructive).

---

## 1. Synthèse rapide

JCode est un agent de codage haute performance écrit en **Rust**, organisé comme un **workspace Cargo** (`crates/`) plus une couche CLI/TUI (`src/`). Il vise la faible consommation mémoire, le parallélisme de sessions et une extensibilité forte (providers, MCP, applets, swarm, cloud move, auto-mise à jour). Il possède des mécanismes de sécurité défensive notables (classification déterministe des commandes shell, tiers de permission, approbation humaine, isolation des chemins), mais il reste un projet autonome à ne pas intégrer comme dépendance.

Points forts à reprendre pour ETHAN : ergonomie CLI structurée, classification de risque shell, gate de réflexion, session leases/migration, compaction de contexte, provider doctor/coverage, CI ratchets.

Points à ne pas reproduire tels quels : auto-modification du binaire (self-dev), dépendance à un runtime Rust monolithique, applets/UI host-specific, cloud move propriétaire, télémétrie par défaut.

---

## 2. Cartographie du dépôt

### 2.1 Langages, frameworks et organisation

- Langage principal : Rust (edition 2021), workspace Cargo (`Cargo.toml` racine, `crates/`).
- Couche CLI : `src/cli` (clap, async tokio).
- Couche présentation : `crates/jcode-tui` et sous-crates (`jcode-tui-*`).
- Cœur applicatif : `crates/jcode-app-core`, `jcode-base`, `jcode-core`, `jcode-storage`, `jcode-protocol`.
- Providers : crates dédiés `jcode-provider-*`.
- SDK TypeScript : `sdk/` et crate `jcode-sdk`.
- Tests : Rust (`#[test]`, `tests/`), Python E2E (`tests/*.py`), CI GitHub Actions.
- Plateformes : Linux, macOS, Windows, iOS companion, desktop.

Structure observée :

```text
src/main.rs              # entrée multicall (jemalloc, hotkey, broker, hibernate)
src/lib.rs               # réexporte jcode-tui + cli
src/cli/args.rs          # définition clap complète (1184 lignes)
src/cli/dispatch/        # mapping clap -> commandes runtime
crates/                  # ~90 crates spécialisés
tests/                   # E2E Rust/Python
.github/workflows/       # CI matricielle
```

Référence : `src/main.rs:1-180`, `src/lib.rs:1-45`, `Cargo.toml`.

### 2.2 Entrée principale et multicall

`src/main.rs` configure l'allocateur (jemalloc ou tuning glibc), installe rustls, puis intercepte plusieurs points d'entrée avant Tokio :

- `setup-hotkey --notify-cli-launch` (setup hints) ;
- hotkey listener macOS ;
- broker de notifications macOS ;
- hibernation waiter ;
- enfin runtime Tokio multi-thread et `jcode::run()`.

Référence : `src/main.rs:48-135`.

Ce pattern « multicall » permet un binaire unique avec plusieurs rôles. Il est puissant mais augmente la complexité de sécurité et de maintenance.

### 2.3 CLI et commandes

La CLI est définie par clap dans `src/cli/args.rs` :

- structure globale `Args` avec options globales : `--provider`, `-C/--cwd`, `--model`, `--resume`, `--continue`, `--socket`, `--no-update-check`, `--debug`, `--trace`, `--trace-file`, `--full-auto`, `--dangerously-skip-permissions`, `--resume-session`, `--read-only`, `--sandbox`, `--headless`, `--session-name`, etc. (lignes 33-150).
- enum `Command` très large : `Serve`, `Acp`, `Server`, `Connect`, `Run`, `Login`, `Account`, `Repl`, `Update`, `Version`, `Usage`, `Telemetry`, `SelfDev`, `Debug`, `Auth`, `Provider`, `Memory`, `Session`, `Ambient`, `Cloud`, `Pair`, `Permissions`, `Transcript`, `Companion`, `Dictate`, `SetupHotkey`, `SetupLauncher`, `Browser`, `Replay`, `Model`, `ProviderTestCoverage`, `ProviderDoctor`, `AuthTest`, `Restart`, `Menubar`, `ApiBridge`, `Mcp`.
- sous-commandes dédiées : `MemoryCommand`, `SessionCommand`, `ProviderCommand`, `AuthCommand`, `AmbientCommand`, `CloudCommand`, `RestartCommand`, `ModelCommand`, `ServerCommand`, `TelemetryCommand`, `AccountCommand`, `McpCommand`.

Références : `src/cli/args.rs:33-150`, `155-560`, `560-1184`.

Le mapping vers le runtime est explicite dans `src/cli/dispatch/subcommand_mapping.rs` (mémoire, ambient, cloud sessions, transcript). Cela montre une séparation claire entre parsing et exécution.

### 2.4 Configuration et profils

- Types de configuration dans `crates/jcode-config-types/src/lib.rs` et modules (display, update policy, menubar, power, session, keybindings, web search).
- Surcharge d'environnement dans `crates/jcode-base/src/config/env_overrides.rs`.
- Fichier de config par défaut dans `crates/jcode-base/src/config/default_file.rs`.
- Profils provider OpenAI-compatible via commande `provider add` (base URL, model, context window, API key env/stdin, auth header, env file, default, overwrite, routing).

Références : `crates/jcode-config-types/src/lib.rs`, `src/cli/args.rs` section `ProviderCommand::Add`.

### 2.5 Modèles et providers LLM

- Providers dédiés : Anthropic, OpenAI, Gemini, Bedrock, Copilot, OpenRouter, Antigravity, Cursor, Grok, env.
- Métadonnées et doctor : `jcode-provider-metadata`, `jcode-provider-doctor`.
- Couverture de tests live : commande `provider-test-coverage` / `model-status`.
- Diagnostic strict : `provider-doctor` avec tiers `offline`, `catalog`, `full`.
- Auth test : `auth-test` (login, probe, refresh, smoke, tool smoke, coverage, context audit).
- OAuth et compte Jcode : `AccountCommand`.

Références : `crates/jcode-provider-*`, `src/cli/args.rs` (`ProviderDoctor`, `AuthTest`, `ProviderTestCoverage`).

### 2.6 Agents, outils, MCP, skills/applets

- MCP : commande `Mcp` avec `test`, `list`, `login`, `logout` ; config fusionnée ; OAuth remote ; tests unitaires de parsing (`src/cli/args/mcp.rs`).
- Applets : crate `jcode-applet-types` définit un système de UI déclarative et sandboxée pour desktop, avec manifest, placement, validation (`crates/jcode-applet-types/src/lib.rs`).
- Outils : listes auto-autorisées dans `crates/jcode-base/src/safety.rs` (`read`, `glob`, `grep`, `ls`, `memory`, `todo`, etc.).
- Swarm : crate `jcode-swarm-core` (coordination multi-agents, messages, rôles, tldr, limites).
- Ambient : types et commandes `AmbientCommand`.

Références : `crates/jcode-applet-types/src/lib.rs`, `crates/jcode-swarm-core/src/lib.rs`, `crates/jcode-base/src/safety.rs`, `src/cli/args/mcp.rs`.

### 2.7 Orchestration, planification, erreurs

- Compaction de contexte : `jcode-compaction-core` avec seuils (`COMPACTION_THRESHOLD=0.80`, `CRITICAL_THRESHOLD=0.95`), conservation des 10 derniers tours, estimation tokens, gestion d'images et payloads OpenAI (`crates/jcode-compaction-core/src/lib.rs`).
- Risk gate deux étapes : `jcode-command-risk` (déterministe) + `gate` (réflexion).
- Gestion d'interruption douce : tests d'injection de messages pendant tool calls (`tests/test_injection_thorough.py`).
- Reprise/reload serveur : `server reload`, handoff de sessions, versioning binaire.
- Session leases pour migration cloud (`crates/jcode-storage/src/session_lease.rs`).

### 2.8 Mémoire, historique, sessions, persistance

- Stockage JSON avec reprise depuis backup (`crates/jcode-base/src/storage.rs`).
- Sessions types (`crates/jcode-session-types/src/lib.rs`).
- Leases de migration (`session_leases`) avec epoch monotone, blocage des copies périmées.
- Cloud move/return avec archive, merge 3-way, OAuth transfer sélectif.
- Replay de session (`ReplayCommand`), export timeline/video.
- Mémoire CLI : `MemoryCommand` (list/search/export/import/stats/clear test).

### 2.9 Permissions, approbations, sécurité

- `SafetySystem` avec tiers `AutoAllowed` / `RequiresPermission`, file de requêtes persistée, historique de décisions, expiration des requêtes de sessions mortes (`crates/jcode-base/src/safety.rs`).
- Liste auto-autorisée limitée aux actions lecture/mémoire/todo (`AUTO_ALLOWED`).
- TUI permissions : approbation/refus unitaire ou global, raison de refus (`crates/jcode-tui-permissions/src/lib.rs`).
- `jcode-command-risk` : classification déterministe par blast radius, wrappers, redirections, substitution, cibles catastrophiques (home/root/credentials), refus absolu pour `Catastrophic`, réflexion pour `Confirm`.
- Gate de justification substantive (min 25 caractères, refus des affirmations vides).
- Secret input masqué (`crates/jcode-terminal-prompt/src/secret.rs`).
- Validation de chemins pour leases (rejet des ids path-like).

Références : `crates/jcode-command-risk/src/lib.rs`, `gate.rs`, `paths.rs` (non détaillé ici), `crates/jcode-base/src/safety.rs`, `crates/jcode-tui-permissions/src/lib.rs`, `crates/jcode-terminal-prompt/src/secret.rs`, `crates/jcode-storage/src/session_lease.rs`.

### 2.10 Tests, CI/CD, documentation, dépendances

- CI GitHub Actions (`ci.yml`, 789 lignes) avec gates : module files, fmt, check all targets/features, clippy `-D warnings`, lockfile, warning budget, code size, test size, panic budget, swallowed errors, crate boundaries, SDK parity, wildcard reexports.
- Tests Rust nombreux (651 fichiers de tests dans crates/tests), tests Python E2E.
- Ratchets de qualité (scripts `check_*`).
- Dépendances : workspace Cargo, lockfile vérifié ; `cargo audit` non disponible dans l'environnement (commande absente).

---

## 3. Audit du CLI (détail)

### 3.1 Ergonomie et cohérence

Forces :
- clap avec help/docs intégrés, options globales claires ;
- sortie JSON/NDJSON pour scripting (`Run --json/--ndjson`, `Version --json`, `Usage --json`, etc.) ;
- alias (`selfdev` pour `SelfDev`, `model-status` pour `ProviderTestCoverage`, `menu-bar`/`statusbar`) ;
- commandes cachées pour usages internes ;
- conflits explicites (`conflicts_with`, `conflicts_with_all`) pour éviter des combinaisons invalides.

Faiblesses observées :
- surface CLI très large et hétérogène ; beaucoup de commandes internes exposées (`Receive`, `Activate`, `Export`, `CompleteReturn`, etc.) ;
- commandes à arguments positionnels libres (`Browser action`, `Debug command`) moins sûres que des sous-commandes typées ;
- dépendance à l'environnement et à des sockets locaux.

### 3.2 Parsing et validation

- Parsing fort via clap derive et `value_parser` (ex. tiers, channels).
- Validation manuelle pour certains cas (login flow id, `key=value`).
- Global options résolues avant dispatch ; erreurs typées.

Références : `src/cli/args.rs:1-150`, `src/cli/args/mcp.rs`.

### 3.3 Sessions et contexte

- Reprise de session (`--resume`, `--continue`, `--resume-session`, `SessionCommand::Rename`).
- Replay avec timeline, swarm sync, export JSON/video.
- Session leases et migration cloud (epoch).
- Contexte compaction avec seuils.

### 3.4 Streaming et affichage

- TUI riche (ratatui) dans crates séparés.
- Affichage inline d'images, LaTeX, diff modes (`DiffDisplayMode`).
- NDJSON pour streaming machine-readable.

Référence : `crates/jcode-config-types/src/lib.rs` (`DiffDisplayMode`).

### 3.5 Erreurs, interruptions, reprises

- Interruption douce testée pendant tool calls (injection après tool results) pour éviter les erreurs de pairing `tool_use/tool_result`.
- Gate de risque renvoie un prompt de réflexion plutôt qu'un blocage silencieux.
- Expiration automatique des permissions de sessions mortes.
- Rechargement serveur avec handoff.

Références : `tests/test_injection_thorough.py`, `crates/jcode-command-risk/src/gate.rs`, `crates/jcode-base/src/safety.rs`.

### 3.6 Exécution d'outils et commandes système

- Outil bash non gaté par défaut historiquement ; le crate `command-risk` a été ajouté comme défense (issue #604 perte de home).
- Classification par blast radius, pas par nom de commande.
- Refus absolu pour cibles catastrophiques.
- Réflexion obligatoire pour cas ambigus.

### 3.7 Configuration utilisateur et projet

- Config typée et sérialisée.
- Surcharge env.
- Profils provider stockés dans fichier privé.
- Clés API via stdin pour éviter l'historique shell.
- Keybindings multi-plateformes.

### 3.8 Extensibilité

- MCP OAuth.
- Applets déclaratifs pour desktop.
- SDK TypeScript et API bridge (socket Unix).
- Plugins? Moins centralisé que ETHAN ; plutôt applets + MCP.
- Self-dev : modification/rebuild/reload du binaire (ne pas reproduire tel quel).

### 3.9 Tests

- Tests unitaires Rust massifs.
- Tests E2E Python.
- CI ratchets stricts.
- Tests de sécurité (`tests/e2e/safety.rs`, injection).

---

## 4. Audit de sécurité

### 4.1 Constats classés par gravité

**Critique / à traiter en priorité**
1. Exécution shell historiquement sans gate (`jcode-command-risk` existe pour corriger #604). Risque de destruction massive si désactivé ou contourné.
   - Référence : `crates/jcode-command-risk/src/lib.rs` (doc module).
2. Auto-allowed actions incluent `memory`, `todo`, etc. ; toute nouvelle action sensible doit être ajoutée à `RequiresPermission` par défaut. Risque de sous-classification.
   - Référence : `crates/jcode-base/src/safety.rs` (`AUTO_ALLOWED`).
3. Applets/MCP sont des surfaces d'extension ; validation déclarative existe mais l'isolation processus dépend de l'hôte.
   - Référence : `crates/jcode-applet-types/src/lib.rs`.

**Élevé**
4. Self-dev modifie et recharge le binaire en production-like ; risque de compromission si le modèle est manipulé.
   - Référence : `crates/jcode-build-support/src/lib.rs`.
5. Cloud move transfère des credentials OAuth sélectivement ; la sécurité dépend du canal SSH et des epochs.
   - Référence : `crates/jcode-storage/src/session_lease.rs`, `src/cli/args.rs` (`CloudCommand`).
6. Télémétrie et collecte de données possibles selon configuration (à vérifier dans chaque déploiement).

**Moyen**
7. Parsing shell statique contournable par obfuscation (`sh -c "$(printf...)"`) ; le design l'admet et utilise la réflexion plutôt qu'un blocage dur.
   - Référence : `crates/jcode-command-risk/src/lib.rs`.
8. Surface CLI interne large (commandes cachées) augmente la surface d'attaque si exposée.

**Faible**
9. Pas de `cargo audit` disponible dans l'environnement ; dépendances non vérifiées ici.

### 4.2 Recommandations défensives

- Reprendre la **classification déterministe par blast radius** comme première ligne, puis une gate de justification pour ETHAN/HROT.
- Conserver l'approbation humaine comme autorité finale (HROT) ; ne jamais laisser le modèle valider.
- Ajouter des tests de contournement (obfuscation, wrappers, redirections, substitutions).
- Auditer les dépendances Rust si ETHAN adopte des composants Rust.
- Garder les credentials hors arguments (stdin), déjà fait dans ETHAN pour provider add.
- Journaliser les décisions et expirer les requêtes de sessions mortes.

---

## 5. Ce qui est réellement implémenté vs annoncé

Implémenté et visible dans le code :
- CLI clap complète, providers multiples, MCP, command-risk, safety tiers, compaction, session leases, swarm types, applets, self-dev, cloud move, CI ratchets.

Annoncé/marketing mais non vérifié ici :
- performances comparatives (benchmarks) ;
- stabilité production ;
- sécurité complète des applets/MCP ;
- absence de vulnérabilités dépendances.

---

## 6. Limitations de cet audit

- Aucun build/test JCode exécuté (pas de `cargo build` pour éviter modification/dépendances) ; seules lectures statiques.
- `cargo audit` non disponible.
- L'audit ne couvre pas tout le code Rust (workspace très large) ; il cible les zones pertinentes pour ETHAN.
- Les numéros de ligne sont indicatifs et peuvent varier selon la version.
