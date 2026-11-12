# Rapport d’intégration — Système de plugins conversationnels ETHAN

> **Contexte** : intégration d’un registre de plugins Core-owned (`PluginRegistry`),
> exposé via l’API `/v1/plugins/*` et rendu dans la WebUI, avec injection conversationnelle.
> Scope validé par l’architecture ETHAN (Core ≠ interface).

## 1. Objectif

Permettre à un utilisateur de **découvrir, installer, activer/désactiver, connecter** des
plugins (référentiels existants Tools/Skills/MCP) et d’en **injecter les outils dans une
conversation** sans que la WebUI ne devienne un second cerveau.

## 2. Principes d’architecture (validés)

| Couche | Responsabilité | Implémentation |
|--------|----------------|----------------|
| `core/plugins/*` | Catalogue, registre, résolution, permissions, capabilities | `types.py`, `catalog.py`, `registry.py` |
| `core/state/webui_store.py` | Compatibilité legacy (délégation au registre) | `register`, `list`, `toggle`, `connect` déléguent au `PluginRegistry` |
| `interfaces/api/routers/v1.py` | Routes HTTP `/v1/plugins/*` + `plugin_ids` dans `chat` | 12 routes + payload injection |
| `interfaces/api/main.py` | Composition root | `PluginRegistry(store, tool_registry)` injecté |
| `interfaces/webui/src/lib/api/plugins.ts` | Client API typé | `listPlugins`, `installPlugin`, `togglePlugin`, `connectPlugin`, etc. |
| `interfaces/webui/src/app/plugins/page.tsx` | Page d’administration (onglets) | Discover / Installed / My |
| `interfaces/webui/src/components/.../plugin-picker.tsx` | Sélecteur compact | contexte conversation → `plugin_ids` |

## 3. Flux

1. L’utilisateur ouvre la WebUI → appel `GET /v1/plugins` → renvoie le catalogue Core
   (manifests) fusionné avec l’état legacy.
2. `install` / `toggle` / `connect` → `POST /v1/plugins/{action}/{id}` → persiste dans le
   `core Store` (Redis/PostgreSQL) ; **aucun secret** n’est renvoyé ou stocké côté frontend.
3. Le bouton d’envoi du chat inclut `plugin_ids` dans le payload `chat`.
4. Le Core, via `resolve_conversation_tools(plugin_ids, tool_registry)`:
   - ne garde que les plugins **actifs** ET **installés** ;
   - résout leurs `tools` référencés auprès du `ToolRegistry` (live, pas statique) ;
   - injecte les tool_ids dans le pipeline existant `tool_ids` (fail-soft : inconnus et
     inactifs ignorés silencieusement).

## 4. Garanties de sécurité

- **Aucun secret** dans le code, le git, les logs, les events, la mémoire ou le frontend ;
- `connect()` rejette les champs secrets (`password`, `api_key`, `token`, …) côté frontend ;
- Le Core lit les secrets uniquement via le secret-manager (variables d’environnement / Vault) ;
- Les scopes de permissions (`read`, `action`, `manage`) contrôlent chaque mutation.

## 5. Compatibilité / Legacy

`webui_store.py` expose les anciens attributs (`{id, name, status, version}`) en lecture,
mais le **manifeste Core a priorité** sur les métadonnées ; l’état legacy est préservé par
le registre (`legacy_merge`). Aucune rupture pour les clients existants.

## 6. Tests

| Suite | Fichier | Résultat |
|-------|---------|----------|
| Core | `tests/test_plugins_core.py` (25 tests) | ✅ 25/25 |
| API | `tests/test_plugins_api.py` | ✅ |
| WebUI unit | `tests/unit/plugins/plugin-picker.test.tsx` (3 tests) | ✅ 3/3 |
| TS | `npx tsc --noEmit` (webui) | ✅ 0 erreurs |

> Note : le lancement `npx eslint` sur des fichiers individuels échoue dans cet environnement
> à cause d’une **erreur de configuration du projet** (`@eslint/eslintrc` "circle" / `plugins`)
> qui se produit également sur des fichiers *non modifiés* (`src/lib/api/plugins.ts`). Il
> s’agit d’un défaut préexistant de l’eslintrc, indépendant de cette intégration et à corriger
> dans une RFC dédiée.

## 7. Smoke test (API)

```bash
# install + enable + connect (sans secret en clair côté client)
curl -X POST "$ETHAN_API/v1/plugins/install/web-search"
curl -X POST "$ETHAN_API/v1/plugins/toggle/web-search"   # status=active
# chat avec plugin_ids → injection de tool_ids dans le payload du noyau
curl -X POST "$ETHAN_API/v1/chat" -d '{"message":"...","plugin_ids":["web-search"]}'
```

## 8. Prochaines étapes

- Finaliser `docker-compose.dev.yml` / `prod.yml` (Phase 2 du boot) ;
- Endpoint `/health/detailed` vérifiant NATS + Redis + PostgreSQL (Phase 3) ;
- Intégrer le picker dans `assistant-top-bar.tsx` (slot existant) si besoin.
