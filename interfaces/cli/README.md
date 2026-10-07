# ETHAN CLI — Terminal Interface

Interface console d'ETHAN. **Une interface ETHAN** : elle affiche et
contrôle, elle ne réimplémente jamais la logique métier (règle AGENTS).
Toute capacité vient du Core, exposée par l'API HTTP (`:8000`) ou — pour
le lifecycle Docker — par `docker compose`.

## Lancement

```bash
./ethan cli --help        # point d'entrée recommandé
./ethan cli status        # état réel des conteneurs
ethan --help              # console script (pip install -e .)
python3 -m interfaces.cli.main --help
```

## Points d'entrée

| Entrée | Cible |
|---|---|
| `./ethan cli …` | `scripts/cmd-cli.sh` → `python3 -m interfaces.cli.main` |
| `ethan` (console script) | `interfaces.cli.main:main` (pyproject racine) |
| `ethan-kernel` (console script) | `core.main:main` (harness kernel, sans rapport avec le CLI) |

## Commandes

Découvertes automatiquement (`registry.discover_commands`) — voir `ethan help`.

Toutes les commandes métier passent par **une seule frontière HTTP**
(`core/api.py` → `core/client.py`) et n'implémentent que leurs verbes et
leurs routes Core. Aucune logique métier ne vit dans le CLI.

### Opérationnel

| Commande | Surface Core |
|---|---|
| `ethan status` | Docker + `GET /v1/state`, `/providers`, `/models`, `/diagnostics` |
| `ethan doctor` | `GET /diagnostics` (12 composants réels) + prérequis local |
| `ethan config` | local (`config.json`) et Core (`GET/PUT /config/{domain}`) |
| `ethan logs` | journal local `~/.ethan/logs.json` + `GET /v1/components/{id}/logs` |

```bash
ethan status                    # vue humans : API, services, providers, modèles
ethan status -o json            # un seul document JSON sur stdout
ethan doctor                    # PASS / WARN / FAIL par composant
ethan doctor preflight          # prérequis locaux uniquement, sans réseau
ethan config get api.base_url
ethan config core-get providers
ethan logs --tail 50 --level error
ethan logs component kernel
```

### Capacités Core

| Commande | Routes |
|---|---|
| `ethan chat` | `POST /v1/chat/completions` (+ `/stream` SSE), `GET /v1/chat/history` |
| `ethan model` | `GET /models`, `/models/installed`, `/models/{id}`, `/models/search`, `POST /models/pull` |
| `ethan provider` | `GET /providers`, `/providers/catalog`, `/{id}/models`, `/{id}/capabilities`, `POST /{id}/test`, `PUT /{id}/default` |
| `ethan agent` | `GET/POST /v1/agents`, `/{id}`, `/{id}/execute`, `/{id}/executions`, `/{id}/resources` |
| `ethan skill` | `GET/POST /v1/skills`, `/{id}/toggle`, `/{id}/run` |
| `ethan knowledge` | `GET /v1/knowledge`, `/collections`, `/{id}/documents`, `/reindex` |
| `ethan extension` | `GET /v1/extensions`, `/operations*`, install/enable/disable/update/uninstall — **1 seule famille** pour capability/plugin/cookbook (machine à états Core) |
| `ethan mcp` | `GET /v1/tools/servers`, `/{id}/status`, `/{id}/sync` |
| `ethan mission` | `GET /v1/missions`, `/{id}/steps/{step}/verify|approve` |
| `ethan document` | `GET /v1/rag/documents`, `POST /v1/rag/retrieve`, `/rag/context` |

Alias conservés : `agents`, `missions`, `documents`.

```bash
ethan provider list -o json | jq '.[] | select(.status=="connected") | .id'
ethan model info llama3                 # alias : model show
ethan model search coding
ethan provider capabilities openai
ethan provider default ollama           # synonyme : provider use
ethan agent run researcher --input "audit the logs"   # POST /{id}/execute
ethan agent run researcher --input @task.md            # charge un fichier
ethan extension install <id>              # attend l'opération (progression sur stderr)
ethan extension install <id> --no-wait    # retourne l'objet opération
ethan extension info <id>                 # état réel (vocabulaire Core)
ethan extension operations                # opérations en cours/terminées (reprise de session)
ethan mcp list
```

### Chat

`ethan chat` est un **pass-through complet** du Core Chat : aucune logique
conversationnelle ne vit dans le CLI. Le REPL local historique a été
supprimé au profit de `POST /v1/chat/completions` (+ `/stream` SSE).

```bash
ethan chat "résume ce dépôt"              # one-shot
ethan chat --stream "écris un poème"       # streaming temps réel (TTY)
ethan chat --stream "…" | tee out.txt      # pipe : stdout = réponse seule
ethan chat --model llama3 --provider ollama "…"
ethan chat --agent researcher "…"          # exécute l'agent via Core
ethan chat --chat-id <id> "…"              # reprend une conversation Core
ethan chat --resume "…"                    # dernière conversation (history)
ethan chat                                 # REPL interactif (TTY)
```

- REPL : `/help`, `/reset`, `/exit` — les réponses non-fatales des erreurs
  Core restent sur stderr, la session survit ; Ctrl-C referme proprement.
- `--stream/--no-stream` : le défaut est le streaming sur TTY, le
  one-shot dans un pipe ; `--resume/--chat-id` force le non-streaming.
- `-o json` : **un seul** document JSON (route non-streaming), jamais de
  flux partiel.
- Événements SSE : `content`, `content_replace` (affichage autoritaire),
  `tool_call`/`tool_result` (stderr en `-v`), `done`, `error` → exit 1.
- Contrat délai : 120 s par défaut pour la génération LLM,
  `--timeout` explicite prioritaire (exit 7 en dépassement).

## Options globales

Acceptées **avant ou après** la famille (`ethan -o json status` ≡
`ethan status -o json`) — contrat §3.1.

| Option | Effet |
|---|---|
| `-o, --output human\|json` | format de sortie (défaut `human`) |
| `-q, --quiet` | rien sur stdout en succès (erreurs sur stderr) |
| `-v`, `-vv` | diagnostics sur **stderr** |
| `--no-color` | désactive la couleur (priorité sur `NO_COLOR`) |
| `--profile <nom>` | profil de configuration |
| `--api-url <url>` | endpoint Core pour cet appel |
| `--timeout <sec>` | délai client (dépassement → exit 7) |
| `-y, --yes` | confirme les opérations destructives |
| `--token <jwt>` | déconseillé — warning stderr, préférer `ETHAN_TOKEN` |
| `-h, --help` / `-V, --version` | aide / version |

`--dry-run` est **réservé** : son usage est refusé avec exit 2, jamais un
no-op silencieux.

## Codes de retour (contrat, figés)

| Code | Signification |
|---|---|
| 0 | succès |
| 1 | échec d'opération (le Core a répondu) |
| 2 | erreur d'usage (option inconnue, argument manquant) |
| 3 | authentification (401) |
| 4 | autorisation (403) |
| 5 | dépendance indisponible (API injoignable, 502/503/504) |
| 6 | ressource inexistante (404) |
| 7 | timeout |
| 8 | conflit d'état (409) |
| 70 | erreur interne du CLI |
| 130 | interruption (Ctrl-C) |

`stdout` ne porte que le résultat ; erreurs, warnings et diagnostics vont
sur `stderr`. En mode `json`, stdout contient **exactement un** document
JSON valide.

## Secrets

- `credentials.json` (mode `0600`) est le **seul** stockage local de token.
- `--token` émet un warning : il est visible dans la liste des processus.
- `config get token` est **refusé** ; `logs` scrube les lignes avant affichage.
- Les clés de provider appartiennent au Core : le CLI ne les affiche jamais.
- `provider create/update` **refuse tout secret en argv** (exit 2) :
  utiliser `--api-key-stdin` (lu depuis stdin, jamais affiché).
- Les champs `api_key`, `secret`, `password`, `token` sont masqués (`***`)
  dans les sorties human **et** JSON (`has_api_key` reste un booléen lisible).

## Architecture

```
commands/   1 commande = 1 famille de verbes + ses routes Core
core/api.py frontière partagée : verbs, rendu, codes de retour
core/       client HTTP (URL, Bearer, timeout, JSON), exit_codes,
            context (options globales), config (profils, credentials 0600)
ui/         rendu terminal
plugins/    plugins CLI découverts dynamiquement (manifeste ETHAN_PLUGIN)
registry.py @register + discovery + purge des handlers REPL
main.py     parsing global, dispatch, aide, codes de retour
```

Flux : `commande → core/api.py → core/client.py → API Core :8000`.
Le token vient de `--token`, puis `ETHAN_TOKEN`, puis
`~/.config/ethan/credentials.json` du profil actif.

## Authentification

```bash
ethan auth login      # POST /auth/login → JWT stocké localement
ethan auth status     # GET /auth/me
ethan auth logout
# alternative : ETHAN_TOKEN=<jwt> ethan <commande>
```

Les sous-commandes `auth create-admin|list|reset-password` utilisent
encore l'accès direct à PostgreSQL (dette connue, en attente d'un
bootstrap admin côté Core API).

## Sessions REPL

`ethan repl` ouvre le chat interactif. Les commandes slash (`/exit`,
`/clear`, `/help`, `/status`, `/session`, `/history`) y sont réservées —
le registre CLI les purge systématiquement de `ethan <commande>`.

- Sessions : `~/.local/share/ethan/sessions/` (JSON, un fichier par session)
- Historique local : `~/.ethan/history.json`
- Logs locaux : `~/.ethan/logs.json`

## Tests

```bash
pytest tests/cli tests/test_cli_plugin_cmd.py   # tests CLI ciblés
```

## Installation

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .     # installe le console script `ethan`
ethan --version
```

Le virtualenv activé fournit `ethan` depuis tout répertoire. Le paquet
installable est celui de la racine (`Ethan`), qui contient aussi le Core et
ses dépendances. `interfaces/cli/pyproject.toml` ne doit pas être utilisé
pour produire un paquet : son build échoue actuellement sur la découverte
des paquets setuptools. `interfaces/cli/install.sh` est un ancien wrapper
`ethan-cli` lié au chemin du checkout, pas l'installation officielle.
Voir le [guide CLI](../../docs/user-guide/cli.md) et le
[rapport de revue production](../../docs/audits/CLI_PRODUCTION_AUDIT.md).
