# 01 — Architecture Map

## Structure observée

- `core/` : autorité métier, managers, registries, security/HROT, applications, plugins, LLM, knowledge, capacities.
- `interfaces/api/` : FastAPI, routers, auth, permissions, persistence.
- `interfaces/webui/` : Next.js/React/TypeScript, pages/hooks/lib API.
- `interfaces/cli/`, `interfaces/desktop/` : autres interfaces.
- `examples/quantar/` : application intégrée TradingAgents.
- `core/plugins/` : services ODIN, Frame, Quantarcompose.
- `core/applications/` : manifestes, registry, discovery, lifecycle.

## Composants et état

| Composant | Emplacement | Rôle réel | État |
|---|---|---|---|
| Core Python | `core/` | autorité métier | opérationnel, large |
| API FastAPI | `interfaces/api/` | exposition HTTP/HROT | opérationnel |
| WebUI | `interfaces/webui/src/` | interface client | opérationnel mais dense |
| Application Registry | `core/applications/application_registry.py` | enregistrement app manifests | opérationnel/persisté |
| Application Discovery | `core/applications/discovery.py` | lecture manifests, état déclaré | opérationnel |
| Capability Manager | `core/capability_manager/` | capacité declaration/validation | à préciser |
| Component Lifecycle | `core/components/` + API | états runtime composants | partiel |
| Plugin Registry | `core/plugins/` | distribution/install lifecycle | opérationnel sous permissions |
| Provider Manager | `core/llm/provider_manager.py` | providers, modèles, clés mémoire | opérationnel pour locaux |
| Provider Gateway | `core/security/hrot_provider_gateway.py` | passerelle textuelle + HROT | in-process / non intégré |
| HROT Durability | `core/hrot/` | approvals/workflow durable | implémenté |
| ODIN/Frame services | `core/plugins/odin.py`, `frame.py` | contrôle local Docker apps | passerelle HTTP mince |
| Quantar service | `core/applications/quantar_service.py` | tâches one-shot container | dépend Docker image |
| Knowledge routers/services | `interfaces/api/routers/knowledge.py` | endpoints knowledge | présent |

## État général

ETHAN possède une architecture riche mais fragmentée. La Core-first strategy est bien présente. Plusieurs routes et managers existent, ce qui rend le diagnostic UX complexe car la WebUI doit composer plusieurs statuts.
