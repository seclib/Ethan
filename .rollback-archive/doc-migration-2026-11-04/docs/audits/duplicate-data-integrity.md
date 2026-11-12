# Duplicate Data Integrity — Audit

> **Statut final : FIXED** — module Core `core/dedup/` + API `/v1/dedup` +
> WebUI `/dedup`.  Read-only detection, secure resolution, jamais de
> suppression automatique.

---

## 1. Problème

ETHAN stocke des ressources dans plusieurs domaines (Library, Projects,
Knowledge, RAG) avec des frontières de persistance différentes (`files`,
`projects`+`documents`, `knowledge`, `rag-documents`).  Rien ne permettait :

* de détecter les fichiers potentiellement identiques (même contenu, même nom,
  même emplacement) ;
* de classer ces doublons (exact / probable / même nom-contenu différent /
  version / même contenu-emplacement différent / déjà indexé / orphelin /
  référence cassée) ;
* de proposer des actions sûres (conserver les deux, remplacer par la version
  la plus récente, conserver la version principale, archiver, supprimer après
  confirmation, réparer une référence, fusionner les associations) ;
* de garantir l'intégrité RAG après déduplication (indexs obsolètes, doubles
  embeddings, collections en double).

---

## 2. Audit de l'existant (avant modification)

| Élément | Existant | Rôle |
| ------- | -------- | ---- |
| `core/state/files.py` | `FileStore` | Métadonnées fichiers (`filename`, `size`, `content_type`, `storage_path`, `metadata`) + contenu binaire optionnel dans `files_content` |
| `core/projects/__init__.py` | `ProjectManager` | Projets (conversation container) + documents RAG rattachés (`documents`) |
| `core/knowledge/manager.py` | `KnowledgeManager` | Nœuds de connaissance (`label`, `node_type`, `source`, `connections`) |
| `core/rag/pipeline.py` | `RAGPipeline` | Catalogue de documents RAG (`rag-documents`), ingestion, retrieval, index vectoriel |
| **Détecteur de doublons** | ❌ **Absent** | → ajouté `core/dedup/detector.py` |
| **Resolveur sécurisé** | ❌ **Absent** | → ajouté `core/dedup/resolver.py` |
| **API dédiée** | ❌ **Absente** | → ajoutée `interfaces/api/routers/dedup.py` |
| **WebUI** | ❌ **Absente** | → ajoutée page `/dedup` |

**Décision** : ne pas créer de second stockage, ne pas dupliquer de pipeline.
La détection lit les domaines Core existants ; la résolution réutilise
`RAGPipeline.delete_document()` et les API Project/Collection officielles.---

## 3. Implémentation

### Backend Core (`core/dedup/`)

- `types.py` — `ScannedItem` (normalisation multi-domaine), `DuplicateGroup`,
  `DuplicateReport`, `DuplicateCategory` (8 catégories), `DuplicateAction`
  (7 actions), `ResolutionResult` (rapport de résolution).
- `detector.py` — `DuplicateDetector.scan()` : scan **read-only** de
  FileStore, ProjectManager, KnowledgeManager et RAGPipeline, puis
  classification en groupes par nom + hash.
- `resolver.py` — `DuplicateResolver.resolve()` : applique une action.
  `DELETE_AFTER_CONFIRM` nécessite `confirmed=True` ; contexte complet
  (associations, emplacements, références RAG, projets) retourné avant toute
  action destructrice.

### API — `interfaces/api/routers/dedup.py`

- `POST /v1/dedup/scan` — lance un scan (jamais de mutation).
- `GET /v1/dedup/report/{scan_id}` — renvoie un rapport déjà généré.
- `GET /v1/dedup/categories` — liste catégories + actions disponibles.
- `POST /v1/dedup/resolve` — applique une action (avec `confirmed`).
- Injection des managers Core au démarrage via `set_dedup_managers()` dans
  `interfaces/api/main.py` ; `Permission.MEMORY` requis.

### WebUI — `/dedup`

- `lib/api/dedup.ts` — client passif (`scanDuplicates`, `getDuplicateReport`,
  `getDedupCategories`, `resolveDuplicateGroup`).
- `components/features/dedup/dedup-workspace.tsx` — bouton Scan, liste des
  groupes par catégorie, actions par groupe, bandeau de confirmation pour
  `delete_after_confirm`.
- `app/dedup/page.tsx` — page ; entrée « Duplicates » ajoutée dans
  `nav-config.ts` (section Organisation).

---

## 4. Sécurité

Règles appliquées dans le resolver (testées) :

1. **Jamais de suppression automatique** — `DELETE_AFTER_CONFIRM` avec
   `confirmed=false` → `needs_confirm`, aucun fichier supprimé.
2. **Le retrait d'un projet/collection ne supprime jamais les octets** — seule
   la relation est retirée.
3. **Contexte complet avant destruction** — associations, emplacements,
   références RAG, projets et collections sont retournés dans
   `ResolutionResult` pour affichage UI.
4. **Échec partiel jamais masqué** — erreurs collectées, statut
   `partially_completed`.
5. **RAG via pipeline officiel** — `RAGPipeline.delete_document()` (record
   durable + catalogue + index vectoriel en un appel) ; pas de double
   collection, pas de double embedding.---

## 5. Tests

| Suite | Scope | Résultat |
| ----- | ----- | -------- |
| `tests/test_dedup_detector.py` (10) | Classification (exact, name, location, already-indexed, orphelins, sérialisation) | ✅ 10/10 |
| `tests/test_dedup_resolver.py` (10) | Contrat sécurité (confirm requis, suppression, archive, merge associations, repair) | ✅ 10/10 |
| `tests/test_dedup_api.py` (4) | Gateway (health, categories, scan, report) | ✅ 4/4 |
| **Total backend** | | ✅ **24/24** |
| `tsc --noEmit` (WebUI) | Types | ✅ exit 0 |
| `next build` (WebUI) | Build | ✅ exit 0 |
| Jest folders + dedup | Régression UI | ✅ 10/10 |

---

## 6. Problèmes restants / limitations

- **`ProjectManager` non composé dans `main.py`** : le scan des documents de
  projets reste câblé dans `DuplicateDetector` mais inactif côté API tant que
  le composition root n'instancie pas `ProjectManager`.  Library, Knowledge et
  RAG fonctionnent aujourd'hui.
- **Hash de contenu** : calculé via `FileStore.download()` (binaire in-Core
  base64 ou `storage_path`).  Les fichiers metadata-only sans `storage_path`
  accessible restent avec un hash vide → classés par nom uniquement.
- **`resolution result` conservé en mémoire** (pas de persistance des
  rapports) ; un redémarrage invalide `GET /report/{scan_id}`.
- **Pas de `different_version` explicite** : la catégorie existe dans
  `DuplicateCategory` mais la détection par métadonnée de version est laissée
  aux évolutions futures (les fichiers sans version sont classés
  `same_name_different_content` si les hash diffèrent).

---

## 7. Documentation

- `docs/architecture/duplicate-detection.md` — architecture complète
  (domaines, catégories, actions, contrat de sécurité, flux API, tests).