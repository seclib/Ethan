# Mission 03 — Matrice de parité WebUI / CLI

Branche : `refactor/ethan-rebuild-p0`. État au 2026-11-11.

Légende : IMPLEMENTED / TESTED / RUNTIME_VALIDATED / PARTIAL / BLOCKED / NOT_IMPLEMENTED / NOT_VALIDATED.

## 03-A — Applications

| Capacité | Core | API | WebUI | CLI | Statut |
|---|---|---|---|---|---|
| Liste des applications découvertes | ✅ `application_registry` | `GET /applications` | ✅ `applications/page.tsx` | ✅ `application list` | IMPLEMENTED |
| Détail d'une application | ✅ | `GET /applications/{app_id}` | ✅ `[app_id]/page.tsx` | ✅ `application show` | IMPLEMENTED |
| Rafraîchir le catalogue | ✅ | `POST /applications/refresh` | ✅ (bouton Actualiser) | ✅ `application refresh` | IMPLEMENTED |
| Applications enregistrées (registry canonique) | ✅ `ApplicationRegistry` | `GET /applications/registered` | (via capabilities) | ✅ `application registered` | IMPLEMENTED |
| Contrats de capacités applicatives | ✅ | `GET /application-capabilities` | ✅ | ✅ `application capabilities` | IMPLEMENTED |
| Validation d'un contrat de capacité | ✅ | `POST /application-capabilities/validate` | ✅ | ✅ `application validate` | IMPLEMENTED |
| Enregistrement d'une capacité | ✅ | `POST /application-capabilities` | (via approval) | ✅ `application register` | IMPLEMENTED |
| Démarrage runtime (odin, frame) | ✅ `get_odin_service`/`get_frame_service` | `POST /applications/{app_id}/start` | ✅ | ✅ `application start` | IMPLEMENTED |
| Arrêt runtime | ✅ | `POST /applications/{app_id}/stop` | ✅ | ✅ `application stop` | IMPLEMENTED |
| Statut runtime | ✅ | `GET /applications/{app_id}/runtime` | ✅ | ✅ `application runtime` | IMPLEMENTED |
| Bind/activate capability implementation | ✅ | `POST .../bind`, `.../activate` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Invocation d'une capacité | ✅ | `POST .../invoke` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Catalogue d'intégration applicative | ✅ | `GET /application-integration-catalog` | ✅ `application-catalog.tsx` | ✅ `application catalog` | IMPLEMENTED |
| Manifests d'applications | ✅ | `GET /application-manifests` | ✅ | ✅ `application manifests` | IMPLEMENTED |

## 03-B — Sessions (chats)

| Capacité | Core | API | WebUI | CLI | Statut |
|---|---|---|---|---|---|
| Liste des sessions (chats) | ✅ `ChatStore` | `GET /chats` | ✅ | ✅ `session list` | IMPLEMENTED |
| Détail d'une session | ✅ | `GET /chats/{chat_id}` | ✅ | ✅ `session show` | IMPLEMENTED |
| Création d'une session | ✅ | `POST /chats` | ✅ | ✅ `session create` | IMPLEMENTED |
| Mise à jour (titre, etc.) | ✅ | `PUT /chats/{chat_id}` | ✅ | ✅ `session update` | IMPLEMENTED |
| Suppression | ✅ | `DELETE /chats/{chat_id}` | ✅ | ✅ `session delete` | IMPLEMENTED |
| Historique des messages | ✅ | `GET /chats/{chat_id}/messages` | ✅ | ✅ `session messages` | IMPLEMENTED |
| Ajout de message | ✅ | `POST /chats/{chat_id}/messages` | ✅ | ✅ (via chat) | IMPLEMENTED |
| Partage d'une session | ✅ | `POST /chats/{chat_id}/share` | ✅ | ✅ `session share` | IMPLEMENTED |
| Filtrage (archived, folder, project, unassigned) | ✅ | `GET /chats?...` | ✅ | ✅ `session list --archived/--folder/--project/--unassigned` | IMPLEMENTED |
| Reprise d'une session existante | ✅ | (via chat_id) | ✅ | ✅ (`--chat-id`/`--session`) | IMPLEMENTED |

## 03-C — Memory (Core)

| Capacité | Core | API | WebUI | CLI | Statut |
|---|---|---|---|---|---|
| Historique conversationnel local (CLI) | n/a (CLI-only) | n/a | n/a | ✅ `memory recent/frequent` | IMPLEMENTED (CLI-only, distinct du Core) |
| Santé mémoire | ✅ `MemoryManager` | `GET /memory/health` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Enregistrement d'événements mémoire | ✅ | `POST /memory/events` | ✅ | ✅ `memory record` | IMPLEMENTED |
| Validation d'événements | ✅ | `POST /memory/events/validate` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Consultation d'un record | ✅ | `GET /memory/events/{record_id}` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Liste des événements | ✅ | `GET /memory/events` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Historique par composant | ✅ | `GET /memory/components/{component}/history` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Records mémoire | ✅ | `GET /memory/records` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Arbre du vault | ✅ | `GET /memory/vault/tree` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Lecture d'un fichier vault | ✅ | `GET /memory/vault/file` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Recherche vault | ✅ | `GET /memory/vault/search` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Backlinks | ✅ | `GET /memory/vault/backlinks` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Graphe vault | ✅ | `GET /memory/vault/graph` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Résolution de chemin | ✅ | `GET /memory/vault/resolve` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Écriture d'un fichier vault | ✅ | `POST /memory/vault/file` | ✅ | ✅ `memory vault-write` | IMPLEMENTED |

## 03-D — RAG / Knowledge

| Capacité | Core | API | WebUI | CLI | Statut |
|---|---|---|---|---|---|
| Liste des connaissances | ✅ | `GET /knowledge` | ✅ | ✅ (`knowledge list`) | IMPLEMENTED |
| Recherche | ✅ | `GET /knowledge/search` | ✅ | ✅ (`knowledge search`) | IMPLEMENTED |
| Collections | ✅ | `GET /knowledge/collections` | ✅ | ✅ (`knowledge collections`) | IMPLEMENTED |
| Création de collection | ✅ | `POST /knowledge/collections` | ✅ | ✅ (`knowledge collection create`) | IMPLEMENTED |
| Arbre des collections | ✅ | `GET /knowledge/collections/tree` | ✅ | (via collections) | PARTIAL |
| Récupération multi-collections | ✅ | `POST /knowledge/collections/retrieve-multi` | ✅ | ✅ `knowledge retrieve-multi` | IMPLEMENTED |
| Détail collection | ✅ | `GET /knowledge/collections/{id}` | ✅ | ✅ (`knowledge collection show`) | IMPLEMENTED |
| Mise à jour collection | ✅ | `PUT /knowledge/collections/{id}` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Déplacement collection | ✅ | `POST /knowledge/collections/{id}/move` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Suppression collection | ✅ | `DELETE /knowledge/collections/{id}` | ✅ | ✅ (`knowledge collection delete`) | IMPLEMENTED |
| Documents d'une collection | ✅ | `GET /knowledge/collections/{id}/documents` | ✅ | ✅ (`knowledge documents`) | IMPLEMENTED |
| Ajout de document | ✅ | `POST /knowledge/collections/{id}/documents` | ✅ | ✅ (`knowledge document add`) | IMPLEMENTED |
| Suppression de document | ✅ | `DELETE .../documents/{doc_id}` | ✅ | ✅ (`knowledge document delete`) | IMPLEMENTED |
| Récupération dans une collection | ✅ | `POST /knowledge/collections/{id}/retrieve` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Détail connaissance | ✅ | `GET /knowledge/{id}` | ✅ | ✅ (`knowledge show`) | IMPLEMENTED |
| Création connaissance | ✅ | `POST /knowledge` | ✅ | ✅ (`knowledge create`) | IMPLEMENTED |
| Mise à jour connaissance | ✅ | `PUT /knowledge/{id}` | ✅ | ✅ (`knowledge update`) | IMPLEMENTED |
| Suppression connaissance | ✅ | `DELETE /knowledge/{id}` | ✅ | ✅ (`knowledge delete`) | IMPLEMENTED |
| Connexions | ✅ | `POST /knowledge/{id}/connections` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Statut RAG | ✅ `core/rag` | (via knowledge) | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Stratégies RAG | ✅ `core/rag/strategies.py` | (via knowledge) | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Indexation / ingestion | ✅ `core/rag/ingestion.py` | (imports) | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Import de documents | ✅ | `POST /knowledge/imports` | ✅ | ❌ absent | NOT_IMPLEMENTED |
| Statut d'import | ✅ | `GET /imports/{job_id}` | ✅ | ❌ absent | NOT_IMPLEMENTED |

## Synthèse

- **Applications** : 0 commande CLI, 14 capacités API non exposées au CLI.
- **Sessions** : 2 capacités CLI (chat_id, resume), 7 capacités API non exposées.
- **Memory (Core)** : 0 commande CLI Core (la commande `memory` existante est CLI-only, historique de commandes).
- **RAG/Knowledge** : ~12 capacités CLI, ~10 capacités API non exposées (retrieve, retrieve-multi, update/move collection, connections, statut RAG, stratégies, ingestion, imports).

## Prochaine étape

Implémenter domain par domain selon l'ordre 03-A → 03-B → 03-C → 03-D, avec validation à chaque étape.
