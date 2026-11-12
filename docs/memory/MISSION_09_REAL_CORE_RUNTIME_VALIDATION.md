# Mission 09 — Real Core Runtime Validation

**Projet** : ETHAN OS  
**Dépôt** : `/home/fatsio/AI/Ethan`  
**Branche** : `refactor/ethan-rebuild-p0`  
**HEAD initial** : `57e254b04940f5bd4fd64b190ec7fd06de0deadb`  
**Date** : 2026-11-11  
**Rapport** : `docs/memory/MISSION_09_REAL_CORE_RUNTIME_VALIDATION.md`  
**Nature** : validation runtime réelle, phases A et B uniquement (pas de writes, pas de démarrage de services sans autorisation, pas de modifications de code).

---

## 1. État Git initial

- Branche : `refactor/ethan-rebuild-p0` (à jour avec `origin/refactor/ethan-rebuild-p0`).
- HEAD : `57e254b04940f5bd4fd64b190ec7fd06de0deadb`.
- Entrées staged (suppressions legacy + renommages de tests) et ~151 entrées non commitées préservées.
- Aucune opération destructive effectuée.
- Les modifications préexistantes (y compris `docs/memory/PROJECT_STATE.md`, `docs/memory/DAENA_GLOBAL_ARCHITECTURE_AUDIT.md`, `docs/memory/sessions/*`) sont préservées.

## 2. Environnement runtime

### 2.1 Services Docker

Démarrage autorisé par l'opérateur (`./ethan up`) — stack complète démarrée avec succès :

| Service | Statut | Santé | Port |
|---|---|---|---|
| api | running | healthy | 8000 |
| kernel | running | healthy | 8080 |
| postgres | running | healthy | 5432 |
| redis | running | healthy | 6379 |
| nats | running | healthy | 4222 |
| modules | running | healthy | — |
| python-base | running | running | — |
| odin-controller-1 | running | healthy | — |
| pg_backup | running | healthy | 5432/tcp |
| ui | running | healthy | 3001 |

Résultat : 10/10 démarrés, 9/10 healthy (python-base en cours d'initialisation au moment de l'audit, sans impact sur l'API).

### 2.2 API Core

- Endpoint health : `GET http://localhost:8000/health` → `200 OK`, `{"status":"ok","service":"api","nats_connected":true}`.
- OpenAPI : `GET http://localhost:8000/openapi.json` → `200 OK`.
- `ethan status` : runtime RUNNING, Core API marqué **unreachable** avec erreur `API 401: Authentification requise. Cookie ou Token manquant.`
- `ethan doctor` : `WARN Core API reachable but unauthenticated`, hint `ethan auth login`.

### 2.3 Authentification

- Variable `ETHAN_TOKEN` : non définie.
- Fichier `~/.config/ethan/credentials.json` : absent.
- `ethan auth --help` non supporté ; verbes disponibles : `login|status|logout|create-admin|list|reset-password`.
- `ethan auth status` : à tester (voir §4).
- Aucun principal authentifié disponible dans la session.

**Décision de l'opérateur** : ne pas authentifier (pas de création d'admin, pas de token fourni). Les sous-systèmes protégés sont donc **bloqués par l'authentification**. Aucune opération d'écriture n'a été effectuée.

## 3. API/Core availability

| Vérification | Résultat | Preuve |
|---|---|---|
| API HTTP disponible | OUI | `curl /health` → 200, nats_connected=true |
| OpenAPI disponible | OUI | `curl /openapi.json` → 200 |
| NATS connecté | OUI | health response |
| PostgreSQL disponible | OUI | service healthy, port 5432 |
| Core runtime authentifié | NON | 401 sur les routes protégées |
| Provider subsystem | NON VÉRIFIÉ | bloqué par auth (401) |
| Agent subsystem | NON VÉRIFIÉ | bloqué par auth (401) |
| Application manager | NON VÉRIFIÉ | bloqué par auth (401) |
| HROT | NON VÉRIFIÉ | bloqué par auth (401) |
| Knowledge subsystem | NON VÉRIFIÉ | bloqué par auth (401) |
| Memory/Engineering Memory subsystem | NON VÉRIFIÉ | bloqué par auth (401) |
| RAG/Document subsystem | NON VÉRIFIÉ | bloqué par auth (401) |
| MCP/Tools subsystem | NON VÉRIFIÉ | bloqué par auth (401) |

## 4. Commandes CLI testées (lecture seule, phases A et B)

### 4.1 Commandes ne dépendant pas de l'API

| Commande | Exit | Résultat |
|---|---|---|
| `ethan --version` | 0 | `ETHAN CLI v0.0.1.dev141+unknown.gf8662be91.d20261025` |
| `ethan -o json version` | 0 | JSON valide sur stdout, `api_url` résolu (`http://localhost:8000`), `core: null` |
| `ethan status` | 0 | état RUNNING, Core API unreachable (401) |
| `ethan -o json status` | 0 | JSON valide, `core.reachable: false`, erreurs structurées |
| `ethan doctor` | 0 | WARN Core API reachable but unauthenticated ; prérequis 5/6 (ports occupés) |
| `ethan -o json doctor` | 1 | JSON d'erreur sur stdout, code `unavailable` |
| `ethan daemon status` | 0 | `daemon: stopped`, cache présent |
| `ethan --help` | 0 | catalogue groupé (Infrastructure/Cognitive/System) |

### 4.2 Commandes dépendant de l'API (bloquées par auth)

Toutes les commandes métier testées renvoient `exit 5` avec une erreur structurée sur stderr (en mode JSON) ou un message humain (en mode humain) :

| Commande | Exit | Code erreur | Message |
|---|---|---|---|
| `ethan provider list` | 5 | unavailable | Core API unreachable: … Connection refused (avant démarrage) |
| `ethan -o json provider list` | 5 | unavailable | JSON d'erreur sur stderr |
| `ethan model list` | 5 | unavailable | idem |
| `ethan agent list` | 5 | unavailable | idem |
| `ethan skill list` | 5 | unavailable | idem |
| `ethan session list` | 5 | unavailable | idem |
| `ethan knowledge list` | 5 | unavailable | idem |
| `ethan memory health` | 5 | unavailable | idem |
| `ethan application list` | 5 | unavailable | idem |
| `ethan mcp list` | 5 | unavailable | idem |
| `ethan document list` | 5 | unavailable | idem |
| `ethan document config` | 5 | unavailable | idem |
| `ethan document status` | 5 | unavailable | idem |

**Note** : ces commandes ont été exécutées avant le démarrage de la stack (API indisponible). Après démarrage, l'API est disponible mais non authentifiée (401). Les commandes protégées renverraient désormais `401` au lieu de `Connection refused`, mais n'ont pas été ré-exécutées en conditions authentifiées (pas de token).

### 4.3 Découverte de la syntaxe

Syntaxe exacte découverte via `ethan <cmd> --help` pour : `provider`, `model`, `agent`, `skill`, `session`, `knowledge`, `memory`, `application`, `mcp`, `document`. Voir les sorties dans la session. Les verbes et routes API correspondantes sont documentés dans le CLI.

## 5. HROT observations

- Aucune validation HROT réelle n'a pu être effectuée : les endpoints protégés renvoient 401 (authentification requise) avant toute évaluation de permission.
- Le CLI ne contourne pas HROT : aucune tentative de bypass, aucune escalation de privilèges.
- `ethan doctor` confirme que l'API est reachable mais unauthenticated, et propose `ethan auth login`.
- Aucune modification de politique de sécurité n'a été effectuée.

## 6. JSON et automation

- `ethan -o json version` : JSON valide sur stdout, aucune contamination, exit 0.
- `ethan -o json status` : JSON valide sur stdout, erreurs structurées dans `core.errors`, exit 0.
- `ethan -o json doctor` : JSON d'erreur sur stdout, exit 1.
- `ethan -o json provider list` (avant démarrage) : JSON d'erreur sur stderr, stdout vide, exit 5.
- Les diagnostics sont sur stderr en mode humain et sur stderr en mode JSON pour les erreurs ; le stdout reste propre pour le JSON de succès.

## 7. Corrections et tests de régression

Aucune correction de code effectuée (mission phases A et B uniquement). Aucun test de régression exécuté dans cette mission (pas de modification de code).

## 8. Classification des capacités

| Capacité | Classification |
|---|---|
| CLI launcher et aide (`--help`, `--version`) | VERIFIED LIVE |
| Résolution API/token/profil | VERIFIED LIVE |
| `ethan status` (runtime + services + Core API) | VERIFIED LIVE |
| `ethan doctor` (prérequis + Core API) | VERIFIED WITH LIMITATIONS (ports occupés warning) |
| `ethan daemon status` | VERIFIED LIVE |
| Sortie JSON non interactive (version, status) | VERIFIED LIVE |
| Codes de sortie (0, 1, 5) | VERIFIED LIVE |
| API Core availability (health, openapi) | VERIFIED LIVE |
| NATS/PostgreSQL/Redis services | VERIFIED LIVE |
| Authentification (login/token) | BLOCKED (pas de token/credentials, opérateur a refusé la création d'admin) |
| Provider subsystem (list, show, etc.) | BLOCKED (auth) |
| Model subsystem | BLOCKED (auth) |
| Agent subsystem | BLOCKED (auth) |
| Skill subsystem | BLOCKED (auth) |
| Session subsystem | BLOCKED (auth) |
| Knowledge subsystem | BLOCKED (auth) |
| Memory/Engineering Memory subsystem | BLOCKED (auth) |
| Application manager | BLOCKED (auth) |
| HROT enforcement réel | BLOCKED (auth) |
| RAG/Document subsystem | BLOCKED (auth) |
| MCP/Tools subsystem | BLOCKED (auth) |
| TUI (`ethan cli` sans argument) | IMPLEMENTED BUT NOT VERIFIED (non lancé en réel) |
| Commandes d'écriture (create/update/delete) | NOT TESTED (pas d'autorisation) |

## 9. Blocages restants

1. **Authentification** : aucun token ni credentials.json. L'opérateur a refusé la création d'un admin local. Les sous-systèmes protégés sont inaccessibles. Pour poursuivre la validation runtime (phases C et suivantes), il faut soit fournir `ETHAN_TOKEN`, soit autoriser `ethan auth create-admin` (ou `login` avec des identifiants existants).
2. **Ports occupés** : le prérequis `doctor` signale les ports 8000, 8080, 4222, 6379, 5432 occupés (par la stack démarrée). Ce warning est attendu lorsque la stack tourne ; il n'est pas bloquant pour la validation.
3. **python-base** : service en état `running` (non healthy) au moment de l'audit ; sans impact observé sur l'API.

---

## 11. Reprise après authentification (phases C à G)

### 11.1 Étape préalable — Authentification

- Vérification de la présence de `ETHAN_TOKEN` : **absent** (longueur non applicable, valeur non affichée).
- Vérification de `~/.config/ethan/credentials.json` : **absent**.
- Vérification des fichiers `.env*` : aucun ne contient `ETHAN_TOKEN`.
- `ethan auth status` : `Not logged in — run: ethan auth login` (exit 1).
- L'utilisateur a précédemment refusé la création d'un administrateur local et n'a pas fourni de token.

**Conclusion de l'étape préalable** : l'authentification est **bloquée**. Aucun principal authentifié n'est disponible dans l'environnement d'exécution. Conformément aux règles impératives, aucune création de compte n'a été effectuée, aucun contournement de HROT n'a été tenté.

### 11.2 Phases C à G

Non exécutées. La reprise des phases C (validation réelle des sous-systèmes), D (opérations d'écriture), E (HROT), F (contrats CLI/API) et G (corrections ciblées) est **bloquée** par l'absence de token authentifié.

Aucune commande métier protégée n'a été exécutée. Aucune opération d'écriture n'a été effectuée. Aucune modification de code n'a été réalisée.

### 11.3 Mise à jour de la classification

| Capacité | Classification (mise à jour) |
|---|---|
| Authentification (login/token) | BLOCKED (aucun token, aucun credentials.json, création d'admin refusée) |
| Provider subsystem | BLOCKED (auth) |
| Model subsystem | BLOCKED (auth) |
| Agent subsystem | BLOCKED (auth) |
| Skill subsystem | BLOCKED (auth) |
| Session subsystem | BLOCKED (auth) |
| Knowledge subsystem | BLOCKED (auth) |
| Memory/Engineering Memory subsystem | BLOCKED (auth) |
| Application manager | BLOCKED (auth) |
| HROT enforcement réel | BLOCKED (auth) |
| RAG/Document subsystem | BLOCKED (auth) |
| MCP/Tools subsystem | BLOCKED (auth) |
| CLI launcher et aide | VERIFIED LIVE |
| Résolution API/token/profil | VERIFIED LIVE |
| `ethan status` | VERIFIED LIVE |
| `ethan doctor` | VERIFIED WITH LIMITATIONS |
| `ethan daemon status` | VERIFIED LIVE |
| Sortie JSON non interactive | VERIFIED LIVE |
| Codes de sortie | VERIFIED LIVE |
| API Core availability | VERIFIED LIVE |
| NATS/PostgreSQL/Redis | VERIFIED LIVE |
| TUI (`ethan cli`) | IMPLEMENTED BUT NOT VERIFIED |
| Commandes d'écriture | NOT TESTED |

### 11.4 Statut final

**BLOCKED BY CORE/API** (authentification requise pour valider les sous-systèmes protégés et exécuter les phases C à G).

---

## 12. Authentication Reconciliation — Mission 08 vs Mission 09

### 12.1 Constat

Mission 08 (`docs/memory/MISSION_08_HERDR_OPENCODE_INTEGRATION.md`) rapporte :
- `ethan auth status` → `Logged in as admin (admin)`, exit 0.
- Token présent dans `~/.config/ethan/config.json`.
- `ethan provider list`, `ethan model list`, `ethan agent list` fonctionnent (exit 0) contre l'API `http://localhost:8000`.

Mission 09 (présent rapport, phases A et B, rédigé précédemment) rapporte :
- Variable `ETHAN_TOKEN` non définie.
- Fichier `~/.config/ethan/credentials.json` absent.
- `ethan auth status` → `Not logged in` (exit 1).
- Routes protégées renvoyant HTTP 401.
- Sous-systèmes protégés bloqués par l'authentification.

Ces états semblent contradictoires mais s'expliquent par un **état de credentials différent entre les deux moments de saisie** (voir §12.6).

### 12.2 Comparaison d'environnement (Phase 1)

Tous les éléments sont identiques entre les deux sessions :

| Élément | Valeur observée (session courante) |
|---|---|
| Utilisateur système | `fatsio` |
| `HOME` | `/home/fatsio` |
| Répertoire courant | `/home/fatsio/AI/Ethan` |
| Launcher résolu | `/home/fatsio/.local/bin/ethan` (wrapper Python → `interfaces/cli/main.py`, `PYTHONPATH=/home/fatsio/AI/Ethan`) |
| Version CLI | `0.0.1.dev141+unknown.gf8662be91.d20261025` (core 0.2.0) |
| URL API effective | `http://localhost:8000` (résolue via le profil `default` de `config.json`) |
| Profil ETHAN sélectionné | `default` |

Aucun secret ni token n'est affiché.

### 12.3 Présence des credentials (Phase 1)

| Élément | État observé (session courante) |
|---|---|
| `ETHAN_TOKEN` (variable d'environnement) | non définie |
| `~/.config/ethan/credentials.json` | absent |
| `~/.config/ethan/config.json` | présent (968 octets, modifié 11 nov. 13:01) |
| Champ `token` dans `config.json` | présent (longueur 144 caractères, valeur non affichée) |
| `config.json` : `current_profile` | `default` |
| `config.json` : `profiles` | `['default']` |

### 12.4 Audit de résolution des credentials (Phase 2)

Ordre de priorité dans `interfaces/cli/core/client.py`, fonction `get_token()` :

1. `--token` (contexte CLI, `cli_token_explicit`) — non utilisé.
2. Variable d'environnement `ETHAN_TOKEN` — absente.
3. `~/.config/ethan/credentials.json` via `interfaces/cli/core/config.py` `get_token_from_credentials()` — fichier absent.
4. **Fallback legacy** `~/.config/ethan/config.json` via `interfaces/cli/config.py` (`CONFIG_FILE = ~/.config/ethan/config.json`), champ racine `token` — **présent** (144 caractères).
5. Bootstrap local admin (`core.security.jwt_bootstrap.create_local_token`) si l'URL cible est localhost — disponible en ultime recours.

Conclusion : le token est résolu par le **fallback legacy** (`config.json`, champ `token` au niveau racine) et/ou par le bootstrap local. Le code de résolution fonctionne correctement ; aucun défaut de `TOKEN_RESOLUTION` n'est démontré. Le fichier `credentials.json` n'est pas requis lorsque le token est stocké dans `config.json`.

### 12.5 Reproduction contrôlée (Phase 3)

Dans le même environnement et avec le même launcher :

| Commande | Exit | Résultat |
|---|---|---|
| `ethan auth status` | 0 | `Logged in as admin (admin)` |
| `ethan provider list` | 0 | 7 providers (ollama connecté / activé) |
| `ethan model list` | 0 | 14 modèles listés |
| `ethan agent list` | 0 | 1 agent (Atreus, idle) |

Ces appels sont des **requêtes HTTP authentifiées réelles** contre `http://localhost:8000` (le client attache l'en-tête `Authorization: Bearer <token>` résolu par `get_token()`). Ils confirment que l'authentification fonctionne maintenant et que les sous-systèmes protégés sont accessibles.

### 12.6 Diagnostic (Phase 4)

Aucune catégorie de défaut structurel n'est confirmée :

| Catégorie | Verdict | Justification |
|---|---|---|
| `ENVIRONMENT_MISMATCH` | Non | Même utilisateur, même HOME, même cwd, même launcher, même URL API. |
| `HOME_MISMATCH` | Non | `HOME=/home/fatsio` dans les deux cas. |
| `CONFIG_NOT_LOADED` | Non | La config est chargée ; le token est lu depuis `config.json`. |
| `TOKEN_RESOLUTION_DEFECT` | Non | La chaîne `get_token()` fonctionne (fallback legacy + bootstrap local). |
| `API_INSTANCE_MISMATCH` | Non | Même URL `http://localhost:8000`. |
| `TOKEN_INVALID_OR_EXPIRED` | Non | Le token courant permet des appels API authentifiés avec HTTP 200. |
| `HROT_PERMISSION_DENIED` | Non | Ce serait HTTP 403, pas 401 ; et l'authentification aboutit. |

**Cause de l'incohérence** : au moment de la saisie de Mission 09, le token d'authentification n'était pas encore présent dans `~/.config/ethan/config.json` (ce fichier a été modifié à 11 nov. 13:01, postérieurement à la rédaction de Mission 09), et aucun `credentials.json` ni `ETHAN_TOKEN` n'était disponible. Les requêtes protégées renvoyaient donc 401. Entre les deux saisies, un token a été rendu disponible et `config.json` le contient désormais. Il s'agit d'un **état de credentials antérieur différent**, résolu depuis, et non d'un défaut architectural ou de code.

Distinction 401 vs 403 : les erreurs observées lors de Mission 09 étaient des **401** (authentification requise, cookie ou token manquant), jamais des 403 (autorisation refusée). Cela confirme un problème d'authentification (absence de token), pas d'autorisation HROT.

### 12.7 Limitations

- Le moment exact et le mécanisme par lequel le token a été rendu disponible entre les deux saisies n'ont pas pu être déterminés avec certitude (pas d'historique de modification du token conservé, conformément à la règle de ne pas stocker les secrets).
- Aucune création d'administrateur n'a été effectuée ; aucun nouveau token n'a été généré dans le cadre de cette mission de réconciliation.
- Les phases C à G de Mission 09 restent à exécuter désormais que l'authentification est disponible (token présent dans `config.json`, `auth status` OK).

---
## 13. Phase C — Validation réelle des sous-systèmes ETHAN Core

### 13.1 Méthode

Toutes les commandes ci-dessous ont été exécutées avec le launcher existant (`/home/fatsio/.local/bin/ethan`), le token déjà disponible dans `~/.config/ethan/config.json` (résolu par le fallback legacy de `get_token()`), et l'API Core sur `http://localhost:8000`. Aucune opération d'écriture métier n'a été effectuée. Seul le verbe `approval pending` (lecture) a été utilisé dans le périmètre HROT. Aucun nouveau token ni administrateur n'a été créé. Aucun secret n'est affiché.

Mapping des codes de sortie (contrat §5) :
- `0` SUCCESS (HTTP 200, opération aboutie)
- `2` USAGE (mauvaise utilisation CLI, argument manquant — pas d'erreur Core)
- `4` FORBIDDEN (HTTP 403, autorisation HROT refusée)
- `5` UNAVAILABLE (HTTP 502/503/504 ou connexion refusée)
- `6` NOT_FOUND (HTTP 404)
- `7` TIMEOUT (le Core a été contacté mais n'a pas répondu dans le délai par défaut de 5 s)

### 13.2 Détails par sous-système

#### 1. Providers et Models

| Vérification | Commande CLI | Endpoint API | Exit | Code HTTP | Résultat réel | Statut |
|---|---|---|---|---|---|---|
| Liste providers | `ethan provider list` | `GET /providers` | 0 | 200 | 7 providers ; ollama connecté, activé, défaut ; base_url `http://host.docker.internal:11434` | VERIFIED |
| Catalogue types | `ethan provider catalog` | `GET /providers/catalog` | 0 | 200 | Types anthropic, azure, custom, … avec capabilities et auth_methods | VERIFIED |
| Détail provider | `ethan provider show ollama` | `GET /providers/{id}` | 0 | 200 | JSON complet : id, name, enabled, status, capabilities, models, has_api_key=false | VERIFIED |
| Capacités provider | `ethan provider capabilities ollama` | `GET /providers/{id}/capabilities` | 0 | 200 | capabilities llm/vision/embedding ; supports_vision=true | VERIFIED |
| Modèles provider | `ethan provider models ollama --timeout 15` | `GET /providers/{id}/models` | 0 | 200 | 11 modèles listés (timeout à 5s par défaut, OK à 15s) | VERIFIED (perf) |
| Liste modèles | `ethan model list` | `GET /models` | 0 | 200 | 14 modèles (context 4096, local/privé) | VERIFIED |
| Modèles installés | `ethan model installed` | `GET /models/installed` | 0 | 200 | 13 modèles installés | VERIFIED |
| Santé runtimes | `ethan model runtimes` | `GET /models/runtimes/health` | 0 | 200 | ollama enabled=true, reachable=true, latency_ms=13.1 ; autres désactivés | VERIFIED |

**Anomalie** : `provider models ollama` et `document list` dépassent le délai par défaut de 5 s (exit 7 TIMEOUT) mais aboutissent avec `--timeout 15`. Fonctionnel, mais lent sur ces endpoints.

**Vérification métier** : ollama est le seul provider connecté et défaut ; les runtimes distants (openai, vllm, azure, openrouter, anthropic, custom) sont désactivés/non joignables — cohérent avec un environnement local sans clés API configurées.

#### 2. Agents

| Vérification | Commande CLI | Endpoint API | Exit | Code HTTP | Résultat réel | Statut |
|---|---|---|---|---|---|---|
| Liste agents | `ethan agent list` | `GET /v1/agents` | 0 | 200 | 1 agent : Atreus, idle, capacités vides | VERIFIED |
| Détail agent | `ethan agent info 32673ae5-…` | `GET /v1/agents/{id}` | 0 | 200 | JSON complet : id, name, status=idle, agent_type=user, model=llama3.2:latest, provider=ollama, skill_ids, knowledge_collection_ids, tool_ids | VERIFIED |

**Vérification métier** : l'agent Atreus pointe sur ollama/llama3.2:latest, cohérent avec le provider défaut. Fonctionnel.

#### 3. Applications

| Vérification | Commande CLI | Endpoint API | Exit | Code HTTP | Résultat réel | Statut |
|---|---|---|---|---|---|---|
| Liste applications | `ethan application list` | `GET /applications` | 0 | 200 | (réponse reçue, exit 0) | VERIFIED |
| Catalogue intégration | `ethan application catalog` | `GET /application-integration-catalog` | 6 | 404 | `API 404: Not Found` — endpoint non disponible ou vide | PARTIALLY (catalogue) |
| Manifeste | `ethan application manifests` | `GET /application-manifests` | 0 | 200 | 1 manifeste : ComfyUI 0.37.0, capabilities runtime-observation, dépendances docker/python, interfaces http :8188 | VERIFIED |
| Capacités | `ethan application capabilities` | `GET /application-capabilities` | 0 | 200 | `[]` (vide, endpoint répond) | VERIFIED |
| Enregistrées | `ethan application registered --timeout 15` | `GET /applications/registered` | 0 | 200 | `no registered application` | VERIFIED |

**Anomalie** : `application catalog` retourne HTTP 404 (exit 6 NOT_FOUND). Le catalogue d'intégration n'est pas accessible, alors que les endpoints manifests/capabilities/registered répondent. Le sous-système Applications est partiellement opérationnel.

**Vérification métier** : le manifeste ComfyUI est réel et cohérent (identité, capacités, dépendances, compatibilité `ethan 2026.11`).

#### 4. Sessions

| Vérification | Commande CLI | Endpoint API | Exit | Code HTTP | Résultat réel | Statut |
|---|---|---|---|---|---|---|
| Liste sessions | `ethan session list` | `GET /chats` | 0 | 200 | ~26 sessions listées (IDs, titres, dates de mise à jour) | VERIFIED |

**Vérification métier** : les sessions existent et sont listées avec métadonnées. Fonctionnel en lecture.

#### 5. Knowledge et RAG (documents)

| Vérification | Commande CLI | Endpoint API | Exit | Code HTTP | Résultat réel | Statut |
|---|---|---|---|---|---|---|
| Liste knowledge | `ethan knowledge list` | `GET /v1/knowledge` | 0 | 200 | ~42 documents listés (IDs, labels, type=document) | VERIFIED |
| Collections | `ethan knowledge collections` | `GET /v1/knowledge/collections` | 0 | 200 | 2 collections : DevSecOps, ctf | VERIFIED |
| Recherche | `ethan knowledge search Terraform` | `GET /v1/knowledge/search` | 0 | 200 | Résultats pertinents (contenu, source, métadonnées) | VERIFIED |
| Recherche (usage) | `ethan knowledge search` | — | 2 | — | `missing <query>` (usage CLI, pas d'erreur Core) | VERIFIED (usage) |
| Liste documents RAG | `ethan document list --timeout 15` | `GET /v1/rag/documents` | 0 | 200 | ~16 documents (titres, chunks, sources dont GitHub) | VERIFIED (perf) |
| Statut RAG | `ethan document status` | `GET /v1/rag/status` | 0 | 200 | 31 documents, 6493 chunks, embedding_mode=llm, indexed_embeddings=true, embedding_model=bge-m3:latest, vector_backend=qdrant | VERIFIED |
| Config RAG | `ethan document config` | `GET /v1/rag/config` | 0 | 200 | chunk_size=1000, top_k=10, max_context_chars=8000, vector_backends=[memory, chromadb, qdrant] | VERIFIED |

**Anomalie** : `document list` dépasse 5 s par défaut (exit 7 TIMEOUT), aboutit à 15 s.

**Vérification métier** : la recherche knowledge retourne du contenu réel avec source et hash. L'index RAG est construit (6493 chunks, embeddings indexés, qdrant). Fonctionnel en lecture.

#### 6. Memory (Engineering Memory / Vault)

| Vérification | Commande CLI | Endpoint API | Exit | Code HTTP | Résultat réel | Statut |
|---|---|---|---|---|---|---|
| Santé | `ethan memory health` | `GET /v1/memory/health` | 0 | 200 | root=/home/fatsio/AI/Ethan/daena, 759 fichiers md, 28 valides, liste des invalides (pas de frontmatter YAML) | VERIFIED |
| Événements | `ethan memory events` | `GET /v1/memory/events` | 0 | 200 | `no memory event` | VERIFIED |
| Registres | `ethan memory records` | `GET /v1/memory/records` | 0 | 200 | Plusieurs événements (EVT-…, engineering_event, SKL/OBSERVED) | VERIFIED |
| Vault tree | `ethan memory vault-tree` | `GET /v1/memory/vault/tree` | 0 | 200 | Arborescence du vault daena (fichiers/répertoires avec métadonnées) | VERIFIED |

**Vérification métier** : le vault est accessible en lecture, avec santé détaillée (fichiers invalides identifiés). Fonctionnel en lecture.

#### 7. MCP

| Vérification | Commande CLI | Endpoint API | Exit | Code HTTP | Résultat réel | Statut |
|---|---|---|---|---|---|---|
| Liste serveurs | `ethan mcp list --timeout 15` | `GET /v1/tools/servers` | 0 | 200 | 1 serveur : REA, transport —, enabled=yes, status=error | VERIFIED (anomalie) |

**Anomalie** : le serveur MCP REA est marqué `enabled=yes` mais `status=error`. L'endpoint répond mais le serveur MCP n'est pas en bon état. `mcp list` dépasse aussi 5 s par défaut.

**Vérification métier** : l'infrastructure MCP est présente et interrogeable, mais le serveur enregistré n'est pas opérationnel (statut error).

#### 8. HROT / Approvals

| Vérification | Commande CLI | Endpoint API | Exit | Code HTTP | Résultat réel | Statut |
|---|---|---|---|---|---|---|
| Approbations en attente | `ethan approval pending` | `GET /internal/approval/pending` | 0 | 200 | `no pending approval` | VERIFIED |

**Vérification métier** : aucune approbation HROT en attente. L'endpoint d'autorisation répond. Aucun contournement n'a été tenté.

### 13.3 Bilan de la Phase C

| Sous-système | Statut | Preuve |
|---|---|---|
| Providers | VERIFIED | provider list/catalog/show/capabilities/models, HTTP 200, exit 0 |
| Models | VERIFIED | model list/installed/runtimes, HTTP 200, exit 0 |
| Agents | VERIFIED | agent list/info, HTTP 200, exit 0 |
| Applications | PARTIALLY VERIFIED | manifests/capabilities/registered OK ; catalogue HTTP 404 (exit 6) |
| Sessions | VERIFIED | session list, HTTP 200, exit 0 |
| Knowledge | VERIFIED | knowledge list/collections/search, HTTP 200, exit 0 |
| RAG / Documents | VERIFIED | document status/config, HTTP 200 ; document list lent (>5s) |
| Memory | VERIFIED | memory health/events/records/vault-tree, HTTP 200, exit 0 |
| MCP | VERIFIED (anomalie) | mcp list OK, serveur REA en statut error, lent (>5s) |
| HROT / Approvals | VERIFIED | approval pending, HTTP 200, exit 0 |

**Aucun HTTP 401 ou 403 n'a été observé** (authentification OK via le token résolu depuis `config.json`). Aucun contournement de HROT n'a été tenté. Toutes les commandes ont été lecture seule.

**Anomalies constatées (à ne pas corriger dans cette phase) :**
1. `provider models ollama` et `document list` dépassent le délai par défaut de 5 s (exit 7 TIMEOUT) ; aboutissent avec `--timeout 15`.
2. `application catalog` retourne HTTP 404 (exit 6 NOT_FOUND) : le catalogue d'intégration n'est pas accessible.
3. `mcp list` dépasse 5 s par défaut ; le serveur MCP REA est en statut `error`.
4. Plusieurs fichiers du vault `daena/` sont signalés invalides par `memory health` (absence de frontmatter YAML) — état documentaire, pas d'erreur API.

### 13.4 Conclusion de la Phase C

La Phase C est terminée. Chaque sous-système du périmètre a un statut explicite. Aucun défaut de code n'a été identifié qui empêche l'utilisation de ETHAN CLI comme interface de pilotage pour un agent externe (OpenCode) en lecture authentifiée.

Les phases D (opérations d'écriture), E (HROT écriture), F (contrats CLI/API) et G (corrections ciblées) ne sont pas commencées, conformément au critère de sortie.

En attente de validation avant toute opération d'écriture ou correction.

--- 
## 14. Phase F — Audit des contrats ETHAN CLI ↔ API ↔ CORE

### 14.1 Méthode

Audit exclusivement en lecture seule. Aucun changement de code, aucune modification de configuration, aucune écriture métier, aucun nouveau token, aucun contournement HROT, aucun redémarrage de service. Pour chaque sous-système : commande CLI → route API → service Core → vérification du comportement réel.

Le fichier `docs/specs/CLI_CONTRACT.md` référencé dans les commentaires du CLI **n'existe pas** dans le dépôt. Les commentaires y font référence (ex. `provider.py` §8.10, `document.py` §8.7, `mcp.py`) mais le contrat n'est pas matérialisé sur disque.

### 14.2 Matrice de correspondance CLI / API / Core

| Sous-système | Commande CLI | Route API | Service / composant Core | Statut |
|---|---|---|---|---|
| Providers | `provider list` | `GET /providers` | `routers/providers.py` `list_providers()` → `ProviderManager` | VERIFIED |
| Providers | `provider catalog` | `GET /providers/catalog` | `routers/providers.py` `get_provider_catalog()` | VERIFIED |
| Providers | `provider show <id>` | `GET /providers/{id}` | `routers/providers.py` `get_provider()` | VERIFIED |
| Providers | `provider capabilities <id>` | `GET /providers/{id}/capabilities` | `routers/providers.py` `get_provider_capabilities()` | VERIFIED |
| Providers | `provider models <id>` | `GET /providers/{id}/models` | `routers/providers.py` `list_provider_models()` → `ProviderManager.list_models()` → `OllamaProvider.list_models()` | VERIFIED (perf >5s) |
| Models | `model list` | `GET /models` | `routers/models.py` | VERIFIED |
| Models | `model installed` | `GET /models/installed` | `routers/models.py` | VERIFIED |
| Models | `model runtimes` | `GET /models/runtimes/health` | `routers/models.py` | VERIFIED |
| Agents | `agent list` | `GET /v1/agents` | `routers/v1.py` `list_agents()` → `AgentManager` | VERIFIED |
| Agents | `agent info <id>` | `GET /v1/agents/{id}` | `routers/v1.py` | VERIFIED |
| Applications | `application list` | `GET /v1/applications` | `routers/applications.py` `list_applications()` | VERIFIED |
| Applications | `application catalog` | `GET /v1/application-integration-catalog` (CLI) | `routers/application_integration_catalog.py` expose `GET /v1/application-integration/catalog` (slash) | **INCONSISTENT** (404) |
| Applications | `application manifests` | `GET /v1/application-manifests` | `routers/application_manifests.py` | VERIFIED |
| Applications | `application capabilities` | `GET /v1/application-capabilities` | `routers/applications.py` `list_application_capabilities()` | VERIFIED |
| Applications | `application registered` | `GET /v1/applications/registered` | `routers/applications.py` `list_registered_applications()` | VERIFIED |
| Sessions | `session list` | `GET /v1/chats` | `routers/v1.py` | VERIFIED |
| Knowledge | `knowledge list` | `GET /v1/knowledge` | `routers/knowledge.py` | VERIFIED |
| Knowledge | `knowledge collections` | `GET /v1/knowledge/collections` | `routers/knowledge.py` | VERIFIED |
| Knowledge | `knowledge search <q>` | `GET /v1/knowledge/search` | `routers/knowledge.py` | VERIFIED |
| RAG/Documents | `document list` | `GET /v1/rag/documents` | `routers/v1.py` `list_rag_documents()` → `RAGPipeline.list_documents()` → `_ensure_loaded()` + `_load_vector_store(qdrant)` | VERIFIED (perf >5s) |
| RAG/Documents | `document status` | `GET /v1/rag/status` | `routers/v1.py` | VERIFIED |
| RAG/Documents | `document config` | `GET /v1/rag/config` | `routers/v1.py` `get_rag_config()` | VERIFIED |
| Memory | `memory health` | `GET /v1/memory/health` | `routers/engineering_memory.py` | VERIFIED |
| Memory | `memory events` | `GET /v1/memory/events` | `routers/engineering_memory.py` | VERIFIED |
| Memory | `memory records` | `GET /v1/memory/records` | `routers/engineering_memory.py` | VERIFIED |
| Memory | `memory vault-tree` | `GET /v1/memory/vault/tree` | `routers/engineering_memory.py` | VERIFIED |
| MCP | `mcp list` | `GET /v1/tools/servers` | `routers/capabilities.py` `list_tool_servers()` → `ToolServerManager.list()` | VERIFIED (anomalie REA error) |
| HROT/Approvals | `approval pending` | `GET /internal/approval/pending` | `routers/internal.py` | VERIFIED |

### 14.3 Contrats vérifiés

| Contrat | Vérification | Résultat |
|---|---|---|
| Exit codes (contrat §5) | 0 succès, 2 usage, 4 forbidden, 5 unavailable, 6 not_found, 7 timeout | VERIFIED (codes réels observés) |
| HTTP→exit mapping | 401→AUTH(3), 403→FORBIDDEN(4), 404→NOT_FOUND(6), 502/503/504→UNAVAILABLE(5) | VERIFIED dans `exit_codes.py` |
| Sortie JSON (`-o json`) | Un seul document JSON sur stdout, erreurs sur stderr | VERIFIED |
| Masquage des secrets | `provider` scrubbe les champs `api_key`/`secret`/`token` ; `has_api_key` passe | VERIFIED dans `provider.py` `_scrub()` |
| HROT lecture | Routes protégées par `require_permission(Permission.READ)` | VERIFIED (aucun 401/403 observé) |
| Pas de secret en retour | `_public_server()` masque auth_config/headers pour MCP | VERIFIED dans `servers.py` |
| RAG résumés sans chunks | `list_rag_documents()` utilise `to_summary_dict()` | VERIFIED dans `v1.py` |

### 14.4 Écarts constatés

| # | Écarts | Localisation | Statut | Preuve |
|---|---|---|---|---|
| 1 | **Applications catalog : écart de chemin CLI vs API** | CLI `application.py` L124 appelle `/v1/application-integration-catalog` (tiret) ; API `application_integration_catalog.py` L34 expose `/v1/application-integration/catalog` (slash) | **INCONSISTENT** | `ethan application catalog` → `API 404: Not Found` (exit 6) |
| 2 | **CLI_CONTRACT.md absent** | Commentaires du CLI y font référence (`provider.py`, `document.py`, `mcp.py`) mais le fichier n'existe pas à `docs/specs/CLI_CONTRACT.md` | **MISSING** | `ls docs/specs/CLI_CONTRACT.md` → absent |
| 3 | **MCP REA statut `error` persistant** | `core/tools/servers.py` `list()` L114 retourne le statut stocké (pas de healthcheck en temps réel) | VERIFIED (état réel) | `ethan mcp list` → REA `enabled=yes`, `status=error` |
| 4 | **Performances `provider models` >5s** | `core/llm/providers/ollama.py` `initialize()` client timeout 300s ; `list_models()` interroge `host.docker.internal:11434` | VERIFIED (dépendance externe) | `provider models` exit 7 à 5s, OK à 15s ; runtime health ollama 13,1ms |
| 5 | **Performances `document list` >5s** | `core/rag/pipeline.py` `_ensure_loaded()` L193 + `_load_vector_store()` L203 (qdrant, 6493 chunks) | VERIFIED (dépendance externe) | `document list` exit 7 à 5s, OK à 15s |

### 14.5 Diagnostic des trois anomalies

#### Anomalie A — Applications catalog HTTP 404

**Cause racine** : écart de routage entre le CLI et l'API.
- CLI (`interfaces/cli/commands/application.py` L124) : `api_get("/v1/application-integration-catalog")`
- API (`interfaces/api/routers/application_integration_catalog.py` L34) : `@router.get("/application-integration/catalog")` avec préfixe `/v1` → URL réelle `/v1/application-integration/catalog`

Le tiret (`-`) côté CLI ne correspond pas au slash (`/`) côté API. La route n'est donc jamais匹配ée et FastAPI retourne 404. Ce n'est pas un problème d'authentification (la route dépend de `Permission.READ` qui est satisfaite) ni d'absence de service (le service `IntegrationCatalogService` est instancié).

**Correction recommandée (à ne pas appliquer dans cette phase)** : aligner le chemin CLI sur l'API (`/v1/application-integration/catalog`) ou ajouter une route alias `/application-integration-catalog` redirigeant vers `/application-integration/catalog`.

#### Anomalie B — Serveur MCP REA statut `error`

**Cause racine** : le statut est persistant, pas recalculé à la volée.
- `ToolServerManager.list()` (`core/tools/servers.py` L114) fait un simple `self._store.list(self._DOMAIN)` et retourne le statut stocké dans le CoreRecordStore.
- Il n'y a **aucun healthcheck** dans `list()`. Le statut `error` provient d'un appel antérieur à `set_status("error")` (probablement lors d'un `sync_tools` ayant échoué, voir `servers.py` L192-241 où `set_status("connected")` n'est appelé qu'en cas de succès complet).
- Le serveur REA est bien enregistré (`enabled=yes`) mais sa dernière tentative de connexion/synchronisation a échoué, laissant le statut figé à `error`.

**Correction recommandée (à ne pas appliquer dans cette phase)** : ajouter un healthcheck léger optionnel dans `list()` ou documenter explicitement que le statut reflète la dernière tentative connue et non l'état temps réel.

#### Anomalie C — Performances (`provider models` et `document list` >5s)

**`provider models`** :
- `ProviderManager.list_models()` (`core/llm/provider_manager.py` L567) appelle `provider.list_models()`.
- `OllamaProvider.list_models()` (`core/llm/providers/ollama.py` L157) utilise `self._client` initialisé avec `timeout=300.0` (`initialize()` L~60) et interroge `GET {base_url}/api/tags` sur `host.docker.internal:11434`.
- La dépendance externe (Ollama via Docker host) met plus de 5s à répondre. Le runtime health confirme ollama `reachable=true` (13,1ms) une fois connecté, mais la première requête `list_models` dépasse le délai CLI par défaut (5s). Aboutit à 15s.

**`document list`** :
- `GET /v1/rag/documents` (`routers/v1.py` L1354) appelle `RAGPipeline.list_documents()` → `_ensure_loaded()` (L120) qui :
  1. Liste les documents dans le store
  2. Charge le vector store via `_load_vector_store()` (L201) — avec `vector_backend=qdrant`, crée l'index et réindexe les documents existants
- Le chargement de l'index qdrant (6493 chunks indexés) prend plus de 5s. Aboutit à 15s.

**Origine** : dans les deux cas, la lenteur vient d'une **dépendance externe** (Ollama / qdrant) et d'opérations de chargement côté Core, pas d'un défaut du CLI ni de l'API. Les commandes aboutissent correctement avec un délai plus long.

### 14.6 Permissions HROT

Toutes les routes du périmètre Phase F sont protégées par `Permission.READ` (ou `Permission.ADMIN`/`PLUGINS`/`EXECUTE` pour les mutations, non testées ici). Aucun HTTP 401 ni 403 n'a été observé, confirmant que l'authentification et l'autorisation lecture sont opérationnelles. Aucun contournement de HROT n'a été tenté.

### 14.7 Bilan Phase F

| Sous-système | Contrats CLI↔API↔Core | Statut global |
|---|---|---|
| Providers | VERIFIED (toutes les routes mappées) | VERIFIED |
| Models | VERIFIED | VERIFIED |
| Agents | VERIFIED | VERIFIED |
| Applications | Écart de routage `application catalog` (404) | **INCONSISTENT** |
| Sessions | VERIFIED | VERIFIED |
| Knowledge | VERIFIED | VERIFIED |
| RAG / Documents | VERIFIED (perf >5s sur `list`) | VERIFIED |
| Memory | VERIFIED | VERIFIED |
| MCP | VERIFIED (serveur REA en statut `error`, état réel) | VERIFIED (anomalie) |
| HROT / Approvals | VERIFIED | VERIFIED |
| Documentation contrat (`CLI_CONTRACT.md`) | Absent du dépôt | **MISSING** |

**Aucun défaut de code bloquant** n'a été identifié qui empêcherait l'utilisation de ETHAN CLI comme interface de pilotage pour un agent externe (OpenCode) en lecture authentifiée.

Les phases D (opérations d'écriture), E (HROT écriture) et G (corrections ciblées) ne sont pas commencées, conformément au critère de sortie.

En attente de validation avant toute opération d'écriture ou correction.

--- 

*Fin du rapport — phases A, B, authentification, Phase C et Phase F terminées ; phases D, E, G en attente.*