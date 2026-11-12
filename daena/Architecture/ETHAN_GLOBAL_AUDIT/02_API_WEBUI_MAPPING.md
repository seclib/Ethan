# 02 — API / WebUI Mapping

## Backend routers observés

| Backend router | Préfixe typique | WebUI frontend |
|---|---|---|
| `interfaces/api/routers/capabilities.py` | `/v1` | `lib/api/capabilities.ts` |
| `interfaces/api/routers/plugins.py` | `/v1` | `lib/api/plugins.ts` |
| `interfaces/api/routers/providers.py` | `/v1` | `lib/api/providers.ts` |
| `interfaces/api/routers/knowledge.py` | `/v1` | `lib/api/knowledge.ts` |
| `interfaces/api/routers/skills.py` | `/v1` | `lib/api/skills.ts` |
| `interfaces/api/routers/tools` (capabilities/tools) | `/v1` | `lib/api/tools.ts` |
| `interfaces/api/routers/odin.py` | `/v1/plugins/odin` | pages `app/odin` |
| `interfaces/api/routers/frame.py` | `/v1/plugins/frame` | pages `app/frame` |
| `interfaces/api/routers/quantar.py` | `/v1/...` | pages `app/quantar` |
| `interfaces/api/routers/extensions.py` | `/v1` | `lib/api/extensions.ts` |
| `interfaces/api/routers/component_lifecycle.py` | `/v1` | `lib/api/components.ts` |

## Observations

- L’API est fragmentée en nombreux routers indépendants, ce qui augmente la surface de liaison.
- WebUI possède un client API par domaine (`src/lib/api/*.ts`), ce qui est cohérent.
- Les permissions sont visibles dans routers via `require_permission(...)` et parfois `gateway_guard(ActionType.*)`.
- Les routes `capabilities` couvrent des sous-domaines très larges (tools, servers, pipelines, prompts, analytics), pas uniquement les capacités.
- Plugins expose `/plugins/install` et `/plugins/{id}/install`, avec permissions et gateway_guard.

## Risques de contrat

- Les noms de champs frontend/backend peuvent diverger dans des cas non inspectés.
- Des services backend sont visibles côté API, mais l’UI peut ne pas les exploiter.
- Les états affichés WebUI doivent être mapés explicitement aux statuts backend (`registered`, `available`, etc.), pas à des flags simples.
