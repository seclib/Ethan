# ETHAN — Plan d'Unification LLM

**Date** : 2026-03-08  
**Auteur** : LLM Unification Agent  
**Statut** : Proposition — aucune modification de code effectuée  
**Portée** : `core/llm/`, `core/providers/`, `interfaces/api/`, `interfaces/cli/`

---

## 1. Résumé Exécutif

ETHAN possède actuellement **deux systèmes de providers LLM parallèles** :

1. **`core/llm/`** — système moderne et complet (8 providers, registry, selector, router, client, manager, provider_manager, store, factory, tracker)
2. **`core/providers/`** — système legacy orphelin (3 providers, interface `ReasoningProvider`, registry simple)

**Aucun fichier externe n'importe `core.providers`** — c'est un système orphelin qui importe lui-même depuis `core.llm`.

De plus, **`core/llm/__init__.py`** définit ses propres types (`ChatMessage`, `ChatResponse`, `ModelInfo`, `LLMProvider`, `ProviderRegistry`) qui dupliquent ceux de `core/llm/types.py` et `core/llm/registry.py`.

**Objectif** : Créer une seule architecture LLM officielle basée sur `core/llm/`, en préservant toutes les fonctionnalités uniques des deux systèmes.

---

## 2. Comparaison des Systèmes

### 2.1 Architecture `core/llm/` (système principal)

```
core/llm/
├── __init__.py              # Réexports + types dupliqués (à nettoyer)
├── types.py                 # Types complets (TaskType, LLMRequirements, ModelInfo, ScoredModel, ChatMessage, ChatResponse, UsageStats)
├── registry.py              # LLMProviderRegistry (catalogue providers + modèles)
├── selector.py              # LLMSelector (score composite 6 critères)
├── router.py                # LLMRouter (catégories : reasoning, code, fast, local)
├── client.py                # LLMClient (circuit breaker par provider, fallback)
├── manager.py               # LLMManager (orchestration)
├── provider_manager.py      # ProviderManager (persistance, healthcheck, activation, default)
├── provider_factory.py      # create_provider_from_config (8 types supportés)
├── store.py                 # ProviderStore (PostgreSQL + Redis)
├── tracker.py               # CostTracker
├── routing.yaml             # Configuration de routage
└── providers/
    ├── base.py              # LLMProvider (interface abstraite + test_connection + initialize)
    ├── ollama.py            # OllamaProvider (local)
    ├── openai.py            # OpenAIProvider (cloud)
    ├── anthropic.py         # AnthropicProvider (cloud)
    ├── vllm.py              # VLLMProvider (local/serveur)
    ├── llamacpp.py          # LlamaCppProvider (local)
    ├── lmstudio.py          # LMStudioProvider (local)
    ├── gemini.py            # GeminiProvider (cloud)
    └── openai_compatible.py # OpenAICompatibleProvider (générique)
```

### 2.2 Architecture `core/providers/` (système legacy)

```
core/providers/
├── __init__.py              # ReasoningProvider (interface abstraite) + ProviderRegistry (simple dict)
└── providers/
    ├── ollama.py            # OllamaProvider (importe depuis core.llm)
    ├── openai.py            # OpenAIProvider (importe depuis core.llm)
    └── anthropic.py         # AnthropicProvider (importe depuis core.llm)
```

### 2.3 Comparaison des interfaces

| Aspect | `core/llm/providers/base.py` | `core/providers/__init__.py` |
|---|---|---|
| Interface | `LLMProvider` (ABC) | `ReasoningProvider` (ABC) |
| Méthodes | `chat`, `chat_stream`, `embed`, `list_models`, `test_connection`, `initialize` | `reason`, `embed`, `health_check` |
| Attributs | `name`, `default_model` (class attrs) | — |
| Registry | `LLMProviderRegistry` (avec modèles) | `ProviderRegistry` (simple dict) |
| Types | `core/llm/types.py` | Types définis dans `core/llm/__init__.py` |

**Conclusion** : `core/providers/` est un système **incomplet et redondant**. L'interface `ReasoningProvider` est moins riche que `LLMProvider` (pas de streaming, pas de list_models, pas de test_connection).

---

## 3. Fonctionnalités Uniques à Préserver

### 3.1 Fonctionnalités uniques de `core/providers/` (legacy)

| # | Fonctionnalité | Fichier | Description |
|---|---|---|---|
| 1 | `pull_model()` | `core/providers/providers/ollama.py` | Pull de modèles depuis le registry Ollama (`/api/pull`) |
| 2 | `close()` | `core/providers/providers/ollama.py`, `openai.py`, `anthropic.py` | Fermeture propre du client HTTP |
| 3 | `base_url` personnalisé | `core/providers/providers/openai.py` | Support d'un endpoint OpenAI alternatif |
| 4 | Auto-registration via env | `core/providers/providers/openai.py`, `anthropic.py` | Enregistrement automatique si `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` est définie |
| 5 | Modèles Anthropic récents | `core/providers/providers/anthropic.py` | `claude-sonnet-4-20250514`, `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, `claude-3-haiku-20240307` |
| 6 | Endpoint `/api/embed` | `core/providers/providers/ollama.py` | Utilise le nouvel endpoint Ollama (`/api/embed`) au lieu de `/api/embeddings` |
| 7 | `max_tokens` par défaut 4096 | `core/providers/providers/anthropic.py` | Plus généreux que le 1024 de `core/llm/providers/anthropic.py` |

### 3.2 Fonctionnalités uniques de `core/llm/providers/` (principal)

| # | Fonctionnalité | Fichier | Description |
|---|---|---|---|
| 1 | `test_connection()` | `base.py` | Test de connexion via `list_models()` |
| 2 | `initialize()` hook | `base.py` | Initialisation asynchrone du client |
| 3 | `OpenAICompatibleProvider` | `openai_compatible.py` | Provider générique pour LiteLLM, OpenRouter, etc. |
| 4 | `GeminiProvider` | `gemini.py` | Support Google Gemini avec streaming |
| 5 | `VLLMProvider` | `vllm.py` | Support vLLM (local/serveur) |
| 6 | `LlamaCppProvider` | `llamacpp.py` | Support llama.cpp (local) |
| 7 | `LMStudioProvider` | `lmstudio.py` | Support LM Studio (local) |
| 8 | `test_connection()` surchargé | `openai_compatible.py` | Test réel avec initialisation automatique |
| 9 | `LLMSelector` | `selector.py` | Score composite 6 critères (qualité, coût, vitesse, confidentialité, contexte, disponibilité) |
| 10 | `LLMRouter` | `router.py` | Routage par catégorie (reasoning, code, fast, local) |
| 11 | `LLMClient` | `client.py` | Circuit breaker par provider + fallback automatique |
| 12 | `ProviderManager` | `provider_manager.py` | Persistance PostgreSQL/Redis, healthcheck, activation, provider par défaut |
| 13 | `ProviderStore` | `store.py` | Persistance config (sans clés API) |
| 14 | `CostTracker` | `tracker.py` | Suivi des coûts |

---

## 4. Plan de Migration

### Phase 0 — Nettoyage de `core/llm/__init__.py`

**Objectif** : Supprimer les types dupliqués de `core/llm/__init__.py` et les remplacer par des réexports depuis `core/llm/types.py` et `core/llm/registry.py`.

**Avant** :
```python
# core/llm/__init__.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator

@dataclass
class ChatMessage: ...  # DOUBLON avec types.py

@dataclass
class ChatResponse: ...  # DOUBLON avec types.py

@dataclass
class ModelInfo: ...  # DOUBLON avec types.py

class LLMProvider(ABC): ...  # DOUBLON avec providers/base.py

class ProviderRegistry: ...  # DOUBLON avec registry.py

registry = ProviderRegistry()  # DOUBLON avec registry.py

def get_provider(name=None): ...  # DOUBLON avec registry.py
```

**Après** :
```python
# core/llm/__init__.py
from core.llm.types import ChatMessage, ChatResponse, ModelInfo, LLMRequirements, ScoredModel, TaskType, UsageStats
from core.llm.registry import LLMProviderRegistry, registry, get_provider
from core.llm.providers.base import LLMProvider
from core.llm.provider_manager import ProviderManager
from core.llm.provider_factory import create_provider_from_config, create_default_providers
from core.llm.store import ProviderStore

__all__ = [
    "ChatMessage", "ChatResponse", "ModelInfo", "LLMRequirements", "ScoredModel", "TaskType", "UsageStats",
    "LLMProviderRegistry", "registry", "get_provider",
    "LLMProvider",
    "ProviderManager", "create_provider_from_config", "create_default_providers", "ProviderStore",
]
```

**Risque** : Faible — les types sont identiques, les réexports préservent la compatibilité.

---

### Phase 1 — Fusion des améliorations dans `core/llm/providers/`

**Objectif** : Transférer les fonctionnalités uniques de `core/providers/` vers `core/llm/providers/`.

#### 1.1 `core/llm/providers/ollama.py`

Ajouter :
- `pull_model(model: str) -> bool` — pull de modèles depuis le registry Ollama
- `close()` — fermeture propre du client
- Utiliser `/api/embed` (nouveau endpoint) au lieu de `/api/embeddings`

```python
async def pull_model(self, model: str) -> bool:
    """Pull a model from Ollama registry."""
    if not self._client:
        return False
    payload = {"name": model, "stream": False}
    response = await self._client.post(
        f"{self._base_url}/api/pull",
        json=payload,
    )
    return response.is_success

async def close(self) -> None:
    """Ferme le client HTTP."""
    if self._client:
        await self._client.aclose()
```

#### 1.2 `core/llm/providers/openai.py`

Ajouter :
- Support de `base_url` personnalisé dans le constructeur
- `close()` — fermeture propre du client
- Auto-registration via `OPENAI_API_KEY` (optionnel, à la fin du fichier)

```python
def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
    self._api_key = api_key
    self._base_url = base_url
    self._client = None

async def initialize(self) -> None:
    try:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
        logger.info("OpenAI provider initialized")
    except ImportError:
        logger.warning("openai package not installed")

async def close(self) -> None:
    """Ferme le client."""
    if self._client:
        await self._client.close()
```

#### 1.3 `core/llm/providers/anthropic.py`

Ajouter :
- Modèles récents (`claude-sonnet-4-20250514`, `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, `claude-3-haiku-20240307`)
- `max_tokens` par défaut 4096 (au lieu de 1024)
- `close()` — fermeture propre du client

```python
async def list_models(self) -> list[ModelInfo]:
    return [
        ModelInfo(id="claude-sonnet-4-20250514", provider=self.name, name="Claude Sonnet 4", context_length=200000, quality_score=0.95, avg_latency_ms=1500.0, capabilities=["chat", "code", "reasoning"]),
        ModelInfo(id="claude-3-5-sonnet-20241022", provider=self.name, name="Claude 3.5 Sonnet", context_length=200000, quality_score=0.93, avg_latency_ms=1500.0, capabilities=["chat", "code", "reasoning"]),
        ModelInfo(id="claude-3-opus-20240229", provider=self.name, name="Claude 3 Opus", context_length=200000, quality_score=0.96, avg_latency_ms=3000.0, capabilities=["chat", "code", "reasoning"]),
        ModelInfo(id="claude-3-haiku-20240307", provider=self.name, name="Claude 3 Haiku", context_length=200000, quality_score=0.85, avg_latency_ms=500.0, capabilities=["chat", "code"]),
    ]

async def close(self) -> None:
    """Ferme le client."""
    if self._client:
        await self._client.close()
```

**Risque** : Faible — ajout de fonctionnalités, pas de suppression.

---

### Phase 2 — Shim de compatibilité pour `core/providers/`

**Objectif** : Garder `core/providers/` fonctionnel pendant la transition, mais le transformer en façade qui réexporte depuis `core/llm/`.

```python
# core/providers/__init__.py
"""Provider Model — Shim de compatibilité.

Ce module est conservé pour la rétrocompatibilité.
La source de vérité est `core/llm/`.
"""

from core.llm.providers.base import LLMProvider as ReasoningProvider
from core.llm.registry import LLMProviderRegistry as ProviderRegistry
from core.llm.types import ChatMessage, ChatResponse, ModelInfo

__all__ = [
    "ReasoningProvider",
    "ProviderRegistry",
    "ChatMessage",
    "ChatResponse",
    "ModelInfo",
]
```

```python
# core/providers/providers/ollama.py
"""Ollama Provider — Shim de compatibilité.

Réexporte depuis core.llm.providers.ollama.
"""

from core.llm.providers.ollama import OllamaProvider

__all__ = ["OllamaProvider"]
```

Même pattern pour `openai.py` et `anthropic.py`.

**Risque** : Nul — aucun import externe vers `core.providers` n'existe.

---

### Phase 3 — Vérification des consommateurs

**Objectif** : Vérifier que tous les consommateurs utilisent `core.llm` et non `core.providers`.

| Consommateur | Import actuel | Action |
|---|---|---|
| `interfaces/api/main.py` | `from core.llm.provider_manager import ProviderManager` | ✅ OK |
| `interfaces/api/routers/providers.py` | `from core.llm.provider_manager import ProviderManager` | ✅ OK |
| `interfaces/api/routers/v1.py` | `from core.llm.provider_manager import ProviderManager` | ✅ OK |
| `interfaces/cli/commands/router.py` | `from core.llm.router import LLMRouter` | ✅ OK |
| `tests/test_provider_manager.py` | `from core.llm.provider_manager import ProviderManager` | ✅ OK |
| `tests/test_provider_integration.py` | `from core.llm.provider_manager import ProviderManager` | ✅ OK |

**Aucun consommateur n'importe `core.providers`** — la migration est sûre.

---

### Phase 4 — Suppression progressive de `core/providers/`

**Objectif** : Supprimer `core/providers/` après une période de transition.

**Conditions de suppression** :
1. Toutes les fonctionnalités uniques ont été fusionnées dans `core/llm/providers/`
2. `pytest tests/` passe
3. Aucun import vers `core.providers` dans le codebase
4. Période de transition de 2 semaines (shim en place)

**Action** : Supprimer `core/providers/` (3 fichiers + `__init__.py`).

---

## 5. Architecture Cible

```
ETHAN
  │
  └── core.llm
        │
        ├── types.py              # Types de données (source de vérité)
        ├── registry.py           # LLMProviderRegistry (catalogue)
        ├── selector.py           # LLMSelector (sélection intelligente)
        ├── router.py             # LLMRouter (routage par catégorie)
        ├── client.py             # LLMClient (circuit breaker + fallback)
        ├── manager.py            # LLMManager (orchestration)
        ├── provider_manager.py   # ProviderManager (persistance + healthcheck)
        ├── provider_factory.py   # Factory (création depuis config)
        ├── store.py              # ProviderStore (PostgreSQL + Redis)
        ├── tracker.py            # CostTracker (suivi des coûts)
        │
        └── providers/
            ├── base.py           # LLMProvider (interface abstraite)
            ├── ollama.py         # Ollama (local) + pull_model + close
            ├── openai.py         # OpenAI (cloud) + base_url + close
            ├── anthropic.py      # Anthropic (cloud) + modèles récents + close
            ├── vllm.py           # vLLM (local/serveur)
            ├── llamacpp.py       # llama.cpp (local)
            ├── lmstudio.py       # LM Studio (local)
            ├── gemini.py         # Gemini (cloud)
            └── openai_compatible.py  # OpenAI-compatible (générique)
```

**Tous les providers restent disponibles** :
- ✅ Ollama
- ✅ OpenAI
- ✅ Anthropic
- ✅ vLLM
- ✅ llama.cpp
- ✅ LM Studio
- ✅ Gemini
- ✅ OpenAI compatible

---

## 6. Chemin d'Accès Unique

```
CLI ──→ core.llm ──→ ProviderManager ──→ LLMProviderRegistry ──→ LLMProvider ──→ Model
WebUI ──→ API ──→ core.llm ──→ ProviderManager ──→ LLMProviderRegistry ──→ LLMProvider ──→ Model
Runtime ──→ core.llm ──→ ProviderManager ──→ LLMProviderRegistry ──→ LLMProvider ──→ Model
```

CLI, WebUI et Runtime utilisent **exactement** le même système `core.llm`.

---

## 7. Règles de Non-Régression

1. **Aucune suppression** de fonctionnalité existante sans remplacement équivalent.
2. **Tous les 8 providers** doivent rester disponibles après la migration.
3. **Shims de compatibilité** : `core/providers/` réexporte depuis `core/llm/` pendant la transition.
4. **Tests existants** : `pytest tests/test_provider_manager.py` et `pytest tests/test_provider_integration.py` doivent passer.
5. **Migration progressive** : chaque phase est indépendante et réversible.
6. **Comparaison avant réécriture** : toute fonctionnalité existante est considérée comme une base validée.

---

## 8. Priorités

| Priorité | Action | Justification |
|---|---|---|
| **P0** | Nettoyer `core/llm/__init__.py` (types dupliqués) | Doublon interne — risque de confusion |
| **P0** | Fusionner `pull_model()` dans `core/llm/providers/ollama.py` | Fonctionnalité unique legacy |
| **P0** | Fusionner `close()` dans les 3 providers dupliqués | Fermeture propre des clients |
| **P0** | Fusionner `base_url` dans `core/llm/providers/openai.py` | Support d'endpoints alternatifs |
| **P1** | Mettre à jour les modèles Anthropic | Modèles récents manquants |
| **P1** | Créer le shim `core/providers/` | Rétrocompatibilité |
| **P2** | Supprimer `core/providers/` | Après période de transition |

---

## 9. Conclusion

L'unification LLM est **sûre et à faible risque** car :

1. **`core/llm/` est déjà le système dominant** — utilisé par l'API, la CLI et les tests
2. **`core/providers/` est orphelin** — aucun import externe
3. **Les fonctionnalités uniques sont limitées** — `pull_model()`, `close()`, `base_url`, modèles récents
4. **La migration est progressive** — shim de compatibilité pendant la transition

Le résultat final est un **chemin d'accès unique** :

```
ETHAN → core.llm → ProviderRegistry → Provider → Model
```

avec les 8 providers disponibles pour CLI, WebUI et Runtime.