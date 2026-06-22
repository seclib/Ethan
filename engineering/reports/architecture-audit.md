# Audit Architectural — Violations de la Constitution

> Date: 2025-06-22
> Actif analysé: `core/`, `providers/`

---

## Résumé

| Règle | Statut | Violations |
|-------|--------|------------|
| C001 | ❌ Échoue | 1 import technologique direct dans `core/` |
| C002 | 🟡 Partiel | Agents s'importent entre eux via `core.events` |
| C003 | 🟡 Partiel | Memory a des Adapters mais pas d'interface unifiée |
| C004 | 🟡 Partiel | Event bus utilisé mais pas systématique |
| C005 | ❌ Échoue | Pas de Capability Model formel |
| C006 | ❌ Échoue | `core/llm/` contient des références à des providers concrets |
| C007 | 🟡 Partiel | Memory en cours (RFC-006) mais implémentations actuelles non conformes |
| C008 | ❌ Échoue | Aucun mécanisme de Safety |

---

## Détail des violations

### C001 — `core/` importe des technologies externes

**Fichier**: `core/memory/redis_backend.py:45`
```python
import redis.asyncio as aioredis
```

**Problème**: Le Core importe directement `redis`.
**Solution**: Déplacer dans `core/memory/providers/redis.py` (RFC-006).

---

### C003 — Pas d'interface abstraite pour Memory

**Fichier**: `core/memory/redis_backend.py`, `core/memory/qdrant_backend.py`, `core/memory/sqlite_backend.py`, `core/memory/chromadb_backend.py`

**Problème**: Ces fichiers importent `from core.memory import MemoryBackend, MemoryEntry, MemoryResult` mais l'interface `MemoryBackend` n'est pas une abstraction pure (ABC).

**Solution**: Remplacer par l'interface `MemoryProvider` définie dans RFC-006.

---

### C005 — Pas de Capability Model

**Problème**: Aucune classe `Capability` abstraite n'existe. Le mot "capability" apparaît uniquement dans `core/plugins.py` comme mapping plugin → nom de capacité.

**Solution**: Implémenter `core/capabilities/` avec l'interface définie dans RFC-007.

---

### C006 — Providers IA couplés au Core

**Fichier**: `core/llm/__init__.py:87,133`
```python
# L.87: """Provider name (e.g., 'ollama', 'openai')."""
# L.133: provider = get_provider("ollama")
```

**Problème**: `core/llm/__init__.py` contient des références explicites aux noms de providers (Ollama, OpenAI). Le Core ne devrait pas connaître ces noms.

**Solution**: 
1. Déplacer `core/llm/` vers un module Provider abstrait
2. Les providers concrets (`providers/ollama.py`, `providers/openai.py`, `providers/anthropic.py`) doivent implémenter une interface commune
3. Le Core appelle `ReasoningProvider.reason()` sans connaître l'implémentation

**Répertoire providers/**:
```
providers/
├── __init__.py
├── anthropic.py
├── ollama.py
└── openai.py
```

Ces fichiers existent déjà mais ne sont pas utilisés par `core/llm/`.

---

### C007 — Memory non conforme

**Fichier**: `core/memory/`

**Problème**: Les fichiers `redis_backend.py`, `qdrant_backend.py`, `sqlite_backend.py`, `chromadb_backend.py` sont des implémentations directes sans abstraction unifiée.

**Solution**: Remplacer par l'architecture RFC-006 (MemoryManager + MemoryProvider interface + providers/ séparés).

---

### C008 — Aucun mécanisme de Safety

**Problème**: Aucune classe `SafetyContext`, `validate()`, ou mécanisme de permissions n'existe dans `core/`.

**Solution**: Implémenter `core/safety/` avec :
- `SafetyContext` dataclass
- `SafetyValidator` interface
- Validation avant toute exécution de Capability

---

## Carte des dépendances actuelles (problématiques)

```
core/agents/base.py
  ├── core/events/ ✅ (acceptable)
  ├── core/llm/ ❌ (devrait être via interface)
  └── core/llm/ChatMessage ❌ (import interne)

core/memory/redis_backend.py
  ├── core/memory/ 🟡 (MemoryBackend existe mais pas ABC pur)
  └── redis ❌ (import direct)

core/llm/__init__.py
  └── ollama ❌ (nom hardcodé)
```

---

## Priorités de correction

| Priorité | Violation | Impact | Effort |
|----------|-----------|--------|--------|
| P0 | C006 — Providers IA couplés | Haut — empêche le changement de modèle IA | 2 jours |
| P0 | C007 — Memory non conforme | Haut — déjà adressé par RFC-006 | 3 jours |
| P1 | C003 — Pas d'interface Memory | Moyen — ralentit les tests | 1 jour |
| P1 | C005 — Pas de Capability Model | Moyen — architecture non extensible | 3 jours |
| P2 | C001 — Imports directs | Faible — un seul fichier concerné | 0.5 jour |
| P2 | C008 — Safety manquant | Faible — peut être implémenté progressivement | 2 jours |

---

## Conclusion

**5 violations majeures** (P0/P1) identifiées. Les RFC-005 (Docker) et RFC-006 (Memory) adressent déjà partiellement C001 et C007. Un RFC dédié est nécessaire pour C005 (Capability Model) et C006 (Provider Model).