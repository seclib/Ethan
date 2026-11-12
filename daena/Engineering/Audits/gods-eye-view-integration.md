# Intégration God's Eye View (GEV) dans ETHAN

> **Statut** : Cadrage acté — Phase A close.
> **Décision structurante** : option **B** (dépendance externe pinnée).
> **Propriétaire** : Core (`core/plugins/gods_eye_view.py`).
> **Dernière mise à jour** : 2026-10-22.

---

## 1. Contexte

`examples/gods-eye-view/` (GEV) est un client géospatial 3D : Cesium, 30+ sources de
données publiques, HUD de télémétrie, panneau MCP, serveur MCP.

GEV est **today** un monolithe : il porte à la fois l'interface (rendu, HUD) et de la
logique métier (appels OpenAI directs, gestion de secrets, autorisation).

Or l'`AGENTS.md` d'ETHAN est explicite :

> Une interface peut : afficher, visualiser, configurer, déclencher, superviser.
> Une interface ne doit pas : implémenter la logique métier, stocker l'état métier,
> définir les providers, définir la mémoire, définir le RAG, définir les missions.

GEV, tel quel, **viole** cette règle sur trois points :

| Dans GEV (interface) | Doit appartenir à |
|---|---|
| `server/providers/openai/*` (summary, realtime) | `core/llm/` |
| `HUD_SUMMARY_INSTRUCTIONS`, `HUD_SYSTEM_PROMPT` | `core/` (source unique) |
| `process.env.OPENAI_API_KEY` (résolution directe) | `core/config/secrets.py` |
| Serveur MCP Node (`npm run mcp`) | MCP ETHAN |
| Autorisation par loopback / same-origin | `core/auth` (JWT + RBAC) |

---

## 2. Décision : option B — dépendance externe pinnée

Trois options étaient ouvertes :

| Option | Description | Verdict |
|---|---|---|
| A. Fork interne | GEV devient un sous-dossier suivi par ETHAN (≈1 594 commits à intégrer) | **Rejetée** — divergence rapide, perte de traçabilité upstream |
| **B. Dép. externe pinnée** | GEV reste un dépôt Git imbriqué, référencé sur un commit précis | **Retenue** |
| C. Inspiration seulement | Réimplémentation complète des couches + HUD dans ETHAN | **Rejetée** — coût disproportionné, valeur du code déjà acquise |

### Constat factuel qui fonde la décision

```
$ git ls-files examples/gods-eye-view | wc -l
0                                    # aucun fichier suivi par ETHAN

$ ls -d examples/gods-eye-view/.git
examples/gods-eye-view/.git         # dépôt Git imbriqué
```

GEV est **déjà** un dépôt Git imbriqué, non suivi par le dépôt ETHAN. L'option B est
donc l'**état de fait** : il suffit de le **rendre explicite et pinné**.

### Invariants de l'option B

1. GEV reste un dépôt Git autonome (`github.com/bilawalsidhu/gods-eye-view`).
2. ETHAN référence un **commit précis** — jamais une branche.
3. GEV **ne modifie jamais** `core/`, `runtime/`, `services/`.
4. Toute divergence GEV→ETHAN passe par le **routeur plugin** (`interfaces/api/routers/gods_eye_view_ai.py`).
5. Les secrets de GEV ne sont **jamais** montés dans le contexte ETHAN.

---

## 3. Architecture cible

```
┌────────────────────────────────────────────────────────────────┐
│                        ETHAN CORE                              │
│                                                                │
│  core/llm/            providers OpenAI, router, sélection      │
│  core/config/         secrets.py (Vault→env), prompts          │
│  core/auth/           JWT, RBAC, TOTP, LDAP, SCIM, API keys    │
│  core/security/       egress (SSRF), policy, data_protection   │
│  core/plugins/        gods_eye_view.py (service + prompts)     │
│  core/events/         bus d'événements immuables                │
└───────────────────────────┬────────────────────────────────────┘
                            │  JWT / jeton d'agent provisionné
                            │  (scope plugins:gods-eye-view-ai)
                            ▼
┌────────────────────────────────────────────────────────────────┐
│              GEV — interface pure (exemples/gods-eye-view)     │
│                                                                │
│  Rendu 3D Cesium · couches de données · HUD · panneaux MCP     │
│  Aucune clé serveur · aucun appel provider direct             │
└────────────────────────────────────────────────────────────────┘
```

**Flux cible d'un résumé HUD :**

```
GEV navigateur
  → POST /v1/plugins/gods-eye-view/ai/hud-summary  (Bearer JWT)
  → ETHAN : RBAC + scope + rate limit + événement
  → core/llm : ProviderManager → OpenAI/Ollama/…
  → réponse 5 mots
  → GEV : validation provenance → affichage (ou fallback déterministe)
```

---

## 4. Périmètre d'exclusion

| Capacité | Décision | Raison |
|---|---|---|
| Voix Realtime WebRTC (`src/voice/realtimeBackend.js`) | **Hors périmètre ETHAN** | Connexion navigateur→OpenAI directe, non compatible multi-provider / egress centralisé / Vault-only. ETHAN renvoie `compatible: False` + repli texte. |
| Serveur MCP Node de GEV | **À retirer à terme** | Doublon du MCP ETHAN. Priorité P2. |
| Les 3 clés browser (`GOOGLE_MAPS_API_KEY`, `CESIUM_ION_TOKEN`, `MAPILLARY_CLIENT_TOKEN`) | **Restent côté GEV** | Ce ne sont pas des secrets (usage navigateur assumé, type token public Mapbox). Restriction par HTTP referrer exigée. |

---


## 5. Matrice de migration

Légende : **M** = migrer vers le Core · **A** = adapter · **G** = garder dans GEV · **R** = retirer.

| # | Élément GEV | Maison cible | Action | Phase | Statut |
|---|---|---|---|---|---|
| 1 | `src/hudSummaryResponse.js` → `HUD_SUMMARY_INSTRUCTIONS` | `core/plugins/gods_eye_view_prompts.py` | **M** | B | ✅ fait |
| 2 | `interfaces/api/routers/gods_eye_view_ai.py` → `HUD_SYSTEM_PROMPT` | idem (source unique) | **M** | B | ✅ fait |
| 3 | `server/providers/openai/hud-summary.js` → `fetch('https://api.openai.com/v1/responses')` | `core/llm` via ProviderManager | **M** | C | ⬜ |
| 4 | `server/providers/openai/realtime.js` (forge de jeton) | hors périmètre | **G** | — | ⬜ |
| 5 | `src/voice/realtimeBackend.js` (WebRTC direct) | hors périmètre | **G** | — | ⬜ |
| 6 | `process.env.OPENAI_API_KEY` (serveur GEV) | `core/config/secrets.py` | **M** | C | ⬜ |
| 7 | `src/hud.js` → `_summaryContext()` | `core/context` + Runtime | **A** | C | ⬜ |
| 8 | `server/providers/openai/rate-limit.js` (per-IP, process-local) | quotas ETHAN | **A** | D | ⬜ |
| 9 | Gate loopback/same-origin GEV | défense en profondeur (conservé) | **G** | — | ⬜ |
| 10 | Serveur MCP Node (`npm run mcp`) | MCP ETHAN | **R** | P2 | ⬜ |
| 11 | `src/data/*` (30+ sources) | GEV | **G** | — | ⬜ |
| 12 | Rendu Cesium / HUD / panneaux | GEV | **G** | — | ⬜ |

### Séquence d'exécution

```
Phase A — cadrage (ce document)                      ✅
Phase B — prompts → Core, source unique              ✅
Phase C — GEV devient client d'ETHAN                 ⬜  ← heart
Phase D — quotas, événements, observabilité          ⬜
Phase P2 — retrait du serveur MCP Node de GEV        ⬜
```

**Phase C est le cœur.** Elle se décompose en 3 sous-étapes indépendantes :

| Sous-étape | Contenu | Test associé |
|---|---|---|
| C1 | GEV lit `GEV_ETHAN_API_URL` + `GEV_ETHAN_TOKEN` ; plus d'URL OpenAI codée en dur | grep anti-doublon |
| C2 | Le serveur GEV relaie `/api/openai/hud-summary` vers ETHAN au lieu d'appeler OpenAI | test contrat |
| C3 | GEV n'a plus besoin de `OPENAI_API_KEY` : la clé vit dans ETHAN (Vault/env) | grep + absence de secret |


## 6. Contrat technique

### 6.1 Endpoint ETHAN

```
POST {GEV_ETHAN_API_URL}/v1/plugins/gods-eye-view/ai/hud-summary
Authorization: Bearer <jeton>
Content-Type: application/json

{
  "placeLabels": ["..."],
  "streetLabels": ["..."],
  "nearbyPlaceLabels": ["..."],
  "enabledLayerLabels": ["..."],
  "enabledLayers": [{"id": "...", "name": "...", "feedState": "nominal"}],
  "feedProvenance": {}
}
```

Réponse :

```json
{ "summary": "Cinq mots exactement ici", "error": null, "model": "gpt-4o-mini" }
```

### 6.2 Jeton

Deux modes, déjà supportés par le routeur :

| Mode | Usage | Endpoint ETHAN |
|---|---|---|
| JWT utilisateur | Session WebUI ETHAN | `POST /v1/auth/login` |
| Jeton d'agent | Serveur GEV autonome | `POST /v1/plugins/gods-eye-view/ai/provision` (ADMIN, TTL 3600 s, scope `plugins:gods-eye-view-ai`) |

### 6.3 Variables d'environnement GEV

| Variable | Rôle | Défaut |
|---|---|---|
| `GEV_ETHAN_API_URL` | Base URL de l'API ETHAN | `http://127.0.0.1:8000` |
| `GEV_ETHAN_TOKEN` | Jeton d'agent (scope plugin) | vide → mode keyless |
| `GEV_ETHAN_TIMEOUT_MS` | Timeout d'appel HUD | `30000` |

> Le mode keyless est conservé : sans `GEV_ETHAN_TOKEN`, GEV retombe sur son
> résumé déterministe (jamais d'appel réseau). C'est le comportement
> `keylessHudSummaryResponse()` existant, à conserver tel quel.

---

## 7. Critères d'acceptation

| # | Critère | Vérification |
|---|---|---|
| AC1 | Zéro appel direct à `api.openai.com` depuis GEV, hors voix Realtime | grep dans la CI |
| AC2 | Zéro `process.env.*` de secret dans GEV (hors 3 clés publiques restreintes) | grep dans la CI |
| AC3 | Le prompt HUD n'existe qu'à un seul endroit (`core/plugins/gods_eye_view_prompts.py`) | test unitaire |
| AC4 | Aucune route GEV accessible sans jeton ETHAN valide hors loopback | test contrat |
| AC5 | Chaque appel IA GEV émet un événement ETHAN immuable | test unitaire |
| AC6 | `tests/interfaces/test_gods_eye_view_ai.py` + `tests/core/test_gods_eye_view.py` passent | pytest |
| AC7 | Le mode keyless de GEV reste fonctionnel (aucune régression) | test GEV |

---

## 8. Risques et mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| GEV non suivi par ETHAN → divergence silencieuse | Élevé | Pin sur commit précis + audit de sécurité à chaque bump |
| Double implémentation des prompts | Moyen | Source unique Core (Phase B) + test AC3 |
| Clé OpenAI encore présente dans GEV après migration | Élevé | Phase C3 + AC2 |
| GEV exposé réseau sans auth ETHAN | **Critique** | Gate ETHAN (AC4) avant toute publication hors loopback |
| Quotas GEV process-local insuffisants multi-tenant | Moyen | Phase D : quotas ETHAN |
| WebRTC voice incompatible egress ETHAN | Faible | Hors périmètre assumé (`compatible: False`) |

---

## 9. Historique des décisions

| Date | Décision | Statut |
|---|---|---|
| 2026-10-22 | Option B (dépendance externe pinnée) | Acté |
| 2026-10-22 | Voix Realtime hors périmètre ETHAN | Acté |
| 2026-10-22 | Prompts HUD → `core/plugins/gods_eye_view_prompts.py` | Acté (Phase B) |
