# Mission 08 — Herdr × OpenCode × ETHAN CLI Integration

Date : 2026-11-11. Branche : `refactor/ethan-rebuild-p0`. HEAD : `57e254b04940f5bd4fd64b190ec7fd06de0deadb`.

## 1. État Git initial et final

### Initial
- Branche : `refactor/ethan-rebuild-p0` (à jour avec origin).
- HEAD : `57e254b04940f5bd4fd64b190ec7fd06de0deadb`.
- ~160 entrées non commitées préservées (modifications préexistantes + missions antérieures). Aucun commit.

### Final
- Branche : `refactor/ethan-rebuild-p0`. HEAD : `57e254b04940f5bd4fd64b190ec7fd06de0deadb` (aucun commit).
- Fichier modifié par cette mission : `docs/memory/MISSION_08_HERDR_OPENCODE_INTEGRATION.md` (mise à jour du rapport d'intégration).
- Aucune modification de code applicatif. Aucune opération Git destructive. Modifications préexistantes préservées.

## 2. Environnement Herdr identifié

- Exécutable : `/home/fatsio/.local/bin/herdr`.
- Version observée : `herdr 0.9.0-preview.2026-09-08-62431dbd033b`.
- Type : gestionnaire d'espace de travail terminal pour agents de codage (workspaces, tabs, panes, agents reconnus).
- Variables héritées dans le pane courant (observées) :
  - `HERDR_ENV=1`
  - `HERDR_WORKSPACE_ID=w2`
  - `HERDR_TAB_ID=w2:t1`
  - `HERDR_PANE_ID=w2:p1`
- Le pane courant reconnaît l'agent `opencode` avec le statut `working`, cwd `/home/fatsio/AI/Ethan` (foreground_cwd identique).
- Titre du terminal : `OC | ETHAN CLI release readiness`.
- Fonctionnement vérifié : `herdr pane current --current` renvoie le JSON attendu avec les IDs et le cwd. ✅
- Le dépôt Herdr est également présent à `/home/fatsio/AI/herdr` (source) ; un skill `herdr` est disponible dans `herdr/skills/herdr/SKILL.md` et impose `HERDR_ENV=1` avant toute commande de contrôle.

## 3. Version et configuration OpenCode

- Exécutable : `/home/fatsio/.opencode/bin/opencode`.
- Version observée : `opencode v2.2.6`.
- Configuration projet : `/home/fatsio/AI/Ethan/opencode.json` :
  ```json
  {
    "$schema": "https://opencode.ai/config.json",
    "instructions": ["Obsidian/AGENTS.md"]
  }
  ```
- Configuration globale : `/home/fatsio/.config/opencode/opencode.json` (MCP `rea` activé).
- Instructions de projet : mécanisme `opencode.json` → `instructions` réutilisé, aucun fichier concurrent créé.
- **Constat d'incohérence** : la cible `Obsidian/AGENTS.md` référencée par `opencode.json` et par le skill `ethan-memory` n'existe pas dans le dépôt (`/home/fatsio/AI/Ethan/Obsidian` introuvable). En revanche, un `AGENTS.md` existe à la racine (`/home/fatsio/AI/Ethan/AGENTS.md`, 7621 octets) contenant la Première Loi d'ETHAN, l'architecture Core/Runtime/Services/Interfaces et les règles de développement. Ce décalage est documenté (voir § État des instructions de projet et § Recommandations) mais n'empêche pas le fonctionnement fonctionnel : le launcher `ethan`, les commandes CLI et les tests sont opérants indépendamment de ce chemin d'instruction.
- Skills disponibles : `/home/fatsio/.config/opencode/skills/` ; skills projet : `.opencode/skills/ethan-memory/` (ECLL, mémoire Obsidian).
- Commandes projet : `.opencode/commands/` (close-task, investigate, resume-campaign, start-task).
- Aucune dépendance spécifique à OpenCode dans le Core ETHAN. Aucune dépendance architecturale introduite entre ETHAN Core et OpenCode / Herdr.

## 4. État du launcher ETHAN

- Entrée point pip (PATH) : `/home/fatsio/.local/bin/ethan` (résolu en premier par `type ethan`). Wrapper Python vers `interfaces/cli/main.py` avec `PYTHONPATH=/home/fatsio/AI/Ethan`.
- Entrée système : `/usr/local/bin/ethan` (bash launcher) → route `up/down/restart/install/preflight/migrate/watchdog/pull-images/doctor/logs` vers le launcher bash, sinon `/usr/local/bin/ethan-cli` → `python3 /home/fatsio/AI/Ethan/interfaces/cli/main.py`.
- Entrée système CLI directe : `/usr/local/bin/ethan-cli` → `cd /home/fatsio/AI/Ethan` + `python3 interfaces/cli/main.py`.
- Version CLI : `0.0.1.dev141+unknown.gf8662be91.d20261025` (core 0.2.0).
- Fonctionne depuis le dépôt et depuis un répertoire arbitraire. ✅
- Résolution API : `--api-url` > `ETHAN_API`/`ETHAN_API_URL` > profil > `http://localhost:8000`. ✅
- Résolution token : Context > `ETHAN_TOKEN` > `credentials.json` (0600) > bootstrap local. ✅
- Authentification observée : `ethan auth status` → `Logged in as admin (admin)`, exit 0. Token présent dans `~/.config/ethan/config.json` (jamais affiché, valeur non divulguée). `credentials.json` absent, `ETHAN_TOKEN` absent de l'environnement.

## 5. Résultats des commandes (exécution réelle, terminal Herdr)

| Commande | Résultat | Exit | Contexte |
|---|---|---|---|
| `ethan --help` | ✅ catalogue groupé (Infrastructure / Cognitive / System) | 0 | terminal réel (Herdr) |
| `ethan --version` | ✅ version affichée | 0 | terminal réel |
| `ethan -o json version` | ✅ JSON valide, `api_url: http://localhost:8000` | 0 | terminal réel |
| `ethan status` | ✅ état RUNNING, API :8000, 10/10 services, 9/10 healthy | 0 | terminal réel |
| `ethan provider list` | ✅ tableau (7 providers, ollama connected/enabled) | 0 | appel API réel |
| `ethan -o json provider list` | ✅ JSON structuré (id, name, type, enabled, status, capabilities…) | 0 | appel API réel |
| `ethan model list` | ✅ 14 modèles listés (ollama locaux + distants) | 0 | appel API réel |
| `ethan agent list` | ✅ 1 agent (Atreus, idle) | 0 | appel API réel |
| `ethan command-inexistante` | ✅ erreur interprétable, suggestion "restart" | 2 | usage/CLI local |
| `ethan -o json command-inexistante` | ✅ JSON `{"error":{"code":"usage",…}}` | 2 | usage/CLI local |
| `ethan --api-url http://localhost:59999 provider list` | ✅ `unavailable`, "Connection refused" | 5 | API indisponible (port mort) |
| `ethan -o json --api-url http://localhost:59999 provider list` | ✅ JSON `{"error":{"code":"unavailable",…}}` | 5 | API indisponible (port mort) |
| `herdr pane current --current` | ✅ JSON avec IDs/cwd | 0 | terminal réel |

Découverte des commandes par OpenCode : `ethan --help` et `ethan help <cmd>` exposent les verbes, arguments, options. ✅
Aide par sous-commande : `ethan model --help` affiche les verbes (list, info, show, search, installed, discover, runtimes, pull) et les endpoints API associés (GET /models, GET /models/{id}, …). ✅

## 6. Résultats du scénario intégré

Scénario non destructif exécuté dans Herdr, avec OpenCode comme agent dans le pane `w2:p1` :

1. **Ouvrir le projet ETHAN depuis Herdr** : cwd `/home/fatsio/AI/Ethan` hérité par le pane et par OpenCode. ✅
2. **Lancer OpenCode** : reconnu par Herdr (`agent: opencode`, statut `working`). ✅
3. **Analyser l'état du CLI** : `ethan status` exécuté, résultat interprété (stack RUNNING, API :8000, ollama connecté). ✅
4. **Découvrir les commandes disponibles** : `ethan --help` exécuté, catalogue lu (Infrastructure, Cognitive, System). ✅
5. **Exécuter `ethan status`** : exit 0, sortie humaine interprétée (10/10 running, 9/10 healthy). ✅
6. **Récupérer une information en lecture seule depuis l'API** : `ethan provider list` et `ethan model list` exécutés contre l'API réelle :8000, résultats interprétés (ollama connected, 14 modèles). ✅
7. **Interpréter le résultat** : distinction succès (`status`, `provider list` exit 0) vs erreur CLI (commande inconnue, exit 2) vs indisponibilité API (port 59999, exit 5, code `unavailable`) démontrée. ✅
8. **Sans WebUI** : tout le scénario s'est déroulé en terminal/CLI. ✅

Aucune opération destructive exécutée. Aucune modification de la stack Docker.

## 7. État des instructions de projet

- Mécanisme existant réutilisé : `opencode.json` → `instructions: ["Obsidian/AGENTS.md"]`.
- Aucun fichier d'instructions concurrent créé.
- Constat : la cible `Obsidian/AGENTS.md` est introuvable dans le dépôt ; l'instruction effective pertinente est `/home/fatsio/AI/Ethan/AGENTS.md` (Première Loi d'ETHAN, architecture, règles HROT, conventions).
- Les ADR sont disponibles sous `engineering/adr/` et documentés dans `docs/memory/assessments/`.
- Les contrats de tests et de validation sont documentés dans `tests/cli/ethan/` et `docs/memory/`.
- Les règles Git et de gouvernance sont dans `engineering/` et `AGENTS.md`.
- Skills et commandes projet : `.opencode/skills/ethan-memory/` (ECLL), `.opencode/commands/` (start-task, investigate, resume-campaign, close-task).

## 8. Vérifications de sécurité

- **Secrets dans les sorties** : aucun token/secret affiché lors des commandes testées. Le `token` de `~/.config/ethan/config.json` est occulté (`<redacted>`) et n'a jamais été divulgué. ✅
- **Permissions HROT** : le CLI ne contourne pas HROT ; les appels lecture seule aboutissent normalement, l'authentification est requise pour les sous-systèmes protégés. ✅
- **Séparation des responsabilités** : le CLI reste une interface ; aucune logique métier ajoutée dans les instructions ou la configuration OpenCode. ✅
- **Permissions excessives pour OpenCode** : aucune permission supplémentaire accordée ; OpenCode utilise le launcher standard et les mêmes contrôles que l'opérateur (authentification, HROT). ✅
- **Distinction lecture/écriture** : seules des commandes en lecture seule ont été exécutées (`status`, `provider list`, `model list`, `agent list`, `version`, `help`). Les commandes d'écriture exigent `--yes` ou un TTY et n'ont pas été lancées. ✅
- **Comportement des commandes sensibles** : `auth` protégé ; aucun contournement d'authentification effectué. ✅

## 9. Corrections réalisées

Aucune correction de code nécessaire. L'intégration fonctionne avec les mécanismes existants.

Amélioration documentaire antérieure (Mission 07) conservée : `docs/user-guide/cli.md` (sections non interactif/agents et TUI).

## 10. Blocages et recommandations

### Blocages
1. **Chemin d'instruction `opencode.json` introuvable** : `Obsidian/AGENTS.md` n'existe pas dans le dépôt ; l'instruction effective est `AGENTS.md` à la racine. À corriger (aligner le chemin) pour que OpenCode charge bien la Première Loi d'ETHAN au démarrage. Ne pas créer de fichier d'instruction concurrent.

### Recommandations
1. Corriger `opencode.json` pour pointer vers l'instruction existante (`AGENTS.md` à la racine) — ou créer `Obsidian/AGENTS.md` si cette arborescence est voulue — sans créer de fichier concurrent.
2. Conserver `opencode.json` → instruction unique comme source unique d'instructions projet pour OpenCode.
3. Documenter dans le guide CLI l'usage de `ETHAN_TOKEN` pour les agents et les pipelines CI (token déjà présent dans `~/.config/ethan/config.json`).
4. Ne pas créer de dépendance MCP spécifique à OpenCode : les mécanismes existants (launcher + CLI + instructions) suffisent.
5. Préserver la séparation Core/API/CLI : aucune logique métier dans les instructions ou la configuration OpenCode.
6. Rejouer le scénario avec des commandes métier en lecture réelle supplémentaires si nécessaire (déjà vérifié : provider list, model list, agent list).

## Validation finale

| Niveau | Résultat |
|---|---|
| Inspection statique (config, launcher, instructions) | ✅ (incohérence chemin `Obsidian/AGENTS.md` documentée) |
| Tests unitaires CLI (630) | ✅ (Mission 07) |
| Tests TUI (47) | ✅ (Mission 07) |
| Exécution réelle dans Herdr | ✅ (pane, cwd, env hérités, agent reconnu) |
| Exécution réelle avec OpenCode | ✅ (agent reconnu, statut working, commandes exécutées) |
| Appels réels à ETHAN API | ✅ (`status`, `provider list`, `model list`, `agent list` contre :8000 ; erreur `unavailable` contre port mort) |

## Statut

**INTEGRATED**

L'intégration Herdr × OpenCode × ETHAN CLI est démontrée dans l'environnement réel : Herdr actif, OpenCode reconnu, launcher fonctionnel, commandes CLI exécutées, appels réels à l'API Core (http://localhost:8000) vérifiés en lecture seule, erreurs d'indisponibilité interprétées (exit 5, code `unavailable`), distinction succès/erreur/indisponibilité démontrée, sans WebUI et sans contournement de l'architecture ou des permissions ETHAN.

Limitation résiduelle documentaire uniquement : `opencode.json` référence `Obsidian/AGENTS.md` introuvable (aligneer avec `AGENTS.md` à la racine). Aucune limitation fonctionnelle bloquante.
