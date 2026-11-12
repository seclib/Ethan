# ESR-002 — Installation Engine

**Statut** : Implémenté
**Date** : 2026-09-23
**Décision parente** : [ADR-4002](/docs/architecture/adr/ADR-4002-install-on-demand.md)
**Code** : [`core/capability_manager/manager.py`](/core/capability_manager/manager.py),
[`interfaces/api/routers/component_lifecycle.py`](/interfaces/api/routers/component_lifecycle.py)

---

## 1. Pipeline d'installation

```text
Detect                detect() — support, prérequis, dépendances, présence, santé
   ↓
Resolve dependencies  _check_dependencies() — système + capability, optionnelles ou non
   ↓
Prerequisites         _check_requirements() — compatibilité (os/arch) + ressources déclarées
   ↓
Prepare               POST /plan → MutationPlan (étapes descriptives, placeholders {config.*} résolus)
   ↓
Install               backend.execute("install") — actions allowlistées
   ↓
Configure             _validate_config() + fusion persistée (write-only)
   ↓
Start                 backend.execute("start") — si start_actions
   ↓
Health check          HealthChecker.evaluate() — paliers basic → functional
   ↓
Validate              transitions STARTING → RUNNING → READY (jamais de saut)
   ↓
Ready                 état persisté + événement bus + audit
```

## 2. Opérations asynchrones

`install` et `uninstall` répondent **202** avec `{operation_id}`.
Progression réelle (aucune simulation) via :

```text
GET  /v1/components/operations                  (READ)
GET  /v1/components/operations/{id}             (READ)
POST /v1/components/operations/{id}/cancel      (ADMIN)
```

`OperationStatus` : `progress` (0–100, calculé sur les étapes réellement
exécutées), `steps_done: [(step, ok, detail)]`, `cancel_requested`,
`done`, `error`. La WebUI poll à 1 s
(`OperationProgress` dans `capability-dialogs.tsx`).

## 3. Rollback

- **Install** : si une étape échoue après exécution, `backend.rollback()`
  est appelé (Docker : tentative de suppression du conteneur créé ; pip :
  `pip uninstall` des paquets posés), puis transition vers
  `NOT_INSTALLED` et `ERROR` avec message.
- **Uninstall** : pas de rollback implémenté — un échec d'arrêt/suppression
  laisse l'état `ERROR` (honnête). Extension future : re-start du service.
- **Cancel** : `cancel_operation` pose `cancel_requested` et annule la
  tâche asyncio (visible sur les opérations en cours) ; sur install, le
  handler `CancelledError` positionne `ERROR` + « installation annulee ».

## 4. Erreurs (mapping HTTP)

| Cause | Core | HTTP |
|---|---|---|
| Capability inconnue | `KeyError` | 404 |
| Transition illégale (ex. stop sur non-installé, install d'un BUSY) | `TransitionError` | 409 |
| Config invalide (champ inconnu, type, borne) | `ValueError/TypeError` | 422 |
| `delete_data` sans confirmation | — | 422 |
| Échec backend (docker absent, pip en échec, endpoint mort) | `RuntimeError` → `ERROR` + `last_error` | opération `done` + `error` |

## 5. Détection (`detect()`)

Pour chaque spec enregistrée :

1. support (`check_prerequisites` du backend) ;
2. prérequis déclarés (`_check_requirements` : compatibilité os/arch +
   ressources déclarées — jamais bloquant si non mesurable) ;
3. dépendances (`_check_dependencies`) ;
4. présence installée (`_detect_installed` : inspect conteneur Docker,
   `find_spec` Python, `which` pour les backends `executable` et
   `node_package` — via le binaire du préfixe ETHAN —, ou `True` pour
   `builtin`) : seule la vérification **déclarée par la spec**
   (`verify_import`, `verify_path`, `verify_binary`) fait foi, jamais une
   présence supposée ;
5. si présent → santé (`_reconcile_health` : RUNNING/UNHEALTHY/READY).

Un composant détecté vers un état propre voit son `last_error` purgé ;
un état `ERROR` exceptionnel est déduit de l'exception de détection
(tronquée). Événements publiés : `ethan.capabilities.installed`,
`install_failed`, `install_cancelled`, `uninstalled`, `configured`,
`started`, `stopped`, `enabled`, `disabled`, `tested` (payloads sans
secret).

## 6. Amendement 2026-09-28 — prérequis, intégrité, logs

- **Prérequis déclarés** (`Requirements`) : compatibilité `os`/`arch` et
  minimums `min_ram_mb`/`min_disk_mb`, vérifiés dans `detect()` et dans le
  pipeline d'installation (étape `requirements`, avant tout appel backend) ;
  une mesure indisponible (psutil absent) est « non vérifiable », jamais
  bloquante. `status()` expose la déclaration.
- **Intégrité Docker** : après `pull`, un digest déclaré
  (`provenance.checksum`) est comparé au `RepoDigest` réel ; non conforme ou
  non comparable → échec explicite, sans conteneur créé. Champ vide = non
  déclaré, jamais « conforme » par défaut.
- **Logs composant** : `CapabilityManager.logs(id, tail)` et
  `GET /v1/components/{id}/logs` (READ). Docker : `docker logs --tail N` du
  conteneur déclaré ; les backends sans processus permanent annoncent
  l'indisponibilité (`available=false`) — jamais de faux contenu.