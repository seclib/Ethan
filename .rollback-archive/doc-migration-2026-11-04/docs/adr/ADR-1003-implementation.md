# ADR-1003 — Single Entry Intent Model — Implementation Report

## Date
2026-06-22

## Statut
✅ **Implémenté**

---

## Résumé

Toutes les entrées utilisateur (text, voice, API, automation) sont maintenant normalisées dans une structure unifiée : **Intent Object**.

---

## Modifications

### 1. Core Model (`core/context/intent.py`)

**Ajouté:**
- `Intent` dataclass avec validation de timestamp
- `IntentParser` interface abstraite
- `TextIntentParser` — entrées texte simples
- `APIIntentParser` — entrées API avec contexte
- `VoiceIntentParser` — entrées vocales (transcript + métadonnées audio)
- `AutomationIntentParser` — entrées automation (triggers + payload)
- `IntentRouter` — routeur central vers le bon parser

### 2. API Entry Point (`apps/api/main.py`)

**Ajouté:**
- Endpoints FastAPI pour chaque type d'entrée:
  - `POST /v1/intent/text`
  - `POST /v1/intent/api`
  - `POST /v1/intent/voice`
  - `POST /v1/intent/automation`
- Normalisation automatique via `IntentRouter`

### 3. Tests (`tests/core/test_intent.py`)

**Ajouté:**
- 14 tests unitaires couvrant:
  - Intent timestamp (défaut + explicite)
  - Tous les parsers (text, api, voice, automation)
  - IntentRouter (routing + erreur source inconnue)

**Résultat:** ✅ 14/14 tests passent

### 4. Example Usage (`core/orchestration/example_usage.py`)

**Modifié:**
- Remplacé la création manuelle d'Intent par `IntentRouter.parse()`
- Démontre le flux ADR-1003 conforme

---

## Conformité ADR-1003

| Règle ADR | Status | Preuve |
|-----------|--------|--------|
| Toute entrée convertie en Intent avant traitement | ✅ | `IntentRouter.parse()` dans `apps/api/main.py` |
| Le Planner ne reçoit que des Intent objects | ✅ | `core/orchestration/planner.py:17` — `def build(self, intent: Intent)` |
| Parsers spécifiques implémentent IntentParser | ✅ | 4 parsers: Text, API, Voice, Automation |

---

## Architecture

```
[Voice] ──┐
[Text] ──┼──► IntentRouter ──► Intent ──► Planner
[API] ──┤
[Auto] ──┘
```

### Flux de traitement

1. **Entrée brute** (texte, dict API, dict voice, dict automation)
2. **IntentRouter.parse(source, raw_input)** détermine le parser
3. **Parser spécifique** extrait et normalise les champs
4. **Intent object** créé avec:
   - `source`: type d'entrée
   - `user_input`: contenu principal
   - `context`: métadonnées spécifiques
   - `timestamp`: horodatage UTC
5. **Planner.build(intent)** reçoit l'Intent unifié

---

## Exemples d'usage

### Text
```python
from core.context.intent import IntentRouter

router = IntentRouter()
intent = await router.parse("text", "Hello world")
# Intent(source="text", user_input="Hello world", context={}, timestamp=...)
```

### API
```python
raw = {"input": "Analyze this", "context": {"user_id": "123"}}
intent = await router.parse("api", raw)
# Intent(source="api", user_input="Analyze this", context={"user_id": "123"}, ...)
```

### Voice
```python
raw = {
    "transcript": "Turn on lights",
    "language": "fr",
    "confidence": 0.95,
    "audio_metadata": {"duration": 2.3}
}
intent = await router.parse("voice", raw)
# Intent(source="voice", user_input="Turn on lights", context={"language": "fr", ...}, ...)
```

### Automation
```python
raw = {
    "trigger": "daily_report",
    "automation_id": "auto_001",
    "trigger_type": "scheduled",
    "payload": {"time": "08:00"}
}
intent = await router.parse("automation", raw)
# Intent(source="automation", user_input="daily_report", context={"automation_id": "auto_001", ...}, ...)
```

---

## Impact

- ✅ **Unified processing pipeline** — Planner toujours recevoir un Intent
- ✅ **Easier memory integration** — Intent stocké comme item mémoire unique
- ✅ **Consistent reasoning flow** — même pipeline quel que soit le type d'entrée
- ✅ **Backward compatible** — Intent existant toujours supporté
- ✅ **Testé** — 14 tests unitaires passent

---

## Références

- [ADR-1003](/engineering/adr/ADR-1003-single-entry-intent-model.md)
- [Constitution Architecturale](/engineering/architecture/constitution.md) — Principe 5
- [RFC-007](/engineering/rfc/rfc-007-architecture-constitution.md) — Règles C004
- [ADR-1002](/engineering/adr/ADR-1002-planner-executor-separation.md)