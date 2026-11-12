# Session — 2026-11-12 — DAĒNĀ P2.8.0 : Correspondance documentaire

Mission : réparer les correspondances entre les catégories documentaires
configurées dans `EngineeringMemoryRegistry` et les emplacements réellement
présents dans le corpus `daena/`, sans toucher au corpus.

---

## 1. Changements effectués

### `core/engineering_memory/registry.py` (modifié)

- **4 destinations corrigées** vers le corpus réel :
  - `COMPONENT` : `Knowledge/Components` → `Knowledge/Composants`
  - `VERIFICATION` : `Knowledge/Tests` → `Knowledge/Tests-et-Preuves`
  - `TEST_RESULT` : `Knowledge/Tests` → `Knowledge/Tests-et-Preuves`
  - `DEPENDENCY` : `Knowledge/Dependencies` → `Knowledge`
- **7 destinations vérifiées correctes et inchangées** : `DECISION`,
  `ENGINEERING_EVENT`, `INCIDENT`, `REPAIR`, `TECHNICAL_DEBT`, `EVIDENCE`,
  `AGENT_REPORT`.
- **3 méthodes en lecture seule ajoutées** :
  - `destination_exists(root, record_type) -> bool`
  - `resolve_destination(root, record_type, record_id, title) -> (Path, bool)`
  - `corpus_mapping() -> dict[str, dict[str, str]]`

### `core/engineering_memory/persistence.py` (modifié)

- `ObsidianPersistence.__init__` accepte `require_existing_destination: bool = False`.
- `write()` refuse, dans ce mode, de créer un répertoire de destination absent
  (`ValidationError`).
- `destination_exists(record_type)` ajouté (lecture seule).

### `core/engineering_memory/service.py` (modifié)

- `EngineeringMemoryService.__init__` accepte `require_existing_destination`.
- `destination_status(record_type)` et `corpus_mapping()` ajoutés (lecture seule).

### `tests/core/test_engineering_memory_destination_mapping.py` (créé)

34 tests ciblés.

### `docs/architecture/dana-p2-7-knowledge-discovery.md` (modifié)

Section §11 « Correspondance documentaire Engineering Memory (P2.8.0) » ajoutée :
correspondance canonique, comportement de `destination_for()`, règles de
protection du corpus. Section « Tests » complétée.

### `docs/memory/PROJECT_STATE.md` et `docs/memory/DECISIONS.md` (modifiés)

Append de l'état de session ; décision **D-006** ajoutée.

---

## 2. Tests exécutés

```bash
cd AI/Ethan
.venv/bin/python -m pytest tests/core/test_engineering_memory_destination_mapping.py -q
# 34 passed

.venv/bin/python -m pytest tests/core/test_engineering_memory.py \
  tests/core/test_engineering_memory_vault.py \
  tests/core/test_engineering_memory_adapters.py \
  tests/core/test_engineering_memory_security.py \
  tests/core/test_agent_manager_engineering_memory.py -q
# 28 passed

.venv/bin/python -m pytest tests/interfaces/ -k "memory or knowledge or engineering" -q
# 11 passed, 199 deselected

.venv/bin/python -m pytest tests/core/ -q --no-header -p no:cacheprovider \
  --ignore=<11 fichiers en erreur de collection pré-existante>
# 27 failed, 859 passed, 1 skipped, 8 errors
```

Les 27 échecs et 8 erreurs sont **pré-existants** (identiques au baseline du
12 novembre : `test_rust_bridge.py` ×23, `test_technology_independence.py`,
`test_model_pipeline_full.py`, `test_model_hub.py`,
`test_application_e2e_phase14.py`, `test_intent_routing.py`).

---

## 3. Résultats

| Indicateur | Valeur |
|---|---|
| Mappings examinés | 11 |
| Mappings corrigés | **4** |
| Mappings vérifiés corrects | **7** |
| Destinations existantes dans le corpus réel | **11 / 11** |
| Tests P2.8.0 | **34 / 34** |
| Non-régression EM | 28 / 28 |
| Non-régression API memory/knowledge | 11 / 11 |
| Suite `tests/core/` | 859 passés (825 + 34) |
| Fichiers du corpus avant / après | 868 / 868, **SHA256 identiques** |
| Répertoires du corpus avant / après | 116 / 116, **identiques** |

---

## 4. Preuves de non-modification du corpus

Manifeste SHA256 de tous les fichiers de `daena/` calculé avant et après
intervention : **différence vide** (aucun fichier modifié, ajouté ou
supprimé). Liste des répertoires : **identique** (aucun répertoire créé,
supprimé ou renommé). Aucun document déplacé, renommé, copié ou modifié.

---

## 5. Hypothèses

- Le corpus de référence est `/home/fatsio/AI/Ethan/daena`, valeur par défaut
  de `ETHAN_ENGINEERING_MEMORY_ROOT` (`interfaces/api/main.py:280`,
  `interfaces/api/routers/engineering_memory.py:30`). Les tests lisent cette
  variable et sont ignorés si le corpus est absent.
- `daena/Metadata/REGISTRY.md` est un document `PROPOSED` du 2026-11-03, antérieur
  à la migration vers les noms de répertoires français. Il n'a pas servi de
  référence, mais en est la source historique.
- `DEPENDENCY` n'a pas de sous-répertoire dédié dans le corpus. La destination
  retenue est la couche `Knowledge`, conformément à la table de routage du
  corpus (`daena/AGENTS.md` : « dépendance → `Knowledge/...` »).

---

## 6. Anomalies restantes

- `daena/Metadata/REGISTRY.md` reste périmé : il annonce `Knowledge/Tests` et
  `Knowledge/Components`. Sa correction modifierait un contenu du corpus, ce
  que les règles de protection de P2.8.0 interdisent. → mission documentaire
  dédiée, avec approbation de l'opérateur.
- L'API `uvicorn` tourne sans `--reload` : le processus en mémoire porte encore
  le code précédent. La correction sera effective au prochain redémarrage.
  `/health` reste à 200, `/v1/memory/health` à 401 (inchangé).
- `daena/Metadata/REGISTRY.md` et `daena/Knowledge/Architecture/MEMORY_DATA_MODEL.md`
  mentionnent encore le préfixe de racine historique `Obsidian/` (le dossier a
  été renommé `daena/`).

---

## 7. Tâches non terminées

- **P2.8.1 non commencée** (conformément à la porte de sortie de P2.8.0).
- Correction de `daena/Metadata/REGISTRY.md` et `MEMORY_DATA_MODEL.md` :
  hors périmètre de P2.8.0 (interdit par les règles de protection du corpus).
- P2.8.2 (ancrage projet), P2.8.3 (relations dirigées) : non commencées.
