# ETHAN CLI — Contrat d'interface

**Version** : 1.0 (dérivé de l'implémentation réelle, Mission 09)  
**Dépôt** : `/home/fatsio/AI/Ethan`  
**Statut** : document de référence pour les commandes CLI existantes.

---

## 1. Principes

- ETHAN Core est la source de vérité métier.
- L'API expose les capacités de Core.
- Le CLI est un client officiel de l'API, au même titre que la WebUI.
- Aucune logique métier n'est réimplémentée dans le CLI.
- Aucune route API n'est inventée : le CLI consomme uniquement les routes existantes.
- HROT est l'autorité en matière de permissions.

## 2. Commandes

Les commandes sont enregistrées dans `interfaces/cli/registry.py` (`COMMAND_HANDLERS`).

Conventions de nommage : verbe à l'infinitif (`list`, `show`, `create`, `update`, `delete`), sous-commandes via `subcommand()`.

Aide : `ethan <cmd> --help` et `ethan help <cmd>` affichent l'aide de la commande (usage + verbes + endpoints).

## 3. Codes de sortie (contrat §5)

| Code | Nom | Signification |
|---|---|---|
| 0 | SUCCESS | Opération aboutie |
| 1 | OPERATION_FAILED | Échec générique |
| 2 | USAGE | Mauvaise utilisation CLI (argument manquant, sous-commande inconnue) |
| 3 | AUTH | Authentification requise (HTTP 401) |
| 4 | FORBIDDEN | Autorisation refusée (HTTP 403) |
| 5 | UNAVAILABLE | Service indisponible (HTTP 502/503/504 ou connexion refusée) |
| 6 | NOT_FOUND | Ressource introuvable (HTTP 404) |
| 7 | TIMEOUT | Le Core a été contacté mais n'a pas répondu dans le délai |

## 4. Sortie JSON

- `ethan -o json <cmd>` ou `ethan --json <cmd>` produit un document JSON unique sur stdout.
- Les erreurs sont sur stderr (mode humain et JSON).
- Le stdout reste propre pour le JSON de succès.
- Les secrets (`api_key`, `secret`, `token`) sont masqués (`_scrub()` dans `provider.py`, `_public_server()` dans `servers.py`).

## 5. Authentification

Ordre de résolution du token (`get_token()` dans `interfaces/cli/core/client.py`) :

1. `--token` (contexte CLI, `cli_token_explicit`).
2. Variable d'environnement `ETHAN_TOKEN`.
3. `~/.config/ethan/credentials.json` (`get_token_from_credentials()`).
4. Fallback legacy `~/.config/ethan/config.json` (champ racine `token`).
5. Bootstrap local admin (`core.security.jwt_bootstrap.create_local_token`) si l'URL cible est localhost.

## 6. Permissions HROT

- Toutes les routes API protégées utilisent `require_permission(Permission.*)`.
- Le CLI ne contourne pas HROT : pas d'accès direct au Core (sauf plugins documentés).
- HTTP 401 → exit 3 (AUTH). HTTP 403 → exit 4 (FORBIDDEN).

## 7. Timeouts

Précédence : `--timeout` > `ETHAN_TIMEOUT` > profil (explicite) > défaut de la commande.

- Commandes rapides : 5 s par défaut.
- Commandes LLM (`chat`) : 120 s par défaut.
- Streaming SSE : même délai que la commande appelante.

## 8. Gestion des erreurs

- `CLIError` avec code structuré (`API-xxx`, `unavailable`, etc.).
- `_print_error()` affiche sur stderr avec formatage couleur.
- Pas de traceback brut exposé à l'utilisateur.
- `KeyboardInterrupt` → exit 130.

## 9. Streaming

- Chat utilise SSE via `stream_sse()` (Core ChatPipeline).
- TUI consomme le même stream.
- `KeyboardInterrupt` propagé (exit 130).

## 10. Contrats API (routes principales)

### Providers
- `GET /providers`, `GET /providers/catalog`, `GET /providers/{id}`, `GET /providers/{id}/capabilities`, `GET /providers/{id}/models`

### Models
- `GET /models`, `GET /models/installed`, `GET /models/runtimes/health`, `GET /models/search`, `POST /models/pull`

### Agents
- `GET /v1/agents`, `POST /v1/agents`, `GET /v1/agents/{id}`, `PUT /v1/agents/{id}`, `DELETE /v1/agents/{id}`, `POST /v1/agents/{id}/execute`, `GET /v1/agents/{id}/resources`, `GET /v1/agents/{id}/executions`

### Applications
- `GET /v1/applications`, `GET /v1/applications/{app_id}`, `POST /v1/applications/refresh`, `GET /v1/applications/registered`, `GET /v1/applications/{app_id}/runtime`, `POST /v1/applications/{app_id}/start`, `POST /v1/applications/{app_id}/stop`, `GET /v1/application-capabilities`, `POST /v1/application-capabilities/validate`, `POST /v1/application-capabilities`, `GET /v1/application-integration/catalog`, `GET /v1/application-manifests`, `POST /v1/application-capabilities/{id}/bind`, `POST /v1/application-capabilities/{id}/activate`, `POST /v1/application-capabilities/{id}/invoke`

### Sessions (chats)
- `GET /chats`, `POST /chats`, `GET /chats/{chat_id}`, `PUT /chats/{chat_id}`, `DELETE /chats/{chat_id}`, `GET /chats/{chat_id}/messages`, `POST /chats/{chat_id}/messages`, `POST /chats/{chat_id}/share`
- Filtres : `?archived=`, `?folder_id=`, `?project_id=`, `?unassigned=`

### Knowledge
- `GET /v1/knowledge`, `GET /v1/knowledge/search`, `GET /v1/knowledge/{id}`, `POST /v1/knowledge`, `PUT /v1/knowledge/{id}`, `DELETE /v1/knowledge/{id}`
- Collections : `GET/POST /v1/knowledge/collections`, `GET/PUT/DELETE /v1/knowledge/collections/{id}`, `POST /v1/knowledge/collections/{id}/move`, `GET /v1/knowledge/collections/{id}/documents`, `POST/DELETE /v1/knowledge/collections/{id}/documents[/{doc_id}]`, `POST /v1/knowledge/collections/{id}/retrieve`, `POST /v1/knowledge/collections/retrieve-multi`, `POST /v1/knowledge/collections/{id}/reindex`
- `POST /v1/knowledge/{id}/connections`, `POST /v1/knowledge/imports`, `GET /v1/knowledge/imports/{job_id}`

### RAG / Documents
- `GET /v1/rag/documents`, `GET /v1/rag/status`, `GET /v1/rag/config`

### Memory (Engineering Memory)
- `GET /v1/memory/health`, `GET /v1/memory/events`, `GET /v1/memory/events/{record_id}`, `POST /v1/memory/events`, `POST /v1/memory/events/validate`, `GET /v1/memory/components/{component}/history`, `GET /v1/memory/records`, `GET /v1/memory/vault/tree`, `GET /v1/memory/vault/file`, `GET /v1/memory/vault/search`, `GET /v1/memory/vault/backlinks`, `GET /v1/memory/vault/graph`, `GET /v1/memory/vault/resolve`, `POST /v1/memory/vault/file`

### MCP / Tools
- `GET /v1/tools/servers`, `GET /v1/tools/servers/{id}`, `POST /v1/tools/servers`, `PUT /v1/tools/servers/{id}`, `DELETE /v1/tools/servers/{id}`, `POST /v1/tools/servers/{id}/enable`, `POST /v1/tools/servers/{id}/disable`, `POST /v1/tools/servers/sync`, `POST /v1/tools/servers/{id}/sync`

### Approval
- `GET /internal/approval/pending`

## 11. Sécurité

- Pas de secret stocké en clair dans les logs ou la sortie JSON.
- HROT vérifié côté API (pas de contournement CLI).
- MCP stdio sandboxé (Tier 3, fail-closed) quand `ETHAN_MCP_STDIO_SANDBOX=docker`.
- Provider catalog masque les champs sensibles (`_scrub()`).

## 12. Références

- `interfaces/cli/registry.py` — enregistrement des commandes.
- `interfaces/cli/core/client.py` — client HTTP partagé.
- `interfaces/cli/core/api.py` — helpers API (api_get, api_post, etc.).
- `interfaces/cli/core/context.py` — parsing des arguments globaux.
- `interfaces/cli/core/errors.py` — erreurs structurées.
- `interfaces/cli/core/exit_codes.py` — codes de sortie.
- `interfaces/cli/main.py` — dispatch et gestion des erreurs.
