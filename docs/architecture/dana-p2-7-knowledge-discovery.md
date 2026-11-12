# DAĒNĀ P2.7 — Découverte documentaire et Knowledge Discovery

> Capacité native d'ETHAN Core. Ce document décrit les contrats exposés aux
> interfaces (WebUI, MCP, agents autorisés) pour la découverte, la
> classification et le référencement des connaissances documentaires.
>
> **Statut : IMPLEMENTED.** Le service est en production dans `core/resources/`.

---

## 1. Vue d'ensemble

DAĒNĀ s'appuie sur deux composants Core existants, sans les dupliquer :

| Composant | Rôle dans DAĒNĀ |
|---|---|
| `core/resources/discovery.py` | **Discovery** — scan des emplacements configurés, extraction des métadonnées, classification |
| `core/resources/registry.py` | **Registry** — identité stable, état, cycle de vie, persistance, relations |
| `core/knowledge/manager.py` | **KnowledgeManager** — nœuds de connaissance exploitables |
| `core/rag/pipeline.py` | **RAG** — indexation et récupération (existant, non modifié) |

### Principes structurels

1. **Une seule source de connaissances.** Le Resource Registry est l'unique
   référentiel d'identité et d'état.
2. **Pas de stockage parallèle.** Le registre persiste via `registry-meta.json`
   ; les KnowledgeNodes via le `CoreRecordStore` existant.
3. **Les fichiers sources ne bougent jamais.** Seules des *références* et des
   *nœuds de connaissance* sont créés. Aucun document n'est déplacé, renommé,
   recopié ou modifié.
4. **Aucune dépendance nouvelle.** Aucun daemon, aucune base de données, aucun
   moteur d'indexation dédié.
5. **Fail-closed.** Les contrôles HROT existants s'appliquent à toutes les
   opérations du registre.

---

## 2. Découverte documentaire

### 2.1 Emplacements surveillés

```python
from core.resources.discovery import KNOWLEDGE_ROOTS
```

| Emplacement | Contenu |
|---|---|
| `AI/Ethan/docs/` | Documentation générale (guides, spécifications, audits, design) |
| `AI/Ethan/docs/user-guide/` | Guide utilisateur (inclus dans `docs/`, traité une seule fois) |

Les racines sont configurables à l'appel :

```python
await registry.discover_documents((Path("/mon/emplacement"),))
```

Aucun parcours global du système de fichiers n'est effectué. Les racines
imbriquées sont dédupliquées par chemin résolu : un document appartenant à
deux racines n'est découvert qu'une fois.

### 2.2 Formats pris en charge

| Extension | Support | Statut |
|---|---|---|
| `.md` (Markdown) | Complet | **Actif** |
| `.rst` (reStructuredText) | Complet | **Actif** |
| Autres | Non supporté | Ignoré |

Les répertoires `__pycache__`, `node_modules`, `.git`, `site` et `.venv` sont
exclus, ainsi que les fichiers cachés.

### 2.3 API

```python
# Scan pur — ne modifie aucun registre.
metas, nodes = discover_documents(roots, create_knowledge_nodes=True)

# Orchestration complète — enregistre, applique le cycle de vie, persiste.
result = await registry.discover_documents(roots)
```

`discover_documents()` (module) est un **scan pur** : il ne touche pas au
registre. `ResourceRegistry.discover_documents()` est l'**orchestrateur** :
enregistrement, idempotence, détection de changement, disparition,
restauration, persistance.

Ce découpage suit exactement le modèle déjà en place pour les Skills
(`discover_skills()` / `ResourceRegistry.discover_skills()`).

---

## 3. Classification

### 3.1 Principe

La classification est **déterministe** et **justifiable** : chaque document
porte la raison de son classement dans
`metadata["classification_reason"]`.

```python
resource_type, reason = classify_document(title, domain, level, categories)
```

Ordre de décision :

1. **Mot-clé explicite dans le titre** — signal le plus fort
   (`ADR`, `agent`, `runbook`, `architecture`, `guide`, …).
2. **Domaine** (sous-répertoire ou métadonnée déclarée) —
   `architecture/`, `decisions/`, `skills/`, `agents/`, `mcp/`, `specs/`, …
3. **Catégorie explicitement déclarée** dans le document —
   `catégorie : agent`, `type : adr`, …
4. **Défaut** — `OTHER`, avec la raison
   `"no explicit signal; defaulting to OTHER"`.

### 3.2 Catégories

| Type | `ResourceType` | Obtenu par |
|---|---|---|
| Skill | `skill` | Domaine `skills/`, ou catégorie déclarée `skill`. **Réservé** : un document qui *mentionne* des Skills n'est pas une Skill. |
| Agent | `agent` | Mot-clé `agent`, domaine `agents/`, catégorie déclarée |
| ADR | `adr` | Mot-clé `adr`, domaine `decisions/`, catégorie déclarée |
| MCP Server | `mcp_server` | Domaine `mcp/`, catégorie déclarée |
| Document | `document` | Mot-clé `guide`/`tutorial`/`documentation`/`reference`, domaines `audit(s)/design/spec(s)` |
| Architecture | `architecture` | Domaine `architecture/`, `conception/` |
| Plugin | `plugin` | Mot-clé `plugin`/`extension`, domaine `plugins/` |
| Runbook | `runbook` | Mot-clé `runbook`/`playbook`, domaine `runbooks/` |
| Application | `application` | Mot-clé `application`/`web app` |
| Autre | `other` | Aucun signal exploitable |

### 3.3 Extensibilité

Les tables `_TITLE_KEYWORDS` et `_DOMAIN_TYPES` dans
`core/resources/discovery.py` sont ouvertes : ajouter une entrée suffit à
étendre la classification, sans toucher au reste du service.

---

## 4. Identité et cycle de vie

### 4.1 Identifiants

Deux mécanismes UUIDv5 coexistent, tous deux déterministes et namespace DNS :

| Type de ressource | Ancrage | Fonction |
|---|---|---|
| Skills, catalogue | `type + chemin canonique + titre normalisé` | `_compute_stable_id()` |
| Documents | **chemin canonique seul** | `_compute_document_stable_id()` |

Le document est ancré sur son chemin, et non sur son titre : un document dont
le titre ou le contenu évolue doit **conserver la même identité**, pour que la
modification soit détectée comme une mise à jour et non comme une ressource
nouvelle.

> Conséquence assumée : un **déplacement** de fichier change l'identité. Le
> registre traite alors l'ancienne référence (`DISAPPEARED`) et la nouvelle
> (nouvelle ressource). Les deux restent traçables ; aucune donnée n'est
> perdue.

### 4.2 Cycle de vie

| Transition | Déclencheur | Effet |
|---|---|---|
| `ACTIVE` | Document trouvé, inchangé | `last_verified` rafraîchi |
| `STALE` | Document trouvé, modifié | Métadonnées et KnowledgeNode actualisés, puis retour à `ACTIVE` |
| `DISAPPEARED` | Document introuvable sur le disque | Métadonnées et provenance **conservées** |
| `ACTIVE` (restauré) | Document réapparu | Restauration explicite via `restore_resource()` |

Le cycle de vie réutilise les transitions existantes du Resource Registry
(`mark_stale`, `mark_disappeared`, `mark_deprecated`, `restore_resource`).
Aucune seconde machine à états n'a été introduite.

---

## 5. États de traitement du contenu

Trois états conceptuels distincts, portés par
`metadata["knowledge_state"]` :

| État | Signification | Condition |
|---|---|---|
| `discovered` | Document identifié | Chemin et métadonnées enregistrés ; **aucun** contenu extrait |
| `extracted` | Contenu réellement extrait | Le texte du document a pu être lu et un extrait exploitable a été produit |
| `indexed` | Contenu réellement indexé | L'ingestion RAG a **réellement abouti** |

> Un document découvert n'est **jamais** présenté comme indexé. L'état
> `indexed` n'est posé que par `ResourceRegistry.index_documents()`, qui
> n'aboutit que si `KnowledgeManager.ingest_into_rag()` retourne un
> identifiant de document RAG.

### 5.1 Extraction

```python
snippet = _extract_content_snippet(content, max_chars=500)
```

- Seuil minimal : 20 caractères utiles.
- 50 premières lignes, plafonnées à 500 caractères.
- Un document vide ou trop court reste `discovered`.

### 5.2 Indexation RAG

```python
from core.rag.pipeline import RAGPipeline

rag = RAGPipeline(vector_backend="memory")
result = await registry.index_documents(rag)
# {"indexed": [...], "indexed_count": N, "failed": [...], "failed_count": M}
```

Aucun nouveau moteur d'indexation n'est créé : le pipeline RAG existant et
`KnowledgeManager.ingest_into_rag()` sont réutilisés.

---

## 6. Intégration KnowledgeManager

### 6.1 Rattachement

L'identité du KnowledgeNode est **alignée sur celle de la ressource** :
`KnowledgeNode.id == ResourceRecord.stable_id`.

Ce point est garanti par l'extension rétrocompatible de
`KnowledgeManager.create(..., node_id=None)` :

- `node_id=None` (défaut) → comportement historique, UUID4 généré ;
- `node_id="..."` → identité imposée et **idempotente** : un nœud existant
  sous cet identifiant est mis à jour, jamais dupliqué.

Conséquence : le lien `ResourceRecord ↔ KnowledgeNode` survit au
rechargement du registre.

### 6.2 Persistance

| Donnée | Support | Survit au redémarrage |
|---|---|---|
| Ressources, statuts, métadonnées | `registry-meta.json` (fichier) | **Oui** |
| KnowledgeNodes | `CoreRecordStore` | **Non** en mémoire ; **Oui** avec PostgreSQL |
| Documents RAG | `RAGPipeline` | **Non** en mémoire ; **Oui** avec PostgreSQL |

En stockage mémoire (configuration par défaut), les KnowledgeNodes sont
recréés par la découverte suivante, sans dupliquer les ressources. En
PostgreSQL, ils sont persistés par le `CoreRecordStore` existant.

> **Aucune validation PostgreSQL ou Redis n'a été réalisée dans le cadre de
> P2.7.** Les résultats annoncés ci-dessus sont obtenus avec le stockage
> mémoire et la persistance JSON du registre.

### 6.3 Rattachement après rechargement

```python
await registry.attach_pending_nodes()
```

Rattache les KnowledgeNodes laissés détachés par le rechargement JSON.
Appelé automatiquement au début de `discover_skills()`,
`discover_documents()` et `link_documents_to_skills()`.

---

## 7. Relations documents ↔ Skills

```python
result = await registry.link_documents_to_skills()
# {"links": [{"document_id": ..., "skill_id": ..., "justification": ...}], "linked_count": N}
```

Deux relations objectives sont retenues :

| Relation | Justification |
|---|---|
| **Structurelle** | Le document réside dans le répertoire de la Skill |
| **Nominale** | Les titres normalisés sont *strictement* identiques |

Aucune relation n'est créée sur une ressemblance approximative. Les Skills du
catalogue ne sont ni modifiés ni dupliqués : seules des relations
`KnowledgeConnection` (`relation_type="documents_skill"`) sont ajoutées.

La normalisation des titres (`_normalize_title`) retire la casse, la
ponctuation et les espaces superflus.

---

## 8. Contrat d'autorisation

Les opérations du registre restent soumises au contrôle HROT existant
(`core/resources/registry.py`) :

```python
from core.resources.registry import (
    _AgentPrincipal, _ExecutionContext, authorize_resource_access, check_access,
)

context = _ExecutionContext(
    principal=_AgentPrincipal(
        principal_id="p-1",
        principal_type="AGENT",
        subject_id="agent-1",
        actor_id="agent-1",
        permissions=["resource:read"],
        scopes=["skill", "document", "resource"],
        auth_proof="<preuve>",
    ),
    agent_id="agent-1",
)

check_access(context, operation="read")   # True
check_access(None, operation="read")      # False — fail-closed
```

Cinq conditions sont cumulatives : contexte présent, `auth_proof` non vide,
`principal_type == "AGENT"`, `agent_id` concordant, permission requise
accordée, `resource_type` dans les scopes.

> **La vérification de `auth_proof` n'est pas cryptographique.** Elle vérifie
> la *présence* d'une preuve non vide, pas une signature. L'intégration native
> HROT (`core.auth`) reste bloquée par la dépendance `jose` dans
> `core/auth/service_identities.py`. L'implémentation interne applique les
> mêmes principes fail-closed.

---

## 9. Limites connues

| Limite | Impact |
|---|---|
| Pas de validation PostgreSQL/Redis | La persistance des KnowledgeNodes n'est validée qu'en mémoire |
| `auth_proof` non vérifié cryptographiquement | Le contrôle d'accès est structurel, pas cryptographique |
| Déplacement de fichier = nouvelle identité | Pas de continuité d'identité au-delà du chemin |
| Format `.rst` peu présent dans le dépôt | Le support RST est implémenté et testé, mais peu exercé en production |
| Pas de RAG à disposition en configuration par défaut | L'état `indexed` suppose un pipeline RAG fourni |
| Contenu extrait plafonné à 500 caractères | Le nœud porte un extrait, pas le document intégral |

---

## 10. Points d'entrée pour les interfaces

### WebUI

```python
registry = get_resource_registry()
await registry.discover_documents()

stats = registry.get_stats()
# {"total_resources", "by_status", "by_type"}
```

`registry.list_by_type(ResourceType.DOCUMENT)` et
`registry.search_resources("terme")` fournissent les listes et la recherche.

### MCP

Les mêmes méthodes `async` sont directement exposables comme outils MCP. La
séquence `discover_documents()` → `index_documents(rag)` →
`link_documents_to_skills()` constitue le pipeline d'indexation.

### Agents autorisés

Les opérations passent par les gates HROT du registre. Un agent doit présenter
un `_ExecutionContext` valide pour accéder aux ressources.

---

> **Persistance** : la cartographie et l'architecture de persistance des
> ressources, des connaissances et de la mémoire d'ingénierie sont
> documentées dans `docs/architecture/dana-p2-8-1-persistence-unification.md`
> (P2.8.1). Ce document-ci traite de la découverte et de la classification.

## 11. Correspondance documentaire Engineering Memory (P2.8.0)

Le corpus documentaire (`daena/`, 868 fichiers) et le registre
`EngineeringMemoryRegistry` doivent désigner **les mêmes emplacements**. Le
registre configurait quatre chemins qui n'existent pas dans le corpus, ce qui
aurait créé des répertoires Parallèles à la première écriture.

### 11.1 Correspondance canonique

| Catégorie | `RecordType` | Destination canonique | Dans le corpus |
|---|---|---|---|
| Composant | `COMPONENT` | `Knowledge/Composants` | oui (répertoire) |
| Décision | `DECISION` | `Knowledge/Decisions` | oui (vide) |
| Événement | `ENGINEERING_EVENT` | `Archives/Events` | oui (118 documents) |
| Incident | `INCIDENT` | `Knowledge/Incidents` | oui (vide) |
| Réparation | `REPAIR` | `Archives/Events` | oui (partagé avec `ENGINEERING_EVENT`) |
| Vérification | `VERIFICATION` | `Knowledge/Tests-et-Preuves` | oui (répertoire) |
| Dépendance | `DEPENDENCY` | `Knowledge` | oui (couche, pas de sous-répertoire dédié) |
| Résultat de test | `TEST_RESULT` | `Knowledge/Tests-et-Preuves` | oui (partagé avec `VERIFICATION`) |
| Dette technique | `TECHNICAL_DEBT` | `Operational-Memory` | oui (26 documents) |
| Preuve | `EVIDENCE` | `_meta` | oui (171 documents) |
| Rapport d'agent | `AGENT_REPORT` | `Archives/Rapports-Agents` | oui (vide) |

Les quatre chemins réparés (`Components` → `Composants`, `Tests` →
`Tests-et-Preuves`, `Dependencies` → `Knowledge`) **n'ont jamais existé** dans
le corpus : les anciens chemins en anglais ne figuraient que dans
`daena/Metadata/REGISTRY.md` (document `PROPOSED` du 2026-11-03, antérieur à
la migration vers les noms français).

Sources de vérité, par ordre de fraîcheur :
`daena/INDEX.md` (2026-11-11) · `daena/AGENTS.md` (2026-11-11) ·
`daena/README.md` (2026-11-11).

### 11.2 Comportement de `destination_for()`

```python
from core.engineering_memory.registry import EngineeringMemoryRegistry

registry = EngineeringMemoryRegistry()
destination = registry.destination_for(RecordType.COMPONENT)
destination.relative_directory   # "Knowledge/Composants"
destination.schema_name          # "Component"
destination.naming                # "CMP-YYYY-NNN-slug.md"
```

- `destination_for()` accepte un `RecordType` **ou** une chaîne.
- Une catégorie inconnue lève `ValueError`.
- `relative_path_for()` conserve l'identifiant de l'enregistrement dans le
  nom de fichier et refuse tout identifiant contenant un séparateur de chemin.

Trois aides **strictement en lecture seule** complètent le contrat :

| Méthode | Effet |
|---|---|
| `registry.destination_exists(root, type)` | indique si la destination existe — ne crée rien |
| `registry.resolve_destination(root, type, id, titre)` | renvoie `(chemin relatif, existe)` — ne crée rien |
| `registry.corpus_mapping()` | expose la table type → destination pour les interfaces |

Au niveau service : `service.destination_status(type)` et
`service.corpus_mapping()`.

### 11.3 Protection du corpus

Le corpus est **en lecture seule par défaut** :

1. Corriger une destination logique ne crée **jamais** de répertoire physique.
2. `ObsidianPersistence` accepte `require_existing_destination=True` : dans ce
   mode, l'écriture **refuse** de créer un répertoire de destination absent
   (`ValidationError`). Désactivé par défaut, le comportement historique est
   conservé.
3. Les identifiants, métadonnées, provenance et chemins sources des
   enregistrements existants sont préservés : la correction ne porte que sur le
   chemin de destination.

---

## 12. Tests

```bash
cd AI/Ethan
.venv/bin/python -m pytest tests/core/test_dana_p2_7_document_discovery.py -q
.venv/bin/python -m pytest tests/core/test_engineering_memory_destination_mapping.py -q
```

38 tests couvrant : découverte Markdown et RST, classification et sa
justification, stabilité UUIDv5, idempotence, détection des modifications,
disparitions, restaurations, extraction, création et mise à jour des
KnowledgeNodes, relations Skills, préservation du catalogue des 391 Skills,
contrôles d'autorisation fail-closed, gestion des erreurs partielles et
non-régression.

**P2.8.0** ajoute 34 tests : correspondance de chaque catégorie réparée,
destinations déjà correctes, `destination_for()` (types connus, chaîne,
inconnue), chemins inexistants et cas d'erreur, comportement en lecture seule,
préservation des identifiants et des métadonnées, compatibilité avec les appels
existants (`search`, `component_history`, idempotence, détection de doublon).

Les tests s'exécutent sur des répertoires temporaires : aucun fichier du
dépôt n'est modifié.
