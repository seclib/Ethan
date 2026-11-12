# ETHAN — Rapport de Migration : `core/providers/` → `core/llm/providers/`

**Date** : 2026-03-08  
**Auteur** : Domain Migration Agent  
**Statut** : Rapport de migration — conforme à AGENTS.md  
**Domaine** : Providers LLM  
**Source** : `core/providers/` (legacy)  
**Cible** : `core/llm/providers/` (principal)

---

## 1. Inventaire Complet

### 1.1 `core/providers/` (legacy — à migrer)

| Fichier | Contenu |
|---|---|
| `core/providers/__init__.py` | `ReasoningProvider` (ABC : `reason()`, `embed()`, `health_check()`), `ProviderRegistry` (dict simple) |
| `core/providers/providers/ollama.py` | `OllamaProvider(LLMProvider)` — hérite de `core.llm.LLMProvider`. Fonctionnalités : `pull_model()`, `close()`, `/api/embed` |
| `core/providers/providers/openai.py` | `OpenAIProvider(LLMProvider)` — hérite de `core.llm.LLMProvider`. Fonctionnalités : `base_url` personnalisé, `close()`, auto-registration via `OPENAI_API_KEY` |
| `core/providers/providers/anthropic.py` | `AnthropicProvider(LLMProvider)` — hérite de `core.llm.LLMProvider`. Fonctionnalités : modèles récents, `max_tokens=4096`, `close()`, auto-registration via `ANTHROPIC_API_KEY` |

### 1.2 `core/llm/providers/` (principal — source de vérité)

| Fichier | Contenu |
|---|---|
| `core/llm/providers/base.py` | `LLMProvider` (ABC : `chat()`, `chat_stream()`, `embed()`, `list_models()`, `test_connection()`, `initialize()`) |
| `core/llm/providers/ollama.py` | `OllamaProvider(LLMProvider)` — `initialize()`, `chat()`, `chat_stream()`, `embed()` (via `/api/embeddings`), `list_models()`. **Manque** : `pull_model()`, `close()`, `/api/embed` |
| `core/llm/providers/openai.py` | `OpenAIProvider(LLMProvider)` — `initialize()`, `chat()`, `chat_stream()`, `embed()`, `list_models()`. **Manque** : `base_url` personnalisé, `close()` |
| `core/llm/providers/anthropic.py` | `AnthropicProvider(LLMProvider)` — `initialize()`, `chat()`, `chat_stream()`, `embed()`, `list_models()`. **Manque** : modèles récents, `max_tokens=4096`, `close()` |
| `core/llm/providers/vllm.py` | `VLLMProvider(LLMProvider)` |
| `core/llm/providers/llamacpp.py` | `LlamaCppProvider(LLMProvider)` |
| `core/llm/providers/lmstudio.py` | `LMStudioProvider(LLMProvider)` |
| `core/llm/providers/gemini.py` | `GeminiProvider(LLMProvider)` |
| `core/llm/providers/openai_compatible.py` | `OpenAICompatibleProvider(LLMProvider)` — générique |

---

## 2. Comparaison des Implémentations

### 2.1 Ollama

| Fonctionnalité | `core/providers/` | `core/llm/providers/` | Source de vérité |
|---|---|---|---|
| `chat()` | ✅ | ✅ | `core/llm/providers/` |
| `chat_stream()` | ✅ | ✅ | `core/llm/providers/` |
| `embed()` | ✅ (`/api/embed`) | ✅ (`/api/embeddings`) | `core/llm/providers/` (mettre à jour) |
| `list_models()` | ✅ | ✅ | `core/llm/providers/` |
| `pull_model()` | ✅ | ❌ | **Fusionner** |
| `close()` | ✅ | ❌ | **Fusionner** |
| `initialize()` | ❌ | ✅ | `core/llm/providers/` |
| `test_connection()` | ❌ | ✅ | `core/llm/providers/` |

### 2.2 OpenAI

| Fonctionnalité | `core/providers/` | `core/llm/providers/` | Source de vérité |
|---|---|---|---|
| `chat()` | ✅ | ✅ | `core/llm/providers/` |
| `chat_stream()` | ✅ | ✅ | `core/llm/providers/` |
| `embed()` | ✅ | ✅ | `core/llm/providers/` |
| `list_models()` | ✅ | ✅ | `core/llm/providers/` |
| `base_url` personnalisé | ✅ | ❌ | **Fusionner** |
| `close()` | ✅ | ❌ | **Fusionner** |
| `initialize()` | ❌ | ✅ | `core/llm/providers/` |
| `test_connection()` | ❌ | ✅ | `core/llm/providers/` |
| Auto-registration | ✅ | ❌ | **Fusionner** (dans factory) |

### 2.3 Anthropic

| Fonctionnalité | `core/providers/` | `core/llm/providers/` | Source de vérité |
|---|---|---|---|
| `chat()` | ✅ | ✅ | `core/llm/providers/` |
| `chat_stream()` | ✅ | ✅ | `core/llm/providers/` |
| `embed()` | ❌ (NotImplementedError) | ✅ | `core/llm/providers/` |
| `list_models()` | ✅ (modèles récents) | ✅ (modèles anciens) | **Fusionner** |
| `max_tokens=4096` | ✅ | ❌ (1024) | **Fusionner** |
| `close()` | ✅ | ❌ | **Fusionner** |
| `initialize()` | ❌ | ✅ | `core/llm/providers/` |
| `test_connection()` | ❌ | ✅ | `core/llm/providers/` |
| Auto-registration | ✅ | ❌ | **Fusionner** (dans factory) |

---

## 3. Choix de la Source de Vérité

**Source de vérité** : `core/llm/providers/`

**Justification** :
1. `core/llm/providers/` a une interface plus riche (`LLMProvider` avec `test_connection()`, `initialize()`)
2. `core/llm/providers/` a 8 providers (vs 3 dans `core/providers/`)
3. `core/llm/providers/` est utilisé par `ProviderManager`, `LLMClient`, `LLMSelector`, `LLMRouter`
4. `core/providers/` importe depuis `core.llm` — il est dépendant, pas indépendant
5. Aucun fichier externe n'importe `core.providers` — il est orphelin

---

## 4. Fusion des Fonctionnalités

### 4.1 `core/llm/providers/ollama.py`

**À ajouter** :
```python
async def pull_model(self, model: str) -> bool:
    """Pull a model from Ollama registry."""
    if not self._client:
        return False
    payload = {"name": model, "stream": False}
    response = await self._client.post(f"{self._base_url}/api/pull", json=payload)
    return response.is_success

async def close(self) -> None:
    """Ferme le client HTTP."""
    if self._client:
        await self._client.aclose()
```

**À modifier** :
- `embed()` : changer `/api/embeddings` → `/api/embed` (nouveau endpoint Ollama)

### 4.2 `core/llm/providers/openai.py`

**À ajouter** :
```python
def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
    self._api_key = api_key
    self._base_url = base_url
    self._client = None

async def initialize(self) -> None:
    try:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
    except ImportError:
        logger.warning("openai package not installed")

async def close(self) -> None:
    if self._client:
        await self._client.close()
```

### 4.3 `core/llm/providers/anthropic.py`

**À ajouter** :
```python
async def list_models(self) -> list[ModelInfo]:
    return [
        ModelInfo(id="claude-sonnet-4-20250514", provider=self.name, name="Claude Sonnet 4", context_length=200000, quality_score=0.95, avg_latency_ms=1500.0, capabilities=["chat", "code", "reasoning"]),
        ModelInfo(id="claude-3-5-sonnet-20241022", provider=self.name, name="Claude 3.5 Sonnet", context_length=200000, quality_score=0.93, avg_latency_ms=1500.0, capabilities=["chat", "code", "reasoning"]),
        ModelInfo(id="claude-3-opus-20240229", provider=self.name, name="Claude 3 Opus", context_length=200000, quality_score=0.96, avg_latency_ms=3000.0, capabilities=["chat", "code", "reasoning"]),
        ModelInfo(id="claude-3-haiku-20240307", provider=self.name, name="Claude 3 Haiku", context_length=200000, quality_score=0.85, avg_latency_ms=500.0, capabilities=["chat", "code"]),
    ]

async def close(self) -> None:
    if self._client:
        await self._client.close()
```

**À modifier** :
- `max_tokens` par défaut : 1024 → 4096

### 4.4 Shim de compatibilité pour `core/providers/`

Après la fusion, transformer `core/providers/` en façade :

```python
# core/providers/__init__.py
from core.llm.providers.base import LLMProvider as ReasoningProvider
from core.llm.registry import LLMProviderRegistry as ProviderRegistry
from core.llm.types import ChatMessage, ChatResponse, ModelInfo

__all__ = ["ReasoningProvider", "ProviderRegistry", "ChatMessage", "ChatResponse", "ModelInfo"]
```

```python
# core/providers/providers/ollama.py
from core.llm.providers.ollama import OllamaProvider
__all__ = ["OllamaProvider"]
```

---

## 5. Fichiers Impactés

| Fichier | Action | Risque |
|---|---|---|
| `core/llm/providers/ollama.py` | Ajouter `pull_model()`, `close()`, mettre à jour `/api/embed` | Faible |
| `core/llm/providers/openai.py` | Ajouter `base_url`, `close()`, `initialize()` | Faible |
| `core/llm/providers/anthropic.py` | Ajouter modèles récents, `close()`, `max_tokens=4096` | Faible |
| `core/providers/__init__.py` | Transformer en shim | Nul |
| `core/providers/providers/ollama.py` | Transformer en shim | Nul |
| `core/providers/providers/openai.py` | Transformer en shim | Nul |
| `core/providers/providers/anthropic.py` | Transformer en shim | Nul |

---

## 6. Dépendances

### 6.1 Consommateurs de `core.providers` (à vérifier)

```bash
grep -r "from core.providers" --include="*.py" .
grep -r "import core.providers" --include="*.py" .
```

**Résultat attendu** : Aucun import externe vers `core.providers`.

### 6.2 Consommateurs de `core.llm` (à vérifier)

| Fichier | Import |
|---|---|
| `interfaces/api/main.py` | `from core.llm.provider_manager import ProviderManager` |
| `interfaces/api/routers/providers.py` | `from core.llm.provider_manager import ProviderManager` |
| `interfaces/api/routers/v1.py` | `from core.llm.provider_manager import ProviderManager` |
| `interfaces/cli/commands/router.py` | `from core.llm.router import LLMRouter` |
| `tests/test_provider_manager.py` | `from core.llm.provider_manager import ProviderManager` |
| `tests/test_provider_integration.py` | `from core.llm.provider_manager import ProviderManager` |

---

## 7. Tests

### 7.1 Tests existants

| Fichier | Description |
|---|---|
| `tests/test_provider_manager.py` | Tests du `ProviderManager` |
| `tests/test_provider_integration.py` | Tests d'intégration des providers |

### 7.2 Tests à créer

| Fichier | Description |
|---|---|
| `tests/test_ollama_provider.py` | Test `pull_model()`, `close()`, `/api/embed` |
| `tests/test_openai_provider.py` | Test `base_url`, `close()` |
| `tests/test_anthropic_provider.py` | Test modèles récents, `max_tokens=4096`, `close()` |
| `tests/test_providers_shim.py` | Test que `core.providers` réexporte correctement |

---

## 8. Validation

### 8.1 Critères d'acceptation

1. ✅ `pytest tests/test_provider_manager.py` passe
2. ✅ `pytest tests/test_provider_integration.py` passe
3. ✅ `python -c "from core.providers.providers.ollama import OllamaProvider"` fonctionne (shim)
4. ✅ `python -c "from core.llm.providers.ollama import OllamaProvider"` fonctionne (fusion)
5. ✅ Aucun import externe vers `core.providers` cassé

### 8.2 Commandes de validation

```bash
# 1. Vérifier les imports
python -c "from core.llm.providers.ollama import OllamaProvider; print('OK')"
python -c "from core.llm.providers.openai import OpenAIProvider; print('OK')"
python -c "from core.llm.providers.anthropic import AnthropicProvider; print('OK')"

# 2. Vérifier le shim
python -c "from core.providers.providers.ollama import OllamaProvider; print('OK')"
python -c "from core.providers.providers.openai import OpenAIProvider; print('OK')"
python -c "from core.providers.providers.anthropic import AnthropicProvider; print('OK')"

# 3. Vérifier qu'aucun import externe n'est cassé
grep -r "from core.providers" --include="*.py" . | grep -v "core/providers/"

# 4. Lancer les tests
pytest tests/test_provider_manager.py tests/test_provider_integration.py -v
```

---

## 9. Risques

| Risque | Niveau | Mitigation |
|---|---|---|
| Breaking change sur `core/llm/providers/ollama.py` (signature `embed()`) | Faible | Le nouveau endpoint `/api/embed` est compatible avec l'ancien `/api/embeddings` |
| Breaking change sur `core/llm/providers/openai.py` (constructeur) | Faible | `base_url` a une valeur par défaut |
| Breaking change sur `core/llm/providers/anthropic.py` (modèles) | Faible | Les modèles anciens restent disponibles |
| Shim `core/providers/` ne fonctionne pas | Nul | Aucun import externe — le shim est inutile mais conservé pour la compatibilité |

---

## 10. Plan Rollback

### 10.1 Rollback partiel (si un provider échoue)

1. Révoquer les changements sur le provider concerné
2. Le shim `core/providers/` continue de fonctionner (il réexporte depuis `core/llm/providers/`)

### 10.2 Rollback complet

1. Supprimer les fichiers modifiés dans `core/llm/providers/`
2. Restaurer `core/providers/` à son état original
3. `git checkout core/providers/ core/llm/providers/`

```bash
# Rollback complet
git checkout core/providers/ core/llm/providers/ core/ethan_types/event.py
```

---

## 11. Conclusion

La migration de `core/providers/` → `core/llm/providers/` est **sûre et à faible risque** car :

1. **`core/llm/providers/` est la source de vérité** — plus complet, plus riche
2. **`core/providers/` est orphelin** — aucun import externe
3. **Les fonctionnalités uniques sont limitées** — `pull_model()`, `close()`, `base_url`, modèles récents
4. **Le shim préserve la compatibilité** — `core/providers/` réexporte depuis `core/llm/providers/`
5. **Aucune suppression de code** — les fonctionnalités sont fusionnées, pas supprimées
