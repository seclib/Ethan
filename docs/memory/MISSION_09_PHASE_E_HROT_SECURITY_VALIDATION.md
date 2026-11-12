# Mission 09 — Phase E — Validation de sécurité HROT & Approval

**Nature** : audit strictement en lecture seule. Aucune opération d'écriture, aucune modification de code, aucune modification de permission ou de token.  
**Date** : 2026-11-11. Branche : `refactor/ethan-rebuild-p0`.

## 1. Résumé exécutif

Le système HROT (Human Root of Trust) est implémenté côté Core (`core/approval/engine.py`, `core/hrot/`) et exposé via l'API interne (`interfaces/api/routers/internal.py`). Les permissions sont définies dans `core/auth/__init__.py` (Enum `Permission`) et appliquées via `require_permission()` dans `interfaces/api/auth.py`.

**Verdict** : le mécanisme HROT est structuré et fail-closed pour les opérations protégées. Les routes API vérifient les permissions via `Depends(require_permission(...))`. Le CLI ne contourne pas HROT (pas d'accès direct au Core, sauf plugins documentés). Aucune vulnérabilité de contournement n'a été identifiée dans le code audité.

## 2. Architecture réelle de HROT

### 2.1 Permissions

Définies dans `core/auth/__init__.py` (Enum `Permission`) :

`READ`, `WRITE`, `ADMIN`, `CHAT`, `AGENTS`, `MEMORY`, `PLUGINS`, `SETTINGS`, `FILES`, `EXECUTE`, `ODIN_AI`, `PROPOSE`, `RECORD`, `MODIFY`, `ARCHIVE`, `VALIDATE`, `HUMAN_APPROVE`, `ADMINISTER`, `GODS_EYE_AI` (alias).

### 2.2 Application des permissions

`interfaces/api/auth.py` : `require_permission(permission)` retourne une dépendance FastAPI qui :
1. Lit `request.state.token_payload`.
2. Extrait le `role`.
3. Vérifie `rbac.has_permission(role, permission)`.
4. Lève `HTTPException(403)` si la permission est absente.

Attributs introspectables : `.permission` et `.permissions` (pour audit/matrice).

### 2.3 ApprovalEngine

`core/approval/engine.py` : moteur d'approbation asynchrone.
- `create_request()` : crée et publie une requête (asyncio.Future).
- `await_decision()` : attend la décision (timeout configurable).
- `resolve()` : résout une requête (exige une `authority` humaine avec `is_human_authority=True`, permissions `ADMIN`, `human=True` ou `principal_type="HUMAN"`, et empêche l'auto-approbation `responder != source_id`).
- `cancel()` : annule une requête en attente.

### 2.4 Human Root of Trust

`core/human_root.py` (référencé dans `internal.py`) : attaché à l'ApprovalEngine via `set_human_root()`. Les approbations sont stockées de manière durable (`core/hrot/durable.py`).

### 2.5 HROT durable (service_identities, capabilities)

`core/hrot/durable.py` et `core/applications/hrot_operations.py` : approbations persistantes pour les opérations sur les services (issue, rotate) avec vérification de hash de contenu, expiration, et consumption unique.

## 3. Matrice des six permissions principales

| Permission | Routes API (exemples) | CLI commandes | Core service protégé |
|---|---|---|---|
| READ | `GET /providers`, `GET /applications`, `GET /v1/knowledge` | `provider list`, `application list`, `knowledge list` | `ProviderManager`, `ApplicationManager`, `KnowledgeManager` |
| WRITE | `POST /v1/agents`, `POST /v1/knowledge`, `POST /chats` | `agent create`, `knowledge create`, `session create` | `AgentManager`, `KnowledgeManager`, `ChatStore` |
| PLUGINS | `POST /providers`, `POST /applications/refresh`, `POST /v1/tools/servers` | `provider create`, `application refresh`, `mcp add` | `ProviderManager`, `ApplicationManager`, `ToolServerManager` |
| EXECUTE | `POST /v1/agents/{id}/execute`, `POST /application-capabilities/{id}/invoke`, `POST /v1/system/exec/operations` | `agent run`, `application invoke`, `exec` | `AgentManager.execute()`, `ExecutionManager` |
| RECORD | `POST /v1/memory/events`, `POST /v1/memory/vault/file` | `memory record`, `memory vault-write` | `EngineeringMemoryService` |
| ADMIN | `GET /internal/approval/pending`, `POST /internal/approval/resolve`, `GET /internal/audit` | `approval pending`, `approval resolve` | `ApprovalEngine`, `AuditLog` |

## 4. Cartographie CLI → API → Core

Toutes les commandes CLI passent par le client HTTP partagé (`interfaces/cli/core/client.py` → `request_json()`). Aucun accès direct au Core (sauf plugins documentés : `PluginValidator` pour plugins locaux).

Le flux est : **CLI → api_get/api_post/... → request_json → HTTP → API route (require_permission) → Core service**.

Les permissions sont vérifiées côté API, pas côté CLI. Le CLI ne peut pas contourner HROT.

## 5. Analyse du cycle d'approbation

### 5.1 ApprovalEngine (core/approval/engine.py)

- **Création** : `create_request()` crée un `ApprovalRequest`, publie via `publish_fn`, enregistre dans `_pending` et `_requests`, et notifie le Human Root of Trust.
- **Enregistrement** : `_requests[request_id] = request`, `_pending[request_id] = future`.
- **Attente** : `await_decision()` utilise `asyncio.wait_for(asyncio.shield(future), timeout=...)`. En cas de timeout, nettoie et retourne `ApprovalStatus.TIMEOUT`.
- **Consultation** : `get_request(request_id)` retourne la requête ou None.
- **Approbation/Refus** : `resolve(request_id, approved, reason, responder, authority)` exige une `authority` humaine avec `is_human_authority=True`, permissions `ADMIN`, `human=True` ou `principal_type="HUMAN"`. Empêche l'auto-approbation (`responder != source_id`).
- **Expiration** : gérée par `await_decision()` (timeout) et par le HROT durable (expiration de l'approval record).
- **Transmission** : `future.set_result(response)` transmet la décision. Le Human Root of Trust est également notifié.
- **Traçabilité** : `_audit_log_fn` enregistre les événements (pending, timeout, resolve).
- **Protection double validation** : `resolve()` vérifie `future.done()` → retourne False si déjà résolu.

### 5.2 HROT durable (core/hrot/durable.py)

- Approbations persistantes avec hash de contenu, expiration, consumption unique.
- Vérification de scope (service_id, operation, parameters).
- Vérification de l'identité du requester (pas de self-approval).
- Expiration vérifiée avant consumption.

## 6. Recherche de contournements

### 6.1 Routes non protégées

Audit des routes API par permission. Les routes de lecture (`GET`) utilisent `Permission.READ` ou sont publiques (health, version). Les routes de mutation utilisent `WRITE`, `PLUGINS`, `EXECUTE`, `RECORD`, `ADMIN`.

**Résultat** : aucune route de mutation sans protection HROT identifiée.

### 6.2 Services appelables sans contrôle

Les services Core sont appelés via l'API. Le CLI n'a pas d'accès direct (sauf `PluginValidator` pour plugins locaux, documenté). Le `PluginValidator` est un validateur AST (lecture seule), pas un service métier.

### 6.3 Vérifications trop tardives

Les permissions sont vérifiées au niveau de la route API (FastAPI dependency injection), **avant** l'appel au service Core. Le service Core n'est jamais appelé si la permission est absente.

### 6.4 Permissions locales

Aucune permission locale dans le CLI. Le CLI ne stocke pas de permissions. Les tokens sont résolus via `get_token()` et envoyés dans l'en-tête `Authorization`.

### 6.5 Contrôles différents selon l'interface

Les permissions sont vérifiées côté API, pas côté interface. WebUI et CLI utilisent les mêmes routes API et donc les mêmes contrôles.

### 6.6 Approbations contournables

`resolve()` exige une `authority` humaine avec `is_human_authority=True` et `permissions` contenant `ADMIN`. L'auto-approbation est empêchée (`responder != source_id`). L'approbation est persistante et consommée une seule fois (HROT durable).

### 6.7 Confusion authentification/autorisation

- Authentification : JWT token (user_id, username, role).
- Autorisation : `rbac.has_permission(role, permission)`.
- Distinction claire dans `require_permission()` : vérifie d'abord le rôle (auth), puis la permission (authz).

## 7. Comparaison avec la Phase D

| Domaine | Permission attendue (Phase D) | Permission réellement vérifiée | Point de contrôle | Statut |
|---|---|---|---|---|
| Providers (create/update/delete) | PLUGINS | `require_permission(Permission.PLUGINS)` | Route API | VERIFIED |
| Models (pull) | PLUGINS | `require_permission(Permission.PLUGINS)` | Route API | VERIFIED |
| Agents (create/update/delete) | WRITE | `require_permission(Permission.WRITE)` | Route API | VERIFIED |
| Agents (execute) | EXECUTE | `require_permission(Permission.EXECUTE)` | Route API | VERIFIED |
| Applications (refresh/start/stop) | PLUGINS | `require_permission(Permission.PLUGINS)` | Route API | VERIFIED |
| Applications (validate) | READ | `require_permission(Permission.READ)` | Route API | VERIFIED |
| Applications (register/bind/activate) | PLUGINS | `require_permission(Permission.PLUGINS)` | Route API | VERIFIED |
| Applications (invoke) | EXECUTE | `require_permission(Permission.EXECUTE)` | Route API | VERIFIED |
| Knowledge (create/update/delete) | WRITE | `require_permission(Permission.WRITE)` | Route API | VERIFIED |
| Knowledge (collections CRUD) | WRITE | `require_permission(Permission.WRITE)` | Route API | VERIFIED |
| Memory (record/vault-write) | RECORD | `require_permission(Permission.RECORD)` | Route API | VERIFIED |
| Sessions (create/update/delete/add/share) | WRITE | `require_permission(Permission.WRITE)` | Route API | VERIFIED |
| MCP (add/update/enable/disable/remove/sync) | PLUGINS | `require_permission(Permission.PLUGINS)` | Route API | VERIFIED |
| Skills (create/update/delete/toggle/run) | WRITE/EXECUTE | `require_permission(Permission.WRITE/EXECUTE)` | Route API | VERIFIED |
| Missions (create/update/delete) | WRITE | `require_permission(Permission.WRITE)` | Route API | VERIFIED |
| Approval (pending/resolve) | ADMIN | `require_permission(Permission.ADMIN)` | Route API | VERIFIED |
| Chat (completions) | WRITE | `require_permission(Permission.WRITE)` | Route API | VERIFIED |
| Exec (operations) | EXECUTE | `require_permission(Permission.EXECUTE)` | Route API | VERIFIED |

## 8. Vulnérabilités et anomalies

Aucune vulnérabilité de contournement HROT identifiée.

**Observations** :
1. Le `PluginValidator` est importé directement dans le CLI (`plugin.py`, `plugin_manager.py`) — documenté comme BLOCKER (plugins locaux, pas de service métier).
2. L'ApprovalEngine accepte `authority=None` → retourne False (fail-closed). Bon.
3. L'auto-approbation est empêchée (`responder != source_id`). Bon.
4. La résolution exige `is_human_authority=True` + `ADMIN` permission. Bon.

## 9. Risques classés par criticité

| Criticité | Risque | Mitigation |
|---|---|---|
| Faible | Token bootstrap local (admin) si URL localhost | Acceptable en dev, à restreindre en prod |
| Faible | `PluginValidator` import direct (plugins locaux) | Documenté, pas de service métier |
| Aucun | Contournement HROT | Aucun identifié |

## 10. Corrections recommandées

Aucune correction nécessaire. Le système HROT est correctement implémenté et fail-closed.

## 11. Verdict

**PRÊT pour les tests d'écriture contrôlés (Phase D).**

Le CLI ne peut pas contourner HROT. Toutes les permissions sont vérifiées côté API avant l'appel au service Core. L'ApprovalEngine est fail-closed et exige une autorité humaine avec permission ADMIN. L'auto-approbation est empêchée. La traçabilité est assurée (audit log).

## 12. État Git

- Branche : `refactor/ethan-rebuild-p0`
- HEAD : `57e254b0 canvas`
- Aucun commit effectué
- Aucune modification de code
