# ADR-4001 — Capability Manager centralisé dans ETHAN Core

> Correspond à la demande « ADR-001 — Capability Manager » (série 4000, car
> ADR-001 est déjà attribué à [ADR-001-agent-system.md](/docs/adr/ADR-001-agent-system.md)).

**Statut** : Implémenté
**Date** : 2026-09-23
**Implémentation** : [`core/capability_manager/`](/core/capability_manager/) —
ESR liés : [ESR-001](/docs/engineering/esr/ESR-001-capability-model.md),
[ESR-002](/docs/engineering/esr/ESR-002-installation-engine.md),
[ESR-003](/docs/engineering/esr/ESR-003-docker-provisioning.md),
[ESR-004](/docs/engineering/esr/ESR-004-local-provisioning.md)

---

## Contexte

ETHAN intègre des composants optionnels (bases de vecteurs, services,
intégrations) dont le cycle de vie — détecter, installer, configurer,
tester, activer, désinstaller — doit être piloté par l'utilisateur depuis
la WebUI. Avant ce système, la page *Settings ▸ Vector Database* affichait
les backends dans un simple `<select>` sans état réel, et aucune interface
ne pouvait distinguer un composant supporté d'un composant installé.

## Problème

1. **Aucune source de vérité** : l'état « installé/actif » n'existait nulle
   part côté Core ; chaque interface devait le deviner.
2. **Logique d'installation dangereuse** : sans cadre, du `docker run` ou du
   `pip install` pourrait être écrit dans une interface, déclenché par des
   chaînes utilisateur non validées (injection).
3. **Homonymie** : `docs/security/05-capability-system.md` décrit déjà les
   *permissions* d'agents (capabilities RBAC). Il ne s'agit pas du même
   concept ; ce document porte sur le **cycle de vie des composants
   optionnels** déployés par ETHAN.

## Décision

Créer `core/capability_manager/`, module Core propriétaire :

| Fichier | Rôle |
|---|---|
| `types.py` | `CapabilitySpec` (déclaratif, développeur-défini), `CapabilityState` (12 états + transitions légales), `ConfigField`, `HealthCheck`, `Dependency`, plans |
| `manager.py` | Machine à états, validation de configuration, opérations asynchrones, audit, événements |
| `backends.py` | Exécution par backend (`docker`, `python_package`, `node_package`, `executable`, `builtin`) avec allowlists d'actions |
| `health.py` | Paliers de santé réels (tcp, endpoint, exec, builtin) |
| `builtin.py` | Catalogue des composants intégrés (`memory`, `ollama`, `qdrant`, `chromadb`, `redis`, `searxng`, `whisper`, `mcp-filesystem`) |

L'API (`interfaces/api/routers/component_lifecycle.py`) est une **passerelle
mince** ; la WebUI
(`interfaces/webui/src/components/features/settings/components/capabilities-section.tsx`)
est un **client passif**.

## Cycle de vie — états, transitions et garanties

La machine à états est celle de
[`types.py`](/core/capability_manager/types.py) : 12 états explicites
(`SUPPORTED`, `NOT_INSTALLED`, `INSTALLING`, `INSTALLED`, `STARTING`,
`RUNNING`, `STOPPED`, `UNHEALTHY`, `CONFIGURATION_REQUIRED`, `READY`,
`UNINSTALLING`, `ERROR`) et des transitions légales
(`CapabilityState.TRANSITIONS`) — aucune opération ne saute d'état par
écriture directe. Les états intermédiaires (`BUSY` : `INSTALLING`,
`STARTING`, `UNINSTALLING`) sont visibles via `status()`.

| Opération | Pré-condition | États traversés | État final |
|---|---|---|---|
| `detect()` | — | réconciliation avec la présence réelle (backend) | `SUPPORTED` (support/dépendance manquants), `NOT_INSTALLED`, sinon `READY`/`UNHEALTHY` selon la santé |
| `plan_install()` | spec enregistrée | aucun (lecture seule) | inchangé — plan + `requires_confirmation` |
| `install()` | ≠ `BUSY` ; `READY` → idempotent | `INSTALLING` → `INSTALLED` → `STARTING` → `RUNNING` → `READY` | `READY` si santé OK, sinon `RUNNING` ; échec backend → rollback puis `ERROR` |
| `configure()` | champ ∈ `config_schema` (allowlist) | `READY`/`RUNNING` → stop + start (si déclarés) | config persistée, état inchangé |
| `test()` | — | santé réévaluée | `READY` si OK, sinon `UNHEALTHY` (`ERROR` préservé) |
| `enable()` | `READY` requis | aucun | `enabled=True`, état inchangé |
| `disable()` | — | aucun | `enabled=False`, état inchangé |
| `start()` | `STOPPED`/`INSTALLED` | `STARTING` → `RUNNING` | `READY` si santé OK, sinon `RUNNING` |
| `stop()` | `RUNNING`/`READY`/`UNHEALTHY` | — | `STOPPED` (données conservées) |
| `plan_uninstall()` | — | aucun (lecture seule) | étape `destructive=True` **seulement** si `delete_data=True` |
| `uninstall()` | dépendant actif interdit ; ≠ `BUSY` | `UNINSTALLING` (arrêt avant retrait) | `SUPPORTED`, `enabled=False`, config purgée ; erreur → `ERROR` |

Garanties verrouillées par
[`tests/core/test_capability_manager.py`](/tests/core/test_capability_manager.py)
(parcours complet inclus) :

- **Plan avant mutation** : toute mutation expose d'abord ses étapes
  (`MutationPlan`), la confirmation est déclarée par la spec développeur.
- **Rollback automatique** : un échec d'installation déclenche le rollback
  backend et ne laisse jamais le composant démarré.
- **Santé réelle** : `READY` exige un health check fonctionnel réussi —
  installé + démarré ≠ prêt.
- **Données** : conservation par défaut ; la suppression n'existe que si
  l'appelant la demande explicitement (voir
  [ADR-4003](/docs/architecture/adr/ADR-4003-data-lifecycle.md)).
- **Sécurité** : aucune chaîne utilisateur n'atteint une commande — spec
  figée + argv allowlistés (voir [ESR-006](/docs/engineering/esr/ESR-006-security-model.md)).
- **Traçabilité** : chaque mutation produit audit + événement bus, et
  l'opération reste listable (`list_operations`).

### Vocabulaire du cycle de vie : demande ↔ états implémentés

Le vocabulaire produit et les états du Core recouvrent le même cycle ; la
correspondance est verrouillée par les tests — jamais par un état en double
(ce serait une seconde vérité).

| Vocabulaire demande | Implémentation | Note |
|---|---|---|
| discovered | `SUPPORTED` | spec enregistrée + support vérifié |
| available | `NOT_INSTALLED` | installable ici (prérequis satisfaits) |
| installing | `INSTALLING` | état intermédiaire (`BUSY`) |
| installed | `INSTALLED` | présence réelle vérifiée par le backend |
| configured | `configure()` (+ `CONFIGURATION_REQUIRED`) | configuration ≠ installation |
| enabled | `enabled=True` | dimension orthogonale (activation ≠ santé) |
| healthy | `READY` | santé fonctionnelle réelle ; exigé par `enable()` |
| disabled | `enabled=False` (+ `STOPPED` si arrêté) | désactivation sans suppression |
| failed | `ERROR` | `last_error` porte la raison |
| uninstalling | `UNINSTALLING` | état intermédiaire (`BUSY`) |

### Vocabulaire : `ComponentManager`

L'API parle de « components » (`/v1/components`, router
`component_lifecycle.py`). Pour éviter toute confusion avec le
`CapabilityManager` du domaine **sécurité**
([`core/security/policy/capabilities.py`](/core/security/policy/capabilities.py),
permissions d'agents), le module expose
`ComponentManager = CapabilityManager` : une **identité stricte** (`is`),
jamais une seconde implémentation ni un wrapper (Première Loi, AGENTS.md).

## Alternatives considérées

| Alternative | Raison du rejet |
|---|---|
| Logique d'installation dans l'API FastAPI | Violerait la Première Loi (le CLI, le Desktop ne pourraient pas réutiliser) ; l'API est une interface remplaçable |
| Chaque interface gère ses composants | Duplication `docker run`/`pip install` en N endroits, incohérence d'états garantie |
| Outil externe (Portainer, Helm…) | Dépendance d'infrastructure supplémentaire, ne couvre pas `python_package`/`builtin`, ne produit pas d'états explicites |
| Stocker l'état côté frontend | Perdu à chaque reload, non partageable entre interfaces, non auditable |

## Conséquences positives

- Une seule implémentation du cycle de vie, réutilisable par WebUI, CLI et
  Desktop via la même API `/v1/components`.
- États explicites partagés (plus de « ✓ Installed » non fondé).
- Actions système figées dans la spec développeur : surface d'injection
  structurellement fermée.
- Catalogue déclaratif extensible (ajouter une spec = une fonction).

## Conséquences négatives

- Nouveau module Core à maintenir (≈ 1 700 lignes, 44 tests).
- Le déploiement Docker réel exige que l'API ait accès au binaire `docker`
  (voir [ESR-003](/docs/engineering/esr/ESR-003-docker-provisioning.md) §
  contraintes) — condition d'environnement, pas gérée par ETHAN.
- Deux concepts partagent le mot « capability » (permissions agents vs
  composants) ; la doc doit toujours les distinguer.

## Sécurité

- **Spec développeur uniquement** : les actions système vivent dans la spec
  figée ; l'utilisateur ne fournit que des valeurs typées (voir
  [ESR-006](/docs/engineering/esr/ESR-006-security-model.md)).
- RBAC par verbe (READ / EXECUTE / SETTINGS / ADMIN) côté API.
- Audit + événements bus sans secrets sur chaque mutation.

## Compatibilité avec l'architecture existante

- Respecte la Première Loi (AGENTS.md) : capacité métier → Core.
- Complète [ADR-3001](/docs/architecture/adr/ADR-3001-unified-record-store.md)
  (l'état des composants persiste dans le CoreRecordStore) et prépare
  [ADR-3004](/docs/architecture/adr/ADR-3004-vector-store-record.md) (les
  backends vectoriels deviennent des composants gérés au lieu d'un select
  statique).
- Aucune rupture d'API existante ; nouveaux endpoints uniquement.

## Amendement 2026-09-28 — prérequis déclarés, intégrité, logs

Audit de conformité de la spec produit (composants, cycle de vie, PRÉREQUIS,
SÉCURITÉ, VALIDATION) : la capacité existait déjà — le module n'a **pas** été
recréé. Trois manques réels ont été comblés dans l'existant.

### Prérequis déclarés (`Requirements`)

| Champ | Contrôle | Honnêteté |
|---|---|---|
| `os` / `arch` | `platform.system()` / `platform.machine()` | exigence absente = non contrôlée |
| `min_ram_mb` | RAM *disponible* | psutil absent → « non vérifiable », **non bloquant** |
| `min_disk_mb` | espace libre (workspace + `/var/lib/docker` pour Docker) | mesure impossible → « non vérifiable » |

Vérifiés dans `detect()` (état `SUPPORTED` + raison si non satisfaits) et dans
le pipeline d'installation (`_do_install`, avant tout appel backend). La
déclaration est exposée par `status()` (`requirements`).

### Intégrité (`provenance.checksum`)

Quand un digest sha256 est déclaré, `DockerBackend` vérifie le `RepoDigest`
réel de l'image tirée après le `pull` : non conforme ou non comparable →
échec explicite, sans conteneur créé. Champ vide = « non déclaré » — jamais
« conforme » par défaut.

### Logs composant

`CapabilityManager.logs(id, tail)` + `GET /v1/components/{id}/logs` (READ).
Docker : `docker logs --tail N` du conteneur déclaré par la spec. Les
backends sans processus permanent (`builtin`, `executable`,
`python_package`, `node_package`) répondent `available=false` + raison —
jamais de faux contenu ni de lecture arbitraire.

Verrouillé par `tests/core/test_capability_manager.py` (prérequis, intégrité,
logs) et `interfaces/api/tests/test_components_lifecycle_api.py` (RBAC READ,
passage par le Core, disponibilité honnête, `tail` borné).