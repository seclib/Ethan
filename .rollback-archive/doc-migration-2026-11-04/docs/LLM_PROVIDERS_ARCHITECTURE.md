# Architecture Multi-Providers LLM — ETHAN

**Auteur** : Architecture Senior
**Date** : 2026-08-02
**Statut** : Proposition — Pré-implémentation
**Séparation respectée** : `core` / `interfaces` / plugins

---

## 1. État Actuel

### 1.1 Infrastructure LLM déjà en place

ETHAN possède **déjà** une excellente base dans `core/llm/` :

| Fichier | Rôle |
|---------|------|
| `core/llm/types.py` | Dataclasses `ChatMessage`, `ChatResponse`, `ModelInfo`, `LLMRequirements`, `ScoredModel` |
| `core/llm/providers/base.py` | Interface abstraite `LLMProvider` |
| `core/llm/registry.py` | `LLMProviderRegistry` — catalogue de providers |
| `core/llm/selector.py` | `LLMSelector` — scoring sur 6 critères (qualité, coût, vitesse, confidentialité, contexte, dispo) |
| `core/llm/client.py` | `LLMClient` — interface unifiée avec circuit breaker par provider |
| `core/llm/router.py` | `LLMRouter` — catégories de tâches (reasoning, code, fast, local) |
| `core/llm/manager.py` | `LLMManager` — orchestrateur façade |
| `core/llm/tracker.py` | `CostTracker` — suivi des coûts |

**Providers déjà implémentés** dans `core/llm/providers/` :

| Provider | Fichier | Statut |
|----------|---------|--------|
| Ollama local | `ollama.py` | ✅ Implémenté |
| OpenAI API | `openai.py` | ✅ Implémenté |
| Anthropic Claude | `anthropic.py` | ✅ Implémenté |
| vLLM local | `vllm.py` | ✅ Implémenté |
| llama.cpp | `llamacpp.py` | ✅ Implémenté |
| LM Studio | `lmstudio.py` | ✅ Implémenté |
| Gemini | `gemini.py` | ✅ Implémenté |

### 1.2 Problèmes identifiés

#### P1 — Le LLMManager n'est jamais instancié
```
Recherche : LLMManager → 1 seul résultat (sa définition dans manager.py)
```
Le `core/llm/manage.py` existe mais **n'est branché nulle part** :
- Pas dans `core/ethan_bootstrap.py` (le kernel ne l'importe pas)
- Pas dans `interfaces/api/main.py` (l'API ne l'instancie pas)
- Pas dans `core/cognition/reasoner/llm.py` (le Reasoner a `TODO: Intégrer le LLM provider`)

**Conséquence** : Le chat `/v1/chat` retourne `[ECHO]`, le Reasoner simule les réponses, aucun vrai LLM n'est appelé.

#### P2 — Double système de providers
Il y a **deux** systèmes de providers en conflit :
1. `core/llm/providers/` — le système moderne avec `LLMProvider`, `LLMManager`
2. `core/providers/providers/` — un **ancien** système avec `ReasoningProvider`, `ProviderRegistry` (auto-register via env vars)

**Risque** : Confusion, doublons, maintenance difficile.

#### P3 — L'API retourne des données statiques en dur
- `interfaces/api/routers/v1.py` : `_default_providers` (liste en dur), `_default_settings` (in-memory)
- La page WebUI "Providers" appelle `/api/v1/providers` qui retourne des données codées en dur
- La page "Settings" édite des valeurs in-memory perdues au redémarrage

#### P4 — Pas de persistence des paramètres
- Les settings LLM sont stockés dans un dict in-memory (`_default_settings`)
- `core/config/loader.py` charge les YAML/env mais **n'a pas de section providers**
- `core/config/schema.py` : `AgentConfig` a `model`/`provider`, mais pas de blocs de config providers
- `core/config/secrets.py` : charge seulement `OPENAI_API_KEY` et `ANTHROPIC_API_KEY`

#### P5 — Le LLM n'est pas branché au flux cognitif
Le flux actuel est : `CLI/WebUI → API /v1/message → NATS → Kernel → Modules`
Mais :
- Le module Executive crée un goal, ne fait **pas d'appel LLM**
- Le Reasoner (`core/cognition/reasoner/llm.py`) a un `_call_llm()` qui lève `NotImplementedError`
- Le chat CLI passe par `/v1/message` (event-driven) mais personne ne génère la réponse

---

## 2. Architecture Cible

### 2.1 Principe directeur

Respecter les règles d'architecture existantes :
```
interfaces (WebUI) → API (NATS publish) → Kernel (orchestrateur) → Modules (execution)
                        ↑                              ↓
                    LLMManager (core/llm) ←── sélection par requirements
```

### 2.2 Schéma cible

```
┌──────────────────────────────────────────────────────────────────┐
│                      CORE (couche cognitive)                     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                    core/llm/                            │    │
│  │                                                        │    │
│  │  ┌──────────┐   ┌──────────────┐   ┌───────────────┐  │    │
│  │  │LLMManager│──▶│LLMProviderReg│──▶│  Providers    │  │    │
│  │  │ (facade) │   │ istry        │   │  ollama       │  │    │
│  │  └────┬─────┘   └──────┬───────┘   │  openai       │  │    │
│  │       │                │           │  anthropic    │  │    │
│  │  ┌────▼─────┐   ┌──────▼───────┐   │  vllm         │  │    │
│  │  │LLMClient │──▶│LLMSelector   │   │  llamacpp     │  │    │
│  │  │ cb/prov  │   │ + LLMRouter  │   │  + autres     │  │    │
│  │  └────┬─────┘   └──────────────┘   └───────────────┘  │    │
│  │       │                                                │    │
│  └───────┼────────────────────────────────────────────────┘    │
│          │                                                     │
│  ┌───────▼───────────────────────────────────────────────┐     │
│  │ Modules cognitifs (Reasoner, Planner, Executive)      │     │
│  │ → utilisent LLMManager via dépendance injectée       │     │
│  └───────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Config : core/config/schema.py + secrets.py            │   │
│  │ Stockage : Redis (live) + PostgreSQL (persistant)      │   │
│  └────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                          ▲
        NATS publish/subscribe │
                          │
┌──────────────────────────────────────────────────────────────────┐
│                     INTERFACES (HTTP)                            │
│                                                                  │
│  api/  →  /v1/chat, /v1/providers, /v1/settings                  │
│  webui →  Proxy Next.js → API                                    │
└──────────────────────────────────────────────────────────────────┘
```

### 2.3 Sélection dynamique

Le `LLMSelector` existe déjà. La sélection dynamique se fera via `LLMRequirements` :

```python
requirements = LLMRequirements(
    task_type="chat",
    preferred_providers=user_prefs["preferred_providers"],  # ["ollama", "openai"]
    require_local=user_prefs.get("prefer_local", False),
    max_cost=user_prefs.get("budget_usd"),
    context_length=user_prefs.get("context_length"),
)
response = await llm_manager.chat(messages=messages, requirements=requirements)
```

---

## 3. Fichiers Concernés

### 3.1 Modifications `core/`

| Fichier | Modification | Raison |
|---------|-------------|--------|
| `core/llm/manager.py` | Réutiliser tel quel (déjà complet) | Facade existante |
| `core/llm/client.py` | Ajouter paramètre `provider_name` pour forcer un provider | Sélection dynamique |
| `core/llm/providers/base.py` | Ajouter méthode optionnelle `test_connection()` | Healthcheck réel |
| `core/config/schema.py` | Ajouter `ProviderConfig` et `ProvidersConfig` | Persistance config |
| `core/config/loader.py` | Mapper les clés `providers.*` dans le schéma | Chargement config |
| `core/config/secrets.py` | Étendre aux clés `VLLM_API_KEY`, `LLAMACPP_URL`, etc. | Secrets |
| `core/ethan_bootstrap.py` | Instancier `LLMManager`, injecter dans le kernel | Branchement réel |
| `core/kernel.py` | Ajouter attribut `llm` optionnel | Distribution aux modules |
| `core/cognition/reasoner/llm.py` | Implémenter `_call_llm()` via `LLMManager` | Réel raisonnement |
| `core/modules/` | Recevoir `LLMManager` dans le contexte | Accès LLM modules |

Nouveau fichier :
| Fichier | Rôle |
|---------|------|
| `core/llm/factory.py` | Factory `create_providers_from_config()` |

### 3.2 Modifications `interfaces/api/`

| Fichier | Modification |
|---------|-------------|
| `interfaces/api/main.py` | Instancier `LLMManager` dans le lifespan, le passer aux routers |
| `interfaces/api/routers/v1.py` | Brancher `/v1/chat`, `/v1/providers`, `/v1/settings` sur le LLMManager + ConfigStore |
| `interfaces/api/routers/v1_providers.py` (nouveau) | Router dédié providers (GET/PUT/POST, healthcheck) |
| `interfaces/api/routers/v1_models.py` (nouveau) | Lister + sélectionner un modèle |
| `interfaces/api/deps.py` (nouveau) | Dépendances FastAPI (`get_llm_manager`, `get_config_store`) |

### 3.3 Modifications `interfaces/webui/`

| Fichier | Modification |
|---------|-------------|
| `src/core/api/api-client.ts` | Ajouter `providersService`, `modelsService`, enrichir `settingsService` |
| `src/app/(dashboard)/providers/page.tsx` | Lister dynamiquement les providers depuis l'API, config par provider |
| `src/app/(dashboard)/settings/page.tsx` | Section LLM : select provider + select model |
| Nouveau : `src/components/providers/provider-form.tsx` | Formulaire de configuration provider |
| Nouveau : `src/features/providers/hooks/use-providers.ts` | Hook React Query |

### 3.4 Nouveaux fichiers de deployment

| Fichier | Rôle |
|---------|------|
| `deploy/llm.env.example` | Template variables d'environnement providers |
| `docs/LLM_PROVIDERS_GUIDE.md` | Guide utilisateur : configurer les providers |

---

## 4. Plan de Modification (par phases)

### Phase 1 — Brancher le LLMManager (Priorité haute, ~1 jour)

**Objectif** : Le système de providers existant devient utilisable.

1. **Créer `core/llm/factory.py`** :
   ```python
   def create_providers_from_config(config: ConfigSchema, secrets: Secrets) -> list[LLMProvider]:
       providers = []
       for name, pconf in config.runtime.providers.items():
           if not pconf.enabled:
               continue
           if name == "ollama":
               providers.append(OllamaProvider(base_url=pconf.base_url))
           elif name == "openai":
               providers.append(OpenAIProvider(api_key=pconf.api_key))
           elif name == "anthropic":
               providers.append(AnthropicProvider(api_key=pconf.api_key))
           # ... vllm, llamacpp, lmstudio
       return providers
   ```

2. **Étendre `core/config/schema.py`** :
   ```python
   @dataclass
   class ProviderConfig:
       name: str
       enabled: bool = False
       base_url: str = ""
       api_key: str | None = None  # Jamais loggé, stocké dans secrets
       default_model: str = ""
       options: dict[str, Any] = field(default_factory=dict)

   @dataclass
   class RuntimeConfig:
       # ... existant ...
       providers: dict[str, ProviderConfig] = field(default_factory=dict)
   ```

3. **Modifier `core/ethan_bootstrap.py`** :
   ```python
   from core.llm.manager import LLMManager
   from core.llm.factory import create_providers_from_config

   # Après création du kernel :
   llm_manager = LLMManager()
   providers = create_providers_from_config(config, secrets)
   for p in providers:
       llm_manager.register_provider(p)
   await llm_manager.initialize()
   kernel.llm = llm_manager
   ```

4. **Modifier `core/kernel.py`** : ajouter `self.llm = None` et le passer aux modules.

### Phase 2 — API réelle pour providers/settings/models (Priorité haute, ~1 jour)

**Objectif** : La WebUI peut lister/configurer dynamiquement les providers.

1. **Créer `interfaces/api/routers/v1_providers.py`** :
   - `GET /v1/providers` → liste depuis le config store (pas de données en dur)
   - `PUT /v1/providers/{name}` → active/désactive, met à jour la config
   - `POST /v1/providers/{name}/test` → appelle `test_connection()`
   - `GET /v1/providers/{name}/models` → liste des modèles disponibles

2. **Créer `interfaces/api/routers/v1_models.py`** :
   - `GET /v1/models` → agrège les modèles de tous les providers actifs
   - `GET /v1/models?provider=ollama` → filtre par provider
   - `PUT /v1/models/default` → définit le modèle par défaut

3. **Modifier `interfaces/api/routers/v1.py`** :
   - Supprimer `_default_providers` et `_default_settings`
   - Brancher `/v1/settings` sur le ConfigStore persistant
   - Brancher `/v1/chat` sur `LLMManager.chat()`

4. **Créer `interfaces/api/config_store.py`** :
   - Wrapper Redis + PostgreSQL pour persister les settings utilisateur
   - Clés : `ethan:settings:{user_id}`, `ethan:providers:{provider_name}`

### Phase 3 — Persistance des paramètres utilisateur (Priorité moyenne, ~1 jour)

1. **Stocker dans PostgreSQL** une table `user_settings` :
   ```sql
   CREATE TABLE IF NOT EXISTS user_settings (
       user_id    TEXT PRIMARY KEY,
       llm_config JSONB NOT NULL DEFAULT '{}',
       updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
   );
   ```

2. **Cache dans Redis** avec TTL 60s pour un accès rapide.

3. **`AgentConfig`** étendu : `default_provider`, `default_model`, `temperature`, `max_tokens`.

### Phase 4 — Branchage du flux cognitif (Priorité moyenne, ~1-2 jours)

1. **Implémenter `_call_llm()`** dans `core/cognition/reasoner/llm.py` :
   ```python
   async def _call_llm(self, prompt, constraints):
       if not self._llm:
           raise RuntimeError("LLM client not configured")
       response = await self._llm.chat(
           messages=[ChatMessage(role="system", content=prompt)],
           requirements=LLMRequirements(task_type="reasoning"),
       )
       return json.loads(response.content)
   ```

2. **Injecter `LLMManager`** dans les modules via `ModuleContext`.

3. **Brancher le chat `/v1/chat`** sur le flux event-driven :
   - Le chat POST crée un event `ethan.intent.user`
   - Le Reasoner consomme l'event, appelle le LLM, publie la réponse
   - Un subscriber `interfaces/api` écoute la réponse et la retourne au client

### Phase 5 — Extension par plugins (Priorité basse, ~2 jours)

1. **Plugin SDK** `plugins/sdk/llm_provider.py` :
   ```python
   class PluginLLMProvider(LLMProvider):
       """Interface pour plugin externe."""
       pass
   ```

2. **Loader** `core/llm/plugin_loader.py` :
   - Scanne `plugins/` pour les classes `LLMProvider`
   - Les instancie avec la config du provider
   - Les enregistre dans `LLMProviderRegistry`

3. **Manifest** `plugin.yaml` :
   ```yaml
   name: my-llm-provider
   type: llm-provider
   entrypoint: provider.py:MyProvider
   ```

---

## 5. Gestion des Secrets

Conforme à `.clinerules/secret.md` :

| Secret | Variable | Source |
|--------|----------|--------|
| OpenAI API Key | `OPENAI_API_KEY` | Vault / env / Docker secrets |
| Anthropic API Key | `ANTHROPIC_API_KEY` | Vault / env / Docker secrets |
| vLLM (si clé) | `VLLM_API_KEY` | Vault / env |
| llama.cpp | pas de clé | URL locale |
| Ollama | pas de clé | URL locale |

**Jamais** stocké dans : code, git, logs, events, memory.

---

## 6. Compatibilité & Non-régression

### Ce qui ne change PAS
- `core/llm/types.py` et `core/llm/providers/base.py` : interface stable
- `core/kernel.py` : le kernel reste orchestrateur pur (ajout d'un attribut optionnel)
- Flux event-driven via NATS : inchangé
- La WebUI : les URLs `/api/*` restent les mêmes

### Ce qui doit être déprécié proprement
- `core/providers/providers/` (ancien système) → migration vers `core/llm/providers/`
- `interfaces/api/routers/v1.py` : `_default_providers`, `_default_settings` → suppression après validation

### Règle d'import (pyproject.toml RÈGLE 3)
```
core.bus n'importe PAS core.llm  ✅ respecté
core.llm n'importe PAS interfaces ✅ respecté
interfaces n'importe QUE core ✅ respecté
```

---

## 7. Résumé des Actions

| # | Action | Fichiers | Priorité |
|---|--------|----------|----------|
| 1 | Factory providers | `core/llm/factory.py` (nouveau) | Haute |
| 2 | Config providers dans schema | `core/config/schema.py` | Haute |
| 3 | Brancher LLMManager dans bootstrap | `core/ethan_bootstrap.py` | Haute |
| 4 | Injecter LLM dans kernel | `core/kernel.py` | Haute |
| 5 | Router providers dynamique | `interfaces/api/routers/v1_providers.py` | Haute |
| 6 | Router models | `interfaces/api/routers/v1_models.py` | Haute |
| 7 | Branchage chat réel | `interfaces/api/routers/v1.py` | Haute |
| 8 | ConfigStore persistant | `interfaces/api/config_store.py` | Moyenne |
| 9 | Table user_settings | SQL migration | Moyenne |
| 10 | Implémenter _call_llm du Reasoner | `core/cognition/reasoner/llm.py` | Moyenne |
| 11 | Plugin SDK LLM provider | `plugins/sdk/llm_provider.py` | Basse |
| 12 | WebUI provider form | `interfaces/webui/src/components/providers/` | Moyenne |
| 13 | Déprécier `core/providers/` ancien | Documentation + suppression guide | Basse |

---

## 8. Critères d'Acceptation

- [ ] `./ethan up` → 7/7 healthy
- [ ] `GET /v1/providers` → liste dynamique (Ollama, OpenAI, Anthropic, vLLM, llama.cpp)
- [ ] `GET /v1/models?provider=ollama` → modèles réels d'Ollama
- [ ] `PUT /v1/providers/ollama` → active/désactive proprement
- [ ] `POST /v1/chat` avec Ollama → vraie réponse LLM
- [ ] Settings persistés en base PostgreSQL (survit au redémarrage)
- [ ] Sang secrets dans les logs : aucune clé API en clair
- [ ] `pytest tests/` → aucune régression (import-linter RÈGLE 3 respectée)