# Session — 2026-11-12 — DAĒNĀ P2.8.3 : Traçabilité automatique des interventions

Mission : rendre toute intervention technique sur ETHAN OS **trouvable,
durable et consultable** dans DAĒNĀ, avec un enregistrement automatique
pour OpenCode et réutilisable par toute autre interface autorisée.

Contraintes : audit préalable de l'existant, aucun second moteur de mémoire,
aucune nouvelle base, aucune migration, aucun type d'enregistrement nouveau,
aucun écrasement de rapport, Git / corpus / PostgreSQL préservés.

---

## 1. État initial — mécanismes de traçabilité existants

| Composant | État initial | Réutilisé ? |
|---|---|---|
| `core/engineering_memory/` | `EngineeringMemoryService` + `ObsidianPersistence` + registre documentaire (`archives/events/`, `knowledge/incidents/`, `knowledge/decisions/`, `operational-memory/`, `_meta/`) | **Oui** — source de vérité unique |
| `core/engineering_memory/models.py` | `MemoryRecord` sans charge utile structurée | Étendu (`metadata` optionnel) |
| `core/projects/anchors.py` (P2.8.2) | `ProjectAnchorService` (async) | **Oui** — rattachement projet |
| `core/resources/repository.py` (P2.8.1) | Source de vérité par donnée, `CoreRecordStore` | Non concerné |
| `core/auth/security.py` | `SecurityPolicy` sur `id/title/source_of_fact/notes/components` | Étendu (charge utile structurée) |
| Audit | `daena/_meta/MEMORY_EVENT_LOG.ndjson` (append-only) | **Oui** |
| `~/.config/opencode/hooks/` | Mécanisme **Claude Code** (plugin ECC), non exécuté par OpenCode | **Non** — faux point d'intégration |
| OpenCode plugins | `.opencode/plugin/`, `.opencode/plugins/` (chargement auto) | **Oui** — point d'intégration réel |

**Lacunes identifiées** : aucun modèle de rapport d'intervention ; aucune
rubrique A→J ; aucun contrôle de fin ; aucune anomalie/dette/faille
documentée ; `session.idle` non émis par OpenCode v2.2.6 ; le rôle
`api-key` n'a aucune permission RBAC (les routes `require_permission` sont
inaccessibles aux clients machine).

## 2. Architecture retenue

```
Plugin OpenCode / CLI / WebUI / agents
        │  HTTP  Authorization: Bearer <clé ethan_… | JWT>
        ▼
interfaces/api/routers/engineering_memory.py   (projection HTTP, 0 logique métier)
        ▼
core/engineering_memory/traceability.py        (TraceabilityService — Core)
        ├── EngineeringMemoryService → ObsidianPersistence → vault daena/
        └── ProjectAnchorService (P2.8.2) → rattachement projet
```

Décisions structurantes (ADR **D-009**) :

- **un service Core**, pas une fonctionnalité d'interface ;
- **types existants réutilisés** : rapport = `ENGINEERING_EVENT`, anomalie =
  `INCIDENT`, dette = `TECHNICAL_DEBT` ; **aucun type nouveau** (P2.8.4
  reste ouverte) ;
- **immuabilité** : jamais de réécriture ; l'historique est porté par des
  **événements corrélés** (`correlation_id`) ;
- **charge utile structurée** : champ `metadata` optionnel sur `MemoryRecord`,
  pour que le contrôle de fin ne dépende pas d'un parsing Markdown ;
- **échec explicite** : un rapport non persisté ne peut pas être déclaré
  documenté (409 / 503) ; trace de secours rejouable hors corpus.

## 3. Fichiers créés et modifiés

### Créés

| Fichier | Contenu |
|---|---|
| `core/engineering_memory/traceability.py` | `InterventionReport` (rubriques A→J), `TraceabilityService`, `report_from_payload()`, `redact()` / `redact_structure()` — **1 550 lignes** |
| `interfaces/api/tests/test_traceability_api.py` | 12 tests API / HROT |
| `tests/core/test_traceability.py` | 28 tests Core |
| `.opencode/plugins/daena-traceability.ts` | Plugin OpenCode : capture automatique + outil `daena_traceability` |
| `docs/architecture/dana-p2-8-3-traceability.md` | Architecture, modèle, cycle de vie, permissions, diagnostic, limites |

### Modifiés

| Fichier | Modification |
|---|---|
| `core/engineering_memory/models.py` | Champ `metadata: dict | None` optionnel ; `to_dict()` préserve les dicts |
| `core/engineering_memory/persistence.py` | Frontmatter découpé **ligne par ligne** ; document illisible isolé ; comparaison canonique JSON |
| `core/engineering_memory/security.py` | Contrôle des secrets dans la charge utile ; marqueur `[REDACTE…]` accepté |
| `interfaces/api/auth.py` | `require_memory_scope()` — portée machine **ou** permission RBAC |
| `interfaces/api/routers/engineering_memory.py` | 7 routes `/v1/memory/traceability/*` + branchement du service |
| `interfaces/api/main.py` | Câblage du `TraceabilityService` sur l'EM et les `ProjectAnchorService` |
| `docs/memory/DECISIONS.md` | ADR **D-009** |
| `docs/memory/PROJECT_STATE.md` | Mise à jour d'état |

## 4. Défauts du socle corrigés (indispensables)

| Défaut | Effet avant | Correctif |
|---|---|---|
| `persistence._read` découpait le frontmatter sur la chaîne `---` | **Tout document dont le corps contient `---` (tableau Markdown) était illisible** — donc tout rapport A→J | Découpage ligne par ligne, colonne 0 |
| `persistence._read` ne gérait pas `OSError` | Un fichier root-owned **interrompait toute lecture du corpus** (GET → 500) | Le fichier est isolé et signalé `invalid_records` |
| `persistence.write` comparait les dicts | Le YAML relit « 2026-11-12 » en `date` → **faux conflits** | Forme canonique JSON (`default=str`) |
| `SecurityPolicy` ignorait `metadata` | Un secret dans une section structurée passait | Contrôle récursif de la charge utile |
| Redaction non appliquée au corps Markdown | Un secret dans une description **était persisté** | `render_markdown()` assaini |

## 5. Tests exécutés — résultats exacts

```
$ .venv/bin/python -m pytest tests/core/test_traceability.py -q
28 passed

$ .venv/bin/python -m pytest interfaces/api/tests/test_traceability_api.py -q
12 passed

$ .venv/bin/python -m pytest tests/core/ -q   # 12 fichiers de collection ignorés (pré-existants)
27 failed, 938 passed, 1 skipped, 8 errors in 65.15s

$ .venv/bin/python -m pytest interfaces/api/tests/ -q
356 passed, 1 skipped, 1 warning in 5.96s
```

- Référence pré-existante `tests/core/` : **910 passés / 27 failed / 8 errors**.
- Après P2.8.3 : **938 passés** (= 910 + 28) / **27 failed / 8 errors**
  → **identiques**. Les 27 échecs et 8 erreurs sont pré-existants
  (`test_rust_bridge` ×23, `test_technology_independence`,
  `test_intent_routing` ×8) et sans rapport avec la mission.
- `interfaces/api/tests/` : **356 passés**, 1 ignoré → aucune régression.

**Persistance réelle** : les documents sont écrits sur disque par
`ObsidianPersistence` (frontmatter YAML + corps Markdown), relus par une
nouvelle instance de service (redémarrage simulé), et comparés **octet par
octet** pour prouver l'absence d'écrasement. Aucun mock de persistance.

## 6. Preuves de persistance et d'exécution réelle

### 6.1 Capture automatique OpenCode

```
$ opencode run --standalone --auto --model opencode/beam-free \
    "Ajoute la ligne 'trace 10' au fichier fichier.txt"

# trace plugin (ETHAN_TRACEABILITY_DEBUG=1)
setup — apiUrl=http://127.0.0.1:8000 enabled=true
abonnement session.execution
evenement: session.execution.succeeded session=ses_e30f1427bffeYOlCkTmLDqOwTS
capture — sessionID=ses_e30f1427bffeYOlCkTmLDqOwTS
capture — fichiers touches=2 [...]
```

Document produit dans le corpus réel :

```
daena/Archives/Events/EVT-20261112T092021277000-OPENCODE-maintenance---evt-20261112t092021277000-opencode.md
```

### 6.2 Enrichissement par l'agent (outil `daena_traceability`)

```
> execute {"code":"return await tools.daena_traceability({\n  action: \"anomaly\", ...
Anomalie enregistrée dans DAENA.
| ID | `INC-TEST-PLUGIN-001` | Statut | recorded (persisté, aucun conflit) |
| Fichier | /home/fatsio/AI/Ethan/daena/Knowledge/Incidents/INC-TEST-PLUGIN-001-...md |
```

### 6.3 Contrôle de fin d'intervention (API conteneurisée)

```
$ curl -X POST .../v1/memory/traceability/interventions/EVT-.../complete
complete: True | persisted: True
   report_persisted True
   required_sections True - complet
   modifications_documented True - 2 fichier(s) documente(s)
   corrections_recensees True - 0 element(s)
   anomalies_enregistrees True - 0 element(s)
   dettes_conservees True - 0 element(s)
   tests_documented True - 0 element(s)
   decisions_recensees True - 0 element(s)
   travaux_restants_identifies True - 1 element(s)
```

### 6.4 Intégrité du corpus `daena/`

Comparaison avec le manifeste de référence P2.8.2 (868 fichiers) :

| | Nombre |
|---|---|
| Fichiers **supprimés** | **0** |
| Fichiers **modifiés** | **1** — `daena/_meta/MEMORY_EVENT_LOG.ndjson` (journal d'audit, append-only par conception) |
| Fichiers **ajoutés** | **17** — rapports de traçabilité créés par les tests, plus les événements EM émis par l'API au démarrage (`skill-update`, `gateway-started`) |

Aucun document préexistant déplacé, modifié ou supprimé.

## 7. État Git

| | Initial (début de session) | Final |
|---|---|---|
| Branche | `refactor/ethan-rebuild-p0` | identique |
| HEAD | `57e254b0` | `9ae9744f` |
| Entrées `git status` | 348 | 14 (+ 1 fichier non suivi) |

**Fait objectif, non causé par cette session** : un processus externe
(auteur `Seclib <thaerudit@gmail.com>`) a créé **deux commits pendant la
session** :

| Commit | Heure | Contenu |
|---|---|---|
| `95a4765b` « context » | 13:20 (+0400) | `.opencode/plugins/daena-traceability.ts`, états `.quantar-tasks/` |
| `9ae9744f` « Dispersion » | 13:24 (+0400) | `core/engineering_memory/traceability.py`, `tests/core/test_traceability.py`, `.gitignore`, journal d'audit |

Il a également modifié `.gitignore` : `Obsidian/*` → `daena/*`. Les 882
fichiers déjà suivis le restent ; la règle n'empêche que l'**ajout** de
nouveaux documents DAĒNĀ non suivis.

**Aucune opération destructive n'a été effectuée par cette session** : pas de
`reset`, pas de `clean`, pas de `stash`, pas de suppression de fichier, pas de
migration, pas d'écriture PostgreSQL, pas de modification de volume Docker
(seul `docker compose build api` + `up -d api`, sans toucher aux volumes ni
aux données).

Le stash `stash@{0}: On main: audit-pre-refactoring-state` est **intact**.

## 8. Anomalies et dettes ouvertes

| # | Élément | Statut |
|---|---|---|
| A1 | Deux documents `daena/` root-owned **illisibles** (`Plan directeur Chantier DAĒNÃ P2.8.md`, `Plan_stabilité_restructuration.md`) | Pré-existante — **isolée** (plus de crash de lecture), non supprimée |
| N1 | Le vault `daena/` est **non inscriptible par l'utilisateur hôte** (uid 1000) ; l'écriture passe par le conteneur `ethan-api` (uid 10001) | Environnement — à arbitrer (droits ou service dédié) |
| N2 | Granularité automatique = **tour d'agent**, pas intervention métier ; capture automatique `NOT_VERIFIED` | Accepté — l'outil `daena_traceability` couvre l'enrichissement |
| N3 | `require_memory_scope()` ajoute une seconde forme d'autorisation à côté du RBAC | Dette — consolidation du modèle d'autorisation à faire |
| N4 | Les rapports ne sont pas indexés par le `VaultService` (recherche plein texte) | Hors périmètre |
| N5 | Promotion des décisions en documents `Decision` non réalisée | Hors périmètre (P2.8.4) |
| N6 | `ResourceRegistry` non branché sur le store partagé | Hors périmètre (P2.8.6) |
| N7 | Missions et sessions archivées non persistées | Hors périmètre (P2.8.7) |

## 9. Niveau réel de validation

| Élément | Niveau |
|---|---|
| Service Core de traçabilité (modèle, écritures, transitions, contrôle de fin) | **IMPLEMENTED + TESTED** |
| Routes API `/v1/memory/traceability/*` | **IMPLEMENTED + TESTED** (12 tests) |
| Persistance réelle dans le vault DAĒNĀ | **RUNTIME_VALIDATED** (documents créés puis relus) |
| Contrôle de fin d'intervention sur un rapport réel | **RUNTIME_VALIDATED** (8/8) |
| Plugin OpenCode — chargement, abonnement, capture, écriture DAĒNĀ | **RUNTIME_VALIDATED** (exécution réelle) |
| Plugin OpenCode — outil `daena_traceability` appelé par un agent | **RUNTIME_VALIDATED** (exécution réelle) |
| Non-régression DAĒNĀ / API | **TESTED** (938 + 356 tests) |
| Ancrage projet d'un rapport réel | **PARTIAL** — le service d'ancrage est branché et testé (26 tests P2.8.2) ; aucun projet `p-alpha` n'existe en production, donc `anchored: false` sur les essais |
| Analyse du contenu d'un tour d'agent (raisonnement, tests) | **NOT_VERIFIED** — hors de portée du plugin ; l'agent doit appeler l'outil |
| Déploiement de la clé de service pour tous les agents | **NOT_VERIFIED** — clé créée et validée, mais la distribution aux autres agents n'est pas faite |

## 10. Modifications hors périmètre

- `core/engineering_memory/{models,persistence,security}.py` :extensions
  **nécessaires** au fonctionnement de la traçabilité (voir §4). Elles
  corrigent des défauts pré-existants du socle documentaire, sans changer le
  routage ni les formats de destination.
- `interfaces/api/auth.py` : `require_memory_scope()` — nouvelle dépendance
  d'autorisation, sur le modèle des routes machine existantes.
- Image Docker `ethan-api` reconstruite (`docker compose build api`) :
  nécessaire pour exposer les nouvelles routes en exécution réelle. Aucun
  volume ni donnée PostgreSQL touché.

## 11. Décision sur la porte de sortie

P2.8.3 est **clôturée** pour le périmètre demandé :

- aucune nouvelle phase de la roadmap n'a été amorcée ;
- P2.8.4 (types documentaires), P2.8.6 (`ResourceRegistry`) et P2.8.7
  (missions / sessions) restent **hors périmètre** et non entamés ;
- l'anomalie A1 et la dette N1 sont **signalées, non traitées** en silence.

**Attente de validation.** Deux points appellent une décision explicite :

1. **N1** — droit d'écriture sur `daena/` pour l'agent hôte, ou passage
   obligé par l'API conteneurisée ?
2. **N3** — faut-il conserver `require_memory_scope()` comme seconde forme
   d'autorisation, ou fusionner portée et RBAC ?

## 12. Récapitulatif des statuts

| Statut | Éléments |
|---|---|
| IMPLEMENTED | service Core, routes API, plugin, modèle de données, corrections du socle |
| TESTED | 40 tests dédiés ; non-régression 938 + 356 |
| RUNTIME_VALIDATED | capture automatique OpenCode, outil agent, persistance DAĒNĀ, contrôle de fin 8/8 |
| E2E_VALIDATED | parcours complet plugin → API → vault → relecture (validé manuellement sur l'API conteneurisée) |
| PARTIAL | rattachement projet en production (projet de test absent) |
| BLOCKED | aucun |
| NOT_VERIFIED | analyse du contenu d'un tour ; distribution de la clé de service aux autres agents |
