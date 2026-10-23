# God's Eye View — Adaptateur IA (ETHAN)

Adaptateur serveur exposant l'**inférence réelle d'ETHAN** au service
God's Eye View (plugin de visualisation). Source de vérité :
`interfaces/api/routers/gods_eye_view_ai.py` (monté au startup par
`interfaces/api/main.py`, qui injecte aussi le `ProviderManager`).

Principe AGENTS.md : **aucune logique métier, aucun secret ici**. Le routeur
translate le contrat OpenAI du GEV vers `ProviderManager` (Core). La WebUI
/ le navigateur ne reçoivent jamais de clé provider.

---

## Endpoints

Base : `/v1/plugins/gods-eye-view/ai`

| Méthode | Chemin | RBAC | Usage |
|---|---|---|---|
| GET | `/capabilities` | `READ` | Cartographie fonctions GEV → ETHAN + limitations |
| GET | `/config` | `READ` | Config plugin (modèle, limites) + modèles autorisés (sans embeddings) |
| PUT | `/config` | `PLUGINS` | Sélection agent/modele (validée contre `list_models`/`list_providers`) |
| POST | `/provision` | `ADMIN` | Jeton d'agent bref (1 h), portée `plugins:gods-eye-view-ai` |
| POST | `/chat` | portée JWT | Chat OpenAI-compatible (JSON ou `stream: true` → SSE) |
| POST | `/hud-summary` | portée JWT | Résumé HUD **5 mots max** (contrainte appliquée côté serveur) |
| POST | `/tools/validate` | portée JWT | Validation d'une action IA (allow-liste fermée, **jamais d'exécution auto**) |

---

## Authentification

Deux chemins acceptés sur `/chat`, `/hud-summary`, `/tools/validate`
(via `_verify_ai_token`, header `Authorization: Bearer` ou cookie
`gevs_ai_token`) :

1. **Jeton de provision** (`POST /provision`, rôle admin requis) :
   payload `{"role": "gevs-ai", "scope": ["plugins:gods-eye-view-ai"], ...}`,
   TTL 3600 s. Destiné au **serveur GEV uniquement** — jamais au navigateur.
2. **JWT utilisateur** dont le rôle possède `Permission.GODS_EYE_AI`
   ou `Permission.ADMIN`. Le rôle `gevs-ai` est enregistré dans
   `core/auth` (RBAC) avec `READ`, `CHAT`, `GODS_EYE_AI`.

Sans token → 401 ; rôle sans portée → 403.

---

## Contrat `POST /chat`

Entrée OpenAI standard :

```json
{
  "messages": [{"role": "user", "content": "..."}],
  "model": "llama3.2:3b",       // optionnel — validé parmi list_models()
  "provider": "ollama",          // optionnel — preferred_providers
  "context_limit": 8000,         // optionnel — troncature du contexte
  "stream": false                // true → SSE text/event-stream
}
```

Sortie : `chat.completion` (choices/message/finish_reason/usage) ou flux
SSE `data: {...chunk...}` terminé par `data: [DONE]`.

Résolution (identique stream/non-stream) :

- `model` donné → recherché dans `manager.list_models()` (404 si absent),
  provider propriétaire passé en `preferred_providers` ;
- sinon `provider` → `preferred_providers` ;
- sinon sélecteur par défaut `LLMRequirements(task_type="chat")`.

Le contexte est tronqué (`_truncate_messages`) : system conservé, plus
récents conservés, plafond `context_limit` (défaut 8000 chars, max 100000)
et 50 messages max. Timeout : `timeout_seconds` config, borné 5–300 s
(défaut 60 s). Toute erreur d'inférence → **502** avec message sanitizé
(aucune clé/URL interne fuitée) ; manager non initialisé → 503.

## Cartographie des fonctions GEV (étapes 1–2)

| Fonction GEV | Compatible | Route ETHAN |
|---|---|---|
| `hud_summary` | ✔ | `POST /hud-summary` |
| `entity_questions` | ✔ | `POST /chat` |
| `voice_commands_text` | ✔ | `POST /chat` |
| `context_analysis` | ✔ | `POST /chat` |
| `tool_actions` | ✔ | `POST /tools/validate` |
| `realtime_voice_audio` | ✘ (WebRTC OpenAI) | repli texte : `POST /chat` |

`/hud-summary` conserve le prompt HUD d'origine (`HUD_SYSTEM_PROMPT`,
5 mots exacts) puis applique `_five_words` côté serveur.

`/tools/validate` : allow-liste `ALLOWED_TOOL_NAMES` (30 outils GEV),
payload ≤ 8000 chars, réponse `requires_explicit_approval: true` —
l'exécution reste explicite côté client.

---

## Vérifications ETHAN (API compatible OpenAI)

ETHAN expose déjà `/api/chat/completions` et `/api/v1/chat/completions`
(adaptateur Open WebUI, `interfaces/api/routers/openwebui.py`) — routes,
auth et formats OpenAI y sont assurés, mais ces routes sont destinées à
Open WebUI (store de conversations dédié). **God's Eye View utilise son
adaptateur `/ai/*`**, qui passe par le même `ProviderManager` Core avec en
plus : la portée de jeton `plugins:gods-eye-view-ai`, l'allow-liste
d'outils GEV, la troncature de contexte et le résumé HUD 5 mots.

Garanties vérifiées par les tests :

- aucun secret dans `GET /config`, dans `PUT /config`, ni dans le jeton
  de provision (claims décodés, absence d'`api_key`/`sk-`) ;
- aucune clé provider côté navigateur : le serveur GEV proxifie, le
  navigateur ne voit que des réponses déjà émises ;
- aucun impact conteneur / fournisseurs globaux : l'adaptateur ne touche
  ni `docker-compose.yml`, ni la configuration des providers (le manager
  est injecté, jamais muté globalement).

---

## Tests

`tests/interfaces/test_gods_eye_view_ai.py` (21 tests) :

- **Contrat** : routes + RBAC déclarés (introspection `permission`),
  cartographie des fonctions, rôle `gevs-ai` enregistré ;
- **Auth** : provision scope utilisable sur chat, 401 sans token, 403
  hors portée ;
- **Chat** : shape OpenAI, 404 modèle inconnu, 502 erreur sanitizée
  (pas de fuite de secret), SSE `data: [DONE]`, 503 sans manager ;
- **Limites de contexte** : `_truncate_messages` (system conservé,
  récents gardés, plafond et 50 messages max) + test HTTP avec
  `context_limit` (le manager ne reçoit jamais plus que le budget) ;
- **Secrets** : `GET /config` sans `api_key`/`secret`/`token`, jeton de
  provision limité à `token`/`expires_in`/`scopes` ;
- **HUD** : résumé 5 mots max + prompt system imposé ;
- **Outils** : allow-liste (403 hors liste, approval explicite) ;
- **Modèle local réel** : roundtrip complet avec `ProviderManager` réel
  et Ollama local (`solar:latest`) — **skip automatique** si Ollama est
  absent ; toute la requête tourne dans une seule boucle asyncio
  (`ASGITransport`).

```bash
pytest tests/interfaces/test_gods_eye_view_ai.py -q
```
