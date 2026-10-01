# ESR-006 — Security Model

**Statut** : Implémenté
**Date** : 2026-09-23
**Décisions parentes** : [ADR-4001](/docs/architecture/adr/ADR-4001-capability-manager.md) (§ Sécurité),
[ADR-4003](/docs/architecture/adr/ADR-4003-data-lifecycle.md)
**Code** : [`interfaces/api/auth.py`](/interfaces/api/auth.py),
[`interfaces/api/routers/component_lifecycle.py`](/interfaces/api/routers/component_lifecycle.py),
[`core/capability_manager/manager.py`](/core/capability_manager/manager.py)
(`_validate_config`), [`core/capability_manager/backends.py`](/core/capability_manager/backends.py)
(`validate_install_actions`, `_run`), [`core/audit/`](/core/audit/)

---

## 1. Authentification

Toutes les routes `/v1/components/*` passent par le middleware JWT
(`auth_middleware` de l'API gateway). Aucune route du router n'est
publique. L'acteur (`current_user_id`) est propagé aux audits et
événements du Core.

## 2. Autorisation (RBAC par verbe)

| Endpoint | Permission minimale |
|---|---|
| `GET /components`, `GET /components/{id}`, `GET /components/{id}/logs`, `GET /components/{id}/plan[/uninstall]` | `READ` |
| `GET /components/operations`, `GET /components/operations/{id}` | `READ` |
| `POST /components/detect` | `EXECUTE` |
| `POST /components/{id}/test` | `EXECUTE` |
| `POST /components/{id}/configure`, `/start`, `/stop`, `/enable`, `/disable` | `SETTINGS` |
| `POST /components/{id}/install` | `ADMIN` |
| `POST /components/{id}/uninstall` | `ADMIN` |
| `POST /components/operations/{id}/cancel` | `ADMIN` |

Les opérations les plus lourdes (deploy/remove de services) et le
contrôle des opérations asynchrones exigent le niveau le plus élevé.

## 3. Audit logs

Chaque mutation est journalisée via `AuditStore`
(`category=SYSTEM`, `action="capability:<op>:<id>"`, actor, détails) :
`install` (erreur incluses), `uninstall` (+ `delete_data`), `configure`
(+ clés modifiées), `start`, `stop`, `enable`, `disable`. Échecs d'audit
non bloquants (log debug) — l'audit ne doit pas casser le service.

## 4. Validation des entrées

`_validate_config` (barrière n°1) :

- champs **inconnus refusés** ;
- types stricts (`string`/`int`/`bool`/`port`), bornes `min/max`,
  ensembles fermés `choices` ;
- **scalaires uniquement** : la sortie validée ne peut contenir ni liste,
  ni dict, ni fragment de commande ;
- champs `required` manquants refusés.

Les valeurs validées ne sont consommées que par **substitution
`{config.<field>}`** dans les actions déclaratives (`_subst`) — jamais
concaténées à une commande.

## 5. Restrictions des commandes

`validate_install_actions` (barrière n°2, à l'enregistrement) :

- **allowlist par backend** : une action non listée refuse l'enregistrement
  de la spec (fail-closed) ;
- spec **développeur-définie et frozen** ; les seules modifications
  runtime (`keep_data` à l'uninstall) sont temporaires et restaurées dans
  un `finally`.

Exécution (barrière n°3) : `asyncio.create_subprocess_exec` —
**jamais `shell=True`**, timeout par défaut 300 s avec kill, sortie
tronquée (800 caractères).

## 6. Prévention de command injection

Chaîne de responsabilité :

```text
Input utilisateur (JSON API)
  → _validate_config (scalaires typés, allowlist de champs)
  → substitutions {config.*} dans la spec figée uniquement
  → actions allowlistées (validate_install_actions)
  → argv figée, subprocess_exec sans shell
```

Aucune étape n'accepte une chaîne utilisateur comme commande, argument de
commande, ou fragment shell. Le health check `exec` n'exécute que des
commandes **figées dans la spec** (`hc.command`).

## 7. Opérations nécessitant confirmation

- `requires_confirmation=True` sur les specs à impact (Docker, pip) :
  le plan (`GET /plan`) doit être présenté à l'utilisateur avant
  `POST /install` (le dialog WebUI l'impose).
- Désinstallation avec suppression de données :
  `delete_data=true` **et** `confirm_delete_data=true` requis — sinon
  **422** ([ADR-4003](/docs/architecture/adr/ADR-4003-data-lifecycle.md)).

## 8. Opérations destructives

Classées par risque croissant :

1. `stop` / `disable` — réversibles, données intactes ;
2. `uninstall` (keep-data) — service retiré, données conservées ;
3. `uninstall` + `delete_data` — **irréversible** : ADMIN + double
   confirmation + plan affiché à l'avance (étape `destructive=True`) +
   audit dédié.

## 9. Secrets

Aucun secret dans les événements bus (payloads = ids, actor, flags) ni
dans les erreurs remontées (`last_error` tronqué). Les `env` de conteneurs
sont déclaratives ; les credentials éventuels passent par la couche
SecretManager (règle AGENTS.md « secret »), jamais par la spec ni la
configuration composant.