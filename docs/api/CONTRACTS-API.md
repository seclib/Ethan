# Contrats API — ETHAN (WebUI ↔ Core)

> **Statut** : contrat **v1** — **vérifié par tests** (13 tests, 2 fichiers).
> **Parents** : [ADR-3006](/docs/architecture/adr/ADR-3006-api-contracts.md)
> (snapshot + tests de contrat), [`ARCHITECTURE-CIBLE.md`](/docs/architecture/ARCHITECTURE-CIBLE.md) §7 (conventions) et §8 (données).
> **Base de vérité** : code **committé** (`22fad583`) — inventaire mesuré :
> **359 routes**, **258 chemins** OpenAPI.
> **Snapshot versionné** : [`docs/api/openapi.v1.json`](/docs/api/openapi.v1.json) (ADR-3006 §1).
> **Règle** : ce catalogue ne décrit **que le réel** — aucun endpoint fictif.
> Les surfaces déclarées mais **non committées** (WIP local) sont listées §13.

## 1. Conventions transverses

Toutes les interfaces (WebUI, CLI, Desktop) consomment les mêmes contrats.

| Aspect | Convention | Preuve |
|---|---|---|
| Versionnement | Préfixe `/v1` ; legacy assumé (`/models`, `/providers`, `/integrations`, `/chats`) — une rupture = nouveau chemin, jamais une modification de forme sous `/v1` | Inventaire 359 routes |
| AuthN | `Authorization: Bearer <JWT>` ou cookie ; sans token → **401** | Mesuré : 87/92 routes P0 + 90/90 routes de domaine en 401 (`test_rbac_*`) |
| AuthZ | `Depends(require_permission(Permission.X))` sur les mutations sensibles ; 403 explicite si rôle insuffisant | `require_permission` : v1.py ×14, projects ×8, integrations ×9, folders ×17, capabilities ×21, internal ×20… |
| Erreurs | `{"detail": "..."}` ; **404** ressource inconnue, **422** règle métier violée (`HTTP_422`), **503** manager non initialisé | Mesuré dans les routeurs : 19× 404, 5× 422, 18× 503 |
| Création | `POST` créateur retourne **201** + l'objet | Mesuré : `models`, `providers`, `integrations`, `reminders` |
| Idempotence | `PUT`/`DELETE` idempotents ; `PATCH` = mise à jour partielle ; `POST` à effet de bascule (`/toggle`) **non** idempotent par nature | Convention + inventaire |
| Streaming | SSE `text/event-stream` (`POST /v1/chat/completions/stream`) ; pas de WebSocket dans le contrat v1 | DEF-08 |
| Pagination | **Non formalisée** dans le contrat v1 (dette — à défaut de `limit`/`offset`, aucun plafond déclaré) | §7.1 |
| Secrets | Aucun credential en réponse (I-05) ; les credentials d'intégration restent dans le domaine `integration-credentials` | Test `test_pas_de_fuite_du_store_interne` + revue |
| Frontière | Aucun chemin/schéma n'expose la structure interne du store (`core_domain_records`, `ethan_config`) | Test `test_pas_de_fuite_du_store_interne` |
| MCP | Non implémenté → **aucun endpoint** ; un test échoue si une route MCP apparaît sans mise à jour du contrat | `test_mcp_non_implemente_aucun_endpoint_fictif` |

**Tests de contrat** (exécutés en CI, `testpaths = ["tests"]`) :

```bash
.venv/bin/python -m pytest tests/test_api_contract_p0.py tests/test_api_contract_domains.py -v
```

- `test_api_contract_p0.py` — surface P0 (92 routes : Chat, Models, Providers, Projects, Knowledge, Folders, Health/State) : existence, RBAC 401, OpenAPI, zéro doublon, plafond schémas ;
- `test_api_contract_domains.py` — domaines ci-dessous (90 routes) : existence, RBAC 401, OpenAPI, MCP absent, snapshot v1, plafond schémas, frontière store.

---

## 2. Projects

**Source de vérité Core** : `core/projects/` (`ProjectManager`) — persistance domaine `projects` (`core_domain_records`). Le Project est un espace de travail persistant (instructions, contexte, documents, defaults) — la conversation hérite du contexte du projet.

| Route | Réponse | Erreurs | Idempotence |
|---|---|---|---|
| `GET /v1/projects` | liste | 401/503 | — |
| `POST /v1/projects` | objet créé | 401/422/503 | non (créateur) |
| `GET /v1/projects/default` | objet | 401/404/503 | — |
| `GET /v1/projects/{project_id}` | objet | 401/404 | — |
| `PATCH /v1/projects/{project_id}` | objet | 401/404/422 | oui (partiel) |
| `DELETE /v1/projects/{project_id}` | succès | 401/404 | oui — **ne supprime pas** les ressources référencées (I-03) |
| `GET /v1/projects/{project_id}/context` | contexte agrégé | 401/404 | — |
| `GET/POST /v1/projects/{project_id}/documents` | liste / document | 401/404/422 | POST non |
| `DELETE /v1/projects/{project_id}/documents/{doc_id}` | succès | 401/404 | oui |

- **Autorisation** : `require_permission` ×8 (`projects.py`).
- **Opérations longues** : l'ingestion documentaire passe par le pipeline RAG (jobs d'import) — pas de nouvel endpoint.
- **Tests** : contrat P0 (`P0_ROUTES`) + `interfaces/api/tests/`.

## 3. Conversations

**Source de vérité Core** : `ChatPipeline` (`core/chat/pipeline.py`) + stores `chats` / `chat-messages` (`core/state/chats.py`). ADR-3007 : unification à venir entre la famille `/chats` et `/v1/chat/*`.

| Route | Rôle | Erreurs | Notes |
|---|---|---|---|
| `GET/POST /chats` | liste / création | 401/422/503 | POST créateur |
| `GET/PUT/DELETE /chats/{chat_id}` | CRUD | 401/404 | PUT partiel |
| `GET/POST /chats/{chat_id}/messages` | historique / ajout | 401/404/422 | messages persistés (`chat-messages`) |
| `POST /chats/{chat_id}/share` | partage | 401/404 | référence seulement |
| `POST /v1/chat/completions` | completion | 401/503 | synchrone |
| `POST /v1/chat/completions/stream` | **SSE** | 401/503 | opération longue = streaming |
| `GET /v1/chat/history` | historique | 401 (Permission.READ) | |
| `POST /api/chat/completions`, `/api/v1/chat/completions` | compat OpenWebUI | 401/503 | passerelle de compatibilité |

- **Opérations longues** : génération LLM (streaming SSE), auto-compact interne au pipeline.
- **Tests** : contrat P0 + domaine `conversations` (8 routes `/chats`).

## 4. Providers

**Source de vérité Core** : `ProviderManager` + `ProviderStore` (table `llm_providers`) — **jamais de clé API en réponse** (I-05).

| Route | Response model | Erreurs |
|---|---|---|
| `GET /providers` | `list` | 401 |
| `GET /providers/catalog` | `dict` (Core `ProviderManager.get_catalog`) | 401/503 — **déclarée avant `/{provider_id}`** (ordre FastAPI) |
| `POST /providers` | `ProviderResponse` (**201**) | 401/422 |
| `GET/PUT /providers/{provider_id}` | `ProviderResponse` | 401/404/422 |
| `DELETE /providers/{provider_id}` | — | 401/404 |
| `GET /providers/{provider_id}/capabilities` | — | 401/404 |
| `PUT /providers/{provider_id}/default` | `ProviderResponse` | 401/404 |
| `GET /providers/{provider_id}/models` | `list` | 401/404 |
| `POST /providers/{provider_id}/test` | `TestConnectionResult` | 401/404 **+ 503 si manager absent** |
| `POST /providers/vision`, `/providers/transcribe` | — | 401/422/503 |

- **Opérations** : `test` = E/S réseau synchrone (timeout côté Core).
- **Tests** : contrat P0 + `tests/test_providers_api.py` (si présent) — voir fixtures domaine.

## 5. Models

**Source de vérité Core** : `ModelStore` (`core/llm/model_store.py`, `core_domain_records`).

| Route | Response model | Notes |
|---|---|---|
| `GET /models` | — (dette) | liste |
| `POST /models` | `dict` (**201**) | création |
| `GET /models/search` | — | recherche |
| `GET/PUT/DELETE /models/{model_id}` | `dict` (PUT) | PUT partiel, DELETE idempotent |
| `POST /models/{model_id}/toggle` | — | **non idempotent** (bascule activé/désactivé) |

- Sémantique : Provider = service fournisseur ; Model = modèle utilisable ; Capability = propriété du provider (`/capabilities`) ; **Usage/Profile** : notion non supportée par le Core (refus d'inventer — D-05).
- **Tests** : contrat P0.

---

## 6. Agents / Missions / Goals

**Source de vérité Core** : `AgentManager` (`agents`, `agent-executions`), `MissionManager` (`missions`), `GoalManager` (`goals`).

| Route | Autorisation | Notes |
|---|---|---|
| `GET/POST /v1/agents` | POST → `Permission.AGENTS` | POST créateur |
| `GET/PUT/DELETE /v1/agents/{agent_id}` | — | CRUD |
| `POST /v1/agents/{agent_id}/execute` | `Permission.EXECUTE` | **opération longue** (exécution agent) |
| `GET /v1/agents/{agent_id}/executions` | — | historique persisté (`agent-executions`) |
| `GET /v1/agents/{agent_id}/resources` | — | ressources associées (références) |
| `GET/POST /v1/missions` | POST → `Permission.EXECUTE` | POST créateur |
| `GET/PUT/DELETE /v1/missions/{mission_id}` | — | CRUD |
| `POST /v1/missions/{mission_id}/steps/{step_id}/approve` | — | **human-in-the-loop** : validation d'étape |
| `POST /v1/missions/{mission_id}/steps/{step_id}/verify` | — | vérification d'étape |
| `GET/POST /v1/goals`, `GET/PUT/DELETE /v1/goals/{goal_id}` | — | CRUD |

- **Async / long** : missions = travail long découpé en étapes (approbation/vérification par étape) ; `execute` agent = exécution asynchrone côté Core, l'API ne bloque pas le résultat.
- **Erreurs** : 401/404/422 ; **503** si les managers ne sont pas initialisés (`v1.py` — 17×503).
- **Tests** : domaine `agents`/`missions`/`goals` (20 routes) + `tests/core/test_cognitive_loop.py`.

## 7. Knowledge / RAG

**Source de vérité Core** : `KnowledgeCollectionManager` (`knowledge`, `knowledge-collections`) + `RAGPipeline` (`rag-documents`, `rag-config`).

**Pipeline unique** : ingestion → embeddings → retrieval → context (`core/rag/`). Aucun second pipeline ne doit être créé (contrainte C-05). Backend vectoriel : ADR-3004 **non tranché** (qdrant/chroma/pgvector — dette G-03).

| Famille | Routes | Notes |
|---|---|---|
| Knowledge CRUD | `GET/POST /v1/knowledge`, `GET/PUT/DELETE /v1/knowledge/{knowledge_id}` | base |
| Collections | `/v1/knowledge/collections` (CRUD, `tree`, `move`, `retrieve`, `retrieve-multi`) | CRUD + navigation |
| Documents | `GET/POST /v1/knowledge/collections/{collection_id}/documents`, `DELETE …/{document_id}` | POST = ingestion |
| Recherche | `GET /v1/knowledge/search` | retrieval |
| Connexions | `POST /v1/knowledge/{knowledge_id}/connections`, `POST …/rag` | liaisons |
| **Jobs d'import** | `POST /v1/knowledge/import`, `/import-batch`, `GET /v1/knowledge/imports/{job_id}` | **async** : polling du job |
| **Reindex** | `POST /v1/knowledge/collections/{collection_id}/reindex` | **opération longue** |
| RAG documents | `GET/POST /v1/rag/documents`, `POST /v1/rag/documents/from-file/{file_id}`, `GET/DELETE …/{document_id}` | pipeline documentaire |
| RAG recherche/contexte | `POST /v1/rag/retrieve`, `/v1/rag/context`, `GET /v1/rag/status`, `/v1/rag/strategies`, `GET/PUT /v1/rag/config` | retrieval + configuration |

- **Autorisation** : `Permission.MEMORY` sur les écritures RAG (`/v1/rag/documents`), `Permission.ADMIN` sur la configuration sensible.
- **Tests** : contrat P0 (knowledge) + domaine `rag` (11 routes).

## 8. Components (surface **non committée** — hors contrat)

La gestion des composants optionnels (détection, installation, configuration, santé, désinstallation) est spécifiée par **ADR-4001→4004** et **ESR-001→005** (Core : `core/capability_manager/`). Les opérations privilégiées passent par le Core — **le WebUI ne manipule jamais Docker/Ollama directement** (contrainte C-07).

**État réel** : le routeur (`interfaces/api/routers/component_lifecycle.py`, 17 routes `/v1/components/*`) est **non committé (WIP)** au 25/09/2026 → **hors contrat v1** (aucun endpoint fictif). Au commit : ajouter ces routes au contrat + au snapshot.

## 9. Skills / Tools

**Source de vérité Core** : `SkillManager` (`skills`), `ToolManager` (`tools`, `tool-pipelines`).

| Route | Autorisation | Notes |
|---|---|---|
| `GET/POST /v1/skills` | POST → `Permission.PLUGINS` | CRUD base |
| `GET/PUT/DELETE /v1/skills/{skill_id}`, `/toggle` | — | CRUD + bascule |
| `GET/POST /v1/skills/export`, `/import` | import → `Permission.PLUGINS` | portabilité |
| `GET /v1/skills/search` | — | recherche |
| `POST /v1/skills/{skill_id}/run` | `Permission.EXECUTE` | **exécution** |
| `POST /v1/skills/{skill_id}/execute` | `Permission.PLUGINS` | exécution (variante) |
| `POST /v1/skills/lab/test`, `GET /v1/skills/lab/results` | `Permission.EXECUTE` | banc d'essai |
| `GET/PUT /v1/skills/{skill_id}/valves` | — | paramètres (valves) |
| `GET/POST /v1/tools`, `DELETE /v1/tools/{tool_id}` | — | outils personnalisés |
| `/v1/tools/pipelines` (CRUD) | — | pipelines d'outils |
| `/v1/tools/servers` (CRUD, `/status`, `/sync`) | — | **serveurs d'outils** (découverte/synchronisation) — à ne pas confondre avec MCP (§11) |

- **Tests** : domaine `skills` (15) + `tools` (14) ; `tests/test_skills_api.py`.

---

## 10. Plugins

**Source de vérité Core** : `PluginRegistry` (`core/plugins/registry.py`) — persistance domaine `webui_plugins`.

| Route | Notes |
|---|---|
| `GET /v1/plugins`, `/v1/plugins/categories` | catalogue + catégories |
| `GET /v1/plugins/{plugin_id}`, `/capabilities`, `/permissions` | détail |
| `POST /v1/plugins/install` | installation (catalogue) |
| `POST /v1/plugins/{plugin_id}/install`, `/update`, `/enable`, `/disable` | cycle de vie |
| `PUT /v1/plugins/{plugin_id}/toggle` | bascule (non idempotent) |
| `DELETE /v1/plugins/{plugin_id}` | désinstallation |
| `POST /v1/plugins/{plugin_id}/connect`, `DELETE …/connection` | connexions (références — pas de credentials en réponse) |

- **Autorisation** : auth requise (401) ; **permissions fines non attachées** aux routes plugin (dette — cf. §14). La validation d'installation est Core-owned (`PluginRegistry.install_custom` → `PluginValidator`, P1-PLUGIN-01).
- **Tests** : domaine `plugins` (14) + `tests/test_plugins_api.py`, `tests/test_plugin_validator.py`.

## 11. MCP

**État : non implémenté.** Aucun module Core, aucune route, aucun serveur MCP au dépôt (audit 25/09/2026).

- Le contrat v1 **ne déclare aucun endpoint MCP** (règle « aucun endpoint fictif ») — garanti par `test_mcp_non_implemente_aucun_endpoint_fictif` : si une route MCP apparaît, le test échoue et exige la mise à jour du contrat.
- `/v1/tools/servers` (§9) est un registre de serveurs d'outils **distinct** du protocole MCP.
- Prérequis avant implémentation : ADR-3010 (à créer — `ARCHITECTURE-CIBLE.md` §3.2).

## 12. Integrations / Connections

**Source de vérité Core** : `IntegrationManager` (`core/integrations/`) — domaines `integrations` + `integration-credentials` (I-05 : les credentials ne sortent **jamais** en réponse).

| Route | Notes |
|---|---|
| `GET/POST /integrations` | POST créateur (**201**) |
| `GET/PUT/DELETE /integrations/{integration_id}` | CRUD |
| `POST /integrations/{integration_id}/connect`, `/disconnect` | cycle de connexion |
| `POST /integrations/{integration_id}/test` | test de connexion (E/S) |

- **Autorisation** : `require_permission` ×9 (`integrations.py`).
- **Connections (comptes externes : email, github, notion…) : surface NON committée** — routeur `connections.py` (9 routes `/connections/*`) en WIP au 25/09/2026 → **hors contrat v1**. Au commit : ajouter au contrat + snapshot.
- **Tests** : domaine `integrations` (8 routes).

## 13. Surfaces déclarées ∪ non committées (WIP local) — hors contrat v1

Ces surfaces existent **uniquement dans le WIP local** (mesuré le 25/09/2026) et sont **exclues du contrat** tant qu'elles ne sont pas committées :

| Surface | Routes (WIP) | Statut au commit |
|---|---|---|
| Components | `/v1/components/*` (17) | ajouter au contrat + snapshot (§8) |
| Connections | `/connections/*` (9) | ajouter au contrat + snapshot (§12) |
| Search v1 | `/v1/search`, `/v1/search/types` | **déplacement** de `/search` (+ `/search/types`) → `WIP_PENDING_REMOVALS` |
| Web tools | `/v1/web-search`, `/v1/web-inspiration`, `/v1/web-research`, `/v1/web-skill-draft` | ajouter (nouveaux domaines web) |
| Projets | `/v1/projects/active` | ajouter |
| Users | `PUT/DELETE /users/{user_id}` **retirés** (dédup — ownership `security.py`) | suppressions = `WIP_PENDING_REMOVALS` dans le test de snapshot |

**Au commit du WIP** : régénérer le snapshot (§15), étendre `DOMAIN_ROUTES`, mettre à jour `WIP_PENDING_REMOVALS` (le vider), et mettre à jour ce catalogue.

---

## 14. Dette contractuelle mesurée (25/09/2026)

| Dette | Mesure | Garde-fou | Cible |
|---|---|---|---|
| Routes sans `response_model` | **175** (85 plafond P0 + 90 domaine) | Plafonds non régressifs dans les 2 contrats | ADR-3006 : schémas au fil des vagues V2-V5 |
| Permissions fines absentes sur `/v1/plugins/*` et une partie de `/v1/skills|tools` | Auth (401) seule | Revue | V2 |
| Pagination non formalisée | Absente du contrat v1 | — | V3 (conversations) |
| Conversations multi-modèle | Famille `/chats` + `/v1/chat/*` | Domaine `conversations` | ADR-3007 (V3) |
| Backend vectoriel | qdrant/chroma coexistants | — | ADR-3004 (V4) |
| Config double source (`ethan_config`) | G-01 | — | ADR-3001 (V2) |
| Snapshot historique `docs/api/openapi.yaml` | Obsolète (juin 2026, « Jarvis OS », 0 route actuelle) | Remplacé par `openapi.v1.json` | Archiver/supprimer en V2 |
| Types TS générés depuis OpenAPI | Non fait | — | DEF-07 |

## 15. Vérification & régénération

```bash
# Contrats (obligatoire avant tout commit touchant interfaces/api) :
.venv/bin/python -m pytest tests/test_api_contract_p0.py tests/test_api_contract_domains.py -v

# Vérifier la surface committée (utilisé pour rédiger ce catalogue) :
JWT_SECRET=x python -c "
import secrets, os
os.environ.setdefault('JWT_SECRET', secrets.token_urlsafe(48))
from interfaces.api.main import app
routes = sorted({(m, r.path) for r in app.routes for m in (getattr(r, 'methods', None) or set()) if m not in ('HEAD','OPTIONS')})
print(len(routes)); [print(m, p) for m, p in sorted(routes, key=lambda x: (x[1], x[0]))]
"

# Régénérer le snapshot v1 (TOUJOURS sur le code committé, jamais sur le WIP) :
JWT_SECRET=x python -c "
import json, secrets, os
os.environ.setdefault('JWT_SECRET', secrets.token_urlsafe(48))
from interfaces.api.main import app
schema = app.openapi()
schema['x-ethan-snapshot'] = {'source_commit': '<sha>', 'generated': '<date>' , 'note': 'ADR-3006 #1'}
json.dump(schema, open('docs/api/openapi.v1.json', 'w', encoding='utf-8'), indent=2, sort_keys=True, ensure_ascii=False)
"
# NB : docs/ est dans .gitignore → `git add -f docs/api/...` requis.
```

**Historique** : v1 — 2026-09-25 — création (contrat P0 existant + 90 routes de domaine + snapshot `openapi.v1.json` + 7 tests de domaine ; preuves : `13 passed` sur clone vierge `22fad583`).
v1 — 2026-09-26 — ajout `GET /providers/catalog` (catalogue Core : types/URLs par défaut/auth/capacités — route déclarée avant `/{provider_id}`) ; snapshot régénéré sur le code committé `0c3991cf` (360 routes).



