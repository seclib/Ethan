# Contrat officiel du CLI ETHAN

| | |
|---|---|
| **Version du contrat** | `1.0` — **PROPOSITION**, à figer avant implémentation |
| **Date** | 2026-10-04 |
| **Portée** | Interface `interfaces/cli/` ↔ Core/Runtime via API HTTP `:8000` |
| **Statut** | Spécification interne. Aucune implémentation n'est engagée par ce document. |
| **Autorité** | AGENTS.md (Première Loi) + audit CLI (état comparé §11) |

> Ce document **définit la cible**, pas l'existant. Les écarts entre l'état
> actuel du code et ce contrat sont listés explicitement en §11 (Migration) et
> ne doivent pas être interprétés comme des bugs de cette spécification.

---

## 1. Principes directeurs

1. **Interface fine.** Le CLI est une *interface* ETHAN : il **affiche,
   déclenche, supervise**. Toute intelligence, tout état métier, toute
   configuration de capacité appartient au Core, consommé via l'API HTTP.
   Le CLI ne réimplémente jamais une logique Core (cf. `ethan router`, §9.3).
2. **Conventions Unix modernes.** `--help`, `--version`, exit codes
   documentés, stdout = résultats, stderr = erreurs et diagnostics,
   composabilité (`|`, `xargs`, variables d'environnement), aucune sortie
   superflue, aucune couleur hors TTY.
3. **Deux modes, un contrat.** Mode *humain* (lisible, coloré en TTY) et mode
   *machine* (`--output json`, stable, sans décoration). Les deux modes
   partagent les mêmes commandes, arguments et exit codes.
4. **Déterminisme scriptable.** Jamais de prompt hors TTY. Toute opération
   destructive exige `--yes` hors TTY. Toute option non implémentée est une
   erreur d'usage (exit 2), jamais un no-op silencieux.
5. **Source unique de vérité.** Chaque famille de commandes correspond à des
   capacités **réellement exposées** par le Core via l'API (voir Annexe A).
   Aucune commande n'existe « pour faire joli ».
6. **Unification reflétée.** Quand le Core unifie des concepts (Capabilities /
   Plugins / Cookbook → *Extensions*), le CLI expose **le modèle unifié**,
   pas les trois systèmes d'origine (§9.1).

### Non-objectifs

- Ce contrat ne couvre pas les interfaces WebUI/Desktop.
- Il ne définit pas les schémas métier (ils appartiennent à l'API Core) :
  il définit *comment* le CLI les consomme et les restitue.
- Il ne couvre pas les bibliothèques Python internes (`core/…`) : le CLI
  ne les importe pas, sauf exceptions locales documentées (§8.19).

---

## 2. Modèle de commandes

### 2.1 Grammaire

```
ethan [options globales] <famille> [<verbe>] [<cible|arguments>] [options]
```

- `ethan` (sans argument) ≡ `ethan help` (exit 0).
- **Famille** = ressource ou domaine (nom **au singulier**, cf. 2.3).
- **Verbe** = action sur la famille. Verbes canoniques (vocabulaire fermé) :

| Verbe | Sens | Exemples |
|---|---|---|
| `list` | lister | `ethan agent list` |
| `show` | afficher une ressource | `ethan mission show <id>` |
| `create` | créer | `ethan agent create --name scout` |
| `update` | modifier | `ethan model update <id> …` |
| `delete` | supprimer (destructif → `--yes` hors TTY) | `ethan skill delete <id>` |
| `search` | rechercher | `ethan knowledge search "audit"` |
| `run` | exécuter | `ethan skill run <id>` |
| `test` | tester | `ethan provider test <id>` |
| `enable` / `disable` | activer / désactiver | `ethan skill disable <id>` |
| `install` / `uninstall` / `update` / `configure` / `plan` | cycle de vie extension | `ethan extension install <id>` |
| `logs` | journaux d'une ressource | `ethan extension logs <id>` |
| `export` / `import` | sérialiser / ingérer | `ethan skill export` |
| `get` / `set` / `unset` | clé/valeur config | `ethan config local set timeout 10` |
| `login` / `logout` / `status` | session | `ethan auth login` |
| `operations` | opérations asynchrones | `ethan extension operations` |

- Familles à action unique (pas de verbe) : `chat`, `repl`, `status`,
  `doctor`, `up`, `down`, `restart`, `version`, `help`, `logs`.
- Un verbe inconnu dans une famille valide → erreur d'usage **exit 2**
  (jamais de REPL, jamais de fallback).

### 2.2 Alias

- Les formes **plurielles** historiques sont des alias stables et
  documentés ; elles ne seront jamais retirées sans version majeure du
  contrat (§10) : `agents`→`agent`, `missions`→`mission`,
  `documents`→`document`.
- Aucun autre alias implicite. Les alias n'apparaissent pas dans `--help`
  sauf en annexe.

### 2.3 Noms canoniques (familles du contrat)

| Famille | Alias | Backend |
|---|---|---|
| `chat` | — | API `/v1/message` |
| `repl` | — | local (interactif) |
| `agent` | `agents` | API `/v1/agents` |
| `mission` | `missions` | API `/v1/missions` |
| `skill` | — | API `/v1/skills` |
| `knowledge` | — | API `/v1/knowledge` |
| `document` | `documents` | API `/v1/rag/*` |
| `memory` | — | API `/v1/memory/*` |
| `model` | — | API `/models` |
| `provider` | — | API `/providers` |
| `extension` | — | API `/v1/extensions` |
| `config` | — | API `/config` + local (`config local`) |
| `auth` | — | API `/auth/*` |
| `status` | — | Docker + API `/v1/health` |
| `doctor` | — | API `/diagnostics` + local |
| `logs` | — | local + Docker + API (extensions) |
| `up` / `down` / `restart` | — | Docker Compose |
| `version` | — | local (+ API si joignable) |
| `help` | — | local |

Familles **locales, interface uniquement** (jamais de logique Core, hors
contrat de données Core) : `daemon`, `history`, `suggest`, `bench`,
`plugin` (packs de commandes CLI — **≠** kind `plugin` des extensions Core,
§9.4).

---

## 3. Conventions globales

### 3.1 Options communes (disponibles sur toutes les commandes)

| Option | Env équivalente | Défaut | Sémantique |
|---|---|---|---|
| `-h, --help` | — | — | Fiche d'aide de la commande ; exit 0. |
| `-o, --output <human\|json>` | `ETHAN_OUTPUT` | `human` | Format de sortie (§4). |
| `-q, --quiet` | — | off | Supprime spinners, en-têtes, hints, progression. En mode `json`, sans effet. |
| `-v, --verbose` | — | off | Diagnostic sur **stderr** : URLs appelées, latences, retries. Cumulable `-vv`. |
| `--no-color` | `NO_COLOR` | auto | Désactive la couleur. Priorité : `--no-color` > `NO_COLOR` > détection TTY. |
| `--profile <nom>` | `ETHAN_PROFILE` | profil actif | Sélectionne le profil de configuration (§6.3). |
| `--api-url <url>` | `ETHAN_API` | profil/défaut | Surcharge l'endpoint pour cet appel. |
| `--timeout <sec>` | `ETHAN_TIMEOUT` | 5 s (API) / 30 s (diagnostics) | Délai client ; dépassement → exit 7. |
| `--yes, -y` | — | off | Confirme les opérations destructives. **Obligatoire** si non-TTY ou mode `json`. |
| `--token <jwt>` | `ETHAN_TOKEN` | — | Déconseillé (visible dans `ps`) ; warning sur stderr. Préférer l'env ou `auth login`. |

Règles :

- Toute option non listée ici et non documentée par la commande → **exit 2**.
- `--dry-run` est **réservé** : son usage est refusé avec exit 2 tant qu'il
  n'est pas implémenté (jamais de no-op silencieux).
- Les options globales sont acceptées **avant ou après** la famille
  (`ethan -o json status` ≡ `ethan status -o json`), sauf collision locale.

### 3.2 TTY, interactivité, confirmations

| Situation | Règle |
|---|---|
| Prompt interactif requis (`auth login` sans options) | Autorisé **uniquement si stdin ET stdout sont TTY** et mode `human`. Sinon exit 2 avec message indiquant l'option non interactive (`--password-stdin`). |
| Confirmation destructive (`delete`, `uninstall`, `down --volumes`) | Mode humain + TTY : prompt `[y/N]`. Non-TTY ou `json` : exige `--yes`, sinon exit 2. |
| Pagination | Jamais de pager automatique ; `--limit/--tail` + scripts. |
| `--watch` (status) | Refusé avec `-o json` (exit 2). |
| Couleurs / unicode | Uniquement si TTY, jamais en mode `json`, jamais si `NO_COLOR`/`--no-color`. En pipes, sortie ASCII simple. |

### 3.3 Répartition stdout / stderr

- **stdout** = le résultat de la commande, et rien d'autre. En
  `--output json` : **un seul** document JSON, valide, sans préambule.
- **stderr** = erreurs, warnings, progression, hints, diagnostics `-v`.
- Un succès sans donnée à montrer n'écrit **rien** sur stdout.
- Les commandes ne mélangent jamais les deux flux (pas de `2>&1` requis
  pour parser la sortie machine).

---

## 4. Formats de sortie

### 4.1 Mode humain (`-o human`, défaut)

- Résultats en tableau ou liste alignée, en-têtes courts.
- Identifiants complets toujours affichés (jamais tronqués) pour
  réutilisation en copier-coller.
- Les états d'extension utilisent le vocabulaire unifié du Core
  (`AVAILABLE`, `ENABLED`, …) — jamais une traduction divergente.

### 4.2 Mode machine (`-o json`)

```
ethan model list --output json
```

Règles de stabilité (contrat) :

1. stdout contient **exactement un** document JSON (objet ou tableau).
2. La charge utile reproduit fidèlement la réponse du Core (pass-through
   des champs API). Le CLI n'invente, ne renomme ni ne masque aucun champ
   métier ; il peut **ajouter** des champs d'enveloppe préfixés si
   nécessaire, jamais en retirer.
3. `list` → tableau ; `show` → objet ; opérations asynchrones → objet
   opération (id, état, progression).
4. Timestamps ISO 8601 UTC (`Z`). Aucune couleur, aucun spinner.
5. Les erreurs ne vont **jamais** sur stdout : voir 4.3.

### 4.3 Erreurs (les deux modes)

- Mode humain (stderr) :

  ```
  ✗ error: <message lisible>
    → <hint éventuel, ex: ethan auth login>
  ```

- Mode `json` (stderr) :

  ```json
  {"error": {"code": "unauthorized", "status": 401,
             "message": "Authentification requise",
             "hint": "ethan auth login"}}
  ```

- Codes d'erreur machine (vocabulaire fermé) :
  `usage`, `unauthorized`, `forbidden`, `not_found`, `unavailable`,
  `timeout`, `conflict`, `operation_failed`, `internal`.

### 4.4 `--quiet`

Exemple de contrat : `ethan extension install x -q` en succès n'affiche
rien et sort 0 si l'opération a abouti ; les erreurs restent sur stderr.
`--quiet` ne change **jamais** le contenu JSON en mode `-o json`.

---

## 5. Exit codes — contrat stable

| Code | Nom | Déclencheur | Mapping HTTP Core |
|---|---|---|---|
| `0` | succès | Commande aboutie. | 2xx |
| `1` | échec d'opération | Le Core a répondu ; l'opération a échoué ou l'état est dégradé (`status`/`doctor` partiels). | 4xx métier non listés ci-dessous, 5xx métier |
| `2` | erreur d'usage | Argument/option invalide, manquant, inconnu, ou option réservée non implémentée ; prompt requis hors TTY ; `--yes` manquant. | — (local, avant tout appel réseau) |
| `3` | authentification | Absent/expiré/invalide. | 401 |
| `4` | autorisation | Authentifié mais permission manquante (AGENTS, EXECUTE, ADMIN, WRITE, MEMORY, PLUGINS…). | 403 |
| `5` | dépendance indisponible | API Core injoignable ; Docker absent ; NATS down remonté par le Core. | connexion refusée, 502, 503, 504 |
| `6` | ressource inexistante | ID inconnu. | 404 |
| `7` | timeout | Délai client dépassé (`--timeout`/`ETHAN_TIMEOUT`) ou attente `--wait` expirée. | — (client) |
| `8` | conflit d'état | Transition interdite (machine à états extension), ressource occupée. | 409 |
| `70` | erreur interne | Bug du CLI (stack inattendue). Jamais utilisé pour un échec métier. | — |
| `130` | interruption | SIGINT (Ctrl-C) — convention `128 + signum`. | — |

Précédence : un 401 l'emporte sur tout autre échec ; `usage` (2) est évalué
avant tout appel réseau ; `unreachable` (5) n'est jamais confondu avec un
échec métier (1). Ces codes sont **figés** : les changements futurs ne
peuvent que réserver des codes non utilisés.

---

## 6. Configuration

### 6.1 Fichiers (XDG)

| Fichier | Contenu | Permissions | Versionné ? |
|---|---|---|---|
| `$XDG_CONFIG_HOME/ethan/config.json` (défaut `~/.config/ethan/config.json`) | Profils (endpoint, timeout, output), préférences locales, `current_profile`. **Aucun secret.** | `0644` | Non |
| `$XDG_CONFIG_HOME/ethan/credentials.json` | Token JWT, date d'expiration, par profil. **Secrets uniquement ici.** | `0600` (obligatoire ; le CLI refuse de lire si plus permissif et corrige le mode) | Non |
| `$XDG_DATA_HOME/ethan/sessions/` | Sessions REPL locales. | `0700` | Non |
| `$XDG_STATE_HOME/ethan/history.json`, `logs.json` | Historique et journal local. | `0644` | Non |

`ETHAN_CONFIG_DIR` (réservé) permettra de déplacer la racine de
configuration (containers/CI). Aucun fichier de configuration n'est jamais
créé par une commande en lecture seule.

### 6.2 Variables d'environnement

| Variable | Rôle | Priorité |
|---|---|---|
| `ETHAN_API` | URL de l'API Core (ex. `http://localhost:8000`). | canonique |
| `ETHAN_API_URL` | Alias historique de `ETHAN_API` — supporté, non documenté en aide. | alias |
| `ETHAN_TOKEN` | JWT (CI, scripts). Préféré à `--token`. | secret |
| `ETHAN_PROFILE` | Profil actif pour la session. | — |
| `ETHAN_OUTPUT` | Format par défaut (`human`/`json`). | — |
| `ETHAN_TIMEOUT` | Timeout client en secondes. | — |
| `NO_COLOR` | Standard `no-color.org`. | — |

### 6.3 Profils

```json
{
  "current_profile": "default",
  "profiles": {
    "default": { "api_url": "http://localhost:8000", "timeout": 5, "output": "human" },
    "prod":    { "api_url": "https://ethan.example.lan", "timeout": 30 }
  }
}
```

- Précédence de résolution (du plus fort au plus faible) :
  **flag CLI > variable d'env > profil actif > défauts**.
- Gestion : `ethan config local profile list|create|use|delete|show`
  (local, jamais d'appel Core). `use` écrit `current_profile`.
- Le profil n'affecte **jamais** les données Core ; uniquement la
  connexion et la présentation.

### 6.4 Secrets — règles absolues (règle AGENTS « secret »)

1. **Jamais** de secret dans : code, dépôt git, logs (local ou Core),
   événements, journal `history.json`, messages d'erreur, sortie
   `--verbose`.
2. Un secret transite uniquement : `ETHAN_TOKEN`, stdin
   (`--password-stdin`, `--api-key-stdin`), ou saisie masquée TTY.
3. `credentials.json` est le **seul** stockage local de secret, en `0600`.
4. Les secrets *des providers* (clés API LLM) appartiennent au Core : le
   CLI les transmet une fois (stdin/prompt masqué) puis ne les relit
   jamais ; il n'affiche que des marqueurs (`•••`).
5. `--token`/`--api-key` en ligne de commande : tolérés, mais warning
   stderr (« visible dans les journaux de processus »).

---

## 7. Authentification

### 7.1 Flux

| Commande | Endpoint | Effet |
|---|---|---|
| `ethan auth login [--username u] [--password-stdin] [--profile p]` | `POST /auth/login` | Obtient un JWT ; écrit `credentials.json` (`0600`) ; affiche utilisateur + permissions. |
| `ethan auth status` | `GET /auth/me` | Affiche utilisateur, rôles, permissions, expiration. Exit 0 si session valide, 3 sinon. |
| `ethan auth refresh` | `POST /auth/refresh` | Renouvelle et réécrit le token. |
| `ethan auth logout` | *(aucun endpoint serveur aujourd'hui)* | Efface le token local ; « best effort » serveur le jour où un endpoint de révocation existe. Exit 0 même si le serveur est injoignable (le local est la source). |

### 7.2 Résolution du token (ordre strict)

1. `--token` (déconseillé → warning stderr)
2. `ETHAN_TOKEN`
3. `credentials.json` du profil actif

Un token expiré n'est jamais rejoué silencieusement : → exit 3 + hint
`ethan auth login`.

### 7.3 Règles

- Toute commande qui appelle une route protégée exige un token. Exceptions
  (surfaces publiques ou locales) : `auth`, `version`, `help`, `status`,
  `up/down/restart`. `doctor` fonctionne en mode partiel sans token
  (section système seule, exit 1 — §8.15). Le mapping 401→exit 3 /
  403→exit 4 est systématique (§5).
- `ethan auth status --output json` renvoie l'objet `/auth/me` du Core
  (permissions incluses) — utilisable comme probe de session.
- Les sous-commandes historiques `create-admin`, `list`, `reset-password`
  (accès PostgreSQL direct depuis l'interface) sont **hors catalogue cible**
  (§9.5) — encore présentes aujourd'hui (§11.1) et à retirer : le bootstrap
  admin appartiendra au Core via API.

---

## 8. Référence des familles

Convention de lecture : « Source » = dépendance réelle (API/Docker/local).
Toutes les commandes acceptent les options globales (§3.1) en plus des
options listées.

### 8.1 `ethan chat`

Source : API `POST /v1/message` (session + trace gérés par le Core).

| Forme | Comportement |
|---|---|
| `ethan chat <message…>` | One-shot : envoie le message. Humain : accusé + `session_id`/`event_id`. `-o json` : réponse Core brute. |
| `ethan chat` (sans message) | Démarre le REPL interactif (≡ `ethan repl`). |

Options : `--session <id>` (reprend une session), `--resume/-r` (dernière
session), `--quiet` (accusé minimal).

- La réponse cognitive complète est **asynchrone** (bus d'événements) :
  le contrat v1 se limite à l'accusé Core ; le suivi de réponse
  (`--follow` / streaming) est réservé à la v1.1 (§10.4).
- Erreurs : 5 API down/NATS ; 3 si JWT requis ; 7 timeout.

### 8.2 `ethan repl`

Interface locale interactive. Commandes slash réservées : `/help`,
`/exit`, `/clear`, `/status`, `/session`, `/history`, `/reset`, `/new`.
Jamais de sortie machine (`-o json` refusé → exit 2). Quitter par `exit`,
`/exit` ou Ctrl-D → exit 0. Le registre purge ces slash-commandes du
dispatch CLI (elles ne sont **pas** des commandes `ethan`).

### 8.3 `ethan agent` (alias `agents`)

Source : API `/v1/agents`.

| Sous-commande | Endpoint | Options |
|---|---|---|
| `list` | `GET /v1/agents` | — |
| `show <id>` | `GET /v1/agents/{id}` | — |
| `create --name <n> [--capabilities c1,c2]` | `POST /v1/agents` | permission AGENTS → exit 4 |
| `start\|pause\|stop <id>` | `PUT /v1/agents/{id}` (`status=…`) | — |
| `delete <id>` | `DELETE /v1/agents/{id}` | `--yes` hors TTY |
| `executions <id>` | `GET /v1/agents/{id}/executions` | `--limit` |
| `resources <id>` | `GET /v1/agents/{id}/resources` | outils/skills/MCP visibles |
| `run <id> --input <texte\|@fichier>` | `POST /v1/agents/{id}/execute` | permission EXECUTE |

### 8.4 `ethan mission` (alias `missions`)

Source : API `/v1/missions`.

| Sous-commande | Endpoint |
|---|---|
| `list [--status <s>]` | `GET /v1/missions?status=` |
| `show <id>` | `GET /v1/missions/{id}` |
| `create <titre…>` | `POST /v1/missions` |
| `update <id> [--title\|--status]` | `PUT /v1/missions/{id}` |
| `delete <id>` | `DELETE /v1/missions/{id}` (`--yes`) |
| `verify <id> <step>` | `POST …/steps/{step}/verify` |
| `approve <id> <step>` | `POST …/steps/{step}/approve` |

`verify`/`approve` = points de contrôle humain (human-in-the-loop) :
sortie explicite `verified`/`rejected`, exit 0/1.

### 8.5 `ethan skill`

Source : API `/v1/skills` (+ lab).

| Sous-commande | Endpoint | Remarque |
|---|---|---|
| `list [--query q]` | `GET /v1/skills` | |
| `show <id>` | `GET /v1/skills/{id}` | |
| `search <q>` | `GET /v1/skills/search` | |
| `create --from-file <json>` | `POST /v1/skills` | permission PLUGINS |
| `update <id> --from-file <json>` | `PUT /v1/skills/{id}` | |
| `delete <id>` | `DELETE /v1/skills/{id}` | `--yes` |
| `enable\|disable <id>` | `POST /v1/skills/{id}/toggle` | |
| `run <id> [--input json]` | `POST /v1/skills/{id}/run` | permission EXECUTE |
| `valves <id> get\|set k=v` | `GET\|PUT /v1/skills/{id}/valves` | |
| `export [--out fichier]` | `GET /v1/skills/export` | |
| `import <fichier>` | `POST /v1/skills/import` | |
| `lab test\|results` | `/v1/skills/lab/*` | |

`run` : `-o json` renvoie le résultat d'exécution Core tel quel.

### 8.6 `ethan knowledge`

Source : API `/v1/knowledge` (graphe + collections + imports).
Verbes locaux : `list`, `search`, `create`, `collections`, `imports`.

| Sous-commande | Endpoint |
|---|---|
| `list` | `GET /v1/knowledge` |
| `search <q>` | `GET /v1/knowledge/search?q=` |
| `create <label> [contenu…]` | `POST /v1/knowledge` |
| `collections list\|show <id>` | `GET …/collections`, `…/collections/{id}` |
| `collections create <nom>` | `POST …/collections` |
| `collections retrieve <id> <query>` | `POST …/collections/{id}/retrieve` |
| `imports status <job-id>` | `GET /v1/knowledge/imports/{job_id}` |

### 8.7 `ethan document` (alias `documents`)

Source : API `/v1/rag/*` — pipeline RAG **exposé tel quel**.

| Sous-commande | Endpoint |
|---|---|
| `list` | `GET /v1/rag/documents` |
| `show <id>` | `GET /v1/rag/documents/{id}` |
| `ingest <titre> <contenu\|--file f>` | `POST /v1/rag/documents` (permission MEMORY) |
| `delete <id>` | `DELETE /v1/rag/documents/{id}` (`--yes`) |
| `search <query>` | `POST /v1/rag/retrieve` |
| `context <query>` | `POST /v1/rag/context` |
| `status` | `GET /v1/rag/status` (+ `strategies`, `config` en `-v`) |

### 8.8 `ethan memory`

Source : API `/v1/memory/*` (mémoire Core : faits, événements, recherche).

| Sous-commande | Endpoint |
|---|---|
| `facts list [--category c] [--limit n]` | `GET /v1/memory/facts` |
| `facts search <q>` | `GET /v1/memory/facts/search` |
| `facts show <id>` | `GET /v1/memory/facts/{id}` |
| `facts create --label … --content …` | `POST /v1/memory/facts` |
| `events list` | `GET /v1/memory/events` |
| `search <q>` | `GET /v1/memory/search` |
| `ingest --from-file <json>` | `POST /v1/memory/ingest` |

> **Note de migration** : l'actuel `ethan memory` (historique local de
> commandes) devient `ethan history` (§8.12) ; `ethan memory` est
> ré-affecté à la mémoire Core. Rupture assumée et documentée (§11).

### 8.9 `ethan model`

Source : API `/models`.

| Sous-commande | Endpoint |
|---|---|
| `list [--provider p]` | `GET /models` |
| `search <q>` | `GET /models/search?q=` |
| `show <id>` | `GET /models/{id}` |
| `create --from-file <json>` | `POST /models` |
| `update <id> --from-file <json>` | `PUT /models/{id}` |
| `delete <id>` | `DELETE /models/{id}` (`--yes`) |
| `enable\|disable <id>` | `POST /models/{id}/toggle` |

La **sélection** de modèle pour une tâche (routage) n'est pas exposée :
elle appartient au Core (voir §9.3, `ethan router` déprécié).

### 8.10 `ethan provider`

Source : API `/providers`.

| Sous-commande | Endpoint | Remarque |
|---|---|---|
| `list` | `GET /providers` | clés masquées (`•••`) |
| `show <id>` | `GET /providers/{id}` | |
| `create --from-file <json>` | `POST /providers` | clé via stdin/prompt masqué uniquement |
| `update <id> --from-file <json>` | `PUT /providers/{id}` | |
| `delete <id>` | `DELETE /providers/{id}` | `--yes` |
| `test <id>` | `POST /providers/{id}/test` | exit 1 si connexion KO |
| `default <id>` | `PUT /providers/{id}/default` | |
| `models <id>` | `GET /providers/{id}/models` | |
| `capabilities <id>` | `GET /providers/{id}/capabilities` | |

Règles secrets (§6.4) : la clé API n'apparaît **jamais** dans un argument
positionnel, un log, ni une sortie ; `--api-key-stdin` ou prompt masqué.
`-o json` ne contient que des références de clé (`key_ref`), pas la valeur.

### 8.11 `ethan extension` — le système unifié

Source : API `/v1/extensions` (13 routes). **Une seule famille** couvre les
trois kinds du vocabulaire Core (`core.extensions.types.ExtensionKind`) :

- `capability` — composant d'infrastructure réel (backend docker/pip/npm, a un runtime) ;
- `plugin` — manifeste déclaratif (outils/skills/MCP référencés, pas de runtime) ;
- `cookbook` — recette instanciant des records (prompts, skills, automations).

| Sous-commande | Endpoint |
|---|---|
| `list [--kind <k>] [--state <s>] [--query q]` | `GET /v1/extensions` (`kind` côté Core ; `state`/`query` = sélection sur champs Core) |
| `info <id>` (synonyme explicite : `show`) | `GET /v1/extensions/{id}` |
| `plan <id>` | `GET /v1/extensions/{id}/plan` |
| `install <id>` | `POST …/install` (202) |
| `uninstall <id>` | `POST …/uninstall` (202, `--yes` obligatoire hors TTY → sinon exit 2, rien d'exécuté) |
| `update <id>` | `POST …/update` (202) |
| `enable\|disable <id>` | `POST …/enable\|disable` (202) |
| `logs <id>` | `GET …/logs` |
| `operations` | `GET /v1/extensions/operations` (en cours ET terminées) |
| `operation <op>` | `GET /v1/extensions/operations/{op}` |
| `cancel <op>` | `POST /v1/extensions/operations/{op}/cancel` |

Routes Core **non exposées** par le CLI (surface minimale) : `configure`,
`?tail=` de `logs` — la WebUI les consomme, le CLI ne crée pas de verbe
supplémentaire sans besoin contractuel.

Comportement des opérations asynchrones (202) :

- **Défaut : attente implicite** — le CLI suit l'opération jusqu'à un état
  terminal `OperationStatus`, en affichant la progression du Core
  (`progress`) sur **stderr** (stdout reste un document unique, §4.2) ;
  exit **0** sur `SUCCESS`, **1** sur `ERROR`/`CANCELLED` (l'`error` réelle
  du Core est affichée, jamais réécrite), **7** si `--wait-timeout` dépasse
  ou si l'opération se termine sur `TIMEOUT`, **130** sur interruption
  utilisateur — l'opération **continue côté Core** et reste récupérable
  (`ethan extension operation <op>`), y compris depuis une nouvelle session
  (persistance Core, aucune mémoire locale du CLI).
- `--no-wait` : retourne immédiatement l'objet opération (exit 0 =
  acceptée). Recommandé en CI avec `ethan extension operation <op>`.
- États **toujours** affichés dans le vocabulaire `ExtensionState`
  (`AVAILABLE`, `INSTALLING`, `ENABLED`, `ERROR`, …) — jamais traduits.
- Transition illégale (ex. uninstall pendant install) → HTTP 409 →
  **exit 8**, message explicite.
- Sécurité : permission `READ` pour les lectures, `SETTINGS` pour le cycle
  de vie (401 → exit 3, 403 → exit 4) — le CLI ne décide jamais d'une
  autorisation, il traduit le statut HTTP (§5).

Cette famille **remplace** : l'ancienne notion « capability » (lifecycle
`/v1/components`, désormais interne/WebUI), le « plugin Core »
(`/v1/cookbook` reste interne) et le « cookbook » séparé (§9.1).

### 8.12 `ethan config`

Deux sous-espaces strictement séparés :

**a) Configuration Core (source de vérité : API `/config`)** —

| Sous-commande | Endpoint |
|---|---|
| `get [chemin]` / `list` | `GET /config` |
| `status` | `GET /config/status` |
| `schema [domaine]` | `GET /config/schema[/…]` |
| `validate` | `GET /config/validate` |
| `export [--out f]` | `GET /config/export` |
| `preferences get` | `GET /config/preferences` |
| `preferences set k=v` | `PUT /config/preferences` (permission WRITE) |

**b) Configuration locale CLI (`config local`)** — ne touche jamais le Core :

`ethan config local get|set|unset|list|path` +
`ethan config local profile list|create|use|delete|show` (§6.3).

Interdits : secrets dans `config local` (§6.4) ; `config` sans sous-commande
affiche un résumé lecture seule (endpoint + profil + statut de session).

### 8.13 `ethan auth`

Voir §7 (flux complet). Rappel : `login`, `status`, `refresh`, `logout`.

### 8.14 `ethan status`

Source : Docker Compose (`docker compose ps`) + API `GET /v1/health`.

| Option | Effet |
|---|---|
| `-o json` | `{services: [...], summary: {running, healthy, total}, api: {status, nats_connected}}` |
| `--watch` | Rafraîchissement 3 s (humain uniquement ; refusé en json) |
| `--quiet` | Résumé une ligne : `8/8 running, 8/8 healthy` |

Exit : **0** si tous les services attendus sont healthy **et** l'API
répond ; **1** si un service est down/degraded (l'état est affiché) ;
**5** si l'information n'est pas lisible (Docker absent).

### 8.15 `ethan doctor`

Source : `GET /diagnostics` (JWT requis) + diagnostic système local
(prérequis : Docker, RAM, disque, ports, compose).

| Option | Effet |
|---|---|
| `-o json` | rapport Core + `api: {state: ok\|unauthorized\|unreachable}` + section système |
| `--token` | déconseillé (§7.2) |

Exit : **0** si aucun composant `error`/`unavailable` et API saine ;
**1** si dégradé ou diagnostic partiel (dont le cas « API joignable mais
non authentifiée » — doctor **n'est pas** un check d'auth : pour ça,
`ethan auth status`).

### 8.16 `ethan logs`

| Forme | Source |
|---|---|
| `ethan logs` | Journal local du CLI (dernier `N`, `--tail`, `-o json`) |
| `ethan logs <service>…` | `docker compose logs` (`-f`, `--tail`, `--since`) — flux brut, `-o json` refusé (exit 2) |
| `ethan extension logs <id>` | `GET /v1/extensions/{id}/logs` (§8.11) |

Aucun log applicatif Core n'est dupliqué localement : le CLI ne fait que
**router** vers la source de vérité.

### 8.16bis `ethan exec` — commande système contrôlée (non-shell)

Source : API `/v1/system/exec/*` (capacité Core `core.system_exec`,
lecture seule, approbation humaine systématique). Le CLI ne lance **jamais**
l'exécutable local : il crée une opération, affiche son périmètre et rend le
résultat du Core. `ethan model list` (Core) ≠ `ethan exec ollama list`
(outil local exécuté par le Core).

| Sous-commande | Endpoint |
|---|---|
| `catalogue` | `GET /v1/system/exec/catalogue` |
| `pending` | `GET /internal/approval/pending` (ADMIN) |
| `approve <approval-id>` / `reject <approval-id>` | `POST /internal/approval/resolve` (ADMIN) |
| `<outil> [args] [--cwd DIR] [--no-wait]` | `POST /v1/system/exec/operations` (**202**, `PENDING_APPROVAL`) |
| `operation <op>` | `GET /v1/system/exec/operations/{op}` (demandeur seul) |
| `cancel <op>` | `POST /v1/system/exec/operations/{op}/cancel` (demandeur seul) |

Comportement : polling jusqu'à `COMPLETED|REFUSED|TIMED_OUT|CANCELLED|ERROR`
(stdout/stderr séparés, `exit_code` Core) ; `Ctrl+C` → cancel puis exit
**130** (le Core termine le groupe) ; exit **0** si `exit_code==0`,
**1** sinon, **7** sur `TIMED_OUT`/attente dépassée. Catalogue fermé
(`ollama`/`git`/`python`/`node` en lecture seule), Docker refusé par
politique (jamais de `docker.sock`), `cwd` relatif sous `ETHAN_EXEC_ROOT`,
secrets redacted, audit `COMMAND`. Pas de streaming : `operation` + `cancel`
sont les seuls suivis.

### 8.17 `ethan up` / `ethan down` / `ethan restart`

Ownership infra assumé (Docker Compose) — documenté dans AGENTS/CLI README.

- `up [--build] [--wait]` : démarre la stack ; `--wait` attend les
  healthchecks (timeout → exit 7).
- `down [--volumes]` : arrête ; `--volumes` est destructif → `--yes`
  obligatoire hors TTY (warning explicite sur les données).
- `restart [service…]` : redémarre tout ou des services ciblés.
- Docker absent → exit 5.

### 8.18 `ethan version` / `ethan help`

- `ethan version` : humain `ethan <version>` ; `-o json` →
  `{"cli": "...", "contract": "1.0", "core": null|"...", "api_url": "..."}`
  (`core` = version du Core si un endpoint la publie — `null` sinon ;
  jamais de valeur inventée).
- `-V/--version` au niveau racine ≡ `ethan version`.
- `ethan help [famille [verbe]]` : catalogue groupé (Infrastructure /
  Cognitive / System / Local) ; `ethan <famille> --help` : fiche détaillée
  (verbes, options, exemples, exit codes). `help` d'une entrée inconnue →
  exit 2. `help` n'appelle jamais le réseau.

### 8.19 Familles locales (interface uniquement — hors contrat de données)

| Famille | Rôle | Remarque |
|---|---|---|
| `daemon start\|stop\|status` | Daemon local (watchers/triggers terminal) | aucun état métier |
| `history [--tail n]` | Historique local des commandes/sessions (ex-`memory`) | XDG state |
| `suggest` | Suggestions locales basées sur l'historique | local |
| `bench` | Auto-benchmark de la CLI (outil dev) | local |
| `plugin validate\|install\|remove\|list\|info` | Packs de commandes CLI (`ETHAN_PLUGIN`) | **≠ kind `plugin` Core** (§9.4) |
| `hello`, `weather` | Plugins d'exemple (`interfaces/cli/plugins/`) | démonstration du système de plugins — jamais garantis par le contrat |

Ces familles peuvent disparaître sans affecter ETHAN (test de la Première
Loi) ; elles ne figurent jamais comme sources de vérité métier.

---

## 9. Conformité architecture (Première Loi appliquée au CLI)

### 9.1 Unification reflétée, pas fragmentée

Le Core a unifié Capabilities / Plugins / Cookbook sous `core.extensions`
(3 kinds, 10 états, persistance `CoreRecordStore`, opérations bornées).
Conséquences contractuelles :

- Une **seule** famille `ethan extension` (§8.11) — jamais trois.
- Les états affichés sont ceux du Core (`ExtensionState`), jamais une
  traduction locale qui divergerait.
- `ethan capability` et `ethan cookbook` **n'existent pas** comme familles
  (voir §9.5) : ce seraient des doublons de surface.

### 9.2 Interdits structurels (test de la Première Loi)

Le CLI ne doit jamais :

1. Importer la logique métier Core (`core.rag`, `core.memory`,
   `core.planner`…) sauf exceptions locales §8.19 ;
2. Écrire un état métier dans un fichier local (l'état vit dans Redis/PostgreSQL via l'API) ;
3. Émettre un événement bus directement (pas de NATS dans l'interface) ;
4. Définir providers/agents/missions/mémoire : il les **consomme** ;
5. Décider d'un routage de modèle (Core uniquement).

### 9.3 `ethan router` — dépréciation

L'actuel `ethan router` (modèles en dur + heuristiques locales de routage)
**viole** l'architecture : le routage est une intelligence Core. Il est :

1. marqué `[deprecated]` dans `help` (visible, non retiré) ;
2. remplacé par la lecture via API (`ethan provider list`,
   `ethan model list`, `ethan config get routing…`) ;
3. supprimé du contrat au plus tard en `1.2` (§10.2).

### 9.4 Homonymie `plugin` — deux notions distinctes, ne jamais fusionner

| Terme | Nature | Famille CLI |
|---|---|---|
| plugin **Core** | kind d'extension déclaratif (outils/skills/MCP) | `ethan extension … --kind plugin` |
| plugin **CLI** | pack de commandes locales (`ETHAN_PLUGIN`) | `ethan plugin list\|validate` |

Les fiches d'aide des deux familles doivent mentionner explicitement la
distinction (une phrase chacune) pour éviter toute confusion.

### 9.5 Commandes retirées du catalogue (jamais recréées)

| Ancienne commande | Raison | Équivalent |
|---|---|---|
| `ethan config_cmd`, `ethan service\| update`, `ethan think`, `ethan run`, `ethan agents` (module legacy) | inventées / simulation / doublons | §8 |
| `ethan skill` (si absent) / `ethan mcp` | pas de surface API MCP aujourd'hui | skills via `/v1/skills` ; MCP = détail interne des extensions (§A.3) |
| `auth create-admin\| list\| reset-password` | accès PostgreSQL direct depuis une interface | bootstrap admin côté Core (futur endpoint) |
| `ethan config_cmd.py` / faux `update.py` | fake commands supprimées | `version` + Git |
| Slash-commands REPL purgés du registre (`/help` → commande réelle) | double dispatch | §8.2 |

### 9.6 Checklist d'admission d'une nouvelle commande

Toute proposition de commande doit répondre **par écrit** (dans la PR) :

| # | Question | Si NON |
|---|---|---|
| 1 | **Core** : la capacité existe-t-elle déjà via l'API ? | → implémenter d'abord dans Core/Runtime (jamais dans le CLI) |
| 2 | **Contrat** : la commande entre-t-elle dans une famille/verbe existant (§2.1) ? | → justifier une nouvelle famille dans ce document |
| 3 | **Runtime** : l'action est-elle idempotente ou asynchrone sans état local ? | → repenser (pas d'état métier local) |
| 4 | **Plugins** : la commande dépend-elle d'un plugin CLI ? | → une commande cœur ne doit jamais l'exiger |
| 5 | **Sécurité** : secrets hors argv/logs (§6.4) ? permissions Core mappées (§5) ? destructif gardé par `--yes` ? | → bloqué |
| 6 | **Maintenance** : sortie `-o json` stable définie ? exit codes définis ? | → incomplet |
| 7 | **Tests** : matrice de tests §12 couverte ? | → refusé |

Résultat : si la commande n'a de sens que pour une interface, elle
appartient au CLI ; sinon elle appartient au Core. Le CLI ne crée jamais
une commande « pour faire joli ».

---

## 10. Politique du contrat

### 10.1 Versionnement

- La version du contrat (`1.0`) est indépendante des versions logicielles
  Core/CLI. Elle est exposée par `ethan version -o json` (`contract`).
- **Ajouts** (nouvelles commandes, nouveaux verbes, nouveaux champs JSON) :
  version mineure, rétrocompatibles.
- **Changements cassants** (renommage de commande, disparition de champ,
  changement d'exit code) : version majeure + période de dépréciation.

### 10.2 Dépréciation

1. La commande est marquée `[deprecated] (retrait prévu en <version>)` dans
   `help` et affiche un warning **stderr** à chaque exécution (jamais en
   `-o json`).
2. Délai minimal : une version mineure complète (ex. déprécié en `1.1`,
   retiré au plus tôt en `1.2`).
3. Les alias (§2.2) ne sont jamais dépréciés : ils sont stables.

### 10.3 Réservé pour 1.1 (mentionné, non implémenté — exit 2 si utilisé)

| Élément | Raison |
|---|---|
| `chat --follow` / streaming SSE | suivi de réponse cognitive (bus asynchrone) |
| `ethan event *` | inspection du bus (subscribe/emit) — nécessite surface API dédiée |
| `ethan automation`, `ethan calendar`, `ethan tool` (write) | surfaces API existantes mais non stabilisées pour le CLI (lecture seule via extensions pour l'instant) |
| `--dry-run` global | sémantique à définir par famille |
| `ETHAN_CONFIG_DIR` | racine config déplaçable |

### 10.4 Compatibilité scripting

Tout ce qui est garanti : exit codes (§5), structure stdout (§4), noms de
familles/verbes (§2), options globales (§3.1). Tout le reste (textes
humains, couleurs, tableaux) peut changer sans bump.

---

## 11. Migration : état actuel → contrat

> Table d'écarts. « Actuel » = état du dépôt à la rédaction (post-audit
> CLI, extensions unifiées). Aucun code n'est modifié par ce document.

### 11.1 Familles

| Actuel | Cible | Action |
|---|---|---|
| `agents` | `agent` (+alias `agents`) | renommage canonique, alias conservé |
| `missions` | `mission` (+alias `missions`) | idem |
| `documents` | `document` (+alias `documents`) | idem |
| `memory` (historique local) | `history` | renommage (rupture : voir §8.8) |
| `memory` | **nouveau** : mémoire Core (`/v1/memory/*`) | ré-affectation du nom + implémentation |
| — | `model` | **à créer** (API `/models` existante) |
| — | `provider` | **à créer** (API `/providers` existante) |
| — | `extension` | **à créer** (API `/v1/extensions` existante) |
| `router` | — | déprécier puis retirer (§9.3) |
| `hello`, `weather` | — | exemples de plugins CLI (`interfaces/cli/plugins/`) — **conservés** comme démonstration du système de plugins, hors contrat (jamais garantis) |
| `plugin` (`validate\|install\|remove\|list\|info`) | conservé | aligner description/usage §8.19 |
| `config` (actuel `get\|set\|reset` sur fichier local) | scindé : Core (`/config`) + `config local` | §8.12 |
| `status`, `doctor`, `logs`, `up/down/restart`, `chat`, `repl`, `auth`, `version`, `help` | conservés | aligner sorties/exit codes §4-§5 |
| `daemon`, `suggest`, `bench` | conservés (locaux) | inchangés, hors contrat de données |
| `knowledge` | conservé | aligner verbes §8.6 |
| `skill` | **à créer** (API `/v1/skills` existante) | famille neuve |
| `auth create-admin\|list\|reset-password` | — | **encore présents avec accès PostgreSQL direct depuis l'interface** → à retirer (§9.5), bootstrap admin côté Core |

### 11.2 Transverse

| Sujet | Actuel | Cible |
|---|---|---|
| Options globales | **quasi absentes** : aucun `-o/--output`, `--quiet`, `--verbose`, `--no-color/NO_COLOR` ; `-v` racine = `--version` (conflit) | §3.1 complètes ; résolution : `-V` = version, `-v` = verbose (`--version`/`version` restent stables) |
| `-o json` | sporadique | systématique, contrat §4.2 |
| Exit codes | ad hoc (0/1 mélangés) | §5 (0,1,2,3,4,5,6,7,8,70,130) |
| Token | `ETHAN_TOKEN` > `config.json` mélangé | §7.2 (`--token` > env > `credentials.json` 0600) |
| Config | `config.json` unique | `config.json` (non secret) + `credentials.json` (0600) + profils §6.3 |
| Doctor | URL/token déjà centralisés ; 401 vs unreachable distingués | conserver, mapper exit §8.15 |
| REPL | slash-handlers purgés du registre (fait) | §8.2 |
| Aide | `help` commande réelle + `__meta__` group/description (fait) | fiches §8.18 avec exit codes/exemples |
| Lifecycle | `up/down/restart` réels (fait) | inchangé |
| Fake commands | supprimées (`service/update/think/run/ethan/`) | ne jamais réintroduire (§9.5) |

### 11.3 Ordre de mise en œuvre recommandé

1. **P0** — flags globaux + exit codes + `-o json` sur l'existant ;
2. **P0** — `model`, `provider`, `extension` (surfaces API déjà prêtes) ;
3. **P1** — `skill`, `memory` (Core), renommage `history` ;
4. **P1** — profils + `credentials.json` 0600 ; retrait `hello`/`weather` ;
5. **P2** — dépréciation `router` ; réservés §10.3.

---

## 12. Validation du contrat

### 12.1 Matrice de tests obligatoire (par commande)

| # | Test | Assertion |
|---|---|---|
| T1 | `ethan <cmd> --help` | exit 0, fiche complète (usage, options, exit codes, exemples) |
| T2 | `ethan <cmd>` sans API | exit 5, message stderr, stdout vide |
| T3 | `ethan <cmd>` avec 401 | exit 3 + hint `ethan auth login` |
| T4 | `ethan <cmd>` avec 403 | exit 4, code `forbidden` |
| T5 | Argument/option invalide | exit 2, **aucun** appel réseau |
| T6 | `-o json` | stdout = 1 seul JSON valide, zéro décoration |
| T7 | `--quiet` | stdout vide en succès (hors json) |
| T8 | destructif sans TTY sans `--yes` | exit 2, rien exécuté |
| T9 | secrets | aucune clé/token dans stdout/stderr/history (§6.4) |
| T10 | 404 / 409 | exit 6 / 8 (le cas échéant) |

Tests transverses : parité `help` ↔ registre (aucune commande sans fiche,
aucune fiche orpheline) ; test anti-doublon `capability|→extension`
(§9.1) ; un test interdit désormais toute réintroduction des familles
retirées (§9.5).

### 12.2 Emplacement des tests

`tests/cli/ethan/{unit,integration,regression}` — conventions déjà en
place (client, registry, entrypoint, matrice de commandes, snapshots).
Les tests de contrat `-o json` s'appuient sur des réponses API simulées
(fixtures), pas sur une stack live, pour rester exécutables en CI headless.

---

## Annexe A — Surfaces API de référence

Sources de vérité côté Core (routes réellement montées à la rédaction) :

| Domaine | Routes |
|---|---|
| Auth | `POST /auth/login`, `GET /auth/me`, `POST /auth/refresh`, `POST /auth/logout`* |
| Message | `POST /v1/message`, `GET /v1/intent`, `GET /v1/health`, `/v1/ws` |
| Agents | `/v1/agents[…/executions\|/resources\|/execute]` |
| Missions | `/v1/missions[…/steps/{id}/verify\|approve]` |
| Skills | `/v1/skills[…\|/search\|/toggle\|/run\|/valves\|/export\|/import\|/lab/*]` |
| Knowledge | `/v1/knowledge[…/search\|/collections\|/imports]` |
| RAG | `/v1/rag/documents\|retrieve\|context\|status\|strategies\|config` |
| Memory | `/v1/memory/facts\|events\|search\|ingest` |
| Models | `/models[…\|/search\|/toggle]` |
| Providers | `/providers[…\|/test\|/default\|/models\|/capabilities]` |
| Extensions | `/v1/extensions[…\|/plan\|/install\|/uninstall\|/update\|/enable\|/disable\|/configure\|/logs\|/operations]` (13 routes) |
| Config | `/config[…\|/status\|/schema\|/validate\|/export\|/preferences]` |
| Diagnostics | `/diagnostics` |
| Components (legacy) | `/v1/components*` — **interne/WebUI**, remplacé par extensions côté CLI |

\* `auth logout` : pas de route serveur aujourd'hui ; le CLI purge le token
local (voir §7.1).

Surfaces volontairement **non couvertes** par la v1.0 du contrat :
`/v1/tools` (lecture seule pour l'instant), `/v1/domains`,
`/v1/automations`, `/v1/calendar`, `/v1/cookbook` (interne, remplacé par
`extension --kind cookbook`), MCP (aucune API dédiée). Elles réapparaîtront
en `1.1` si leur surface API se stabilise (§10.3).

---

## Annexe B — Historique du document

| Version | Date | Changement |
|---|---|---|
| 1.0 (proposition) | 2026-10-04 | Version initiale. S'appuie sur : AGENTS.md (Première Loi), audit CLI post-unification, ADR-4005 (extension trust model), ADR-4006 (tool applications), extensions unifiées `core/extensions/`. |

### Références

- `AGENTS.md` — Première Loi (interface vs Core), règle secrets.
- `docs/architecture/adr/ADR-4005-extension-trust-model.md`
- `docs/architecture/adr/ADR-4006-tool-applications-privilege-boundary.md`
- `interfaces/cli/README.md` — documentation opérationnelle du CLI.
- Audit CLI (état comparé) — base de la section §11.

---

> **Statut : PROPOSITION — en attente de validation.**
> Toute divergence constatée entre ce document et le code doit être
> traitée soit comme un bug de code, soit comme un amendement de ce
> document (PR avec justification, §9.6), jamais comme un flou toléré.
