# Mission 07 — Audit de préparation à la stabilisation du CLI ETHAN

Date : 2026-11-11. Branche : `refactor/ethan-rebuild-p0`. HEAD initial : `57e254b04940f5bd4fd64b190ec7fd06de0deadb`.

## 1. État Git initial et final

### Initial
- Branche : `refactor/ethan-rebuild-p0` (à jour avec `origin/refactor/ethan-rebuild-p0`).
- HEAD : `57e254b04940f5bd4fd64b190ec7fd06de0deadb`.
- Entrées staged (suppressions legacy + renommages de tests) et ~145 entrées non commitées préservées.
- Aucune opération destructive effectuée.

### Final
- Branche : `refactor/ethan-rebuild-p0`.
- HEAD : `57e254b04940f5bd4fd64b190ec7fd06de0deadb` (aucun commit).
- Fichiers modifiés par cette mission :
  - `interfaces/cli/main.py` (correction `_show_version` : `api_url` résolu via `get_base_url()` au lieu de `ctx.api_url` vide).
  - `docs/user-guide/cli.md` (sections « Utilisation non interactive et par des agents » et « TUI »).
  - `Obsidian/Architecture/ADR/ADR-4010-cli-tui.md` (documentation de l'architecture TUI existante).
  - `docs/memory/MISSION_07_RELEASE_READINESS.md` (ce rapport).
- Les modifications préexistantes sont préservées. Aucun commit.

## 2. État du packaging et de l'installation

- Point d'entrée officiel : `ethan = interfaces.cli.main:main` (pyproject racine, hatch-vcs).
- Launcher système : `/usr/local/bin/ethan` → `/usr/local/bin/ethan-cli` → `python3 interfaces/cli/main.py` avec `PYTHONPATH=/home/fatsio/AI/Ethan`.
- Version installée : `0.0.1.dev141+unknown.gf8662be91.d20261025` (hatch-vcs, dirty).
- `interfaces/cli/pyproject.toml` est marqué non-distribuable (checkout uniquement) ; la voie officielle est le paquet racine `Ethan`.
- Installation éditable (`pip install -e ".[server,dev]"`) requise pour les dépendances FastAPI/psutil.
- Dépendances CLI : httpx, pyyaml, asyncpg, bcrypt, requests (documentées dans `requirements.txt`).
- Résolution de profils : `${XDG_CONFIG_HOME:-~/.config}/ethan/` ; `ETHAN_CONFIG_DIR` pour override ; profils via `config list/get/set/profiles`.
- Résolution de l'API : `--api-url` > `ETHAN_API`/`ETHAN_API_URL` > profil (`api.base_url`) > `http://localhost:8000`.
- Résolution du token : `Context` > `ETHAN_TOKEN` > `credentials.json` (0600) > bootstrap local (si API locale).
- Variables d'environnement examinées : `ETHAN_API_URL`, `ETHAN_API`, `ETHAN_TOKEN`, `ETHAN_TIMEOUT`, `ETHAN_OUTPUT`, `ETHAN_PROFILE`, `ETHAN_CONFIG_DIR`, `ETHAN_NO_COLOR`, `DATABASE_URL`, `POSTGRES_PASSWORD`.
- Installation testée depuis un répertoire arbitraire (`/tmp`) : `ethan --help` et `ethan --version` fonctionnent (PYTHONPATH injecté par le launcher). ✅

## 3. Résultats des commandes de diagnostic

| Commande | Résultat | Contexte |
|---|---|---|
| `ethan --help` | ✅ affiche le catalogue groupé (Infrastructure/Cognitive/System), exit 0 | terminal réel |
| `ethan --version` | ✅ `ETHAN CLI v0.0.1.dev141+...`, exit 0 | terminal réel |
| `ethan -o json version` | ✅ JSON valide sur stdout, `api_url` résolu (`http://localhost:8000`), exit 0 | terminal réel |
| `ethan status` | ✅ état dégradé propre (`STOPPED`, API unreachable), exit 0, pas de traceback | terminal réel |
| `ethan cli` (TUI) | ⚠️ non lancé en réel (API indisponible) ; point d'entrée et aide vérifiés | non vérifié en réel |
| `pytest tests/cli/ethan -q` | ✅ **630 passed**, 1 warning | tests (venv 3.11) |
| `pytest tests/cli/ethan/tui -q` | ✅ **47 passed**, 1 warning | tests |
| `ruff check interfaces/cli` | ✅ All checks passed | tests |
| `lint-imports` | ✅ 5 kept, 0 broken (1594 fichiers) | tests |

### API indisponible pendant l'audit
La stack Docker (NATS/PostgreSQL/Core API) n'était pas démarrée et aucune instance Core n'écoutait sur `localhost:8000`. Conformément aux consignes (pas de modification système sans autorisation), je n'ai pas démarré la stack. Les tests réels dépendant de l'API n'ont donc pas été exécutés dans cette mission ; ils sont marqués « non vérifié » ci-dessous.

## 4. État de l'expérience CLI

- **Noms et hiérarchie** : 33 commandes enregistrées dans `COMMAND_HANDLERS`, avec alias (`agents`/`agent`, `documents`/`document`, `missions`/`mission`). Groupes affichés dans l'aide. ✅
- **Options globales** : `-o/--output human|json`, `-q/--quiet`, `-v`, `--no-color`, `--profile`, `--timeout`, `--api-url`, `--token`, `--dry-run` (réservé). ✅
- **Arguments obligatoires** : validés par handlers ; erreurs de type usage (exit 2) avec message et hint. ✅
- **Aide** : `ethan --help`, `ethan help <cmd>`, `ethan <cmd> --help` (via `_CommandHelp`) ; aide JSON avec `--help` en mode JSON. ✅
- **Messages d'erreur** : `CLIError` + `_print_error` + codes de sortie cohérents ; mapping HTTP → exit code (401→3, 403→4, 404→6, 503→5, timeout→7). ✅
- **Affichage JSON** : `emit()` produit du JSON lisible avec `--json`/`-o json` ; stdout réservé au JSON, erreurs sur stderr. ✅
- **Affichage humain** : couleurs, tableaux rich. ✅
- **Suggestions de commande** : `UX.suggest_command`. ✅
- **Codes de sortie** : contractuels (0,2,3,4,5,6,7,8,70,130). ✅
- **Streaming SSE** : consommé via `stream_sse()` ; annulation via `abort_event`. ✅
- **Pagination** : ⚠️ la plupart des endpoints ne supportent pas limit/offset ; impact faible (datasets petits en dev). Documenté.
- **Nommage mixte des verbes** : `collection-update` vs `collection delete` vs `document-add`. ⚠️ à harmoniser (priorité basse, non bloquant).

## 5. État du TUI

- Emplacement : `interfaces/cli/tui/` (app, core_client, models, terminal, __main__).
- Démarrage/fermeture : gérés par `app.py` ; Ctrl-C/Ctrl-D. ✅ (tests)
- Navigation clavier : ↑/↓, PgUp/PgDn, Home/End, Tab, Esc. ✅
- Commandes slash : `/help`, `/exit`, `/quit`, `/new`, `/reset`, `/clear`, `/sessions`, `/session`, `/agents`, `/agent`, `/models`, `/model`, `/providers`, `/provider`, `/tools`, `/status`, `/approve`, `/history`, `/retry`. ✅
- Streaming : thread secondaire + file `stream_queue` ; `_apply_event`. ✅
- Sessions : autorité unique Core (`/chats`), pas de registre local. ✅
- HROT : aucun contrôle local ; statuts Core affichés ; panneau `/approve` via `/internal/approval/*` et `/internal/hrot/*`. ✅
- **Limitation connue** : le Core n'émet pas d'événement SSE `permission_request` pendant l'exécution d'un outil ; `SecureToolEnforcer` rejette fail-closed. Le TUI affiche le refus mais ne peut pas arbitrer l'exécution en cours. Contrat proposé mais non implémenté (hors périmètre). Documenté dans ADR-4010.
- **Client API partagé** : le TUI passe par `interfaces.cli.core.client` (request_json/stream_sse). ✅
- Tests : 47 tests passent (entrée, connexion, agents/modèles, streaming, sessions, outils, HROT, indisponibilité Core). ✅
- **Non vérifié en réel** : lancement TUI dans un terminal de taille variable avec API live (API indisponible pendant l'audit).

## 6. Compatibilité avec les agents (OpenCode et autres)

- **Commandes non interactives** : toutes les opérations métier sont disponibles sans TUI. ✅
- **Absence de prompt bloquant en mode automatisé** : `_confirm_destructive` (extension) vérifie `sys.stdin.isatty()` et exige `--yes` sinon (exit 2). `auth login` accepte username en argument et password via getpass (non scriptable pour le mot de passe — par conception sécurité). ⚠️ documenté.
- **Codes de sortie fiables** : ✅
- **Sorties structurées** : ✅ (`-o json`)
- **Messages d'erreur interprétables** : ✅ (JSON sur stderr en mode JSON)
- **Comportement en cas de timeout** : timeout_error → exit 7. ✅
- **Enchaînement de commandes** : commandes indépendantes, sans état local partagé. ✅
- **Absence de dépendance à une session TUI** : ✅
- **Difficultés identifiées pour OpenCode** :
  1. `auth login` nécessite une saisie interactive du mot de passe (getpass) ; pour l'automatisation, utiliser `ETHAN_TOKEN` injecté.
  2. Les commandes d'écriture (memory record, application register/validate, knowledge connect/collection-*/document-*) ne sont pas validées en conditions réelles avec des payloads valides (pas de données de test disponibles).
  3. `ethan cli` (TUI) n'est pas utilisable par un agent (interface plein écran) — mais toutes les opérations sont accessibles en mode non interactif.
- **Aucune dépendance spécifique à OpenCode dans le Core** : confirmé (le CLI est générique). ✅

## 7. Résultats de sécurité

- **Stockage/transmission des tokens** : JWT dans `credentials.json` (mode 0600) ; `ETHAN_TOKEN` privilégié pour les scripts ; `--token` déconseillé (visible dans la liste des processus, avertissement émis). ✅
- **Permissions HROT** : toutes les routes API vérifient `require_permission` ; le CLI ne contourne pas HROT (pas d'accès direct au Core, sauf admin DB directe protégée par `--i-understand-direct-db` et garde-fou mot de passe). ✅
- **Validation des arguments** : parseur strict ; valeurs invalides → usage error (exit 2). ✅
- **Exécution de commandes** : `ethan exec` passe par le Core (pas d'exécution shell directe par le CLI). ✅
- **Accès aux fichiers** : `memory vault-write` via API ; pas d'écriture arbitraire locale. ✅
- **Exposition des secrets dans les logs** : `scrub()` dans `logs.py` redacte tokens/passwords/API keys/JWT avant affichage. ✅
- **Traitement des erreurs sensibles** : erreurs API mappées sans divulguer le token. ✅
- **Aucun affaiblissement de la sécurité pour l'ergonomie** : confirmé. ✅

## 8. Tests exécutés

| Niveau | Couverture | Résultat |
|---|---|---|
| Unitaires (commandes, config, erreurs, registry, discovery, streaming, UX, colors, logging, memory, client, daemon, entrypoint, integrity, first-run, loading, intent, diag) | `tests/cli/ethan/unit/` | inclus dans les 630 |
| Intégration (appels API mockés via TestClient) | `tests/cli/ethan/integration/` | inclus dans les 630 |
| TUI | `tests/cli/ethan/tui/` | 47 passed |
| Régression (matrice de commandes, contrats API, snapshot, compat plugin) | `tests/cli/ethan/regression/` | inclus dans les 630 |
| Benchmarks | `tests/cli/ethan/benchmarks/` | inclus |
| **Total CLI** | | **630 passed**, 1 warning |
| Ruff | `interfaces/cli` | All checks passed |
| lint-imports | 5 contrats | 5 kept, 0 broken |
| Terminal réel | `ethan --help`, `--version`, `-o json version`, `status`, `help application` | ✅ |
| Intégration API réelle | nécessite stack Docker/Core | ⚠️ non vérifié (API indisponible) |
| TUI réel | nécessite API + terminal | ⚠️ non vérifié |
| OpenCode réel | pilotage par agent | ⚠️ non vérifié (pas exécuté dans cette mission) |

## 9. Fichiers modifiés

1. `interfaces/cli/main.py` — correction de la sortie `version` JSON (`api_url` résolu via `get_base_url()`).
2. `docs/user-guide/cli.md` — ajout des sections « Utilisation non interactive et par des agents » et « TUI ».
3. `Obsidian/Architecture/ADR/ADR-4010-cli-tui.md` — documentation de l'architecture TUI (nouveau fichier).
4. `docs/memory/MISSION_07_RELEASE_READINESS.md` — ce rapport (nouveau fichier).

## 10. Défauts corrigés

- **Version JSON trompeuse** : `ethan -o json version` affichait `"api_url": ""` même si le défaut résolu est `http://localhost:8000`. Corrigé en utilisant `get_base_url()` (qui applique profil/env/défaut). Défaut confirmé et reproductible, correction minimale.

Aucun autre défaut bloquant confirmé. Les écarts documentés (capacités Core non exposées par l'API : statut RAG, stratégies, indexation ; import multipart) sont des limites d'architecture/API, pas des défauts du CLI, et ne bloquent pas la stabilisation de l'interface.

## 11. Risques et blocages restants

1. **Capacités Core non exposées par l'API** (statut RAG, stratégies, indexation) : le CLI ne peut pas les afficher. Nécessite des routes API dédiées (hors périmètre CLI). Risque faible.
2. **Import de documents** : format multipart, non adapté au CLI JSON. Nécessite une implémentation multipart dédiée si requis par l'exploitation. Risque moyen pour les workflows RAG documentaires.
3. **Commandes d'écriture non validées en réel** (memory record, application validate/register/bind/activate/invoke, knowledge connect/collection-*/document-*) : tests unitaires/intégration OK, validation réelle partielle (pas de données de test valides). Risque moyen.
4. **Harmonisation du nommage des verbes** (`collection-update` vs `collection delete`) : cosmétique, non bloquant.
5. **Pagination** : absente sur la plupart des endpoints ; impact faible en dev, à prévoir pour les grands datasets.
6. **Auth login non scriptable pour le mot de passe** : par conception (sécurité) ; utiliser `ETHAN_TOKEN`. À documenter dans les guides d'automatisation.
7. **Limitation TUI (approbation in-stream)** : contrat SSE manquant ; documenté (ADR-4010). Non bloquant pour la stabilisation de l'interface.
8. **API non disponible pendant cet audit** : les validations réelles dépendant du Core n'ont pas été exécutées. À compléter lors d'une session avec la stack démarrée.

## Décision finale

**READY WITH LIMITATIONS**

Le CLI ETHAN est utilisable comme interface d'administration et d'exploitation autonome, fiable pour les humains comme pour les agents, dans les limites des contrats API existants. Les contrôles automatisés (630 tests, ruff, lint-imports) passent. Les écarts restants sont documentés (capacités Core non exposées par l'API, import multipart, validations réelles partielles, limitation TUI in-stream) et ne constituent pas des défauts bloquants du CLI. La stabilisation peut être engagée avec ces limitations documentées.
