# ETHAN Knowledge Workspace — Architecture Phase 1

## 1. Vision et périmètre

### 1.1 Objectif
Créer un environnement documentaire natif dans ETHAN WebUI, inspiré d'Obsidian, qui utilise le référentiel existant `Obsidian/` comme source de vérité unique, sans duplication ni second moteur Knowledge.

### 1.2 Périmètre Phase 1
Cette phase définit l'architecture technique, les contrats API et le découpage du MVP. Aucune implémentation fonctionnelle majeure n'est engagée.

### 1.3 Principe fondamental
- `Obsidian/` reste la source documentaire unique.
- Markdown reste le format principal.
- YAML conserve les métadonnées structurées.
- Les liens internes `[[Document]]` restent compatibles avec Obsidian Desktop.
- Le WebUI ne doit pas accéder directement au système de fichiers.
- Toute logique métier réside dans Core/API.

---

## 2. Étude de référence — Nodum

### 2.1 Profil du projet
- **Nom** : Nodum (nodummd/nodum)
- **Licence** : MIT
- **Stack** : FastAPI + Next.js, multi-tenant, self-hostable
- **Stockage** : PostgreSQL
- **Éditeur** : CodeMirror 6
- **Fonctionnalités** : Wikilinks, backlinks, graphe GPU-rendered, canvas, publishing, web clipper, collaboration temps réel

### 2.2 Architecture backend Nodum
- Structure : `app/{api, services, models, schemas}`
- Pattern : routers minces, services épais (`ServiceResponse.unwrap()`)
- Réponses : `{"data": ...}` / erreurs `{"error": {"code", "message"}}`
- Migrations numérotées (`0001_...`)
- Alembic pour les migrations

### 2.3 Architecture frontend Nodum
- Next.js (app router)
- État workspace : Zustand
- Données serveur : TanStack Query
---

## 3. Document Repository — Service contrat

### 3.1 Responsabilités

Le **DocumentRepository** est un service Core distinct de `KnowledgeManager`. Il gère l'accès au référentiel `Obsidian/` comme système de fichiers documentaire.

Responsabilités :
1. Scanner le référentiel autorisé
2. Lister les dossiers et documents
3. Lire un document
4. Modifier un document (avec hash de concurrence)
5. Créer un document
6. Renommer un document
7. Supprimer un document (avec autorisation)
8. Lire et préserver les propriétés YAML
9. Résoudre les liens internes `[[...]]`
10. Calculer les backlinks
11. Détecter les modifications externes

### 3.2 Modèles de données (Python)

```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

@dataclass(frozen=True, slots=True)
class DocumentId:
    relative_path: str

@dataclass(slots=True)
class DocumentProperties:
    raw_frontmatter: str
    parsed: dict[str, Any]
    has_frontmatter: bool

@dataclass(slots=True)
class DocumentLink:
    target: str
    display_text: str | None
    line_number: int
    resolved: bool
    resolved_path: str | None

@dataclass(slots=True)
class Document:
    id: DocumentId
    relative_path: str
    absolute_path: Path
    title: str
    content: str
    properties: DocumentProperties
    links_out: tuple[DocumentLink, ...]
    links_in: tuple[str, ...]
    hash: str
    size_bytes: int
    modified_at: datetime
    created_at: datetime | None
    tags: tuple[str, ...]
    document_type: str

@dataclass(slots=True)
class DocumentTreeEntry:
    name: str
    relative_path: str
    entry_type: str
    children: list["DocumentTreeEntry"] | None = None
    document_id: str | None = None

@dataclass(slots=True)
class DocumentTree:
    root: str
    entries: list[DocumentTreeEntry]
    total_documents: int
    total_directories: int

@dataclass(slots=True)
class DocumentSearchResult:
    document_id: str
    relative_path: str
    title: str
    snippet: str
    score: float
    match_type: str
```

### 3.3 Interface Python — DocumentRepository

```python
from typing import Protocol

class DocumentRepository(Protocol):
    async def get_document_root(self) -> Path: ...
    async def list_tree(self, *, root: str | None = None, max_depth: int = 10) -> DocumentTree: ...
    async def read_document(self, relative_path: str) -> Document: ...
    async def write_document(self, relative_path: str, content: str, *, expected_hash: str | None = None) -> Document: ...
    async def create_document(self, relative_path: str, content: str = "", properties: dict[str, Any] | None = None) -> Document: ...
    async def rename_document(self, old_path: str, new_path: str) -> Document: ...
    async def delete_document(self, relative_path: str, *, authorized: bool = False) -> bool: ...
    async def resolve_link(self, link_text: str, from_document: str | None = None) -> Document | None: ...
    async def get_backlinks(self, relative_path: str) -> list[Document]: ...
    async def search(self, query: str, *, limit: int = 20, search_type: str = "full") -> list[DocumentSearchResult]: ...
    async def get_document_hash(self, relative_path: str) -> str: ...
    async def detect_external_changes(self, relative_path: str, known_hash: str) -> bool: ...
```

### 3.4 Implémentation interne (hors interface)

L'implémentation concrète `FilesystemDocumentRepository` :
- Utilise `pathlib.Path` pour l'accès fichier
- Valide tous les chemins avec `Path.resolve()` et vérification de la racine
- Parse le frontmatter YAML avec `yaml.safe_load`
- Calcule les liens avec regex `\[\[([^\]]+)\]\]`
- Maintient un index en mémoire des backlinks (reconstruit au scan)
- Détecte les modifications externes par comparaison de hash

---

## 4. Sécurité et intégrité

### 4.1 Racine documentaire
- Configurable via variable d'environnement `ETHAN_DOCUMENT_ROOT` (défaut : `/home/fatsio/AI/Ethan/Obsidian`)
- Validée au démarrage : doit exister, être un répertoire, et ne pas contenir de liens symboliques sortants
- Tous les accès sont limités à cette racine

### 4.2 Protection path traversal
- Tout chemin relatif est normalisé avec `Path.resolve()`
- Vérification que le chemin résolu est bien sous la racine : `resolved.is_relative_to(root)`
- Rejet des chemins contenant `..`, des chemins absolus, et des caractères null
- Validation des noms de fichiers (pas de `/` dans les noms individuels)

### 4.3 Protection des liens symboliques
- Scan récursif avec `os.walk(followlinks=False)`
- Vérification explicite que chaque fichier/dossier n'est pas un symlink sortant de la racine
- Rejet de toute opération sur un symlink qui sort de la racine

### 4.4 Permissions HROT
- Toute opération destructive (suppression, renommage) requiert une autorisation HROT explicite
- L'autorisation est vérifiée côté serveur via `require_permission(Permission.WRITE)` ou `Permission.DELETE`
- Le contenu d'un document ne constitue jamais une autorisation

### 4.5 Concurrence d'écriture
- Hash SHA-256 du contenu calculé à la lecture
- À l'écriture, si `expected_hash` est fourni, comparaison avec le hash actuel
- Si différence → `ConflictError` (HTTP 409) avec le hash actuel et le hash attendu
- Le frontend doit afficher le conflit et proposer une résolution (merge manuel ou écrasement)

### 4.6 Audit des modifications
- Chaque opération d'écriture/création/suppression est loggée avec :
  - Utilisateur (identité JWT)
  - Chemin du document
  - Hash avant et après
  - Timestamp
  - Type d'opération
- Les logs sont envoyés au système d'audit ETHAN existant

### 4.7 Gestion des erreurs de sauvegarde
- Erreurs I/O → HTTP 500 avec détail
- Conflit de concurrence → HTTP 409 avec hashes
- Permission refusée → HTTP 403
- Fichier non trouvé → HTTP 404
- Chemin invalide → HTTP 422
- Toutes les erreurs sont propagées au frontend (pas de masquage)

- Accès API centralisé : `web/src/lib/api/`
- Éditeur : CodeMirror 6
- Graphe : GPU-rendered (WebGL)
- Tests : Playwright e2e (7 tests)
- CI : gitleaks + tests sur chaque push

### 2.4 Composants réutilisables pour ETHAN

| Composant Nodum | Réutilisable dans ETHAN ? | Décision |
|-----------------|---------------------------|----------|
| CodeMirror 6 | Oui — déjà évalué pour ETHAN | Réutiliser, licence MIT |
| Zustand pour l'état workspace | Oui — déjà utilisé dans ETHAN | Réutiliser |
| TanStack Query pour les données serveur | Oui — déjà utilisé | Réutiliser |
| Pattern ServiceResponse.unwrap() | Partiellement — ETHAN utilise des réponses directes | Adapter, pas imposer |
| GPU-rendered graph | À évaluer | Reporté Phase 2 (React Flow ou Sigma.js) |
| Web Clipper | Hors périmètre Phase 1 | Reporté |
| Collaboration temps réel | Hors périmètre Phase 1 | Reporté |

### 2.5 Ce que ETHAN ne prend PAS de Nodum
- Pas de second moteur Knowledge (ETHAN a déjà KnowledgeManager)
- Pas de second système de collections (ETHAN a KnowledgeCollectionManager)
- Pas de second moteur RAG
- Pas de base de données PostgreSQL dédiée (ETHAN utilise le référentiel fichier)
- Pas d'architecture multi-tenant (ETHAN est single-tenant par instance)

---

## 5. Contrats API

### 5.1 Conventions
- Préfixe `/v1/documents/*` (distinct de `/v1/knowledge/*`)
- Authentification : JWT via cookie HttpOnly (proxy Next.js)
- Réponses : données directes (pas de wrapper `{"data": ...}`) — convention ETHAN existante
- Erreurs : `{"detail": "..."}` — convention FastAPI existante
- Permissions : `require_permission(Permission.READ/WRITE/DELETE)`

### 5.2 Endpoints proposés

#### Arborescence
```
GET  /v1/documents/tree
     ?root=<sous-dossier>     (optionnel, défaut: racine)
     ?max_depth=10            (optionnel, défaut: 10)
     → DocumentTree
```

#### Lecture
```
GET  /v1/documents/{path}
     → Document (contenu + propriétés + liens + hash)
```
Le `{path}` est le chemin relatif encodé en URL.

#### Écriture (avec concurrence)
```
PUT  /v1/documents/{path}
     Body: { "content": "...", "expected_hash": "abc123..." }
     → Document (mis à jour)
     Erreurs: 409 (conflit), 403 (permission), 422 (chemin invalide)
```

#### Création
```
POST /v1/documents
     Body: { "path": "Nouveau/document.md", "content": "...", "properties": {...} }
     → Document (créé)
     Erreurs: 409 (existe déjà), 422 (chemin invalide)
```

#### Renommage
```
POST /v1/documents/{path}/rename
     Body: { "new_path": "Nouveau/chemin.md" }
     → Document (renommé)
     Erreurs: 404 (non trouvé), 409 (destination existe), 422 (chemin invalide)
```

#### Suppression
```
DELETE /v1/documents/{path}
     → { "deleted": true, "path": "..." }
     Erreurs: 403 (permission), 404 (non trouvé)
```

#### Liens et backlinks
```
GET  /v1/documents/{path}/links
     → { "outgoing": [DocumentLink], "backlinks": [DocumentSummary] }

GET  /v1/documents/{path}/backlinks
     → [DocumentSummary]
```

#### Résolution de lien
```
POST /v1/documents/resolve-link
     Body: { "link_text": "Nom du document", "from_document": "path/to/source.md" }
     → Document | null
```

#### Recherche
```
GET  /v1/documents/search
     ?q=terme de recherche
     &limit=20
     &type=full|title|tag|property
     → [DocumentSearchResult]
```

#### Hash
```
GET  /v1/documents/{path}/hash
     → { "hash": "sha256...", "modified_at": "..." }
```

#### Propriétés YAML
```
GET  /v1/documents/{path}/properties
     → DocumentProperties

PUT  /v1/documents/{path}/properties
     Body: { "properties": { "key": "value" } }
     → Document (propriétés mises à jour, contenu préservé)
---

## 6. Indexation documentaire

### 6.1 Stratégie distincte du Knowledge Graph
L'index documentaire est une **projection read-only** des fichiers du référentiel. Il ne constitue pas un second moteur RAG ni un second Knowledge Manager. Il sert uniquement à accélérer la recherche et la navigation.

### 6.2 Modèle d'index

```python
@dataclass(slots=True)
class DocumentIndexEntry:
    document_id: str
    relative_path: str
    title: str
    document_type: str
    tags: tuple[str, ...]
    properties: dict[str, Any]
    links_out: tuple[str, ...]
    links_in: tuple[str, ...]
    content_hash: str
    modified_at: datetime
    word_count: int
    headings: tuple[str, ...]
```

### 6.3 Cycle de vie de l'index
1. **Scan initial** : Au démarrage du service, scan complet du référentiel (736 fichiers). Durée estimée : < 2s.
2. **Index en mémoire** : L'index est maintenu en mémoire (dict[path → DocumentIndexEntry]).
3. **Mise à jour incrémentale** : À chaque lecture/écriture, l'entrée correspondante est mise à jour.
4. **Détection externe** : Un watcher filesystem (optionnel, Phase 2) détecte les modifications externes et déclenche un re-scan partiel.
5. **Reconstruction** : Un endpoint `POST /v1/documents/reindex` permet de reconstruire l'index complet.

### 6.4 Intégration avec le Knowledge Graph existant
- L'index documentaire est une **source de données** pour le Knowledge Graph.
- Quand un document est lu/modifié, le KnowledgeManager peut être notifié via l'Event Bus.
- Le Knowledge Graph stocke des **références** aux documents (par chemin), pas des copies du contenu.
- Pas de duplication : le contenu reste dans les fichiers.

### 6.5 Intégration ECLL (ETHAN Continuous Learning Loop)
Les catégories documentaires suivantes sont reconnues automatiquement à partir des métadonnées et du chemin :
- Architecture (dossier `Architecture/`)
- ADR (dossier `Architecture/ADR/`)
- Runbooks (dossier contenant "runbook" ou tag `runbook`)
- Experiences (dossier contenant "experience" ou tag `experience`)
- Attempts (dossier contenant "attempt" ou tag `attempt`)
- Incidents (dossier contenant "incident" ou tag `incident`)
- Lessons (dossier contenant "lesson" ou tag `lesson`)
- Knowledge (dossier `Knowledge/`)
- Research (dossier contenant "research" ou tag `research`)
- Projects (dossier contenant "project" ou tag `project`)

La détection est basée sur :
1. Le chemin relatif (prefixe de dossier)
2. Les tags dans le frontmatter YAML
3. Les propriétés `type` ou `category` du frontmatter

```

---

## 7. Architecture frontend

### 7.1 Composants réutilisés (sans modification)
- `KnowledgeHub` — cockpit unifié (onglets existants)
- `KnowledgeBrowser` — navigation collections/dossiers
- `KnowledgeWorkspace` — espace de travail existant
- `FoldersWorkspace` — gestion des dossiers
- `LibraryWorkspace` — bibliothèque existante

### 7.2 Nouveaux composants à créer (Phase 2+)

| Composant | Responsabilité | Priorité |
|-----------|---------------|----------|
| `DocumentExplorer` | Arborescence du référentiel Obsidian/ | MVP-A |
| `DocumentEditor` | Éditeur Markdown (CodeMirror 6) | MVP-C |
| `DocumentPreview` | Rendu Markdown avec résolution des liens | MVP-D |
| `DocumentTabs` | Gestion des onglets multiples | MVP-E |
| `DocumentProperties` | Affichage/édition des propriétés YAML | MVP-F |
| `BacklinksPanel` | Liste des documents qui pointent vers le document actuel | MVP-F |
| `DocumentSearch` | Recherche dans le référentiel | MVP-F |
| `DocumentGraph` | Visualisation du graphe de liens (Phase 2) | Phase 2 |
| `DocumentCanvas` | Espace de cartographie visuelle (Phase 2) | Phase 2 |

### 7.3 Gestion de l'état frontend

- **État des onglets** : Zustand store (`document-tabs.store.ts`)
  - Liste des onglets ouverts (chemin, titre, état de sauvegarde)
  - Onglet actif
  - Historique de navigation
- **Données serveur** : TanStack Query
  - `useQuery(['document-tree'])` pour l'arborescence
  - `useQuery(['document', path])` pour le contenu
  - `useQuery(['document-backlinks', path])` pour les backlinks
  - `useMutation` pour les écritures (avec invalidation du cache)
- **Accès API** : Centralisé dans `src/lib/api/documents.ts`

### 7.4 Intégration dans la navigation

Le Knowledge Workspace sera accessible depuis le KnowledgeHub existant, via un nouvel onglet "Documents" ou une route dédiée `/knowledge/documents`.

Les composants existants (`KnowledgeBrowser`, `KnowledgeWorkspace`) ne sont pas modifiés — le nouveau workspace est un ajout parallèle.

### 7.5 Éditeur Markdown — CodeMirror 6

Choix technologique : **CodeMirror 6** (licence MIT)

Raisons :
- Déjà évalué et utilisé par Nodum
- Support natif du Markdown
- Extensible (wikilinks, syntax highlighting, tables, mermaid)
- Performant pour les gros documents
- Compatible avec l'écosystème React (via `@uiw/react-codemirror`)

Configuration minimale :
- Extension Markdown (`@codemirror/lang-markdown`)
- Extension pour les wikilinks (custom, regex `\[\[([^\]]+)\]\]`)
- Extension pour les blocs de code (syntax highlighting)
- Thème sombre cohérent avec ETHAN

### 7.6 Résolution des liens internes

Algorithme de résolution (côté serveur) :
1. Extraire le texte du lien `[[target]]` ou `[[target|display]]`
2. Chercher un fichier dont le nom (sans extension) correspond exactement à `target`
3. Si non trouvé, chercher un fichier dont le titre (H1) correspond à `target`
4. Si non trouvé, chercher un fichier dont le chemin relatif contient `target`
5. Retourner le premier match ou `null` (lien non résolu)

La résolution est faite côté serveur pour garantir la cohérence. Le frontend affiche le lien avec un style différent si non résolu.

### 7.7 Backlinks

Les backlinks sont calculés par l'index documentaire :
1. À chaque scan, pour chaque document, extraire les liens sortants
2. Construire une map inversée : `target_path → [source_paths]`
3. L'endpoint `/v1/documents/{path}/backlinks` retourne cette liste

---

## 8. Découpage du MVP

### Sous-livrable A — Document Repository et lecture réelle
**Objectif** : Lire les vrais documents du référentiel `Obsidian/`.

**Livrables** :
- `core/documents/repository.py` — `FilesystemDocumentRepository`
- `core/documents/models.py` — Modèles de données
- `core/documents/index.py` — Index documentaire
- `interfaces/api/routers/documents.py` — Endpoints REST
- Tests unitaires : lecture, sécurité path traversal, YAML parsing

**Critères de validation** :
- `GET /v1/documents/tree` retourne l'arborescence complète de `Obsidian/`
- `GET /v1/documents/{path}` retourne le contenu réel d'un fichier Markdown
- Les propriétés YAML sont correctement parsées
- Les liens `[[...]]` sont extraits
- Le path traversal est bloqué (test avec `../../../etc/passwd`)

### Sous-livrable B — Explorateur documentaire
**Objectif** : Naviguer dans l'arborescence depuis le WebUI.

**Livrables** :
- `DocumentExplorer` composant React
- `src/lib/api/documents.ts` — Client API
- Intégration dans KnowledgeHub (nouvel onglet)
- Tests composant : rendu de l'arborescence, navigation, sélection

**Critères de validation** :
- L'utilisateur voit l'arborescence complète de `Obsidian/`
- Clic sur un dossier → déplie/replie
- Clic sur un document → ouvre le document
- La navigation est fluide (< 100ms par action)

### Sous-livrable C — Éditeur Markdown et sauvegarde
**Objectif** : Éditer et sauvegarder des documents.

**Livrables** :
- `DocumentEditor` avec CodeMirror 6
- `PUT /v1/documents/{path}` avec concurrence
- Gestion des conflits (hash mismatch → 409)
- Tests : édition, sauvegarde, conflit, erreur

**Critères de validation** :
- L'utilisateur peut modifier un document et le sauvegarder
- La modification est persistée sur disque
- Obsidian Desktop retrouve la modification
- Un conflit de concurrence affiche une erreur claire
- Les propriétés YAML sont préservées

### Sous-livrable D — Preview et résolution des liens
**Objectif** : Prévisualiser le Markdown et naviguer via les liens.

**Livrables** :
- `DocumentPreview` composant
- Rendu Markdown (remark/rehype)
- Résolution des `[[...]]` en liens cliquables
- Navigation entre documents via les liens

**Critères de validation** :
- Le preview affiche le Markdown correctement
- Les liens `[[...]]` sont cliquables et naviguent vers le document cible
- Les liens non résolus sont visuellement distincts
- Les images et assets sont affichés

### Sous-livrable E — Onglets et historique
**Objectif** : Gérer plusieurs documents ouverts.

**Livrables** :
- `DocumentTabs` composant
- Zustand store pour les onglets
- Historique de navigation (back/forward)
- Documents récemment ouverts

**Critères de validation** :
- L'utilisateur peut ouvrir plusieurs documents dans des onglets
- La fermeture d'un onglet fonctionne
- L'historique de navigation fonctionne (back/forward)
- Les documents récemment ouverts sont listés

### Sous-livrable F — Backlinks et recherche
**Objectif** : Explorer les relations entre documents.

**Livrables** :
- `BacklinksPanel` composant
- `DocumentSearch` composant
- Endpoint de recherche documentaire
- Endpoint backlinks

**Critères de validation** :
- Les backlinks d'un document sont affichés correctement
- La recherche retourne des résultats pertinents
- La recherche est rapide (< 500ms pour 736 documents)
- Les résultats de recherche sont cliquables

---

## 9. Fichiers concernés par la future implémentation

### Core (nouveaux)
```
core/documents/__init__.py
core/documents/models.py
core/documents/repository.py
core/documents/index.py
core/documents/link_resolver.py
core/documents/yaml_parser.py
core/documents/security.py
```

### API (nouveau router)
```
interfaces/api/routers/documents.py
```

### Frontend (nouveaux composants)
```
interfaces/webui/src/components/features/documents/components/document-explorer.tsx
interfaces/webui/src/components/features/documents/components/document-editor.tsx
interfaces/webui/src/components/features/documents/components/document-preview.tsx
interfaces/webui/src/components/features/documents/components/document-tabs.tsx
interfaces/webui/src/components/features/documents/components/document-properties.tsx
interfaces/webui/src/components/features/documents/components/backlinks-panel.tsx
interfaces/webui/src/components/features/documents/components/document-search.tsx
interfaces/webui/src/lib/api/documents.ts
interfaces/webui/src/store/document-tabs.store.ts
```

### Tests (nouveaux)
```
tests/core/test_document_repository.py
tests/core/test_document_index.py
tests/core/test_document_link_resolver.py
tests/core/test_document_security.py
tests/interfaces/test_documents_api.py
interfaces/webui/tests/unit/documents/*.test.tsx
```

### Configuration
```
.env / .env.example — ajouter ETHAN_DOCUMENT_ROOT
```

---

## 10. ADR — Décision architecturale

### ADR-1017 : Knowledge Workspace — Document Repository séparé du Knowledge Manager

**Statut** : Proposé

**Contexte** : Le système Knowledge existant (KnowledgeManager) gère des nœuds de connaissance dans un store persistant. Le référentiel `Obsidian/` est un ensemble de fichiers Markdown/YAML. Il faut un service dédié pour accéder à ces fichiers sans transformer KnowledgeManager en gestionnaire de fichiers.

**Décision** : Créer un `DocumentRepository` séparé, dans `core/documents/`, qui gère l'accès au référentiel fichier. Le KnowledgeManager reste inchangé et peut recevoir des références aux documents via l'Event Bus.

**Conséquences** :
- Deux services distincts avec des responsabilités claires
- Pas de modification de KnowledgeManager
- L'index documentaire est une projection read-only des fichiers
- Le Knowledge Graph peut référencer des documents sans les dupliquer

---

## 11. Résumé des choix technologiques

| Composant | Choix | Licence | Justification |
|-----------|-------|---------|---------------|
| Éditeur Markdown | CodeMirror 6 | MIT | Évalué par Nodum, performant, extensible |
| Rendu Markdown | remark + rehype | MIT | Standard de l'écosystème React/Next.js |
| État des onglets | Zustand | MIT | Déjà utilisé dans ETHAN |
| Données serveur | TanStack Query | MIT | Déjà utilisé dans ETHAN |
| Parsing YAML | PyYAML | MIT | Déjà utilisé dans ETHAN |
| Graphe (Phase 2) | React Flow ou Sigma.js | MIT | À évaluer lors de la Phase 2 |
| Canvas (Phase 2) | React Flow | MIT | À évaluer lors de la Phase 2 |

---

## 12. Contraintes respectées

- Aucun refactoring global
- Aucun déplacement des 736 documents
- Aucune duplication du référentiel
- Aucun second Knowledge Manager
- Aucun second moteur RAG
- Aucun contournement HROT
- Aucun changement Docker
- Modifications Git préexistantes préservées
- Architecture proposée, pas implémentée
- Nodum étudié, composants réutilisables identifiés, architecture non importée

Mise à jour incrémentale : quand un document est modifié, seuls ses liens sortants sont re-calculés, et la map inversée est mise à jour.
