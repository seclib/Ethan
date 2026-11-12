# C4 Architecture — Level 2: Container Diagram

## Vue d'ensemble

Cette vue montre les conteneurs principaux d'ETHAN Cognitive OS : services applicatifs, bases de données et message broker.

## Diagramme ASCII

```
┌────────────────────────────────────────────────────────────────────────┐
│                      ETHAN Cognitive OS — Containers                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─────────────┐                                                      │
│  │ API Gateway │  FastAPI + Uvicorn                                    │
│  │   :8000     │  - Reçoit les requêtes HTTP                           │
│  │             │  - Valide et émet les events NATS                     │
│  └──────┬──────┘  - Health checks                                      │
│         │                                                              │
│         │ publish / subscribe                                          │
│         ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │              Cognitive Kernel (Python asyncio)               │      │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │      │
│  │  │ Event Router │  │ Goal Manager │  │ Module Registry │  │      │
│  │  └──────────────┘  └──────────────┘  └─────────────────┘  │      │
│  │  ┌──────────────┐  ┌─────────────────────────────────────┐  │      │
│  │  │State Manager │  │          Scheduler                 │  │      │
│  │  └──────────────┘  └─────────────────────────────────────┘  │      │
│  └─────────────────────────────────────────────────────────────┘      │
│              │                              │                         │
│              │                              │                         │
│    ┌─────────▼──────────┐                  │                         │
│    │   Event Router     │──────────────────┘                         │
│    │   (NATS)           │   dispatches by capability                 │
│    └────────────────────┘                                            │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                        Modules (Independants)                   │  │
│  │                                                                │  │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │  │
│  │   │  Executive   │  │   Planner    │  │     Memory       │    │  │
│  │   │   Module     │  │   Module     │  │     Module       │    │  │
│  │   └──────────────┘  └──────────────┘  └──────────────────┘    │  │
│  │                                                                │  │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │  │
│  │   │  Execution   │  │  Reflective  │  │   (extensible)   │    │  │
│    │   │   Module     │  │   Module     │  │                  │    │  │
│    │   └──────────────┘  └──────────────┘  └──────────────────┘    │  │
│    └────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌──────────────────┐  ┌────────────────────────────────────┐        │
│  │    Scheduler     │  │         State Layer                │        │
│  │                  │  │                                    │        │
│  │ Cron + background│  │  ┌─────────────┐ ┌─────────────┐  │        │
│  │ schedules events │  │  │    Redis    │ │ PostgreSQL  │  │        │
│  │                  │  │  │  (live)     │ │ (persistent) │  │        │
│  └──────────────────┘  │  └─────────────┘ └─────────────┘  │        │
│                         └────────────────────────────────────┘        │
└────────────────────────────────────────────────────────────────────────┘
        │                    │                    │
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────────┐┌──────────────────┐┌──────────────────────┐
│    NATS          ││     Redis        ││    PostgreSQL        │
│   JetStream      ││   7-alpine       ││      16-alpine       │
│  :4222 (client)  ││   :6379         ││      :5432           │
│  :8222 (mgmt)    ││  TTL, sessions   ││  events, goals,      │
│  :6222 (cluster) ││  goals, modules  ││  modules, audit      │
└──────────────────┘└──────────────────┘└──────────────────────┘
```

## PlantUML

```plantuml
@startuml C4_Container
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

title Container Diagram — ETHAN Cognitive OS

Person(user, "User", "CLI / API / GUI")

Container_Boundary(ethan, "ETHAN Cognitive OS") {
    Container(api, "API Gateway", "FastAPI, Python", "Entry point, validates intents, emits events to NATS")
    Container(kernel, "Cognitive Kernel", "Python asyncio", "Event orchestrator, no business logic")
    Container(modules, "Cognitive Modules", "Python", "Pluggable cognitive services: executive, planner, memory, reflective")

    ContainerDb(redis, "Redis", "Redis 7", "Live state, sessions, goals TTL, module heartbeats")
    ContainerDb(postgres, "PostgreSQL", "PostgreSQL 16", "Events, goals, modules, audit log, persistent state")

    ContainerQueue(nats, "NATS JetStream", "NATS 2.10", "Message broker, pub/sub, request-reply, queue groups")

    Container(scheduler, "Scheduler", "Python asyncio", "Cron triggers, background tasks, scheduled events")
}

Rel(user, api, "Sends intents", "HTTPS POST /v1/message")
Rel(api, nats, "Publishes intent events", "TCP :4222")
Rel(nats, kernel, "Delivers events", "wildcard subscriptions")

Rel(kernel, modules, "Dispatches by capability", "module.dispatch.*")
Rel(modules, nats, "Publishes results", "task.created, task.plan, memory.stored")
Rel(nats, kernel, "Routes responses", "goal.>, module.>")

Rel(kernel, redis, "Syncs live state", "TCP :6379")
Rel(kernel, postgres, "Persists events/goals", "TCP :5432")
Rel(scheduler, nats, "Triggers scheduled events", "schedule.trigger")

Rel(modules, redis, "Stores memory (optional)", "TCP :6379")
Rel(modules, postgres, "Audit events (optional)", "TCP :5432")

@enduml
```

## Conteneurs et responsabilités

| Conteneur | Technologie | Responsabilité | Port |
|-----------|------------|----------------|------|
| **API Gateway** | FastAPI + Uvicorn | Point d'entrée HTTP, validation, émission events | 8000 |
| **Cognitive Kernel** | Python asyncio | Orchestrateur événementiel, routing, state sync | N/A |
| **Modules** | Python asyncio | Services cognitifs pluggables, découplés | Interne |
| **NATS JetStream** | NATS 2.10 | Broker événementiel, pub/sub, request-reply,持久性 | 4222/8222/6222 |
| **Redis** | Redis 7 | State live, TTL, sessions, goals, heartbeats | 6379 |
| **PostgreSQL** | PostgreSQL 16 | Events persistants, goals, modules, audit | 5432 |
| **Scheduler** | Python asyncio | Tâches cron, événements planifiés | Interne |

## Flux entre conteneurs

```
1. User → API Gateway (POST /v1/message)
2. API Gateway → NATS (publish: intent.user)
3. NATS → Cognitive Kernel (subscribe: intent.>)
4. Cognitive Kernel → GoalManager (create goal)
5. Cognitive Kernel → ModuleRegistry (find_by_capability "handle.intent")
6. Cognitive Kernel → NATS (publish: module.dispatch.intent.user)
7. NATS → Module Executive (subscribe)
8. Module Executive → NATS (publish: task.created)
9. NATS → Module Planner (subscribe)
10. Module Planner → NATS (publish: task.plan)
11. NATS → Module Memory (subscribe)
12. Module Memory → Redis (store event)
13. Module Memory → NATS (publish: memory.stored)
14. Cognitive Kernel → PostgreSQL (insert event)
15. Cognitive Kernel → User (response)
```

## Technologies et dépendances

- **API Gateway** dépend de: NATS client, Pydantic, Uvicorn
- **Cognitive Kernel** dépend de: NATS client, Redis, PostgreSQL (asyncpg), Scheduler, Registry, GoalManager
- **Modules** dépendent de: NATS client, SDK module
- **State Layer** = Redis + PostgreSQL complémentaires
- **NATS** = seul moyen de communication inter-modules