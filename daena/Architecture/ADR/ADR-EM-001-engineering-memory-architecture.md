# ADR-EM-001 — Architecture Engineering Memory pour ETHAN

Date : 2026-11-03
Statut : PROPOSED
Décision : proposée, à valider humainement avant implémentation.
Contexte : `/home/fatsio/AI/Ethan/Obsidian`, Première Loi d'ETHAN, `Obsidian/Architecture/ADR/ADR-001-agent-system.md`, `Obsidian/Architecture/ADR/ADR-4004-core-source-of-truth.md`

## Contexte

ETHAN possède déjà un dépôt avec une architecture clairement séparée : `core/`, `interfaces/`, `plugins/`, `core/persistence`, `core/knowledge` et des services API. Le flux d'événements existe principalement via `core/events` (alias `core.ethan_types.event` et `core.bus.memory_bus`), avec une capacité de validation via `core.registry.events.EventSchemaRegistry`, une capacité de persistence dans `core/persistence` et une capacité d'ingestion de sources IA via `core/knowledge/agent_traces`.

L'Engineering Memory actuellement présente dans `Obsidian/` est une mémoire documentaire officielle et hors Git, complétée par les archives, les synthèses et l'indexation. Elle doit rester la référence humaine et agent sans devenir une seconde base documentaire concurrente.

Le besoin n'est pas de tout réécrire, mais de disposer d'un service centralisé qui exploite et alimente cette mémoire.

## Problème

Aujourd'hui, l'information technique est dispersée :

- le code et les tests sont dans le dépôt ;
- les ADR sont dans `docs/adr` et `docs/architecture/adr` ;
- les rapports et audits sont dans `docs` et `Obsidian` ;
- les connaissances importées existent aussi dans `core/knowledge` et `core/knowledge/agent_traces` ;
- les événements ne partagent pas toujours le même modèle ;
- les synthèses d'agents ne sont pas toujours des preuves.

Sans une architecture Engineering Memory, le risque est un drift entre le code, les docs, le travail des agents et l'état vérifié.

## Décision proposée

Créer un **Memory Service** dans le Core, exposé via l'API existante, dont le rôle est de collecter, valider, persister et interroger la mémoire Engineering Memory. Le service ne crée pas une base documentaire rivale. Il exploite d'abord une source documentaire canonique : le dossier `Obsidian`.

Les composants minimums sont :

1. Memory Service
2. Event Collector
3. Validation Engine
4. Persistence Adapter
5. Registry
6. Query / Retrieval API

Ils alimentent une séparation stricte entre :

- `Historical Record`
- `Technical Knowledge`
- `Verified Current State`

## Architecture logique

```text
Agent / WebUI / Plugin / Tool / Backend
  → Event Collector
  → Validation Engine
  → Persistence Adapter
  → Obsidian
  → Indexation
  → Retrieval API
  → Agents / WebUI / Administrateur
```

Cette architecture s'inscrit dans le principe Core-first d'ETHAN. `interfaces` ne sont que des adaptateurs. Les agents n'ont pas accès direct en écriture au disque sans passer par le service et ses validations.

## Réutilisation du code existant

- `core/registry/events.py` peut fournir l'EventSchemaRegistry et la validation JSON.
- `core/persistence` peut fournir l'adapter de persistance et les migrations.
- `core/bus` et `core/bus/backends/rust_event_store` peuvent fournir le transport et le stockage événementiel, éventuellement en mode shadow.
- `core/knowledge` et `core/knowledge/agent_traces` peuvent fournir l'ingestion et le normaliseur.
- `interfaces/api/routers` peuvent exposer les routes `memory/*`, `knowledge/*` et `events`.
- `Obsidian/` reste la source documentaire officielle.

## Séparation des couches

### Historical Record

- Archives brutes, transcripts, events, migrations, audits.
- Aucune réécriture pour imposer une harmonie artificielle.
- Preuves et sources.

### Technical Knowledge

- ADR, ESR, ASR, architecture, composants, dépendances.
- Synthèses validées et guides de récupération.

### Verified Current State

- Ce qui est prouvé par le dépôt, les tests, les logs et les audits.
- Pas de synthèse d'agent comme preuve.
- Source de décision pour l'état courant.

## Responsabilités Rust vs Python

### Python (core/interfaces)

- Memory Service et API.
- Modèle de données, validation de haut niveau, frontmatter YAML et Markdown.
- Intégration avec `core/knowledge` pour l'ingestion.
- Authentification et RBAC via `core/auth` et les routeurs API.
- Plugins, providers, RAG et orchestration existants.
- Persistance relationnelle SQLite / PostgreSQL.
- Gestion Git et références source.
- Tests et parité.

### Rust (`core/rust`, `core/bus/backends/rust_event_store`)

- Event store optionnel en mode shadow mode.
- Accélération possible pour le transport, le hashing et l'indexation bas-niveau.
- Journalisation append-only à haute performance si la charge le demande.
- Health check et diagnostics bas-niveau via `ethan_health`.

### Règle

Le cœur métier et le moteur de jugement restent en Python. Rust complète les chemins chauds. Aucun service Rust ne doit devenir obligatoire si la fallback Python existe.

## Conséquences

1. ETHAN garde son architecture principale.
2. La memory service utilise les services existants au lieu de les contourner.
3. La provenance et la séparation des couches deviennent explicites.
4. Les synthèses d'agents et les résultats narratifs sont confinés à `PROVISIONAL`.
5. L'intégration Wasm et mobiles via `interfaces/web`, le terminal et les plugins restent inchangés.

## Alternatives

- Copier Obsidian dans un service central : rejeté, car cela ferait une seconde source.
- Faire un Knowledge Graph complet en prérequis : rejeté, car le stockage doit rester simple et lisible.
- Interdire la mémoire documentaire : rejeté par design.

## Décision pour l'étape suivante

Passer à l'étape d'ESR/ASR et à la préparation technique. L'implémentation code reste dans une phase dédiée et ne doit pas commencer sans validation humaine des données et des contrats.

---

Document lié : `Obsidian/Architecture/ESR/ESR-EM-001-engineering-memory.md`.
