# Cartographie interfaciale — qui expose quelle capacité ETHAN

> **Date** : 2026-09-30 · **Rôle** : Lead Product Architect
> **Périmètre** : `interfaces/*` (api, webui, cli, shell, channels, desktop) —
> **aucune modification Core**
> **Complémentaire de** : `docs/design/2026-09-30-ux-refonte-cartographie.md`
> (cartographie WebUI route → composant → API → Core).
>
> **Méthode** : inventaire statique (imports, endpoints, ports) **+ preuves
> vivantes** (requêtes réelles contre l'API de dev et écoute des ports). Chaque
> ligne « État » ci-dessous est un fait mesuré le 30/09/2026, pas une
> hypothèse.
>
> **Principe (AGENTS.md)** : les interfaces révèlent ETHAN, elles ne le
> définissent pas. Toute interface doit atteindre Core par le transport
> existant — jamais en réimplémentant une capacité.

---

## 1. Inventaire des interfaces

| Interface | Techno | Transport vers ETHAN | Cible | État mesuré |
|---|---|---|---|---|
| `interfaces/api` | FastAPI | **est** la passerelle HTTP (routeurs + `core.*`) | — | ✅ `:8000` à l'écoute, `/health` OK (`nats_connected: true`) |
| `interfaces/webui` | Next.js 15 (port **3001**) | proxy Next `/api/*` → API | `:8000` | ✅ E2E 19/1 en vert (webServer auto `:3001`) |
| `interfaces/cli` | Python (`ethan` CLI, commands/) | HTTP + socket **via `client.py`** | `http://localhost:8002` | ⚠️ **`:8002` fermé** (`curl` → code 000, aucun processus) |
| `interfaces/shell` | bash/zsh/fish (`ethan-shell`) | `curl` brut (`ETHAN_API`, défaut `:8000`) | `:8000/v1/message`, `:8000/v1/state` | ✅ **réparé et vérifié vivant** (30/09/2026) : `POST /v1/message` → `success:true` + `event_id`, `GET /v1/state` → état réel. Auth lue dans `ETHAN_TOKEN` |
| `interfaces/channels` | Python (Telegram, Discord, WhatsApp) | handler **injecté en processus** (`MessagingGateway`) | Core | ⚠️ **jamais instancié** hors de son propre paquet (grep `MessagingGateway(` →0 usage) |
| `interfaces/desktop` | Tauri + Vite/React (`frontend/src`) | HTTP direct | `http://localhost:8000` (+ `:1234/v1` Ollama) | ⚠️ 7 pages ; structure `src-tauri` dupliquée (`desktop/` et `frontend/`) à clarifier |

Ports observés (`ss -ltn` + `port_registry.json`) : **8000 API** ✅ · **3001
WebUI** (démarré par Playwright) · **3002 Grafana** (absent à l'instant du
mesurage) · **8002 CLI** ❌ rien à l'écoute.

---

## 2. Matrice capacités (Core) × interfaces

Légende : ✅ exposé et câblé · ⚠️ exposé mais écart constaté (§4) · — non exposé.

| Capacité Core | Routeur API | WebUI (route) | CLI (commande) | Shell | Desktop | Channels |
|---|---|---|---|---|---|---|
| Chat / conversations | `openwebui.py`, `v1.py` → `core/chat` | `/` | `chat`, `run`, `think` | ⚠️ `/v1/message` non atteint | `ChatPage` | — |
| Projects | `projects.py` → `core/projects` | `/projects`, `/projects/[id]` | — | — | — | — |
| Providers / Models | `providers.py`, `models.py` → `core/llm` | `/providers`, `/models` | `router` | — | `SettingsPage`, `DataSourcesPage` | — |
| Knowledge / RAG | `knowledge_imports.py`, `v1.py` → `core/knowledge`, `core/rag` | `/knowledge`, `/library` | — | — | `DataSourcesPage` | — |
| Skills | `v1.py` → `core/skills` | `/skills`, `/skills/lab` | `plugin` (partiel) | — | — | — |
| Tools / MCP | `v1.py`, `capabilities.py` → `core/tools` | `/tools`, `/mcp` | — | — | — | — |
| Memory | `v1.py` → `core/memory` | `/workspace` | `memory` | — | — | — |
| Agents | `v1.py` → `core/agents` | `/agents` | — | — | `AgentsPage` | — |
| Missions / Automations | `v1.py`, `capabilities.py` → `core/missions`, `core/goals` | `/missions`, `/automations` | — | — | `DashboardPage` | — |
| Auth / Security | `security.py`, `api_keys.py`, `internal.py` → `core/auth`, `core/audit` | `/security` | `auth` | ❌ sans JWT | `LogsPage` (partiel) | — |
| Plugins | `v1.py` → `core/plugins` | `/plugins` | `plugin` | — | — | — |
| Folders / Domains / Dedup | `folders.py`, `core_domains.py`, `dedup.py` | `/folders`, `/domains`, `/dedup` | `domains` | — | — | — |
| Reminders / Search | `reminders.py`, `search.py` | sections Settings | — | — | — | — |
| Integrations / Connections | `integrations.py`, `connections.py` | `/connections` + section Settings | — | — | — | — |
| Diagnostics / Logs | `diagnostics.py`, `internal.py` | `/diagnostics`, `/logs` | `status`, `doctor`, `logs` | ⚠️ dégrade en JSON `offline` | `LogsPage` | — |
| Runtime (up/down) | — (`./ethan`, systemd, docker) | — | `up`, `down`, `restart`, `service`, `daemon` | — | — | — |
| Messagerie (Telegram/Discord/WhatsApp) | — | `/channels` (canaux Core) | — | — | — | ⚠️ gateway non câblée |

---

## 3. Preuves vivantes (rejouables)

```bash
# 1) Le Shell appelle-t-il des routes réelles ?
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:8000/message   # → 404
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:8000/v1/message # → 422 (route OK, payload KO)
curl -s -o /dev/null -w '%{http_code}\n'        http://localhost:8000/state       # → 404
curl -s -o /dev/null -w '%{http_code}\n'        http://localhost:8000/v1/state    # → 200 (avec JWT)

# 2) La cible du CLI répond-elle ?
ss -ltn | grep 8002            # → rien (client.py : HTTP_URL = localhost:8002)

# 3) La gateway Channels est-elle montée ?
grep -rn 'MessagingGateway(' core interfaces | grep -v channels/gateway  # → aucun usage

# 4) La WebUI atteint-elle bien Core ?
npx playwright test            # → 19 passed / 1 skipped (port 3001 → 8000)
```

Sans JWT, **toutes** les routes `/v1/*` renvoient 401 (middleware d'auth ;
`PUBLIC_PATHS` dans `interfaces/api/auth.py` ne couvre ni `/v1/message` ni
`/v1/state`).

---

## 4. Écarts constatés → décisions

| # | Écart (preuve) | Cause racine | Décision | Statut |
|---|---|---|---|---|
| **I1** | Shell : `POST /message` → 404, `GET /state` → 404 ; avec le bon préfixe → 422 (`content` ≠ `input`) ; sans JWT → 401 | 3 causes cumulées : préfixe `/v1` absent, champ `payload` de 2019 (`content` vs `input`), auth jamais fournie | Corrigé : préfixe `/v1` + champ `input` + token lu dans `ETHAN_TOKEN` (jamais en dur). **2 bugs collatéraux découverts en proving vivant** — voir §4.1 | ✅ **clos** (13 tests contrat + preuve HTTP réelle) |
| **I2** | CLI : `client.py`/`config.py` → `http://localhost:8002`, port fermé | Le runtime HTTP attendu par la CLI n'est pas servi par la stack actuelle (8000 = API) | Arbitrer : pointer la CLI vers l'API `:8000` (même contrat) **ou** remettre en service un daemon dédié. Décision d'architecture, pas un fix silencieux | 📋 ouvert |
| **I3** | `MessagingGateway` jamais instancié hors de `interfaces/channels/` | Canal non câblé dans le bootstrap Core | Confirmer l'intégration (bootstrap → gateway) **ou** documenter le retrait — une interface non montée n'est pas une capacité | 📋 ouvert |
| **I4** | Collision de nom : `interfaces/cli/core/*` (kit UI : colors, ux, intent…) **et** `core/` (ETHAN Core) portent tous deux le nom `core` ; la CLI importe `core.llm.*` (ETHAN) **et** `core.colors` (local) | Deux packages homonymes selon l'ordre `sys.path` | Renommer le kit local (`interfaces/cli/ui_core/`) lors d'un lot CLI — aujourd'hui la résolution fonctionne mais est fragile | 📋 reporté |
| **I5** | Desktop : appels `http://localhost:8000` en direct (hors proxy WebUI), + `:1234/v1` (Ollama) ; deux dossiers `src-tauri/` | Frontend hérité (open-jarvis) partiellement branché | Valider l'auth et la source unique de config avant toute promesse de parité Desktop | 📋 ouvert |
| **I6** | WebUI ↔ API | — | ✅ conforme : proxy Next → `:8000`, E2E vert | ✅ |
| **I7** | `TestClient(app)` (fixture `contract_client`) échoue : `nats: 'Authorization Violation'` → 10 tentatives → `TimeoutError` (6 erreurs dans `test_api_contract_p0.py` / `test_api_contract_domains.py`). Le serveur **en cours** sur `:8000`, lui, a `nats_connected: true` | Les identifiants NATS du `.env` local ne correspondent pas à ceux du NATS servi par la stack (le conteneur a ses propres credentials) | Aligner `NATS_USER`/`NATS_PASSWORD` entre `.env` et la stack, ou rendre la fixture indépendante de NATS. **Pré-existant** : reproduit à l'identique en retirant `tests/interfaces/` du dépôt de travail | 📋 ouvert (hors périmètre Shell) |

**Règle appliquée** : aucun correctif « à moitié ». Un écart d'interface se
corrige **avec sa cause racine** (sinon il masque la vraie panne), et toute
décision d'auth/token passe par la couche de secrets du repo (env non commité,
Vault, Docker secrets).

### 4.1 Retour d'expérience I1 : ce que l'analyse statique ne voyait pas

La correction du Shell a d'abord passé une **revue de code** puis un **test
statique** (13 assertions). Les deux ont laissé passer deux pannes réelles,
trouvées uniquement en appelant l'API en vie (`:8000` écoutait réellement) :

| Panne | Symptôme observé | Cause | Correction |
|---|---|---|---|
| **Faux état « offline »** | `_ethan_status` sans token affichait `{"detail":"Authentification requise…"}` **comme si c'était l'état de ETHAN**, et sortait `0` | `curl … \|\| echo fallback` juge sur **corps non vide** ; or une réponse 401 a un corps JSON | Le code HTTP est capturé (`-o <fichier> -w '%{http_code}'`) ; seul un `2xx` est pris pour l'état. 401 → message explicite + repli honnête |
| **Diagnostics incohérents** | API éteinte → `ERR: HTTP 000 — ` (vide, sans hostname) | `000` est **l'absence de réponse** de curl, pas un code HTTP ; il tombait dans `case *)` | Cas `000` explicite : nomme l'URL morte et suggère `ethan up` |

**Leçon méthodologique** : une interface réseau ne se vérifie pas en lisant le
code. Les deux fautes ci-dessus donnaient une sortie *crédible* — c'est
précisément le mode de panne que la phase B cherchait à éliminer. Les tests
`test_le_code_000_n_est_pas_pris_pour_un_code_http` et
`test_le_status_ne_juge_plus_sur_le_seul_corps_non_vide` verrouillent
désormais ce comportement.

**Vérification vivante (30/09/2026, API sur `:8000`)** :

```text
POST /v1/message (token admin)  → {"success":true,"event_id":"8be5cf59-…",
                                    "message":"Event emitted into cognitive system"}  exit 0
GET  /v1/state  (token admin)   → {"mode":"idle","modules_active":["cli","api"],…}    exit 0
POST /v1/message (sans token)   → ERR: authentification requise (HTTP 401)            exit 1
POST /v1/message (port 9999)    → ERR: API injoignable (http://localhost:9999)         exit 1
```

Le JWT de test a été généré en mémoire depuis `JWT_SECRET` du `.env` local,
écrit en `/tmp` mode 600, puis **supprimé** — aucune credential n'entre dans
le dépôt ni dans les logs (règle « secret »).

---

## 5. Contrat minimal pour une NOUVELLE interface

Avant d'ajouter une interface, répondre oui à tout :

1. **Transport** : j'atteins Core par l'API (`:8000/v1/*`) ou l'Event Bus —
   jamais par une copie de la logique métier.
2. **Routes** : chaque endpoint que j'appelle existe (test de contrat ou
   vérification `curl` avec JWT) — cf. §3.
3. **Auth** : je lis le token en environnement/secret, jamais en dur.
4. **Capacité** : je n'expose que ce que Core expose déjà (pas d'écran fantôme
   — cf. R5 du cartographie WebUI).
5. **Non-régression** : un garde-fou (unit ou contrat) empêche la dérive de
   vocabulaire et les doublons de menu (`nav-dedup.test.ts` en est l'exemple).

---

## 6. Roadmap (ordre recommandé)

| Phase | Contenu | Pourquoi cet ordre | Risque |
|---|---|---|---|
| **A ✅ faite** | Cartographie WebUI + interfaciale, R5 `/gallery` retiré du menu, garde-fous `nav-dedup.test.ts` (destinations, libellés, hash, vocabulaire canonique) | On ne répare pas ce qu'on n'a pas cartographié | nul |
| **B ✅ faite** | **I1 — Shell réparé** : préfixe `/v1`, champ `input`, token lu dans l'env, diagnostics par cause racine, + 13 tests de contrat statiques **et** preuve HTTP vivante (§4.1). fish aligné sur `core.sh` | Interface cassée aujourd'hui, correctif autonome, aucun Core touché | faible |
| **C** | **I2 + I4 — lot CLI** : arbitrage `:8002` vs `:8000`, renommage `interfaces/cli/core` → `ui_core`, rejeu `ethan status/chat` | Décision d'archi à prendre avant tout code | moyen (portée CLI) |
| **D** | **I3 — Channels** : monter `MessagingGateway` dans le bootstrap **ou** retrait documenté | Sans câblage, ce n'est pas une capacité ETHAN | faible |
| **E** | **I5 — Desktop** : auth + config unique, clarification des deux `src-tauri` | Bloquant avant toute promesse de parité | moyen |
| **F** | **Contrats** : tests de contrat API (routes consommées par chaque interface) pour figer §3 | Empêche la dérive des 3 causes de I1 | faible |

---

## 7. Validations de ce lot

```bash
cd interfaces/webui && npm run validate   # tsc + eslint + jest
cd interfaces/webui && npx playwright test # E2E :3001 → :8000
```

Résultats du lot (2026-09-30) : `validate` exit 0 — **51 suites / 301 tests**
(inclut le garde-fou vocabulaire) ; E2E **19 passed / 1 skipped** (skip
environnemental : aucun agent réel dans le Core de dev).

⚠️ Ce fichier et son jumeau WebUI sont sous `docs/` (ignoré par `.gitignore`) :
les inclure avec `git add -f docs/design/2026-09-30-cartographie-interfaciale.md`.


