# PERSISTENCE_AND_AUDIT.md

# Persistance et Audit — P0-1S HROT Security Hardening

**Repository :** `/home/fatsio/AI/Ethan`
**Branche :** `refactor/ethan-rebuild-p0`
**Date :** 2026-11-11

---

## 1. Persistance des grants PermissionService

### État actuel

`PermissionService` (dans `core/applications/permissions.py`) accepte un paramètre `store` optionnel dans son constructeur :

```python
def __init__(
    self,
    *,
    production_mode: bool = False,
    trust_verifier: Any = None,
    store: Any | None = None,
) -> None:
```

Si un `store` est fourni, les grants (`PermissionGrant`) et les requêtes (`PermissionRequest`) sont persistés via `store.save_record(...)` et rechargés via `_load_from_store()` lors de l'initialisation.

### État actuel dans la composition root (`interfaces/api/main.py`)

Dans `main.py`, l'`ApplicationIntegrationRegistry` est créé sans `permission_service` :

```python
registry = ApplicationIntegrationRegistry()
```

Ce qui entraîne la création d'un `PermissionService(production_mode=False)` **sans store** dans `ApplicationIntegrationRegistry.__init__` (ligne 124) :

```python
self.permission_service = permission_service or PermissionService(production_mode=False)
```

**Conséquence :** Les grants HROT sont en mémoire uniquement et disparaissent au redémarrage du processus API.

### Recommandation pour la production

Pour activer la persistance des grants HROT :

1. Créer un `ApplicationStateStore` avec un chemin de fichier durable :
   ```python
   from core.applications.persistence import ApplicationStateStore
   permission_store = ApplicationStateStore(path="/var/lib/ethan/permission_grants.db")
   ```

2. Créer un `PermissionService` avec ce store :
   ```python
   permission_service = PermissionService(store=permission_store, production_mode=False)
   ```

3. Passer le `permission_service` au `ApplicationIntegrationRegistry` :
   ```python
   registry = ApplicationIntegrationRegistry(permission_service=permission_service)
   ```

4. Injecter le registre dans `invoke_capability` (déjà fait via `registry.permission_service`).

### Tableau de persistance

| Composant | Stockage actuel | Persistant au redémarrage ? | Action requise |
|-----------|----------------|------------------------------|----------------|
| `PermissionService._grants` | Mémoire uniquement | Non | Passer un `ApplicationStateStore` |
| `PermissionService._decisions` (audit) | Mémoire uniquement | Non | Passer un `ApplicationStateStore` ou utiliser `EventCollector` |
| `ApplicationIntegrationRegistry._records` | Mémoire uniquement (sauf si `store` configuré) | Non | Configurer `ApplicationStateStore` |
| `CapabilityAuthorizationService._decisions` | Mémoire uniquement | Non | Passer un `store` ou utiliser `EventCollector` |

---

## 2. Piste d'audit (Audit Trail)

### Mécanisme actuel

Deux couches d'audit existent :

1. **`CapabilityAuthorizationService._decisions`** : Liste en mémoire des décisions d'autorisation (ALLOW/DENY) avec `CapabilityAuthorizationDecision` (acteur, agent, application, capacité, binding, permission, raison, horodatage).

2. **`PermissionService._decisions`** : Liste en mémoire des décisions d'évaluation de permission (`AuthorizationDecision`).

Les deux sont accessibles via la méthode `audit_trail()` qui retourne un tuple de décisions.

### Limites

- **Pas de persistance durable :** Les deux listes sont en mémoire uniquement. Au redémarrage, toute la piste d'audit est perdue.
- **Pas d'envoi vers `EventCollector` :** Les décisions d'autorisation HROT ne sont pas envoyées à l'`EventCollector` du `ApplicationIntegrationRegistry`, qui est pourtant conçu pour capturer les événements d'intégration.

### Recommandation

Pour une piste d'audit durable :

1. **Option A (recommandée) :** Après chaque décision d'autorisation dans `invoke_capability`, enregistrer l'événement via `event_collector.record()` (déjà disponible dans `ApplicationIntegrationRegistry`) :
   ```python
   registry.event_collector.record({
       "event_id": str(uuid.uuid4()),
       "schema_version": OBSERVABILITY_SCHEMA_VERSION,
       "app_id": application_id,
       "instance_id": instance_id,
       "timestamp": datetime.now(timezone.utc).isoformat(),
       "event_type": "authorization",
       "operation": "invoke_capability",
       "status": "allowed" if _hrot_decision.allowed else "denied",
       "provenance": "command_palette_authorization",
       "evidence_refs": [manifest_digest],
       "origin": "verified",
   })
   ```

2. **Option B :** Configurer un `ApplicationStateStore` pour le `PermissionService` afin de persister les grants, et utiliser une table dédiée pour les décisions d'autorisation.

### Ce qui est conservé dans l'audit (quand activé)

| Champ | Description |
|-------|-------------|
| `decision` | `ALLOW` ou `DENY` |
| `reason_code` | Code de raison (ex: `ALLOWED`, `NO_MATCHING_PERMISSION`, `MISSING_BINDING`, `UNTRUSTED_PRINCIPAL`, etc.) |
| `message` | Message descriptif |
| `actor_id` | Identité de l'acteur |
| `agent_id` | Identifiant de l'agent |
| `execution_id` | Identifiant de l'exécution |
| `application_id` | Identifiant de l'application |
| `capability_id` | Identifiant de la capacité |
| `binding_id` | Identifiant du binding |
| `permission` | Permission requise |
| `evaluated_at` | Horodatage de l'évaluation |

**Aucune donnée sensible (payload, credentials, tokens) n'est enregistrée dans la piste d'audit.**

---

## 3. Révocation des grants

Un grant peut être révoqué via `PermissionService.revoke_permission(permission_id, ...)`. Une fois révoqué, `grant.is_valid()` retourne `False`, et l'autorisation est refusée lors de l'évaluation suivante (`PermissionService.evaluate()` vérifie `grant.is_valid()`).

La révocation est persistée si un `store` est configuré (`store.save_record("permission_grants", ...)`).

---

## 4. Résumé des états de persistance

| Composant | Mémoire | Disque (si store configuré) | Survit au redémarrage ? |
|-----------|---------|------------------------------|--------------------------|
| `PermissionService._grants` | ✅ | ❌ (sauf store configuré) | Non (sauf avec store) |
| `PermissionService._decisions` | ✅ | Non | Non |
| `CapabilityAuthorizationService._decisions` | ✅ | Non | Non |
| `ApplicationIntegrationRegistry._records` | ✅ | Oui (si store configuré) | Oui (avec store) |
| `DurableHrotStore` | ✅ | Oui (JSONL ou PostgreSQL) | Oui |

---

## 5. Conclusion

La persistance des grants et de la piste d'audit est actuellement **en mémoire uniquement**. Pour une utilisation en production, un `ApplicationStateStore` doit être configuré et injecté dans le `PermissionService` et/ou l'`ApplicationIntegrationRegistry`. Cette limitation est documentée et doit être prise en compte avant tout déploiement en production nécessitant une traçabilité durable des autorisations.
