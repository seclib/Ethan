# Session — 2026-11-11 — CLI Mission 02 : socle CLI (assainissement et unification)

## Contexte
Branche : `refactor/ethan-rebuild-p0` — commit `57e254b0 canvas`.
Mission 02 (CLI) : terminer les points laissés ouverts par l'audit précédent —
suite de tests CLI restaurée, divergence REPL supprimée, timeouts contextuels,
aides de sous-commandes, frontière Core/CLI.

État initial : 122 entrées non commitées (47 hors CLI — WebUI/Core/Observation —
préservées intactes), 630 tests CLI verts sur `tests/cli/ethan`, 5 modules de
tests legacy en erreur de collection.

## Axe A — Suite de tests CLI

- `tests/cli/legacy_openjarvis/` : 47 fichiers de tests historiques
  `openjarvis` (CLI **Click**, Runtime legacy, `AgentRegistry`/`ToolRegistry`,
  `openjarvis.tools.*`) déplacés **intacts**, avec `README.md` (justification
  par catégorie) et `conftest.py` (`collect_ignore_glob = ["*"]`). Le paquet
  `openjarvis` n'a jamais été commité dans cette branche : ces tests
  portaient sur du code supprimé. Aucun test supprimé.
- `COMMANDS` → `COMMAND_HANDLERS` dans les 6 modules qui référençaient l'ancien
  nom du registre.
- `conftest.py` : 6 fixtures documentées dans `REGRESSION_TEST_SYSTEM.md` mais
  jamais implémentées (`mock_api_offline`, `mock_api_online`, `mock_logs_empty`,
  `mock_memory_empty`, `mock_no_user_plugins`, `mock_config_defaults`) ;
  isolation de `cli.core.daemon_loop` (CACHE_DIR/CACHE_FILE/LOG_FILE).
- Pollution croisée corrigée : trois modules supprimaient `sys.modules['cli.*']`
  sans restaurer → les modules rechargés perdaient les monkeypatch des autres
  tests (frontière HTTP du TUI) et réécrivaient dans le `~/.ethan` réel.
  Restauration du registre après essai (`test_command_matrix`,
  `test_command_performance`, `test_memory_usage`).
- Contrats de tests obsolètes adaptés aux API actuelles : `_pid_write(pid)`,
  `cmd_start` via `subprocess.Popen` (plus `os.fork`), `_cache_write` déplacé
  dans `core/daemon_loop.py`, `MEM_FILE`/`PID_FILE`/`CACHE_FILE` en `str`
  (`os.path.dirname` et non `Path.parent`), commandes `status`/`chat` patchées
  sur la frontière HTTP `cli.core.api` (plus les attributs `alive`/`get_state`
  supprimés du CLI), libellé d'état « STOPPED » (au lieu de « OFFLINE »).
- Moteur de snapshots : `SnapshotEngine.normalize()` rendu public (la capture
  normalisait, la comparaison non → faux écarts) ; chemin de snapshot aligné
  sur le moteur (`{command}__{hash}.txt`) ; re-découverte des commandes dans
  `test_snapshot_regression.py` (la fixture autouse vide le registre → les
  snapshots étaient ignorés en silence).
- Benchmark `status` : `docker info`/`docker ps` mockés (la latence du démon
  Docker rendait le benchmark intermittent) ; seuil de « fuite de modules »
  converti en delta relatif (81 modules = arbre complet, pas une fuite).

**Bug Core corrigé au passage** : `core/client.py::get_token()` ignorait
silencieusement un token legacy non-JWT (1 partie) au lieu de l'adopter →
fallback `config.json` cassé. Le token n'est écarté que s'il est un JWT
expiré.

## Axe B — Divergence REPL supprimée

- `ethan repl` retiré de l'interface publique : erreur d'usage explicite
  (« The 'repl' command has been removed » → « use 'ethan cli' »).
- Modules legacy supprimés (dépendances du Runtime `:8002` / socket Unix
  `/run/ethan/runtime.sock`) : `repl.py`, `client.py` (`RuntimeClient`),
  `session.py` (second registre de sessions local), `boot.py`, `startup.py`,
  `commands/handler.py` (handlers slash), `commands/parser.py`, paquet `ui/`.
- `registry.py` : purge des handlers slash et helpers associés retirés (sans
  objet après la suppression du REPL).
- `interfaces/cli/config.py` : clés `runtime_socket`/`runtime_http`/`sessions_dir`
  retirées du défaut (plus lues par le code).
- Les fonctionnalités uniques du REPL (`/help`, `/exit`, `/clear`, `/status`,
  `/session`, `/history`) sont **toutes couvertes par le TUI**, qui consomme
  déjà les sessions **Core** (`/chats`).
- Données utilisateur conservées : les 9 fichiers de `~/.local/share/ethan/sessions`
  ne sont plus lus ni écrits par le code, mais **n'ont pas été supprimés**.

## Axe C — Timeouts contextuels

Cause racine : `DEFAULTS.profiles.default.timeout = 5.0` (core/config) et le
fallback de `get_profile()` (`cfg["api"]["timeout"]` → 5.0) **plafonnaient
toutes les commandes**, y compris les générations LLM dont le délai propre
(120 s) était passé en `default=` — donc jamais utilisé.

- `core/config.py` : plus de `timeout` implicite dans le profil `default` (le
  délai devient une propriété de chaque commande) ; `api.timeout` n'est repris
  que s'il est défini par l'utilisateur.
- `core/client.py::get_profile()` : idem.
- `core/client.py::get_token()` : token opaque (non-JWT) désormais adopté.

Précédence vérifiée : `--timeout` > `ETHAN_TIMEOUT` > profil (explicite) >
défaut de la commande (5 s rapide / 120 s LLM).

## Axe D — Aide de sous-commandes

- `core/context.py` : `--help` / `-h` **après** une commande lui est transmis
  (il était consommé comme option globale → seule l'aide globale pouvait
  s'afficher) ; idem pour les flags groupés (`-vh`).
- `main.py` : `is_help` ne déclenche l'aide globale que si aucune commande
  n'est identifiée ; `ethan <cmd> --help` et `ethan help <cmd>` affichent
  l'aide de la commande (exit 0).
- `core/api.py` : `subcommand()` lève `_CommandHelp` (aide informative : usage +
  verbes + endpoint) au lieu d'une erreur d'usage ; helper
  `render_command_help()`.
- `commands/plugin.py` (dispatch propre) : aide dédiée.
- `commands/chat.py` : hint obsolète « use 'ethan repl' » → « use 'ethan cli' ».

## Axe E — Frontière Core/CLI

- `commands/router.py` : **plus aucun import `core.llm.*`**. La commande
  consomme l'API Core (`GET /model-routers`, `POST /model-routers/route`) via
  `core/api.py`, en alimentant le routage avec les modèles réellement publiés
  par `GET /models`. Le catalogue `DEFAULT_MODELS` local (inventé, obsolète :
  `claude-sonnet-4`, `gpt-4o`…) est supprimé.
- `interfaces/api/routers/model_router.py` : la route `/route` désérialise
  désormais les modèles JSON en `ModelInfo` (le routeur Core attend des
  objets, pas des dicts → `AttributeError` sur tout appel HTTP de la route).
- `commands/plugin.py` / `plugin_manager.py` : import direct de
  `core.plugins.validator` **conservé et justifié** — BLOCKER documenté :
  ces commandes gèrent des plugins **locaux au poste du client**
  (`~/.local/share/ethan/plugins`, clone Git local) ; le Core ne voit pas ces
  fichiers et `/v1/plugins` expose un autre cycle de vie (ids de catalogue).
  Déporter la validation demanderait d'envoyer le code du plugin au serveur,
  donc de changer le modèle d'exécution : hors périmètre.

## Tests exécutés et résultats

| Commande | Résultat |
|---|---|
| `pytest tests/cli/ethan -q` | **630 passed** (stable sur 5 runs consécutifs) |
| `pytest tests/cli -q` | **630 passed**, 0 erreur de collection, 0 échec |
| `ruff check interfaces/cli` | **All checks passed!** |
| `lint-imports` | **5 kept, 0 broken** (1592 fichiers, 7849 dépendances) |
| `docker compose build --progress=plain api` | **EXIT=0** |
| `docker compose build --progress=plain ui` | **EXIT=0** |

## Validations runtime (Core vivant, ollama local)

- `ethan --version` → `ETHAN CLI v0.0.1.dev137+… (core 0.2.0)`.
- `ethan chat "Réponds simplement OK"` **sans `--timeout`** → `◇ chat 1acd9064-… · ollama/lfm3-omni:latest` puis **`OK`**.
- `ethan router reasoning|code|fast|local` → `lfm3-omni:latest` (routage via l'API).
- `ethan router bogus` → erreur d'usage propre ; `--api-url` invalide → « Core API unreachable ».
- `ethan agent/provider/model/skill/mcp/knowledge/plugin --help` → aide propre de
  chaque commande (usage + verbes + endpoint), exit 0.
- `ethan help agent` → aide de `agent`.
- `ethan repl` → refus explicite pointant vers `ethan cli`.
- `ethan cli` en **PTY réel 120×40** : démarre, se connecte au Core, affiche
  agent/modèle/provider/session, rend la conversation (« Réponds simplement OK »
  → « OK »), 0 squelette résiduel, aucune mention « unreachable ».
- `~/.local/share/ethan/sessions` : 9 fichiers conservés, plus aucun accès
  depuis le code.

## Reste à faire

- **BLOCKER** — validation de plugins locaux via l'API : exige un arbitrage sur
  le modèle d'exécution des plugins (client vs serveur).
- `ethan plugin` reste adossé à `core.plugins.validator` (import direct
  assumé et documenté).
- La WebUI n'expose toujours pas `/model-routers` comme route de navigation
  utilisateur (sans rapport avec la frontière CLI/Core, non traité).
- Dettes hors périmètre non traitées : `window.location.href` de la sidebar,
  `setState` en effet, migration `middleware` → `proxy`.
