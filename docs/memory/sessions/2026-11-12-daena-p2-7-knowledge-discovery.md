# Session — 2026-11-12 — DAĒNĀ P2.7 : Knowledge Discovery natif

Mission : implémenter réellement P2.7 — découverte, classification et
référencement des connaissances documentaires dans ETHAN Core, en réutilisant
les composants existants.

---

## 1. Changements effectués

### `core/resources/discovery.py` (modifié)

- **Échappement de chaînes corrigé** : `content.split(chr(92) + "n")` découpait
  sur la séquence littérale `\n` (deux caractères) au lieu du saut de ligne.
  Remplacé par `content.split(chr(10))`. Symptôme : le titre extrait d'un
  document couvrait l'intégralité de son contenu.
- **`await` hors fonction `async`** : `discover_knowledge` et
  `discover_all_knowledge` appelaient `await` sans être `async`. Corrigé, puis
  remplacés par une architecture alignée sur `discover_skills`.
- **Module rendu importable** : ajout des fonctions de découverte des Skills
  (`_read_skill_file`, `_classify_resource`, `discover_skills`,
  `discover_all_resources`), absentes après les réécritures antérieures.
- **Import de `core.resources.registry` supprimé** — élimination du cycle
  d'import à la source.
- **Nouvelles API** :
  - `classify_document(title, domain, level, categories) -> (ResourceType, str)`
    — classification déterministe, extensible (tables `_TITLE_KEYWORDS` et
    `_DOMAIN_TYPES` ouvertes) et justifiée.
  - `discover_documents(knowledge_roots, create_knowledge_nodes)` — scan pur,
    déduplication par chemin résolu, extraction distincte de la découverte.
  - `_compute_document_stable_id(source)` — UUIDv5 ancré sur le chemin canonique.
  - `_extract_content_snippet(content, max_chars)` — extraction conditionnelle.
  - `knowledge_root_list(roots)` — normalisation des racines.

### `core/resources/registry.py` (modifié)

- **Imports de `core.resources.discovery` rétablis au niveau module** (le cycle
  n'existe plus).
- **Nouvelle API** :
  - `discover_documents(knowledge_roots=None)` — orchestrateur complet :
    scan, idempotence, détection de changement, disparition, restauration,
    persistance.
  - `index_documents(rag)` — indexation RAG réelle ; l'état `indexed` n'est posé
    que si l'ingestion aboutit.
  - `link_documents_to_skills()` — relations objectives documents↔Skills.
  - `attach_pending_nodes()` — rattachement des KnowledgeNodes après rechargement.
  - `_mark_missing_documents()`, `_is_under_roots()`, `_count_knowledge_states()`.
- **Bugs pré-existants corrigés** :
  - double comptage des statuts dans `discover_skills` (bloc
    `status_counts[new_records[-1]...]` supprimé) ;
  - `_reconstitute_pending_nodes()` n'était jamais appelé ;
  - `_update_record()` ne rafraîchissait pas le contenu du KnowledgeNode ;
  - `_has_resource_changed()` ne comparait pas les métadonnées documentaires ;
  - f-string incompatible Python 3.11 (guillemets imbriqués, PEP 701) qui
    rendait `core.resources.registry` **non importable** dans le venv du projet.
- **`_normalize_title()`** ajouté comme helper module-level.

### `core/knowledge/manager.py` (modifié)

- `create(..., node_id=None)` : identifiant imposé optionnel. À `None`, le
  comportement historique est conservé. Avec un identifiant, la création est
  idempotente (mise à jour au lieu de duplication).
- Conséquence : `KnowledgeNode.id == ResourceRecord.stable_id`.

### Fichiers créés

- `tests/core/test_dana_p2_7_document_discovery.py` — 38 tests.
- `docs/architecture/dana-p2-7-knowledge-discovery.md` — documentation des
  contrats pour les futures interfaces WebUI et MCP.

### Fichiers supprimés

- `core/knowledge/p27_knowledge_discovery.py` — artefact corrompu d'une session
  antérieure, sans référence dans le dépôt.
- `core/resources/discovery.py.base64`, `.bak_p2.7`, `.bak_orig`, `.bak_final`,
  `.orig` — sauvegardes de travail intermédiaires.

---

## 2. Tests exécutés

```bash
cd AI/Ethan
.venv/bin/python -m pytest tests/core/test_dana_p2_7_document_discovery.py -q
# 38 passed

.venv/bin/python -m pytest tests/core/ -q --no-header -p no:cacheprovider \
  --ignore=tests/core/test_types.py --ignore=tests/core/test_config.py \
  --ignore=tests/core/test_config_key_validation.py \
  --ignore=tests/core/test_config_phase3.py --ignore=tests/core/test_config_phase4.py \
  --ignore=tests/core/test_config_phase5.py --ignore=tests/core/test_config_skills_sources.py \
  --ignore=tests/core/test_credentials.py --ignore=tests/core/test_preset_configs.py \
  --ignore=tests/core/test_recommend_model.py --ignore=tests/core/test_registry.py \
  --ignore=tests/core/test_skills_learning_config.py
# 27 failed, 825 passed, 1 skipped, 8 errors
```

Les 38 tests P2.7 couvrent les 15 domaines exigés : découverte Markdown, RST,
classification et justification, stabilité UUIDv5, idempotence, détection des
modifications, disparitions, restaurations, extraction, création et mise à jour
des KnowledgeNodes, relations Skills, préservation des 391 Skills, contrôles
d'autorisation fail-closed, erreurs partielles, non-régression.

---

## 3. Résultats

| Indicateur | Valeur |
|---|---|
| Skills découverts | **391** (préservés sans modification) |
| Documents découverts | **145** |
| KnowledgeNodes créés | **145** (documents) + **391** (Skills) |
| Documents indexés dans le RAG | **536** (391 Skills + 145 documents), 0 échec |
| Relations documents↔Skills | **2** (justification : titres normalisés identiques) |
| Registre final | **536** ressources, toutes `active` |
| Idempotence | stable sur 3 passes consécutives |
| Persistance JSON | validée après redémarrage (536 ressources relues, états préservés) |
| Fichiers sources | intacts, jamais déplacés ni modifiés |

Classification des 145 documents : `other` 119, `document` 10, `architecture` 9,
`agent` 5, `plugin` 1, `mcp_server` 1.

---

## 4. Hypothèses

- Le backend RAG disponible par défaut est `memory` ; les embeddings sont
  simulés (« no LLM client — using mock embeddings »). Aucune validation
  PostgreSQL ni Redis n'a été réalisée.
- `CoreRecordStore` est en mémoire par défaut : les KnowledgeNodes ne survivent
  pas au redémarrage, contrairement au registre (JSON). Ils sont recréés par la
  découverte suivante, sans dupliquer les ressources.
- Les 27 échecs et 8 erreurs de la suite `tests/core/` sont **pré-existants** :
  aucun des fichiers de test concernés n'importe `core.resources` ou
  `core.knowledge`, et les violations d'architecture signalées concernent des
  fichiers non modifiés (`core/hrot/durable.py`, `core/adapters/*`).

---

## 5. Limites restantes

1. **Aucune validation PostgreSQL / Redis.** La persistance des KnowledgeNodes
   n'est validée qu'en mémoire ; celle du registre, qu'en JSON.
2. **`auth_proof` non cryptographique.** Le contrôle HROT interne vérifie la
   présence d'une preuve non vide, pas une signature. L'intégration native
   (`core.auth`) reste bloquée par la dépendance `jose` dans
   `core/auth/service_identities.py`.
3. **Déplacement de fichier = nouvelle identité.** L'ancrage documentaire est
   le chemin ; l'ancienne référence passe `DISAPPEARED`, la nouvelle est créée.
4. **Contenu extrait plafonné à 500 caractères** (50 premières lignes).
5. **Support RST peu exercé** : aucun fichier `.rst` n'est présent dans
   `AI/Ethan/docs/` à la date de la session.

---

## 6. Tâches non terminées

- P2.8 (traçabilité des chantiers, builds, rapports, erreurs, décisions) — hors périmètre.
- P2.9 (serveur MCP pour Codex et OpenCode) — hors périmètre.
- P2.10 (intégration des agents ETHAN) — hors périmètre.
- Interface WebUI DAĒNĀ — hors périmètre, à faire après stabilisation.
- Validation PostgreSQL / Redis du `CoreRecordStore` pour les KnowledgeNodes.
