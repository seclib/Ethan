# ETHAN — Unified AI Providers — Architecture Decision

**Date** : 2026-09-09
**Auteur** : Principal AI Platform Engineer
**Statut** : Implémenté
**Portée** : `core/llm/`, `interfaces/api/routers/providers.py`, WebUI providers

---

## 1. Architecture autoritative (choisie)

Le modèle de provider unifié d'ETHAN vit **exclusivement** dans `core/llm/`.
Aucun second registre n'a été créé — le registre unique existant
(`LLMProviderRegistry`) est utilisé en interne par `ProviderManager` et
`LLMClient`.

```
core/llm/
├── providers/base.py         → LLMProvider (ABC) — INTERFACE UNIFIÉE
│                              chat / chat_stream / embed / list_models
│                              + vision_analyze / transcribe (optionnels)
├── providers/*.py            → ollama, openai, azure, anthropic, gemini,
│                              vllm, llamacpp, lmstudio, openai-compatible,
│                              openrouter
├── provider_manager.py       → ProviderManager — ORCHESTRATEUR UNIQUE
│                              (activation, healthcheck, routing par
│                              capacité, chat/embed/vision/transcribe)
├── provider_factory.py       → create_provider_from_config
├── store.py                  → ProviderStore — persistance PG `llm_providers`
│                              (+ Redis cache + mémoire). SANS SECRETS.
├── model_store.py            → ModelStore — fiches modèles custom
│                              (CoreRecordStore, modèles non découverts)
├── registry.py               → LLMProviderRegistry — LE registre (mémoire)
├── types.py                  → ProviderCapability (enum canonique) + types
└── client.py / selector.py / router.py / tracker.py
```

**Injection API** : `interfaces/api/main.py` crée le `ProviderManager` au
startup et l'injecte dans les routers `providers`, `models`, `v1`,
`openwebui`, `capabilities` — une seule instance, une seule source.

## 2. Capacités normalisées

Nouvel enum `ProviderCapability` (`core/llm/types.py`) — forme canonique
sérialisable exposée à l'API et à la WebUI :

| Capacité | Méthode `LLMProvider` | Providers |
|---|---|---|
| `llm` | `chat`, `chat_stream` | tous |
| `vision` | `vision_analyze` | openai, azure, gemini, anthropic, ollama (llava), openrouter |
| `embedding` | `embed` | openai, azure, ollama, vllm, openai-compatible… |
| `speech_to_text` | `transcribe` | openai (whisper), azure, gemini, openai-compatible |
| `transcription` | `transcribe` (alias STT) | idem |

- `LLMProvider.capabilities()` retourne la liste canonique dérivée des flags
  `supports_vision / supports_embedding / supports_transcription /
  supports_speech_to_text` (rétro-compatibilité totale des flags existants).
- `ProviderManager.describe_provider()` expose désormais `capabilities`
  + `has_api_key` (booléen). **La clé API n'est jamais sérialisée.**
- `ProviderManager.get_provider_capabilities()` = source unique pour
  l'endpoint `GET /providers/{id}/capabilities` (le routeur n'accède plus
  au registre en interne).

## 3. WebUI — configuration providers & modèles

- `lib/api/providers.ts` : type `Provider` étendu avec `capabilities` et
  `has_api_key` ; `ProviderCapabilities` avec `supports_speech_to_text`.
- `providers-workspace.tsx` : badges de capacités (LLM, Vision, Embeddings,
  Speech-to-Text, Transcription) + indicateur « Clé configurée » par carte.
- `provider-form-dialog.tsx` : le champ clé API n'est envoyé **que si
  renseigné** — un champ vide signifie « conserver la clé actuelle »
  (le backend ne renvoie jamais la clé, elle ne peut pas être pré-remplie).
- Models : le catalogue `/models` (découverts + fiches custom `ModelStore`)
  et le workspace `models-workspace.tsx` restent inchangés — déjà alignés

## 4. Sécurité — secrets

Rappels appliqués et vérifiés par tests :

1. **Clés des providers LLM** : jamais persistées (`ProviderStore` retire
   `api_key` avant save), injectées en mémoire depuis env/Vault
   (`_inject_secrets`), jamais renvoyées (`ProviderResponse.has_api_key`).
2. **PUT `api_key=""`** : ne crée pas d'intention de wipe — le routeur
   ignore la chaîne vide (rotation = clé non vide uniquement).
3. **TTS / Images (`TTSEngine`, `ImageGenerator`)** : ⚠️ corrigeait une
   fuite — `configure()` stockait l'`api_key` **en clair** dans le
   CoreRecordStore et `get_config()` la renvoyait (exposée via
   `GET /audio/config`). Désormais : clé en mémoire d'instance uniquement,
   `get_config()` filtre `api_key/apiKey` et retourne `has_api_key`.
4. Les configs legacy déjà persistées avec une clé en clair sont masquées
   à la lecture (filtre du résiduel `api_key/apiKey`).

---

## 5. Systèmes legacy à déprécier (rapport)

| Système | Fichier | État | Action recommandée |
|---|---|---|---|
| `LLMManager` | `core/llm/manager.py` | Mort en production (aucun import métier) | **Supprimer** dans une prochaine release — `ProviderManager` est l'autorité |
| Providers fictifs du CoreWebUIStore | `core/state/webui_store.py` (`_DOMAIN_PROVIDERS`, openai/anthropic/huggingface/pinecone en dur) | Non branché à aucun routeur | **Retirer les méthodes providers** du store ; conserver goals/facts/events |
| `TTSEngine` config parallèle | `core/llm/tts.py` | Utilisé (`/audio/*`), mais doublonne avec le modèle unifié | **RFC** : migrer TTS sous `ProviderManager` (capability `tts`) puis déprécier le stockage `tts-config` |
| `ImageGenerator` config parallèle | `core/llm/images.py` | Stub (generate vide), doublonne | **RFC** : capability `image_generation` sur le modèle unifié, puis déprécier |

Ces modules sont marqués « ⚠️ DÉPRÉCIÉ » dans leurs docstrings.

---

## 6. Tests

| Suite | Contenu |
|---|---|
| `tests/test_unified_providers.py` | +18 tests : enum `ProviderCapability`, `capabilities()` par provider réel (openai/anthropic/ollama/stubs), `describe_provider` (capabilities + has_api_key sans fuite), `get_provider_capabilities`, masquage TTS/Images, non-persistance de clé |
| `interfaces/api/tests/test_providers_capabilities_api.py` | +6 tests : endpoint `/capabilities` canonique sans secrets, schéma `ProviderResponse`, 404 inconnu, `api_key=""` ignoré, rotation de clé propagée à l'instance |
| Régression | `test_provider_manager.py`, `test_chat_pipeline.py`, `test_rag_infrastructure.py`, `tests/core/test_domain_stores.py` : verts |

---

## 7. Verdict

Le modèle unifié `core/llm/` (LLMProvider + ProviderManager + ProviderStore
+ ModelStore) est **l'architecture autoritative** : couverture complète des
capacités (LLM, Vision, Embeddings, Speech-to-Text, Transcription),
un seul registre, secrets jamais exposés, WebUI purement décorative.
Les systèmes legacy listés en §5 sont isolés, documentés et prêts à être
retirés après migration TTS/Images (RFC à venir).
  sur le modèle unifié.