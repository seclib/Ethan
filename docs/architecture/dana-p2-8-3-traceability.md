# DAĒNĀ P2.8.3 — Traçabilité automatique des interventions

> Date : 2026-11-12
> Branche : `refactor/ethan-rebuild-p0`
> Statut : IMPLEMENTED + TESTED + RUNTIME_VALIDATED
> ADR : `docs/memory/DECISIONS.md` → **D-009**

## 1. Objetif

Toute intervention technique menée sur ETHAN OS doit laisser une trace
documentaire **persistante, consultable et cumulative** dans DAĒNĀ.

Une intervention n'est pas « documentée » parce qu'un rapport a été écrit :
elle est documentée lorsque le rapport est **effectivement persisté dans le
corpus** et **relisible** par les Mechanisms Core existants.

Le dispositif couvre :

- les implémentations, corrections, modifications architecturales, de
  configuration ou de dépendances, maintenances, optimisations,
  investigations, audits, tests et modifications de sécurité ;
- OpenCode (plugin + outil d'agent), et par construction toute autre
  interface autorisée à appeler l'API ETHAN (CLI, WebUI, agents).

## 2. Principes

| Principe | Application |
|---|---|
| **Une seule source documentaire** | Le vault `daena/` via `EngineeringMemoryService`. Aucun second moteur de journalisation, aucune nouvelle base. |
| **Aucun type d'enregistrement nouveau** | Un rapport est un `ENGINEERING_EVENT`, une anomalie un `INCIDENT`, une dette une `TECHNICAL_DEBT`. P2.8.4 reste ouverte. |
| **Immuabilité** | Un document n'est jamais réécrit. Un changement d'état est un **événement corrélé** (`correlation_id`). |
| **Liens, pas duplication** | Un rapport référence ses anomalies, corrections, décisions et tests **par identifiant**. |
| **Idempotence** | Le même contenu réenregistré ne produit pas de second document. |
| **Aucune fuite de secret** | Rédaction avant persistance + `SecurityPolicy` de l'Engineering Memory en seconde barrière. |
| **Logique métier dans le Core** | `core/engineering_memory/traceability.py`. Les interfaces ne font que transporter et projeter. |

## 3. Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  Producteurs (clients, sans logique métier ni stockage propre)      │
│                                                                      │
│  ┌────────────────────┐        ┌──────────────────────────────────┐  │
│  │ Plugin OpenCode    │        │ CLI / WebUI / agents / API       │  │
│  │ .opencode/plugins/ │        │                                  │  │
│  │ daena-traceability │        │                                  │  │
│  │  • capture auto    │        │                                  │  │
│  │  • outil agent     │        │                                  │  │
│  └─────────┬──────────┘        └───────────────┬──────────────────┘  │
└────────────┼─────────────────────────────────────┼────────────────────┘
             │  HTTP  POST /v1/memory/traceability/*                    │
             │  Authorization: Bearer <clé ethan_… | JWT>               │
             ▼                                                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ETHAN Core                                                           │
│                                                                      │
│  interfaces/api/routers/engineering_memory.py                        │
│    → projection HTTP (aucune logique métier)                         │
│                    │                                                 │
│                    ▼                                                 │
│  core/engineering_memory/traceability.py                             │
│    • TraceabilityService      (écriture, transitions, contrôle)     │
│    • InterventionReport       (rubriques A→J)                        │
│    • report_from_payload()    (coercion des interfaces)              │
│    • redact() / redact_structure()                                  │
│                    │                                                 │
│                    ▼                                                 │
│  core/engineering_memory/service.py → ObsidianPersistence            │
│                    │                                                 │
│                    ▼                                                 │
│  core/projects/anchors.py (P2.8.2) — rattachement projet            │
└───────────────────────┬──────────────────────────────────────────────┘
                        ▼
        ┌───────────────────────────────┐
        │  Vault DAĒNĀ (daena/)        │
        │  Archives/Events/             │  rapports d'intervention
        │  Knowledge/Incidents/         │  anomalies
        │  Operational-Memory/          │  dettes techniques
        │  Knowledge/Decisions/        │  décisions (P2.8.4)
        └───────────────────────────────┘
```

### 3.1 Fichiers

| Fichier | Rôle |
|---|---|
| `core/engineering_memory/traceability.py` | Modèle + service Core (nouveau) |
| `core/engineering_memory/models.py` | Champ `metadata` optionnel sur `MemoryRecord` (étendu) |
| `core/engineering_memory/persistence.py` | Frontmatter robuste, fichiers illisibles isolés, comparaison canonique JSON (corrigé) |
| `core/engineering_memory/security.py` | Contrôle des secrets dans la charge utile structurée (étendu) |
| `interfaces/api/auth.py` | `require_memory_scope()` — portée machine ou permission RBAC (nouveau) |
| `interfaces/api/routers/engineering_memory.py` | 7 routes `/v1/memory/traceability/*` (nouveau) |
| `interfaces/api/main.py` | Câblage du service Core (étendu) |
| `.opencode/plugins/daena-traceability.ts` | Plugin OpenCode : capture automatique + outil `daena_traceability` (nouveau) |
| `tests/core/test_traceability.py` | 28 tests Core (nouveau) |
| `interfaces/api/tests/test_traceability_api.py` | 12 tests API / HROT (nouveau) |

### 3.2 Extension du modèle `MemoryRecord`

Le modèle canonique (`daena/Knowledge/Architecture/MEMORY_DATA_MODEL.md`)
ne prévoit qu'un champ `notes` texte. Le contrôle automatique de fin
d'intervention doit pouvoir vérifier huit conditions **sans parser du
Markdown** : un champ `metadata: dict | None` optionnel a été ajouté.

```yaml
metadata:
  intervention_id: EVT-20261112T092021277000-OPENCODE
  kind: intervention
  traceability_schema: 1.0.0
  nature: maintenance
  validation_level: NOT_VERIFIED
  files_modified: [fichier.txt]
  tests: [{name: ..., command: ..., passed: 3, failed: 0}]
  anomalies: [{anomaly_id: ..., state: OPEN}]
  ...
```

Rétrocompatibilité vérifiée : les enregistrements existants n'ont pas de
`metadata` et se relisent identiquement ; la comparaison d'idempotence
utilise désormais une forme canonique **JSON** (le YAML relit certaines
chaînes comme des dates, ce qui produisait de faux conflits).

## 4. Modèle de données

### 4.1 Rapport d'intervention — `ENGINEERING_EVENT`

| Champ | Rubrique | Description |
|---|---|---|
| `intervention_id` | A | `EVT-<AAAAMMJJTHHMMSSffffff>-<ORIGINE>` |
| `created_at` | A | Horodatage ISO-8601 |
| `project_id` | A | Projet (ancre P2.8.2) ; `null` = global |
| `mission` / `phase` | A | Rattachement de chantier |
| `agent` | A | Agent ou outil intervenant |
| `session_id` | A | Session OpenCode (traçabilité inter-sessions) |
| `nature` | A | 13 natures (feature, bugfix, architecture, configuration, dependency, maintenance, optimization, investigation, audit, testing, security, documentation, refactoring) |
| `status` | A | Statut du document (ensemble.registry) |
| `validation_level` | A/H | `IMPLEMENTED`, `TESTED`, `RUNTIME_VALIDATED`, `E2E_VALIDATED`, `PARTIAL`, `BLOCKED`, `NOT_VERIFIED` |
| `context`, `initial_problem`, `initial_state`, `pre_existing_anomalies`, `constraints` | B | État initial |
| `work_description`, `features`, `components`, `files_created`, `files_modified`, `files_deleted`, `schema_or_config_changes`, `change_reasons` | C | Travaux réalisés |
| `corrections[]` | D | Problème, cause racine, solution, composants, tests, résultat |
| `anomalies[]` | E | Identifiant, description, composant, gravité, impact, cause, état, référence |
| `security_findings[]` | F | Nature, composant, risque, impact, mesures correctives, état, tests |
| `technical_debt[]` | G | Identifiant, description, origine, justification, risque, priorité, action, dépendances, statut |
| `tests[]`, `tests_not_run[]`, `validation_limits[]` | H | Tests, commandes, résultats, limites |
| `decisions[]` | I | Décision, raisons, alternatives, conséquences, ADR |
| `remaining_work[]`, `deferred_actions[]`, `next_steps[]`, `persistent_risks[]` | J | Travaux restants |

### 4.2 Anomalie — `INCIDENT`

Document **immuable** dont le statut reste `OPEN`. L'évolution est portée
par des événements `ENGINEERING_EVENT` corrélés :

```
INC-2026-001-XXX            (document, état OPEN, immuable)
  └─ INC-2026-001-XXX-ST-FIXED-001   (événement corrélé, état FIXED)
```

États de la nomenclature : `OPEN`, `INVESTIGATING`, `FIXED`, `DEFERRED`,
`BLOCKED`. Le statut **document** reste dans l'ensemble du registre
(`OPEN`, `INVESTIGATING`, `MITIGATED`, `RESOLVED`, `VERIFIED`,
`FALSE_POSITIVE`) ; l'état fin est porté par l'événement de transition.

### 4.3 Dette technique — `TECHNICAL_DEBT`

Destination `Operational-Memory/`, statut `IDENTIFIED`. Ce n'est **pas** un
bug : une dette est conservée avec son origine, sa justification de
maintien, son risque et l'action recommandée.

### 4.4 Décision — `Decision`

Le champ `decisions[]` du rapport décrit la décision et renvoie à son ADR.
La **promotion** d'une décision vers un document `Knowledge/Decisions/`
reste hors périmètre (P2.8.4).

## 5. Cycle de vie d'une intervention

```
   ┌──────────────┐   agent termine un tour    ┌───────────────────┐
   │  Agent        │ ─────────────────────────►│ Plugin OpenCode   │
   │  (OpenCode)   │   session.execution.*     │ capture auto      │
   └──────────────┘                           └─────────┬─────────┘
                                                        │ POST /interventions
   ┌──────────────┐   outil daena_traceability           │
   │  Agent        │ ───────────────────────────────────►│
   │                │   rapport / anomalie / dette        │
   └──────────────┘                                     │
                                                        ▼
                                        ┌────────────────────────────┐
                                        │ TraceabilityService        │
                                        │ (Core)                     │
                                        │  • redaction des secrets   │
                                        │  • contrôle des statuts    │
                                        │  • écriture immuable       │
                                        │  • ancrage projet          │
                                        └───────────┬────────────────┘
                                                    ▼
                                   ┌────────────────────────────────┐
                                   │ Vault DAĒNĀ (Obsidian)        │
                                   │ + audit _meta/MEMORY_EVENT_LOG│
                                   └────────────────────────────────┘
```

### 5.1 Contrôle de fin d'intervention — 8 conditions

`POST /v1/memory/traceability/interventions/{id}/complete` (ou
`TraceabilityService.complete()`) vérifie :

| # | Condition | Contrôle |
|---|---|---|
| 1 | Un rapport a été créé ou complété | `report_exists` + `required_sections` |
| 2 | Les modifications réalisées sont documentées | `modifications_documented` |
| 3 | Les corrections sont recensées | `corrections_recensees` |
| 4 | Les anomalies découvertes sont enregistrées | `anomalies_enregistrees` |
| 5 | Les dettes techniques identifiées sont conservées | `dettes_conservees` |
| 6 | Les tests et leurs résultats sont documentés | `tests_documented` |
| 7 | Les travaux non terminés sont identifiés | `travaux_restants_identifies` |
| 8 | Le rapport est persistant et consultable | `report_persisted` (le fichier existe) |

La réponse distingue explicitement `complete`, `persisted`, `missing` et
`unresolved_anomalies`. **Un rapport non persisté ne peut pas être déclaré
documenté** : la route renvoie `409` avec le détail des conditions en échec.

Condition 2 : une intervention sans modification de fichier (investigation,
audit, documentation, test) est admise si sa description est renseignée ;
sinon le rapport est considéré comme insuffisamment documenté.

### 5.2 Échec de persistance

Si l'écriture dans le vault échoue :

1. l'échec est **signifié** (`status: failed`, `persisted: false`, `error`) ;
2. une **trace de secours** est écrite hors du corpus, au format identique
   (frontmatter YAML + corps Markdown), donc rejouable :
   `~/.ethan/traceability-fallback/<id>.md` (+ `<id>.json`) ;
3. la reprise avec le **même contenu** ne crée pas de doublon
   (comparaison de signature) ; un contenu différent est conservé dans une
   variante numérotée.

La route API renvoie `503` dans ce cas. Le plugin OpenCode applique la même
logique : si l'API est injoignable, il journalise l'échec et écrit
`<projet>/.ethan/traceability-fallback/<id>.json`.

## 6. Intégration OpenCode

### 6.1 Point d'intégration réel

`~/.config/opencode/hooks/` est un mécanisme **Claude Code** (plugin ECC) :
il n'est pas exécuté par OpenCode. Le point d'intégration effectif est le
système de **plugins** OpenCode : `.opencode/plugin/` ou `.opencode/plugins/`
(chargement automatique, sans configuration).

### 6.2 Plugin `daena-traceability`

`.opencode/plugins/daena-traceability.ts`

**Capture automatique.** Le plugin s'abonne à
`session.execution.succeeded` et `session.execution.failed`.

> **Vérification réelle** : `session.idle` existe dans le binaire OpenCode
> mais **n'est pas émis** en v2.2.6. Les événements réellement observés lors
> d'un tour d'agent sont `session.execution.started/succeeded/failed`,
> `session.step.*`, `session.tool.*`, `session.text.*`, etc. La capture se
> déclenche sur `session.execution.succeeded` — **validé en exécution réelle**.

À chaque fin d'exécution, le plugin :

1. lit `ctx.vcs.status()` → `{ location, data: [{ file, status, additions, deletions }] }` ;
2. ignore les tours sans modification de fichier ;
3. déduplique par **signature** du jeu de fichiers (stockage plugin
   `ctx.storage`, clé par session) : un même état de l'arbre ne produit pas
   un second rapport ;
4. construit un rapport `NOT_VERIFIED` (la capture automatique ne connaît
   pas le contenu du travail, seulement ses traces materializees) ;
5. POST `/v1/memory/traceability/interventions`.

**Enrichissement par l'agent.** L'outil `daena_traceability` est enregistré
par le plugin. Actions : `report`, `anomaly`, `transition`, `debt`,
`complete`, `list`. Il ne contient aucune logique : il transporte la charge
utile vers le Core.

### 6.3 Configuration

| Variable | Rôle | Stockage |
|---|---|---|
| `ETHAN_API_URL` | URL de l'API ETHAN (défaut `http://127.0.0.1:8000`) | environnement |
| `ETHAN_TRACEABILITY_KEY` | Clé de service `ethan_…` portant la portée `memory:traceability` | environnement |
| `ETHAN_TRACEABILITY_AGENT` | Nom d'agent enregistré dans le rapport | environnement |
| `ETHAN_TRACEABILITY_PROJECT` | Projet par défaut (ancre P2.8.2) | environnement |
| `ETHAN_TRACEABILITY_DEBUG` | `1` active la trace de diagnostic (fichier) | environnement |

Le secret **n'est jamais écrit dans le dépôt**. Sans clé, le plugin se
déactive explicitement et le signale : aucune traçabilité n'est prétendue.

### 6.4 Limites du plugin

- La capture automatique ne connaît que l'**état de l'arbre de travail** :
  ni le raisonnement, ni les tests exécutés, ni les anomalies. Elle est donc
  `NOT_VERIFIED` par construction ; l'enrichissement passe par l'outil.
- La granularité est le **tour d'agent**, pas la session complète : plusieurs
  rapports peuvent concerner une même session (un par jeu de fichiers
  distinct).
- `ctx.vcs.status()` ne voit que le dépôt courant ; un travail effectué
  dans un worktree annexe n'est pas couvert.

## 7. API HTTP

Base : `/v1/memory/traceability`

| Méthode | Route | Effet |
|---|---|---|
| `POST` | `/interventions` | Enregistre un rapport (201 / 409 / 503) |
| `GET` | `/interventions` | Liste les rapports (limit, défaut 50) |
| `GET` | `/interventions/{id}` | Rapport + structure + événements corrélés |
| `POST` | `/interventions/{id}/complete` | Contrôle des 8 conditions (200 / 409) |
| `POST` | `/anomalies` | Enregistre une anomalie (201 / 409 / 503) |
| `POST` | `/anomalies/{id}/transition` | Transition d'état corrélée (201 / 422) |
| `POST` | `/debts` | Enregistre une dette (201 / 409 / 503) |

L'identifiant d'intervention est **généré par l'API** lorsqu'il est absent.

## 8. Permissions (HROT)

Les routes de traçabilité acceptent deux formes d'autorisation, vérifiées
sur le **principal vérifié** (`AgentPrincipal`) :

1. une **portée** `memory:traceability` — clé de service `ethan_…`, JWT de
   service, ou JWT porteur de la portée ;
2. une **permission RBAC** — `record` en écriture, `read` en lecture
   (sessions humaines).

`require_memory_scope()` (nouveau, `interfaces/api/auth.py`) porte cette
double vérification. Le rôle `api-key` n'ayant aucune permission RBAC, une
clé de service est refusée par `require_permission` : les routes de
traçabilité utilisent donc la dépendance par portée, sur le modèle existant
des routes machine à machine (`odin_ai`, `gods_eye_view_ai`).

Rien n'est contourné : le principal est construit par
`build_agent_principal()`, lui-même alimenté par le middleware
d'authentification après validation de la clé ou du jeton.

## 9. Règles de conservation

1. Un document n'est **jamais écrasé**. Un identifiant réutilisé avec un
   contenu différent produit un conflit (`409`) et un événement corrélé
   qui trace la divergence.
2. L'historique d'une anomalie est porté par ses **événements corrélés** :
   le document d'origine reste lisible et la chronologie est reconstituable.
3. Le rapport **référence** ses anomalies, dettes, failles et décisions par
   identifiant ; il ne les recopie pas comme documents indépendants.
4. Une information non rattachée à un projet reste **globale** : aucune
   appartenance n'est déduite.
5. Les secrets sont **redigés** avant persistance ; un marqueur explicite
   `[REDACTE…]` est accepté par la `SecurityPolicy` (il n'est pas un
   secret), tout autre secret est refusé.
6. Les archives sont **immuables** (`daena/Archives/` ne se modifie pas) :
   les rapports d'intervention y sont écrits une fois.

## 10. Procédures de diagnostic

| Symptôme | Piste |
|---|---|
| Aucun rapport créé par OpenCode | Vérifier `ETHAN_TRACEABILITY_KEY` (le plugin se désactive sans clé) ; activer `ETHAN_TRACEABILITY_DEBUG=1` et lire le fichier de trace. |
| Le plugin ne se charge pas | `opencode plugin list` — le plugin doit apparaître en source `local`. |
| L'événement de fin n'est pas émis | Le plugin s'abonne à `session.execution.succeeded` ; `session.idle` n'est pas émis en v2.2.6. |
| L'API refuse la clé | La clé doit porter la portée `memory:traceability` ; sinon `403`. |
| Le rapport est écrit hors du vault | Le processus n'a pas les droits d'écriture sur `daena/` : la trace de secours est dans `~/.ethan/traceability-fallback/`. |
| `complete` renvoie `409` | Consulter `checks` et `missing` : la section fautive est nommée. |
| Un document du corpus est illisible | Il est listé dans `invalid_records` de `verify_integrity()` et **isolé** : il n'interrompt plus la lecture du corpus. |

## 11. Limites connues

| Limite | Statut |
|---|---|
| Le vault `daena/` est en lecture seule pour l'utilisateur hôte (uid 1000) ; l'écriture passe par le conteneur `ethan-api` (uid 10001). | Environnement — vérifié |
| Deux fichiers du corpus (`Plan directeur Chantier DAĒNÃ P2.8.md`, `Plan_stabilité_restructuration.md`) sont root-owned et illisibles ; ils sont isolés par la lecture, pas supprimés. | Anomalie pré-existante (A1) |
| La granularité automatique est le tour d'agent, pas l'intervention métier. | Accepté — l'outil agent permet l'enrichissement |
| Les décisions ne sont pas promues en documents `Decision`. | Hors périmètre (P2.8.4) |
| Le registre documentaire (`ResourceRegistry`) n'est pas branché sur le store partagé. | Hors périmètre (P2.8.6) |
| Les missions et sessions archivées ne sont pas persistées. | Hors périmètre (P2.8.7) |
| Les rapports ne sont pas indexés par le `VaultService` (recherche plein texte). | Hors périmètre |

## 12. Tests

| Fichier | Contenu |
|---|---|
| `tests/core/test_traceability.py` | 28 tests : création, correction, anomalie non résolue, faille, dette, tests, association projet/phase, historique, absence d'écrasement, persistance après redémarrage, erreur de persistance, reprise sans doublons, absence de fuite de secrets, non-régression DAĒNĀ. |
| `interfaces/api/tests/test_traceability_api.py` | 12 tests : 401 sans identité, 403 sans portée, 201 avec portée, session admin, cycle documentaire complet, conflit 409, contrôle de fin, état invalide 422. |

La persistance est **réelle** : les documents sont écrits sur disque via
`ObsidianPersistence` (frontmatter YAML + corps Markdown), relus par une
nouvelle instance de service (redémarrage simulé) et vérifiés octet par
octet en cas de conflit.

Non-régression : `tests/core/` = **938 passés** (910 + 28), 27 échecs et
8 erreurs **pré-existants** inchangés ; `interfaces/api/tests/` = 356 passés,
1 ignoré.
