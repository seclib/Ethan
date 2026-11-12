# Session — 2026-11-12 — DAĒNĀ P2.8.1 : Unification de la persistance

Mission : établir un modèle de persistance cohérent, durable et partagé pour
les données DAĒNĀ, en réutilisant les mécanismes existants d'ETHAN Core.

Prérequis : P2.8.0 validée. Contraintes : aucune nouvelle base, aucun
nouveau moteur de stockage, aucune migration destructive, stash intact.

---

## 1. État Git initial et final

| | Initial | Final |
|---|---|---|
| Branche | `refactor/ethan-rebuild-p0` | identique |
| HEAD | `57e254b0` | `57e254b0` (aucun commit) |
| Modifiés (M) | 76 | 78 |
| Renommés (R) | 47 | 47 |
| Supprimés (D) | 12 | 12 |
| Non suivis (??) | 189 | 193 |
| **Total** | **324** | **330** |
| Stash | `stash@{0}: On main: audit-pre-refactoring-state` | **intact** |

Les +6 entrées non suivies : `core/resources/repository.py`,
`tests/core/test_resource_persistence_unification.py`,
`docs/architecture/dana-p2-8-1-persistence-unification.md`,
`scripts/migrate_registry_to_pg.py`, `docs/memory/sessions/2026-11-12-daena-p2-8-1-*.md`,
`docs/memory/assessments/` (déjà présent).

Aucune opération Git destructive. Aucun fichier supprimé ni déplacé. Le corpus
`daena/` est resté **strictement intact**.

---

## 2. Cartographie de la persistance avant / après

Voir `docs/architecture/dana-p2-8-1-persistence-unification.md` §2.

| | Avant | Après |
|---|---|---|
| `ResourceRecord` | fichier `registry-meta.json` | **`core_domain_records[resources]`** (autorité) ; le fichier reste export + amorçage |
| `KnowledgeNode` produits par le registre | **mémoire seule** (perdus au redémarrage) | store partagé (durables) |
| `MemoryRecord` (Engineering Memory) | fichiers `daena/` | inchangé — nature documentaire |
| `KnowledgeNode` (KnowledgeManager) | PG `knowledge` | inchangé |

---

## 3. Défauts confirmés et corrigés

| ID | Défaut | Correction |
|---|---|---|
| D1 | `KnowledgeManager()` sans store dans le registre | `KnowledgeManager(store=store)` |
| D2 | Stockage fichier hors `CoreRecordStore` | `ResourceRepository` sur le domaine `resources` |
| D3 | RAG sans store dans la découverte | store injectable ; le câblage runtime relève de P2.8.6 |
| D4 | Le fallback de chargement ignorait un chemin explicite | chemin explicite faisant foi |
| D5 | `discovered_at` / `last_verified` perdus au round-trip | relus dans `from_dict` |
| D6 | Double comptage des statuts | bloc de comptage redondant supprimé |
| D7 | `_reconstitute_pending_nodes` jamais appelé | appelé par `load_from_repository()` |

---

## 4. Fichiers créés et modifiés

### Créés

| Fichier | Rôle |
|---|---|
| `core/resources/repository.py` | `ResourceRepository` — persistance PG des ressources, domaine `resources` |
| `tests/core/test_resource_persistence_unification.py` | 25 tests ciblés |
| `scripts/migrate_registry_to_pg.py` | migration préparée, dry-run par défaut |
| `docs/architecture/dana-p2-8-1-persistence-unification.md` | architecture de persistance |
| `docs/memory/sessions/2026-11-12-daena-p2-8-1-persistence-unification.md` | ce rapport |

### Modifiés

| Fichier | Modification |
|---|---|
| `core/resources/registry.py` | injection `store` ; `persist()` ; `load_from_repository()` ; chemins de cycle de vie async ; fidélité du round-trip ; chemin explicite faisant foi |
| `core/knowledge/manager.py` | inchangé sur ce point (D-005 data de P2.7.1) |
| `docs/memory/DECISIONS.md` | ADR **D-007** |
| `docs/memory/PROJECT_STATE.md` | historique de phase |
| `docs/architecture/dana-p2-7-knowledge-discovery.md` | renvoi croisé vers le doc de persistance |

---

## 5. Tests exécutés

```bash
cd AI/Ethan
.venv/bin/python -m pytest tests/core/test_resource_persistence_unification.py -q
# 25 passed

.venv/bin/python -m pytest tests/core/test_engineering_memory_destination_mapping.py \
  tests/core/test_dana_p2_7_document_discovery.py tests/core/test_engineering_memory.py \
  tests/core/test_engineering_memory_vault.py tests/core/test_engineering_memory_adapters.py \
  tests/core/test_engineering_memory_security.py \
  tests/core/test_agent_manager_engineering_memory.py -q
# 100 passed

.venv/bin/python -m pytest tests/core/ -q --no-header -p no:cacheprovider \
  --ignore=<11 fichiers en erreur de collection pré-existante>
# 27 failed, 884 passed, 1 skipped, 8 errors
```

Les 27 échecs et 8 erreurs sont **strictement identiques** à la référence
pré-existante (pont Rust ×23, `test_technology_independence`,
`test_model_pipeline_full`, `test_model_hub`,
`test_application_e2e_phase14`, `test_intent_routing`). Aucun de ces fichiers
n'importe `core.resources` ni `core.knowledge`.

---

## 6. Preuves de durabilité et de cohérence

- `test_knowledge_nodes_created_by_discovery_are_durable` : les nœuds produits
  par la découverte sont relus depuis le store partagé.
- `test_registry_loads_from_repository` / `test_durability_after_simulated_restart` :
  un registre reconstruit relit l'état depuis la source de vérité.
- `test_round_trip_preserves_discovery_dates` : l'historique n'est plus écrasé.
- `test_registry_and_repository_agree` : mémoire et source de vérité coïncident.

---

## 7. Migration — préparée, non exécutée

```bash
.venv/bin/python scripts/migrate_registry_to_pg.py
# status=simulation, enregistrements_source=536, a_ecrire=536, ecrits=0
```

Vérifié après le dry-run : le domaine PG `resources` est **resté à 0 ligne**.
Le `--apply` a été validé sur un store **mémoire isolé** (536 écrits). Le
fichier `registry-meta.json` source est inchangé.

**La migration n'a pas été exécutée sur les données réelles** : elle requiert
une autorisation explicite distincte de l'opérateur.

---

## 8. Risques et anomalies restantes

| ID | Risque / anomalie | État |
|---|---|---|
| A1 | 2 fichiers `root` apparus dans `daena/` pendant une session | Ouverte |
| A2 | `daena/Metadata/REGISTRY.md` périmé | Ouverte (corpus non modifiable) |
| A3 | `uvicorn` sans `--reload` | Ouverte |
| A4 | `DEPENDENCY` sans sous-répertoire dédié | Ouverte |
| A5 | Contenu `daena/` en `PROPOSED` | Ouverte |
| A6 | Documentation obsolète | Partiellement traitée (`opencode.json` corrigé) |
| R1 | `ResourceRegistry` non branché sur le store partagé en production | **Assumé** — P2.8.6 |
| R2 | Domaine PG `audit_log` : 66 lignes `service.test` (données de test en base de production) | Ouverte — opérateur |
| R3 | Trois pistes d'audit coexistantes (PG, JSONL, NDJSON EM) avec périmètres différents | Inchangé — hors périmètre |

---

## 9. Niveau réel de validation

| Niveau | Éléments |
|---|---|
| **IMPLEMENTED** | `ResourceRepository`, registre unifié, `persist()` / `load_from_repository()`, fidélité du round-trip, chemin explicite faisant foi, 4 défauts de cycle de vie corrigés |
| **TESTED** | 25 tests ciblés (25/25) ; 100 tests EM/P2.7/P2.8.0 (100/100) ; suite `tests/core/` 884 passés, Δ = +25 sans régression |
| **RUNTIME_VALIDATED** | Non — le `ResourceRegistry` n'est pas encore branché sur le store partagé en production (P2.8.6). Le dry-run de migration a été exécuté sur les données réelles en **lecture seule** |
| **E2E_VALIDATED** | Non |
| **NOT_VERIFIED** | Migration réelle (non exécutée) ; durabilité en production du registre |

---

## 10. Tâches non terminées

- **P2.8.2** — non commencée.
- **P2.8.6** — câblage runtime du `ResourceRegistry` sur le store partagé
  (intégration fonctionnelle) : requis pour que la persistance unifiée soit
  effective en production.
- Migration `registry-meta.json` → PG : autorisation opérateur requise.
- Nettoyage du domaine PG `audit_log` (données de test) : opérateur.
