# ETHAN — Audit de fiabilité et préparation d'une migration Rust progressive

## 1. Cartographie des Composants et Flux
L'architecture d'ETHAN est basée sur un modèle de **Cognitive OS** où le `CognitiveKernel` agit comme l'orchestrateur central.

### Composants Réels et Responsabilités
| Composant | Fichier Clé | Responsabilité | Dépendances |
| :--- | :--- | :--- | :--- |
| **Cognitive Kernel** | `core/kernel.py` | Routage d'événements, cycle de vie des modules, dispatching. | EventBus, StateBackend, Registry |
| **Event Bus** | `core/bus/nats_bus.py` | Communication asynchrone via NATS JetStream. | NATS Server |
| **State Management** | `core/state/composite_backend.py` | Gestion hybride État Live (Redis) et Persistant (PostgreSQL). | Redis, PostgreSQL |
| **RAG Pipeline** | `core/rag/pipeline.py` | Ingestion, indexation vectorielle et récupération de contexte. | Vector Store, Embeddings |
| **Memory System** | `core/memory/manager.py` | Gestion de la mémoire sémantique et épisodique. | Vector Store, StateBackend |
| **Auth/Security** | `core/auth/`, `core/security/` | Validation des identités, contrôle d'accès (RBAC) et gardes de prompts. | PostgreSQL, JWT |

### Flux de Communication
1. **Interface** $\rightarrow$ **Event Bus** : Un événement d'intention (`intent.>`) est publié.
2. **Event Bus** $\rightarrow$ **Kernel** : Le Kernel intercepte l'événement et le route vers le module compétent via le `ModuleRegistry`.
3. **Kernel** $\rightarrow$ **Module** : Le module exécute la logique métier et publie un résultat sur le bus.
4. **Module** $\rightarrow$ **State/Memory** : L'état est synchronisé via le `CompositeStateBackend`.

---

## 2. Analyse de Fiabilité et Défauts Observables

### Gestion des Erreurs et États Incohérents
- **Kernel Rollback** : Le `CognitiveKernel._rollback_startup` est une implémentation "best-effort" (`core/kernel.py:173`). En cas de crash partiel au boot, l'état des composants peut être indéterminé.
- **Sync State Silencieuse** : Le `_sync_state` du Kernel (`core/kernel.py:294`) capture les exceptions avec un simple `logger.warning`. Une panne du backend d'état peut entraîner une perte de traces d'événements sans interrompre le flux, créant une divergence entre l'exécution et l'audit.
- **Trous d'implémentation (TODOs)** : 
    - `core/bus/backends/nats_jetstream.py:78` : La méthode `read` est vide.
    - `core/bus/backends/redis_streams.py:60` : La méthode `read` est vide.
    - `core/bus/store.py:188` : La rétention n'est pas implémentée.

### Concurrence et Récupération
- **Verrous Python (asyncio.Lock)** : Utilisation massive de `asyncio.Lock` dans `core/bus/memory_bus.py` et divers plugins. Bien que correct pour de l'asynchrone simple, cela devient un goulot d'étranglement lors de montées en charge massives de l'Event Bus.
- **Absence de Backpressure** : Le `EventRouter` (`core/bus/router.py`) exécute les handlers via `await route.handler(event)` sans mécanisme de queue de priorité réelle ou de limitation de débit au niveau du routeur lui-même.

### Validation et Tests
- **Couverture Faible** : Le `STABILITY_REPORT.md` indique une couverture des tests Core $< 30\%$.
- **Validation d'entrées** : La validation repose largement sur des types Python et des `try/except` génériques, augmentant le risque d'exceptions non gérées en production.

---

## 3. Classification des Risques

| Problème | Statut | Risque | Justification |
| :--- | :--- | :--- | :--- |
| ** Lecture Event Store vide** | **Confirmé** | Critique | Les backends NATS et Redis Streams ne lisent pas les événements (`read` est vide). Le replay est impossible. |
| **Divergence État/Audit** | **Plausible** | Moyen | La synchronisation d'état est non-critique ; un échec de sync ne bloque pas le kernel. |
| **Deadlocks asyncio** | **Hypothèse** | Faible | Risque lié à la complexité des verrous imbriqués dans les plugins. |
| **Fuites de mémoire RAG** | **Plausible** | Moyen | L'indexation en mémoire (`vector_backend="memory"`) peut saturer la RAM sur de gros corpus. |

---

## 4. Analyse des Candidats Rust

### Matrice de Décision
| Composant | Risque | Autonomie | Complexité | Bénéfice Rust | Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Event Bus Backend** | Haut | Très Haute | Moyenne | Performance, Typage strict, Fiabilité | **9/10** |
| **RAG Ingestion/Indexing** | Moyen | Haute | Haute | Parallélisme CPU, Gestion mémoire | **6/10** |
| **State Backend (Composite)** | Moyen | Moyenne | Haute | Sécurité mémoire, Concurrence | **5/10** |

### Candidat Sélectionné : L'Event Bus Backend (et Store)
**Preuves tirées du dépôt :**
1. `core/bus/nats_bus.py` et `core/bus/interface.py` définissent un contrat strict.
2. Les implémentations actuelles de stockage (`nats_jetstream.py`, `redis_streams.py`) sont incomplètes ou fragiles.
3. Le volume d'événements est le cœur battant d'ETHAN ; toute latence ou corruption ici impacte tout le système.

---

## 5. Plan d'Expérimentation : Rust Event Store

### Contrat d'Interface (FFI / PyO3)
L'objectif est de remplacer `core/bus/backends/base.py` et ses implémentations par un module Rust compilé via PyO3.
- **Interface Rust** : 
    - `write(event: Event) -> Result<Position, Error>`
    - `read(pattern: String, start: DateTime) -> Iterator<Event>`
    - `save_checkpoint(...)`
- **Communication** : Utilisation de `serde_json` pour maintenir la compatibilité avec les événements JSON actuels.

### Stratégie de Tests et Validation
1. **Shadow Mode** : Le backend Rust écrit en parallèle du backend Python actuel.
2. **Diff-Check** : Un script compare les événements stockés par les deux versions.
3. **Stress Test** : Injection de $10^6$ événements/sec pour mesurer la réduction de latence et la stabilité mémoire.

### Critères de Succès
- **Zéro perte d'événement** sur 24h de charge continue.
- **Réduction de la latence** de publication $\ge 50\%$.
- **Consommation RAM** stable (pas de croissance linéaire avec le volume).

### Retour Arrière (Rollback)
Le système conserve l'interface `EventBus` abstraite. Le retour arrière consiste à modifier la configuration pour réinjecter l'instance `NATSBus` Python au lieu du module Rust.

---

## 6. Questions Non Résolues et ADR
- **ADR à clarifier** : La stratégie de rétention des événements (`core/bus/store.py:188`) doit être définie avant d'implémenter le stockage en Rust.
- **Interopérabilité** : Faut-il passer par NATS JetStream (externe) ou implémenter un WAL (Write-Ahead Log) local en Rust pour une fiabilité maximale ?
- **Déploiement** : L'ajout de Rust complexifie le `Dockerfile.kernel`. Est-ce acceptable pour le cycle de déploiement actuel ?

## Recommandation Finale

**L'audit révèle que la priorité absolue n'est pas la performance, mais la complétude.**
Le système possède des fonctions critiques vides (Lecture du bus). 

**Recommandation :**
1. **Phase 1 (Immédiate)** : Corriger l'architecture Python existante pour implémenter les méthodes `read` et la rétention.
2. **Phase 2 (Expérimentale)** : Migrer uniquement le **Backend de Stockage d'Événements (Event Store)** vers Rust pour garantir l'immuabilité et la performance du log.
3. **Ne pas migrer** le reste du Core pour le moment, car la logique métier est encore en évolution.
