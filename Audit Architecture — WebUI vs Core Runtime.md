## Audit Architecture — WebUI vs Core/Runtime

J'ai analysé en profondeur la structure actuelle. Voici le diagnostic complet et le plan de création du rapport.

---

### Constat majeur : doublons internes au Core

Avant même d'analyser WebUI, j'ai identifié **deux systèmes de providers LLM parallèles dans le Core** :

1. **`core/llm/`** — système moderne et complet :
   - `LLMProviderRegistry`, `LLMSelector`, `LLMClient`, `LLMRouter`
   - `ProviderManager` (persistance via `ProviderStore` PostgreSQL/Redis)
   - `provider_factory.py`, `store.py`, `tracker.py`
   - Providers : `ollama.py`, `openai.py`, `anthropic.py`, `vllm.py`, `gemini.py`, `llamacpp.py`, `lmstudio.py`, `openai_compatible.py`

2. **`core/providers/`** — ancien système legacy :
   - `ReasoningProvider` (interface abstraite)
   - `ProviderRegistry` (simple dict)
   - Providers : `ollama.py`, `openai.py`, `anthropic.py`
   - **Importe depuis `core.llm`** (le `__init__.py` définit ses propres `ChatMessage`, `ChatResponse`, `ModelInfo`, `LLMProvider`, `ProviderRegistry`)

3. **`core/llm/__init__.py`** définit ses propres types (`ChatMessage`, `ChatResponse`, `ModelInfo`, `LLMProvider`, `ProviderRegistry`) **en plus** de `core/llm/types.py` et `core/llm/registry.py` — doublon interne.

---

### Tableau d'audit complet

| Fonction | WebUI | Core | Statut | Action |
|---|---|---|---|---|
| **Ollama Provider** | Oui (via API) | Oui (2× : `core/llm/providers/` + `core/providers/providers/`) | **doublon Core** | Fusionner vers `core/llm/providers/` |
| **OpenAI Provider** | Oui (via API) | Oui (2×) | **doublon Core** | Fusionner vers `core/llm/providers/` |
| **Anthropic Provider** | Oui (via API) | Oui (2×) | **doublon Core** | Fusionner vers `core/llm/providers/` |
| **Provider Manager** | Non (proxy API) | Oui (`ProviderManager`) | **OK** | WebUI = client pur |
| **RAG / Documents** | Oui (page placeholder) | **Non** (pas de `core/rag/`) | **manquant** | Créer `core/rag/` |
| **Memory** | Oui (services API) | Oui (`core/memory/`, `core/facts/`) | **OK** | WebUI = client pur |
| **Planner** | Oui (page + hooks) | Oui (3× : `core/planner/`, `core/modules/planner/`, `core/executive/`) | **doublon Core** | Unifier vers `core/planner/` |
| **Goals** | Oui (hooks + page) | Oui (3× : `core/goals/`, `core/planner/goal_manager.py`, `core/executive/goal_manager.py`) | **doublon Core** | Unifier vers `core/goals/` |
| **Agents** | Oui (page + hooks) | **Partiel** (`core/modules/base.py` définit `Agent`, mais `core/agents/` n'existe pas) | **incomplet** | Créer `core/agents/` |
| **Skills** | Oui (page + services) | Oui (`core/skills/`) | **OK** | WebUI = client pur |
| **Knowledge** | Oui (page + services) | **Partiel** (`core/facts/` couvre une partie) | **incomplet** | Migrer vers `core/knowledge/` |
| **Configuration** | Oui (settings page) | Oui (`core/config/`) | **OK** | WebUI = client pur |
| **Authentication** | Oui (login/register) | Oui (`core/auth/` RBAC) | **OK** | WebUI = client pur |
| **Settings** | Oui (services API) | **Partiel** (in-memory dans `interfaces/api/routers/v1.py`) | **incomplet** | Migrer vers `core/config/` |
| **Plugins** | Oui (page + services) | Oui (`plugins/`) | **OK** | WebUI = client pur |
| **Flux/Events** | Oui (page + services) | Oui (`core/bus/`, `core/events/`) | **OK** | WebUI = client pur |
| **Missions** | Oui (page + services) | **Non** (in-memory dans `interfaces/api/routers/v1.py`) | **manquant** | Créer `core/missions/` |
| **Chat** | Oui (assistant) | Oui (`core/llm/`) | **OK** | WebUI = client pur |

---

### Problème critique : `interfaces/api/routers/v1.py`

Ce fichier contient **toute la logique métier en mémoire** :
- Agents, Goals, Missions, Skills, Knowledge, Memory, Settings, Providers, Plugins
- Stockage in-memory (`MemoryStore` class) — **perdu au redémarrage**
- Providers hardcodés (`_default_providers`), plugins hardcodés (`_default_plugins`)
- Settings hardcodés (`_default_settings`)

C'est une **violation directe de l'architecture ETHAN** : la logique métier est dans l'interface API, pas dans le Core.

---

### Classification

**A. Doit rester dans WebUI (UI pure) :**
- Composants, pages, navigation, graphiques, thèmes
- Hooks React (useAgents, useGoals, etc.) — ce sont des clients API
- Services WebUI (settings.service.ts, etc.) — ce sont des clients API

**B. Doit appartenir au Core :**
- `interfaces/api/routers/v1.py` → toute la logique métier in-memory doit migrer vers `core/`
- `core/providers/` → fusionner dans `core/llm/providers/`
- `core/llm/__init__.py` → types dupliqués à supprimer (utiliser `core/llm/types.py`)
- `core/planner/` + `core/modules/planner/` + `core/executive/` → unifier
- `core/goals/` + `core/planner/goal_manager.py` + `core/executive/goal_manager.py` → unifier
- Créer `core/rag/`, `core/agents/`, `core/missions/`, `core/knowledge/`

**C. Doit être partagé via API/Event :**
- Tous les endpoints REST dans `interfaces/api/` (déjà le cas)
- Les événements NATS via `core/bus/`

---

### Plan de création du rapport

Je propose de créer `docs/architecture/webui-core-audit.md` avec :

1. **Résumé exécutif** — constat principal
2. **Tableau d'audit complet** (comme ci-dessus)
3. **Analyse détaillée par domaine** — pour chaque fonctionnalité : état actuel, doublons, source de vérité, recommandation
4. **Classification A/B/C** — ce qui reste en WebUI, ce qui va au Core, ce qui est partagé
5. **Plan de migration contrôlée** — par phases, sans casser le code existant
6. **Priorités** — P0 (doublons Core), P1 (logique métier dans l'API), P2 (création de modules manquants)

---

### Prochaines étapes

Pour créer ce rapport, je dois passer en **ACT MODE** pour :
1. Créer le répertoire `docs/architecture/`
2. Rédiger le rapport complet `webui-core-audit.md`
3. Vérifier le contenu

Le rapport sera un document d'analyse uniquement — **aucune modification de code** ne sera effectuée.

Passez en **ACT MODE** pour que je crée le rapport.