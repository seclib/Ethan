# C4 Architecture Documentation — ETHAN Cognitive OS

## Vue d'ensemble

Cette documentation décrit l'architecture d'ETHAN Cognitive OS selon le modèle C4 (Context, Containers, Components, Code).

**Version:** 0.3.0  
**Phase:** 0.3 — Cognitive Kernel Core  
**Date:** 2025-01-23

## Structure de la documentation

```
docs/architecture/
├── C4-Level1-System-Context.md    # Vue système — acteurs et frontières
├── C4-Level2-Containers.md        # Vue conteneurs — services et bases
├── C4-Level3-Components-Kernel.md # Vue composants — Kernel détaillé
├── C4-Level4-Code-View.md         # Vue code — classes et interfaces
├── C4-Event-Flow.md               # Flux événementiels détaillés
└── C4-README.md                   # Ce fichier — index
```

## Niveau 1 — System Context

**Fichier:** `C4-Level1-System-Context.md`

Montre le système ETHAN dans son contexte global :
- **Acteurs:** User (humain), API externe (système)
- **Système central:** ETHAN Cognitive OS
- **Systèmes externes:** NATS, Redis, PostgreSQL

**Technologies:** PlantUML C4_Context, ASCII diagram

## Niveau 2 — Container Diagram

**Fichier:** `C4-Level2-Containers.md`

Décompose le système en conteneurs déployables :
- **API Gateway** (FastAPI) — point d'entrée HTTP
- **Cognitive Kernel** (Python asyncio) — orchestrateur
- **Modules** (Python) — services cognitifs pluggables
- **NATS JetStream** — broker événementiel
- **Redis** — state live
- **PostgreSQL** — state persistant
- **Scheduler** — tâches cron

**Technologies:** PlantUML C4_Container, ASCII diagram

## Niveau 3 — Component Diagram

**Fichier:** `C4-Level3-Components-Kernel.md`

Détaille les composants internes du Kernel :
- **Event Router** — routing, subscriptions wildcards
- **Goal Manager** — lifecycle des goals
- **Module Registry** — découverte et health checks
- **State Manager** — sync Redis + PostgreSQL
- **Scheduler** — triggers planifiés

**Technologies:** PlantUML C4_Component, ASCII diagram

## Niveau 4 — Code-Level View

**Fichier:** `C4-Level4-Code-View.md`

Montre les classes principales et leurs relations :
- **CognitiveKernel** — classe principale
- **GoalManager** — gestion des goals
- **ModuleRegistry** —registre des modules
- **EventBus / NatsEventBus** — abstraction NATS
- **RedisLiveState / PostgresPersistentState** — state
- **Event / EventType** — schéma d'événements

**Technologies:** PlantUML class diagram, code snippets

## Flux événementiels

**Fichier:** `C4-Event-Flow.md`

Documente les scénarios concrets :
- **Scénario 1:** Traitement intention utilisateur (intent → task → plan → memory → reflection)
- **Scénario 2:** Événement planifié (cron)
- **Scénario 3:** Gestion d'erreur module (timeout, retry, fail)
- **Topics NATS** — rôle de chaque topic

**Format:** Diagrammes ASCII, tableaux

## Concepts clés

### Event-Driven Architecture

Toute communication inter-composants se fait via NATS :
- **Publish/Subscribe** — broadcast d'événements
- **Request-Reply** — appel synchrone optionnel
- **Queue Groups** — load balancing des modules

### Capability-Based Routing

Le Kernel route les events vers les modules selon leurs **capabilities** déclarées :
- `handle.intent` → Executive Module
- `handle.task` → Planner Module
- `store.event` → Memory Module
- `handle.completion` → Reflective Module

### State Duality

- **Redis** = state live, TTL, sessions, heartbeats
- **PostgreSQL** = state persistant, events, goals, audit

### No Business Logic in Kernel

Le Kernel ne fait **que router** :
- Aucune intelligence métier
- Aucun LLM
- Aucune décision stratégique
- Responsabilité unique: orchestrer

## Comment lire cette documentation

1. **Commencer par Level 1** — comprendre le contexte global
2. **Puis Level 2** — voir les conteneurs et leurs interactions
3. **Ensuite Level 3** — détail du Kernel (cœur du système)
4. **Enfin Level 4** — code et interfaces
5. **Consulter Event Flow** — scénarios concrets

## Génération des diagrammes

Les diagrammes PlantUML peuvent être générés avec :

```bash
# Installer PlantUML
brew install plantuml  # macOS
apt-get install plantuml  # Ubuntu

# Générer les PNG
plantuml docs/architecture/C4-Level1-System-Context.md
plantuml docs/architecture/C4-Level2-Containers.md
plantuml docs/architecture/C4-Level3-Components-Kernel.md
plantuml docs/architecture/C4-Level4-Code-View.md
```

## Références

- [C4 Model](https://c4model.com/)
- [PlantUML C4-PlantUML](https://github.com/plantuml-stdlib/C4-PlantUML)
- [ETHAN RFC-008](engineering/rfc/rfc-008-cognitive-kernel-phase-0.2.md)
- [ETHAN ADR-1003](engineering/adr/ADR-1003-single-entry-intent-model.md)

---

**Mainteneur:** ETHAN Architecture Team  
**Dernière mise à jour:** 2025-01-23