# Architecture cible — Models & Providers ETHAN (inspiré Open WebUI)

> **Principe** : une seule source de vérité (`core/`), une seule registry models, une seule registry providers, une seule config. Open WebUI sert de **référence UX** ; ETHAN Core est la source de vérité. Le futur ETHAN WebUI est un *thin client*.
> **Ne modifie aucun fichier.** Ce document est un livrable d'analyse (nouveau fichier `docs/plans/`).

---

## 1. Architecture cible (diagramme de flux)

```
                 ┌──────────────────┐
                 │  Ollama (hôte)   │   ← reste indépendant
                 │  OLLAMA_HOST:11434│   ← http(s) vers host
                 └─────────┬────────┘
                           │ (API native Ollama / OpenAI-compatible)
                           ▼
        ┌──────────────────────────────────────┐
        │  ETHAN Provider Layer (core/llm)     │
        │  - provider_factory.py               │
        │  - providers/{ollama,openai,...}.py  │  ← transports homogènes
        │  - registry.py (LLMProviderRegistry)  │
        │  - ProviderManager (healthcheck, auth)│
        │  - routing.yaml / selector.py         │  ← routing + coûts/latence
        │  - secrets.py (clés jamais persistées)│
        └─────────┬────────────────────────────┘
                  │ discovers + valide
                  ▼
        ┌──────────────────────────────────────┐
        │  ETHAN Model Registry (core/llm)     │
        │  - model_store.py (ModelStore)       │  ← cartes custom (params/meta/acl)
        │  - types.py (ModelInfo)              │  ← modèles découverts + scores
        │  - tracker.py (latence/coût)         │
        │  - store.py (ProviderStore PG/Redis) │
        └─────────┬────────────────────────────┘
                  │ agrège (discovered + custom)
                  ▼
        ┌──────────────────────────────────────┐
        │  ETHAN API (interfaces/api)          │
        │  - routers/models.py  → /v1/models   │
        │  - routers/providers.py → /v1/providers│
        │  - v1.py /v1/chat (chat_stream)      │
        └─────────┬────────────────────────────┘
                  │ REST + SSE/WebSocket
                  ▼
        ┌──────────────────────────────────────┐
        │  ETHAN WebUI  (thin client)          │
        │  ← fork UX Open WebUI (SvelteKit/Next)│
        │  - lib/api/models.ts, providers.ts   │
        │  - features/providers, features/models│
        │  - components/settings/ai-providers  │
        └──────────────────────────────────────┘
```

**Source de vérité unique** : les modèles découverts viennent du Provider Layer ; les **fiches custom** viennent du `ModelStore`. L'API expose un **catalogue agrégé unifié** (`/v1/models`). Il n'y a **qu'une** registry côté Core.

---

## 2. Fonctionnalités à récupérer d'Open WebUI

| Fonctionnalité OWUI | Pourquoi la récupérer | Source de vérité cible ETHAN |
|---|---|---|
| **Provider "Connections" modale** (AddConnectionModal) avec types (Ollama/OpenAI/Anthropic/Google/Azure/vLLM/LMStudio/OpenRouter/OpenAI-Compatible/Groq/AIML/Cloudflare/llama.cpp) | UX complète + validation en ligne | `interfaces/api/routers/providers.py` + `core/llm/provider_factory.py` |
| **OpenRouter config** (mode, routing, allow... ) | Gestion fine du routing OpenRouter | `core/llm/routing.yaml` + OWN adapter |
| **OpenAI-Compatible custom** (base_url override) | Providers privés/self-host | `core/llm/providers/openai_compatible.py` |
| **Model cards custom** : `base_model_id`, `params` (temp/top_p/max_tokens/etc), `meta` {capabilities, tags, profile_image_url, description}, `is_active`, `access_grants` | Personnalisation par modèle | `core/llm/model_store.py` ModelStore |
| **Model access control** (view_option created/shared, access_grants) | Partage/ACL par modèle | ModelStore `acl` + `core/auth` groups |
| **Sync models** (pull depuis provider) | Catalogue à jour | ProviderManager.list_models |
| **Toggle / Default model / Provider par défaut** | UX de sélection | ProviderManager.set_default_provider / ModelStore.is_active |
| **Healthcheck / status connexion provider** | Fiabilité | ProviderManager.test_connection + `status` dans describe |
| **Profils d'évaluation** (model profiles) | Benchmarking | `core/learning/evaluations.py` |
| **Suggérences de prompts** par défaut | Onboarding | core/config defaults |
| **Tracker coûts/latence** (token_usage, analytics) | Observabilité | `core/llm/tracker.py` + `core/metrics/analytics.py` |
| **Multi-provider fallback** via routing | Résilience | `core/llm/router.py` + selector |

---

## 3. Données à stocker (schémas unifiés)

### 3.1 Provider config (source de vérité `core/llm/store.py` → `ProviderStore`)
**Pas de secrets** (clés → `core/config/secrets.py`).

| Champ | Type | Source OWUI | Commentaire ETHAN |
|---|---|---|---|
| `provider_id` | str | connection key | PK `llm_providers` |
| `type` | enum (ollama,openai,anthropic,gemini,vllm,lmstudio,llamacpp,openai-compatible) | `type` connexion | enum validé factory |
| `enabled` | bool | enabled | ProviderManager |
| `base_url` | str | base_url | transport |
| `default_model` | str | default_model | |
| `display_name` | str | custom name | |
| `meta` | json | — | icon, order, tags UI |
| `routing` | json | openrouter config, allow... | routing.yaml override |
| `secrets_ref` | str | api_key (🔴 ici dans OWUI) | → `core/config/secrets.py` : `provider_id.api_key` |

> ⚠️ OWUI stocke `api_key` dans `PersistentConfig` (DB) — **violation** `.clinerules/secret.md`. Migration = les clés vivent dans `secrets.py` (env/Vault/Docker secrets) et sont injectées en mémoire par `ProviderManager._inject_secrets()`.

### 3.2 Model card (source de vérité `core/llm/model_store.py` → `ModelStore`)

| Champ | Type | Source OWUI (`models` table) | Commentaire ETHAN |
|---|---|---|---|
| `id` | uuid/str | id | uuid auto |
| `base_model_id` | str? | base_model_id | référence modèle découvert |
| `name` | str | name | |
| `provider` | str | — (déduit) | provider propriétaire du modèle |
| `params` | json | params (temperature, top_p, max_tokens, …) | ModelStore.params ✅ déjà présent |
| `meta.description` | str? | meta.description | ✅ |
| `meta.capabilities` | json? | meta.capabilities | ✅ ModelInfo.capabilities |
| `meta.tags` | list | meta.tags | → ModelStore.meta.tags |
| `meta.profile_image_url` | str? | meta.profile_image_url | → ModelStore.meta |
| `is_active` | bool | is_active | ✅ |
| `acl` | list | access_grants | ✅ ModelStore.acl (mapping groups/users + permission) |
| `created_at` / `updated_at` | iso/timestamp | created_at/updated_at | ✅ |

> 🟡 **Gap** : `ModelInfo` ETHAN n'a pas de `model` (nom technique envoyé au provider) ni `info`/tags. `ModelStore.meta` accepte `extra` → on y range tags/profile_image. Les cartes custom ET les modèles découverts sont **agrégés** dans `/v1/models`.

### 3.3 Modèles découverts (en mémoire / cache)

| Champ | Source |
|---|---|
| `id`, `provider` | `provider.list_models()` |
| `name`, `context_length`, `capabilities` | ModelInfo (provider) |
| `is_local`, `is_private`, `pricing`, `quality_score`, `avg_latency_ms` | `core/llm/tracker.py` + selector |
| `is_available` | ProviderManager healthcheck |

---

## 4. API nécessaires (ETHAN `interfaces/api`)

| Domaine | Endpoint | Méthode | Source de vérité |
|---|---|---|---|
| **Providers** | `/v1/providers` | GET | ProviderManager.list_providers |
|  | `/v1/providers` | POST (create connexion) | provider_factory + ProviderStore |
|  | `/v1/providers/default` | GET | ProviderStore.get_default |
|  | `/v1/providers/{id}/default` | PUT | set_default_provider |
|  | `/v1/providers/{id}` | PUT (toggle/enabled) | set_enabled |
|  | `/v1/providers/{id}/test` | POST (healthcheck) | test_connection |
|  | `/v1/providers/{id}/models` | GET | list_models |
|  | `/v1/providers/secrets` | GET/PUT (isolé) | core/config/secrets |
| **Models** | `/v1/models` | GET (agrégé discovered+custom) | ProviderManager.list_models + ModelStore.list_models |
|  | `/v1/models` | POST (custom card) | ModelStore.create_model |
|  | `/v1/models/{id}` | GET/PUT/DELETE | ModelStore |
|  | `/v1/models/{id}/toggle` | POST | ModelStore.toggle_model |
|  | `/v1/models/{id}/access` | PUT | ModelStore acl |
|  | `/v1/models/sync` | POST | ProviderManager.list_models → ModelStore |
|  | `/v1/models/defaults` | GET | core/config |
|  | `/v1/models/import` `/export` | POST/GET | ModelStore |
| **Chat** | `/v1/chat` | POST + SSE stream | ChatPipeline.chat_stream |
|  | `/v1/models/usage` | GET | tracker.py |

---

## 5. UI à réutiliser (Open WebUI = référence UX)

| Composant OWUI | Adaptation ETHAN WebUI (thin client) | Source de vérité consommée |
|---|---|---|
| `ChatControls.svelte` (température/top_p/max_tokens/live) | `features/assistant/components/chat-controls.tsx` | `/v1/chat` params |
| `ModelSelector.svelte` (pin + provider) | `components/shared/model-selector.tsx` | `/v1/models` + `/v1/providers/default` |
| `AddConnectionModal.svelte` (providers) | `features/providers/create-provider-modal.tsx` | `/v1/providers` POST |
| `SettingsModal.svelte` + settings/[tab] connections | `components/settings/ai-providers-section.tsx` + `/dashboard/settings` | `/v1/providers`, `/v1/config/connections` |
| workspace/models (create/edit) | `features/providers/` + use-models.ts | ModelStore |
| models list toggle/pin/export | `features/providers/hooks/use-models.ts` | `/v1/models` |
| OpenRouter config form | adapter (routage YAML) | `/v1/providers/{id}` routing |
| analytics tokens/usage | `features/providers/` usage | `/v1/models/usage` |

---

## 6. Fonctionnalités manquantes dans ETHAN Core (à ajouter)

| # | Fonctionnalité OWUI absente chez ETHAN | Action (MOVE-TO-CORE) |
|---|---|---|
| 1 | **OpenRouter provider** (routing/config `mode`, `allow`) | Ajouter `core/llm/providers/openrouter.py` + `routing.yaml` |
| 2 | **Azure provider** | Ajouter `core/llm/providers/azure.py` |
| 3 | **Google (Gemini) provider** | `core/llm/providers/gemini.py` (déjà listé mais absent du seed config) → activer |
| 4 | **Groq / AIML / Cloudflare / DeepSeek** | Ajouter providers openai-compatible |
| 5 | **Llama.cpp provider** | Ajouter `core/llm/providers/llamacpp.py` |
| 6 | **LMStudio provider** | `core/llm/providers/lmstudio.py` (déjà listé) → seed config |
| 7 | **Model `tags`** (UI filtrage) | Ajouter tags dans ModelStore.meta + `/v1/models/{id}/tags` |
| 8 | **Model `profile_image_url`** (icône) | → ModelStore.meta |
| 9 | **Model `info`** (schema openai) | → ModelInfo.metadata |
| 10 | **`model` technique** (envoyé au provider) | ModelInfo doit porter le nom technique → ajout champ `model` | 
| 11 | **Routing OpenRouter / multi-provider fallback config UI** | routing.yaml + UI | 
| 12 | **Provider status WebSocket** (realtime dispo) | core/events EventBus + `/v1/providers/{id}/status` WS | 

> Le reste (ProviderManager, ProviderStore, ModelStore, ModelInfo, registry, selector, tracker, secrets) **existe déjà** et est plus robuste qu'OWUI (PG+Redis, secrets isolés).

---

## 7. Schéma de données (unifié) — équivalent OWUI → ETHAN

```
OpenWebUI                              ETHAN Core (source de vérité)
────────────────────────────────────   ────────────────────────────────────
configs.py PersistentConfig            core/config/ (loader, schema, service, secrets)
  ├── connections (Ollama,OpenAI,…)   │   └── core/llm/providers/* (homogènes)
  └── tool/terminal servers           │       + ProviderStore (PG/Redis, NO secrets)
                                      │       + secrets.py (Vault/env) ← clés NEVER in DB
models.py Model                       core/llm/model_store.py (ModelStore)
  ├─ id/user_id/base_model_id/name     │   ├── id, base_model_id, name, provider, params,
  ├─ params (ModelParams)              │   ├── meta(tags, profile_image_url, description, capabilities),
  ├─ meta (capabilities/tags/img)      │   ├── is_active, acl, created/updated_at
  ├─ is_active                         │   └── CoreRecordStore (PG+Redis)
  ├─ access_grants                     │
  └─ created_at/updated_at             │   Modèles découverts → ModelInfo (en mémoire/cache)
                                      │   → agrégés dans /v1/models
routers/configs.py                    interfaces/api/routers/{providers,models}.py
  /connections, /models               /v1/providers, /v1/models, /v1/providers/{id}/test
routers/models.py                     core/llm/{provider_manager,registry,router,selector,tracker}
                                      (healthcheck, routing.yaml, LLMSelector, LLMRouter, tracker)
```

---

## 8. Stratégie de migration (3 phases — sans duplication)

### Phase A — Consolidation immédiate (les bases sont là)
- Les endpoints ETHAN `models.py` / `providers.py` exposent **déjà** le catalogue. ✅
- OWUI reste **indépendant** (référence) ; le futur WebUI consomme `/v1/models` + `/v1/providers`.

### Phase B — Alignement OWUI → ETHAN Core (features manquantes)
- Ajouter les **providers manquants** (OpenRouter, Azure, Gemini activé, Groq, Azure, llamacpp, DeepSeek) → **MOVE-TO-CORE** (un seul registry).
- Étendre `ModelInfo` (champ `model` technique, tags) + `ModelStore` (tags/image via meta) → garder `extra='allow'`.
- **`routing.yaml`** pour le fallback multi-provider (inspiré OpenRouter `mode`).
- WebUI fork: `features/providers` + `model-selector` consomment les nouveaux endpoints.

### Phase C — UX richness Open WebUI (thin)
- Fork des composants UX (AddConnectionModal, settings tabs, model cards, analytics usage) → Next.js.
- Aucune logique métier dans la UI : tout passe par `/v1/models` & `/v1/providers`.

### Risques & contre-mesures
- **Risque** : double registry si le backend OWUI forké est conservé → **interdit** ; le backend OWUI reste *référence indépendante*, jamais connecté au WebUI ETHAN.
- **Risque** : fuite de secrets → clés **toujours** dans `core/config/secrets.py`, jamais dans ProviderStore ni DB models.
- **Risque** : Provider offline → `circuit_breaker.py` + healthcheck + `is_available` dans ModelInfo pour masquer.

---

## 9. Conclusion — oui, Open WebUI est récupérable, mais comme UX uniquement

- ETHAN Core possède **déjà les fondations** : ProviderManager (healthcheck, secrets injection, PG/Redis store), ModelStore (custom cards + ACL), ModelInfo (with scoring & capabilities), `routing.yaml`/selector/tracker.
- Open WebUI **apporte** : le catalogue complet des *providers* (OpenRouter, Azure, Gemini, Groq…), la richesse UX (modales connexions, healthcheck en ligne, profils évaluation, analytics usage, fallback routing).
- **Plan** : migrer les providers manquants + étendre ModelInfo/ModelStore (Phase B), puis forker l'UX dans le thin WebUI (Phase C). **Une seule source de vérité** = `core/llm/`. Ollama reste indépendant sur l'hôte et est simplement **découvert** par le Provider Layer.
