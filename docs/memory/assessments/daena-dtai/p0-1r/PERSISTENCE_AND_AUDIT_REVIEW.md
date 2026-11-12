# PERSISTENCE_AND_AUDIT_REVIEW.md

Audit D — Persistance, révocation, approbation et piste d'audit.

Mission P0-1R — Indépendant, lecture seule.

---

## 1. PermissionService — Persistance des grants

### 1.1 Implémentation (`core/applications/permissions.py` ligne 259-645)

`PermissionService` est un service **en mémoire par défaut** :

```python
def __init__(self, *, production_mode=False, trust_verifier=None, store=None):
    self._production_mode = production_mode
    self._trust_verifier = trust_verifier
    self._store = store
    self._requests: dict[str, PermissionRequest] = {}
    self._grants: dict[str, PermissionGrant] = {}
    self._decisions: list[AuthorizationDecision] = []
    if store is not None:
        self._load_from_store()
```

- Les grants (`PermissionGrant`) et requests (`PermissionRequest`) sont stockés dans des dictionnaires Python (`_grants`, `_requests`).
- Un `store` optionnel (`ApplicationStateStore`) permet la persistance et la rechargement (`_load_from_store` ligne 630-642).
- **Sans store : tout est perdu au redémarrage du processus.**

### 1.2 Injection du permission_service

Dans `CapabilityAuthorizationService.__init__` (ligne 193-211) :

```python
self.permission_service = permission_service
if self.permission_service is None:
    try:
        from core.applications.permissions import PermissionService
        self.permission_service = PermissionService(production_mode=False)
    except Exception:
        self.permission_service = None
```

Si aucun `permission_service` n'est fourni, une nouvelle instance `PermissionService(production_mode=False)` est créée **en mémoire, sans store**.

Dans `invoke_capability()` (`capability_execution.py` ligne 194-197) :

```python
perm_svc = getattr(registry, "permission_service", None)
authz = CapabilityAuthorizationService(registry=registry, permission_service=perm_svc)
```

Le `permission_service` provient du registre d'applications (`registry.permission_service`). Dans `ApplicationIntegrationRegistry.__init__` (`application_registry.py` ligne 124) :

```python
self.permission_service = permission_service or PermissionService(production_mode=False)
```

**Si le registre est créé sans `permission_service` (ce qui est le cas dans les tests et probablement en production par défaut), le `PermissionService` est en mémoire pur.**

### 1.3 Conséquence : disparition au redémarrage

Tous les `PermissionGrant` créés via `grant_permission()` ou `approve_request()` sont stockés dans `self._grants` (dictionnaire Python). Sans `store` configuré, ils disparaissent au redémarrage du processus ETHAN.

**Cela signifie :** une autorisation HROT accordée (grant) avant un redémarrage ne sera plus valide après redémarrage, et toute invocation de capacité sera refusée (étape HROT policy → `NO_MATCHING_PERMISSION` → DENY). Ce n'est pas une faille de sécurité (c'est fail-closed), mais c'est une limitation opérationnelle importante.

---

## 2. DurableHrotStore — Stockage durable des approbations

### 2.1 Implémentation (`core/hrot/durable.py`)

`DurableHrotStore` gère les approbations durables (`DurableHrotApproval`) avec :

- **Stockage JSONL** par défaut (`~/.ethan/hrot/approvals.jsonl`) — fichier append-only avec verrou thread (`threading.Lock`) et verrou fichier (`fcntl.flock`).
- **Stockage PostgreSQL** optionnel (`DATABASE_URL` ou `database_url` paramètre) via `asyncpg` avec table `hrot_approvals`.
- États : `PENDING`, `APPROVED`, `DENIED`, `EXPIRED`, `CONSUMED`.
- Méthodes : `create()`, `get()`, `list_pending()`, `resolve()` (approbation/rejet), `consume()` (consommation de l'approbation avec vérification de `content_hash`).

### 2.2 Intégration avec PermissionService

**Aucune intégration automatique n'existe entre `DurableHrotStore` et `PermissionService`.** Ce sont deux systèmes séparés :

- `DurableHrotStore` gère les approbations HROT (demandes d'approbation humaine avec preuve cryptographique).
- `PermissionService` gère les grants de permissions (résultats d'approbation).

La création d'un grant via `PermissionService.grant_permission()` ou `approve_request()` nécessite un `HumanAuthority` et optionnellement une preuve (`approval_proof`/`hrot_proof`/`proof`), mais **la preuve n'est pas automatiquement liée à une entrée `DurableHrotStore`**. Les deux systèmes vivent indépendamment.

### 1.3 Révocation

- `PermissionGrant.revoke()` marque le grant comme `REVOKED` avec timestamp. `is_valid()` retourne False si révoqué.
- `DurableHrotStore.resolve()` peut passer une approbation de `PENDING` à `APPROVED` ou `DENIED`.
- `DurableHrotStore.consume()` marque une approbation comme `CONSUMED` avec vérification du `content_hash` (anti-rejeu).
- La révocation est **immédiatement respectée** par `PermissionService.evaluate()` (ligne 548-550 : `if not valid_grants` vérifie `grant.is_revoked()`).

### 1.4 Expiration

- `PermissionGrant.is_expired()` vérifie `expires_at`.
- `DurableHrotApproval.is_expired()` vérifie `expires_at`.
- Les grants expirés sont traités comme invalides par `PermissionService.evaluate()` (ligne 548-550).

---

## 3. Piste d'audit

### 3.1 CapabilityAuthorizationService._decisions (mémoire)

```python
self._decisions: list[CapabilityAuthorizationDecision] = []
```

Chaque décision (ALLOW ou DENY) est ajoutée via `_record()` (ligne 558-563). Accessible via `audit_trail()` (ligne 565-566).

**Limitation :** stocké en mémoire uniquement. Disparait au redémarrage. L'échec de `_record()` est silencieusement ignoré (`try/except: pass` ligne 559-562).

### 3.2 PermissionService._decisions (mémoire)

```python
self._decisions: list[AuthorizationDecision] = []
```

Accessible via `audit_trail()` (ligne 644-545). Même limitation : mémoire uniquement, persiste via `_store` si configuré (`_store.save_record("authorization_decisions", ...)` ligne 598-599).

### 3.3 EventCollector / IntegrationEvent (`core/applications/observability.py`)

`ApplicationIntegrationRegistry` enregistre des événements d'intégration (`IntegrationEvent`) avec `event_id`, `schema_version`, `app_id`, `instance_id`, `timestamp`, `event_type`, `operation`, `status`, `provenance`, `evidence_refs`, `origin`. Ces événements sont produits lors de l'enregistrement d'application (ligne 233-248 de `application_registry.py`).

**Cependant, les décisions d'autorisation HROT individuelles (ALLOW/DENY par invocation) ne sont pas envoyées à `EventCollector`.** Elles sont seulement dans `_decisions` (mémoire).

### 3.4 Données sensibles dans les logs

- `capability_authorization.py` : les décisions d'autorisation contiennent `reason_code` et `message` mais **pas le payload de la requête** ni les credentials. Le `binding` (objet) est inclus dans la décision mais ne contient pas de secret.
- `invoke_capability()` : en cas d'échec HROT, le message d'erreur contient `reason_code` et `message` mais pas le payload. En cas de succès, le résultat de l'implémentation est retourné (peut contenir des données métier, mais ce n'est pas un log).
- **Pas de secrets/tokens/credentials dans les décisions d'autorisation.** CONFIRMÉ.

---

## 4. Synthèse des faiblesses de persistance et audit

| # | Faiblesse | Sévérité | Preuve |
|---|-----------|----------|--------|
| PERSIST-01 | `PermissionService` en mémoire par défaut — grants perdus au redémarrage | HIGH | `permissions.py:259-278`, `capability_authorization.py:205-211` |
| PERSIST-02 | Aucun lien automatique entre `DurableHrotStore` (approbations durables) et `PermissionService` (grants) | MEDIUM | Absence de code liant les deux systèmes |
| PERSIST-03 | Piste d'autorisation (`_decisions`) en mémoire uniquement — disparait au redémarrage | MEDIUM | `capability_authorization.py:204,558-566` ; `permissions.py:278,644-545` |
| PERSIST-04 | Pas d'envoi des décisions HROT vers `EventCollector` (observabilité événementielle) | LOW | Absence d'appel à `event_collector` dans `invoke_capability` ou `CapabilityAuthorizationService` |
| PERSIST-05 | Pas de secrets dans les décisions d'audit | CONFORME | Revue du code : `reason_code` et `message` uniquement, pas de payload |

---

## 5. Conclusion

La persistance des autorisations HROT est une **limitation majeure** : sans `store` configuré sur `PermissionService`, tous les grants disparaissent au redémarrage. Cela rend le système fail-closed (sécurisé) mais inopérant en production sans configuration de persistance.

La piste d'audit est fonctionnelle en mémoire mais non durable par défaut. Les décisions d'autorisation ne contiennent pas de données sensibles.
