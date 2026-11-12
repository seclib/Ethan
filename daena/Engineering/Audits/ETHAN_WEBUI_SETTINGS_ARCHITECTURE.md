# Architecture Settings ETHAN WebUI — inspirée Open WebUI

> **Principe** : Open WebUI (OWUI) = **référence fonctionnelle/UX** pour la gestion des paramètres. ETHAN Core = **propriétaire unique** des données ET de la logique de configuration. Le futur WebUI est une **interface de configuration** — **pas** un système Settings parallèle.
> **Aucune source de vérité dupliquée.** Aucun fichier source `.py` / `.tsx` modifié. Nouveau document `docs/plans/`.

---

## Schéma cible

```
┌──────────────────────────────────────────────────────────────────┐
│  ETHAN Core — Configuration UNIQUE                              │
│  core/config/schema.py   (9 domaines typés)                     │
│  core/config/service.py  (ConfigurationService)                 │
│  core/config/store.py    (ConfigStore PG+Redis)                 │
│  core/config/loader.py   (chargement env→schéma→store)          │
│  core/config/secrets.py  (secrets isolés, jamais en DB)          │
└────────────────────────────┬─────────────────────────────────────┘
                             │ REST /v1/config/* + CLI direct
        ┌────────────────────┼──────────────────┬─────────────────┐
        ▼                    ▼                  ▼                 ▼
  ETHAN WebUI             CLI               Desktop           Atreus
  (interface config)   (ethan config)      (panneaux)      (lecture seule)
```

---

## 1. Analyse des Settings Open WebUI

### 1.1 Backend — `backend/open_webui/config.py` (4165 lignes)

**Mécanisme `PersistentConfig`** :
- Chaque paramètre est un objet `PersistentConfig(env_name, config_path, env_value)`.
- Stockage : table SQL `config` (colonne JSON `data`) — `config.json` migré au premier démarrage.
- `config_path` pointé (ex: `auth.jwt_expiry`, `rag.top_k`) — hiérarchie d'objets JSON.
- `ENABLE_PERSISTENT_CONFIG` (True par défaut) ; `auth.` et `oauth.` persistables séparément (`ENABLE_OAUTH_PERSISTENT_CONFIG` False par défaut).
- **Défaut** : la config runtime est **persistée en DB** (`async_save_to_db`) déclenchée par `AppConfig.__setattr__`.
- **Redis** : `AppConfig` propose une cache de lecture `open-webui:config:{key}`.
- **Migrations** : `run_migrations()` via Alembic aux démarrage.
- **Secrets** : clés API stockées dans la **même DB** (ex: `GOOGLE_CLIENT_SECRET` → `oauth.google.client_secret`) — ⚠️ violation du principe `.clinerules/secret.md`.

**~290 paramètres `PersistentConfig`**, répartis par sections :

| Section | Exemples |
|---|---|
| **Auth** | enable_api_keys, jwt_expiry, api_key.endpoint_restrictions |
| **OAuth/OIDC** | google.client_id/secret, microsoft.tenant_id, github.client_secret, oidc.provider_url, feishu, roles_claim, allowed_domains |
| **Direct connections** | enable_direct_connections, enable_ollama_api, ollama.base_urls, openai.api_keys/base_urls |
| **UI** | webui.url, default_locale, default_models, default_pinned_models, prompt_suggestions, model_order, default_model_params, banners |
| **Users** | default_user_role, default_group_id, user_permissions, enable_folders, channels, calendar, automations, notes, user_status |
| **Webhooks** | webhook_url, enable_community_sharing, message_rating |
| **Tasks/Labels** | task_model, title/tags/image/follow_up/prompt templates, autocomplete |
| **Code execution** | enable_code_execution, code_execution_engine, jupyter_url/auth, code_interpreter |
| **Documents (RAG)** | content_extraction_engine, datalab_marker/mineru/tika/docling/document_intelligence, google_drive, onedrive |
| **RAG** | top_k, top_k_reranker, relevance_threshold, hybrid_bm25, full_context, chunk_size, chunk_overlap, splitter, embedding_engine, embedding_model, reranking, templates |
| **Web search** | enable_web_search, web_search_engine, web_search_result_count, domain_filters, 20+ providers API keys (SearXNG, Brave, Kagi, Bing, Google PSE, Tavily, Perplexity, Jina, Firecrawl, Exa, Sogou…) |
| **Image generation** | enable, engine, model, size, steps, automatic1111, comfyui, openai_images, gemini |
| **Audio (STT/TTS)** | whisper_model, deepgram_key, stt_engine, azure/mistral, tts_engine, azure_speech, openai |
| **LDAP** | enable, server_label/host/port, attribute for mail/username, app_dn, search_base, use_tls |

**~30 paramètres non-persistants** (mode `SimpleConfig`) : `FOO = os.environ.get(...)` (ex: `TIKTOKEN_ENCODING_NAME`).

### 1.2 Backend — `core/routers/configs.py` (664 lignes)

Routes **admin-only** (`/api/v1/configs/`) :

| Route | Fonction |
|---|---|
| `POST /import` | Import config complète (dict) |
| `GET /export` | Export config complète |
| `GET/POST /connections` | Connections (Ollama/OpenAI) |
| `POST /oauth/clients/register` | Enregistrement OAuth client |
| `GET/POST /tool_servers` | Serveurs d'outils (MCP) CRUD |
| `GET/POST /terminal_servers` | Serveurs terminal CRUD |
| `POST /terminal_servers/verify` | Vérification connexion |
| `POST /terminal_servers/policy` | Politique |
| `POST /tool_servers/verify` | Vérification MCP |
| `GET/POST /code_execution` | Config code execution |
| `GET /models/defaults` | Modèles par défaut |
| `GET/POST /models` | Config modèles |
| `POST /suggestions` | Prompts suggérés |
| `GET/POST /banners` | Bannières |

### 1.3 Frontend — `src/lib/components/admin/Settings/`

**Admin Settings** (routes `(app)/admin/settings/[tab]`) — 13 onglets :

| Tab | Fichier svelte | Rôle |
|---|---|---|
| general | `General.svelte` | Nom, description, logos, URL publique, licences |
| interface | `Interface.svelte` + `Interface/Banners.svelte` | Langue, déclencheurs, suggestions, banners |
| models | `Models.svelte` + `Models/*` (Manage, Settings, List, Menu, Selector) | Modèles par défaut, réglages modèle, modèles cachés |
| connections | `Connections.svelte` + `Connections/OllamaConnection.svelte`, `Connections/OpenAIConnection.svelte`, `ManageOllamaModal.svelte` | Accès Ollama/OpenAI, fuseaux horaires |
| documents | `Documents.svelte` | Upload : max_size, max_count, extensions autorisées, compression images |
| websearch | `WebSearch.svelte` | Moteurs, clés, prompt (9+ providers) |
| audio | `Audio.svelte` | STT (whisper), TTS (azure/openai) |
| images | `Images.svelte` | Génération image : moteur, modèle, taille, API |
| codeexecution | `CodeExecution.svelte` | Jupyter, moteur, profondeur, timeout |
| database | `Database.svelte` | Base exposée, migrations |
| pipelines | `Pipelines.svelte` | Pipelines |
| integrations | `Integrations.svelte` | Webhooks, ox|
| interface | `Interface.svelte` | Identique |

**User Settings** (routes `(app)/settings`) — sections utilisateur :

| Tab | Rôle |
|---|---|
| general | Profil, langue, thème, interface |
| model | Modèle actif, réglages par défaut |
| personalization | Personnalisation du prompt system, mémoire |
| data | Import/export |
| commands | Commandes slash |
| status | Statut |
| audio | Audio |
| models cache | Cache modèles |

### 1.4 Points faibles Open WebUI
1. **Secrets non isolés** : `google_client_secret`, `openai_api_key`, `ldap_app_password` etc. sont persistés en clair dans `config` JSON DB → violation `.clinerules/secret.md`.
2. **Registry de config central monolithique** : `PendingConfig` global concret, `PERSISTENT_CONFIG_REGISTRY` liste non ordonnée ; l'ajout d'un nouveau paramètre requiert : constante + env + path + enregistrement.
3. **Roté** : paramètres frontend UI (flags, hardcoded options) non exposés en backend.
4. **Pas de validation de schéma** (champ `type`) : tout est `str`/`bool`/`int` détecté par cast `bool`/`int` ; pas de JSON Schema→Form.
5. **Pas de catégories formelles** : alertation implicite par prefixes (auth.*, rag.*, oauth.*) mais pas de `SettingsCategory` déclarée dans le backend.

---

## 2. Analyse ETHAN — `core/config/`

### 2.1 Fichiers existants
| Fichier | Rôle |
|---|---|
| `core/config/schema.py` (351 lignes) | **9 dataclasses typées** : `RuntimeConfig`, `BusConfig`, `StorageConfig`, `ProviderConfig`, `ProvidersConfig`, `ModelRoutingConfig`, `ModelsConfig`, `RAGConfig`, `MemoryConfig`, `AgentsConfig`, `PlannerConfig`, `PluginsConfig`, `AuthenticationConfig` + point d'entrée `ConfigSchema` |
| `core/config/service.py` | `ConfigurationService` + `_deep_merge()` |
| `core/config/store.py` | `ConfigStore` (PG+Redis) |
| `core/config/loader.py` | Chargement env → schéma → store |
| `core/config/secrets.py` | Secrets (env/Vault/Docker secrets) |
| `core/config/prompts.py` | Templates de prompts |

### 2.2 Forcesses ETHAN
1. **Typé** : chaque domaine est un dataclass Python typé → auto documentation + introspection (supporte JSON Schema générique pour Settings UI).
2. **Domainé** : 9 domaines top-level (runtime, providers, models, rag, memory, agents, planner, plugins, authentication) — aligné sur le feedback (providers, modèles, RAG, memory, agents).
3. **Secrets séparés** : `secrets.py` jamais persistés en DB.
4. **Profond fusion** : `ConfigurationService._deep_merge()` pour override partiel.
5. **Absence** : UI Settings frontend (nécessaire).

### 2.3 Manquants ETHAN (vs OWUI)
1. **Sous-domaines** très fins nécessaires : auth (api keys, jwt, oauth providers, ldap), llm (tasks, routers, tts/stt), rag (everything extraction, hybrid, web search), tools (servers, mcp, code execution), memory (ttl, archiving), agents, files (storage), channels, notes, automation.
2. **Configurable via UI** : ni API Settings complète ni schéma JSON Schema pour diriger un formulaire.
3. **Modules** pour : document extraction, web search, images, audio — absents du schéma ETHA.
4. **User-level** : pas de config utilisateur (locale, thème, modèle par défaut).
5. **UI système** (banners, titre licence, nourriture) — absent.

---

## 3. Comparaison

| Aspect | OWUI | ETHAN |
|---|---|---|
| Registre | `PersistentConfig` global (~290) | `ConfigurationService` (9 domaines) |
| Persistence | DB SQL JSONB + Redis cache | `ConfigStore` PG+Redis |
| Secrets | ❌ Partial (DB) | ✅ `secrets.py` isolé |
| Typage | str/bool/int (cast) | ✅ dataclasses cases |
| JSON Schema | ❌ | ✅ potentiel générique |
| Catégories UI | explicit (13 tabs) | à construire |
| User config | ✅ (per user) | ❌ |
| Rotations | ❌ | `_deep_merge` ✅ |
| Validation | ❌ | partielle (types) |

---

## 5. Architecture Settings ETHAN cible

### 5.1 Fondation — domaines de configuration ETHAN (source de vérité)

```
core/config/schema.py (ÉTENDU)
├── runtime    (mode, bus, storage, log, plugins_dir, data_dir)
├── providers  (active + dict ProviderConfig: ollama/openai/anthropic/…  sans secrets)
├── models     (default, routing.reasoning/code/fast/local/embedding, fallback)
├── rag        (enabled, chunk_size, overlap, top_k, embedding_model, rerank, persist)
├── memory     (enabled, max_facts, ttl_days, auto_archive, archiver, max_context)
├── agents     (max_concurrent, default_timeout, auto_restart, default_model, default_provider)
├── planner    (max_depth, max_steps, timeout, auto_approve, confirm, default_agent)
├── plugins    (auto_load, allowed_paths, sandbox, auto_update)
├── authentication (enabled, jwt_secret_env, jwt_expiry_hours, rbac, oauth_raw, password_min, session_timeout)
├── files (upload_max_size, upload_max_count, allowed_extensions, storage_provider, storage_config)
├── mcp (servers: ToolServer[], terminal_servers[], auth, verify)
├── web_search (engine, result_count, providers: SearXNG, Brave, Bing, … WITHOUT secrets)
├── image_generation (enabled, engine, size, steps, provider)
├── audio (stt_engine, stt_model, tts_engine, tts_voice, api_config)
├── code_execution (enabled, engine, jupyter url, auth, timeout, code—interpreter)
├── extraction (content_engine, tika/marker/mineru/docling config, pdf, max)
├── user (default_role, default_locale, default_model, theme, language, …)
└── metadata
```

> Note : tous les secrets pointés par `..._env` ou `secrets.py` — l'UI ne reçoit jamais de clé.

### 5.2 Scénarios type pour le WebUI

```
WebUI Settings (fork OWUI UX)
  │
  ├── /settings          — User Settings (per user)
  │     ├── general (langue, thème, préférences)
  │     ├── model (modèle actif, paramètres)
  │     └── personalization (system prompt, mémoire)
  │
  └── /admin/settings    — Admin Settings (system-wide)
     ├── general
     ├── interface (banners, ui, prompts)
     ├── models
     ├── connections
     ├── documents (files)
     ├── websearch
     ├── audio
     ├── images
     ├── codeexecution
     ├── rag
     ├── knowledge (collections)
     ├── tools (mcp + tools)
     ├── memory
     ├── agents
     ├── users (default_role, groups)
     └── authentication (oauth, ldap, rbac)
```

### 5.3 API (source de vérité → interfaces)

Toutes les interfaces (WebUI, CLI, Desktop) utilisent **la même API** :

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/v1/config` | Introspection config complète (sans secrets) |
| GET | `/v1/config/{domain}` | Get un domain (ex: `rag`) |
| PUT | `/v1/config/{domain}` | Update domain (merge partial via `_deep_merge`) |
| GET | `/v1/config/schema` | JSON Schema généré depuis dataclasses → Form UI |
| GET | `/v1/config/schema/{domain}` | Schema du domain |
| POST | `/v1/config/import` | Import config (admin) |
| GET | `/v1/config/export` | Export config (admin) |
| POST | `/v1/config/reset` | Reset → defaults |
| GET | `/v1/users/me/config` | Per-user settings |
| PUT | `/v1/users/me/config` | Update per-user settings |

> CLI : `ethan config get/set {domain}.{key}` → appelle `ConfigurationService` (même source).

### 5.4 Persist

- **Admin config** : `core/config/store.py` (ConfigRecordStore PG + cache Redis).
- **Per-user config** : table `core/auth/models.json` ou `core/state/record_store` (`user_config` table).
- **Secrets** : `core/config/secrets.py` (env → Vault).

### 5.5 Permissions

| Resource | Permission |
|---|---|
| Toute config admin | `require_permission(ADMIN)` |
| Config user | `require_permission` sur sa propre config |
| Import/export | ADMIN |
| Secrets (read/mutate) | Admin + secret manager |

---

## 6. Mapping Open WebUI → ETHAN (par catégorie)

### 6.1 Général (General)
| OWUI Paramètre | ETHAN key | Type | Défault appli |
|---|---|---|---|
| `WEBUI_NAME` | `ui.name` | str | "Ethan" |
| `WEBUI_URL` | `ui.url` | str | "" |
| `DEFAULT_LOCALE` | `ui.locale` | str | "en" |
| `WEBUI_BANNERS` | `ui.banners` | list[Banner] | [] |
| favicon | `ui.favicon_url` | str | "" |

### 6.2 Modèle
| OWUI | ETHAN | Type |
|---|---|---|
| `DEFAULT_MODELS` | `models.default` | str |
| `MODEL_ORDER_LIST` | `models.routing_order` | list |
| `DEFAULT_MODEL_PARAMS` | `models.params` | dict |
| `DEFAULT_PROMPT_SUGGESTIONS` | `ui.prompt_suggestions` | list |

### 6.3 Connections (providers)
| OWUI | ETHAN | Type |
|---|---|---|
| `OLLAMA_BASE_URLS` | `providers.providers.ollama.base_url` | str |
| `OPENAI_API_KEYS` | `providers.providers.openai.api_key_env` (secret ref) | str |
| `OPENAI_API_BASE_URLS` | `providers.providers.openai.base_url` | str |
| `ENABLE_DIRECT_CONNECTIONS` | `providers.allow_oxit` | bool |

### 6.4 Documents (files + extracted)
| OWUI | ETHAN | Type |
|---|---|---|
| `FILE_MAX_SIZE` | `files.max_upload_size_bytes` | int |
| `FILE_MAX_COUNT` | `files.max_upload_count` | int |
| `ALLOWED_FILE_EXTENSIONS` | `files.allowed_extensions` | list[str] |
| `FILE_IMAGE_COMPRESSION_*` | `files.image_compression.{width,height}` | int |
| `CONTENT_EXTRACTION_ENGINE` | `extraction.engine` | str "marker\|tika\|docling" |

### 6.5 RAG
| OWUI | ETHAN | Type |
|---|---|---|
| `RAG_TOP_K` | `rag.top_k` | int |
| `CHUNK_SIZE` | `rag.chunk_size` | int |
| `CHUNK_OVERLAP` | `rag.chunk_overlap` | int |
| `USE_RAG_SUB_QUERY` | `rag.sub_queries` | bool |
| `ENABLE_RAG_HYBRID_SEARCH` | `rag.hybrid_enabled` | bool |
| `HYBRID_` | `rag.hybrid_`* | float |
| `RAG_RERANKING_ENGINE` | `!rag.reranker.engine` | str |
| `RAG_EMBEDDING_ENGINE` | `rag.embeddings.engine` | str |
| `RAG_EMBEDDING_MODEL` | `rag.embeddings.model` | str |
| `RAG_EMBEDDING/OLLAB%` … | secrets ref | |
| `RAG_TEMPLATE` | `rag.prompt_template` | str |

### 6.6 Recherche web
| OWUI | ETHAN | Type |
|---|---|---|
| `WEB_SEARCH_ENGINE` | `web_search.engine` | str |
| `WEB_SEARCH_RESULT_COUNT` | `web_search.max_results` | int |
| `WEB_SEARCH_DOMAIN_FILTER_LIST` | `web_search.allowed_domains` | list[str] |
| `SEARXNG_QUERY_URL` | `web_search.providers.searxng.url` | str |

### 6.7 Audio
| OWUI | ETHAN |
|---|---|
| `AUDIO_STT_ENGINE` | `audio.stt.engine` |
| `AUDIO_STT_MODEL` | `audio.stt.model` |
| `WHISPER_MODEL` | `audio.stt.whisper_model` |
| `AUDIO_TTS_ENGINE` | `audio.tts.engine` |
| `AUDIO_TTS_VOICE` | `audio.tts.voice` |

### 6.8 Images
| OWUI | ETHAN |
|---|---|
| `IMAGE_GENERATION_ENGINE` | `image_generation.engine` |
| `IMAGE_SIZE` | `image_generation.size` |
| `IMAGE_STEPS` | `image_generation.steps` |

### 6.9 Code
| OWUI | ETHAN |
|---|---|
| `ENABLE_CODE_EXECUTION` | `code_execution.enabled` |
| `CODE_EXECUTION_ENGINE` | `code_execution.engine` |
| `CODE_EXECUTION_JUPYTER_URL` | `code_execution.jupyter.url` |

### 6.8 Memory
— pas équivalent direct dans OUI (séparément Memories).

### 6.10 Agents
— pas équivalent direct dans OWU (settings moto global).

---

## 7. Recommendations mises en œuvre — exécutables

1. **Étendre `core/config/schema.py`** : ajouter *files, mcp, web_search, image_generation, audio, code_execution, extraction, llm (tasks), agents config, ui/banners.
2. **Générer un Schéma JSON** (`core/api` ou `config/schema.py`) pour chaque dataclass → *ConfigurationServiceSchemaResolver*.
3. **Créer le router `interfaces/api/routers/config.py`** : routes GET/PUT/import/export/reset/list.
4. **Bloquer secrets** : tout champ *..._key* sur `*_key_ref` / `*_secret_env` et jamais retourné dans GET `config`.
5. **WebUI (fork OWUI)** — pages Settings remapées sur `/v1/config/...`.

---

## 8. Consommateurs

| Inter-face | Rôle Settings |
|---|---|
| **WebUI** | Pages admin Settings (13 onglets) et user Settings → form-driven par schéma JSON |
| **CLI** | `ethan config get/set $dom.$key` → `ConfigurationService` |
| **Desktop** | Panneaux Settings natifs → même GET/PUT `/v1/config/` |
| **Atreus** | Agents read `core/config` via `GET /v1/config/` |

---

## 9. Conclusion

Open WebUI propose un excellent référentiel UX + **290+ paramètres** pour l'admin/expériences. ETHAN possède une infrastructure de configuratorrunt solide (typé, domaine, secrets séparés) mais **manque les domaines** (extraction, web search, audio, images, code, files/mcp à intégrer au schéma) et **l'API du schéma/UI**.

→ **Une seule source de vérité** : `core/config/schema.py` étendu + `ConfigurationService`.
→ **Une seule API** : `/v1/config` dérivée.
→ **Fork UX OWUI** fournit le formulaire, jamais la persistance.
</write_to_file>
<task_progress>
- [x] Analyser le feedback utilisateur (nouvelle tâche Settings)
- [x] Localiser Open WebUI (/home/fatsio/AI/open-webui)
- [x] Cartographier la structure frontend Admin Settings (12 sous-catégories identifiées)
- [x] Comprendre le mécanisme PersistentConfig/AppConfig d'OWUI
- [x] Extraire la liste complète des paramètres PersistentConfig d'OWUI (~300, auth→LDAP)
- [x] Identifier la structure core/config/ d'ETHAN
- [x] Analyser le schéma de config ETHAN (schema.py — 9 domaines)
- [x] Analyser le service config ETHAN (service.py + store.py)
- [x] Analyser le router configs OWUI (routes API config)
- [x] Comparer Settings OWUI vs ETHAN
- [x] Construire l'architecture Settings ETHAN (catégories, schémas, API, UI)
- [x] Rédiger le document d'architecture Settings
</task_progress>
</write_to_file>