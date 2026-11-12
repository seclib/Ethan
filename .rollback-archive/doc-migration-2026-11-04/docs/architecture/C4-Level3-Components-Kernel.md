# C4 Architecture — Level 3: Component Diagram — Cognitive Kernel

## Vue d'ensemble

Le Cognitive Kernel est décomposé en 5 composants principaux, chacun avec une responsabilité unique. Aucune logique métier ne réside dans le kernel — il ne fait que router, synchroniser et orchestrer.

## Diagramme ASCII

```
┌────────────────────────────────────────────────────────────────────┐
│                  Cognitive Kernel — Composants                     │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                     Event Router                            │   │
│  │  + subscribe wildcards: kernel.>, goal.>, module.>, intent.>│   │
│  │  + dispatch_event(event) → capability-based routing         │   │
│  │  + _on_system_event(event)                                   │   │
│  │  + _on_goal_event(event) → GoalManager                       │   │
│  │  + _on_module_event(event)                                   │   │
│  │  + _on_intent_event(event) → create goal + dispatch          │   │
│  │  + _sync_state(event) → Redis + PostgreSQL                   │   │
│  └────────────────────────┬─────────────────────────────────────┘   │
│                            │                                      │
│         ┌──────────────────┼──────────────────┐                   │
│         │                  │                  │                   │
│         ▼                  ▼                  ▼                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │
│  │ Goal Manager │  │Module Registry│  │   State Manager       │    │
│  │              │  │              │  │                       │    │
│  │ + create()   │  │ + register() │  │ + _sync_state()       │    │
│  │ + complete() │  │ + discover() │  │   Redis: setex()      │    │
│  │ + fail()     │  │ + find_by_   │  │   PG: insert()        │    │
│  │ + update_    │  │   capability()│ │                       │    │
│  │   step()     │  │ + health_    │  │                       │    │
│  │              │  │   check()    │  │                       │    │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘    │
│         │                  │                       │                 │
│         │     ┌────────────▼────────────┐          │                 │
│         │     │      Scheduler         │          │                 │
│         │     │                        │          │                 │
│         │     │ + start() / stop()     │       Redis + PostgreSQL     │
│         │     │ + schedule_cron()      │          │                 │
│         │     │ + _task_loop()         │          │                 │
│         │     └────────────────────────┘          │                 │
│         │                                        │                 │
│         ▼                                        ▼                 │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                   NATS JetStream                           │    │
│  │                                                            │    │
│  │  Topics:                                                   │    │
│  │  - kernel.>                                                │    │
│  │  - goal.>                                                  │    │
│  │  - module.>                                                │    │
│  │  - intent.>                                                │    │
│  │  - module.dispatch.<type>                                  │    │
│  │  - system.*                                                │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## PlantUML

```plantuml
@startuml C4_Component_Kernel
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

title Component Diagram — Cognitive Kernel

Container_Boundary(kernel, "Cognitive Kernel") {
    Component(router, "Event Router", "Python asyncio", "Wildcard subscriptions, dispatch, state sync")
    Component(goals, "Goal Manager", "Python", "Goal lifecycle: create, update_step, complete, fail")
    Component(registry, "Module Registry", "Python", "Module discovery, capabilities, health checks")
    Component(state, "State Manager", "Python", "Event sync to Redis + PostgreSQL")
    Component(scheduler, "Scheduler", "Python", "Cron triggers, background tasks")
}

ContainerQueue(nats, "NATS JetStream", "Message Broker")
ContainerDb(redis, "Redis", "Live state")
ContainerDb(postgres, "greSQL", "Persistent state")

' Router flow
Rel(router, nats, "Subscribes", "kernel.>, goal.>, module.>, intent.>")
Rel(router, registry, "find_by_capability", "capability → ModuleManifest[]")
Rel(router, goals, "create / complete / fail", "Goal lifecycle")
Rel(router, state, "_sync_state(event)", "Redis + PostgreSQL")

' Goals flow
Rel(goals, postgres, "insert/update goals", "insert/update")
Rel(goals, redis, "cache goal", "setex goal:*")
Rel(goals, nats, "publish goal events", "goal.created, goal.completed")

' Registry flow
Rel(registry, postgres, "insert/select modules", "INSERT … ON CONFLICT")
Rel(registry, nats, "publish module events", "system.module.registered")

' State flow
Rel(state, redis, "event snapshot", "setex event:{id}")
Rel(state, postgres, "persist event", "INSERT INTO events")

' Scheduler flow
Rel(scheduler, nats, "triggers", "schedule.trigger")
Rel(router, scheduler, "start/stop", "")

@enduml
```

## Composants et responsabilités

| Composant | Méthodes principales | Responsabilité |
|-----------|----------------------|-----------------|
| **Event Router** | `start()`, `stop()`, `dispatch_event()`, `handle_event()` | Point d'entrée principal, routing événementiel |
| **Event Router** | `_on_system_event()` | Traitement events système |
| **Event Router** | `_on_goal_event()` | Forward vers GoalManager |
| **Event Router** | `_on_module_event()` | Log réponses modules |
| **Event Router** | `_on_intent_event()` | Création goal + dispatch initial |
| **Event Router** | `_sync_state()` | Synchronisation Redis + PostgreSQL |
| **Goal Manager** | `create()`, `update_step()`, `complete()`, `fail()` | Lifecycle complet des goals |
| **Module Registry** | `register()`, `discover()`, `find_by_capability()` | Découverte et routing par capacité |
| **State Manager** | `_sync_state()` | Réplication event → Redis + PostgreSQL |
| **Scheduler** | `start()`, `stop()`, `schedule_cron()` | Tâches périodiques |

## Dépendances entre composants

```
Event Router
    ├── GoalManager       (création et suivi des goals)
    ├── ModuleRegistry    (découverte modules)
    ├── Scheduler         (démarrage/arrêt)
    └── Redis + PostgreSQL (sync state)

GoalManager
    ├── EventBus          (émission events goal.*)
    ├── PostgreSQL        (insert/update goals)
    └── Redis             (cache goals)

ModuleRegistry
    ├── PostgreSQL        (insert/select modules)
    ├── Redis             (health heartbeats)
    └── EventBus          (émission events système)

State Manager
    ├── Redis             (event:{id})
    └── PostgreSQL        (events table)

Scheduler
    └── EventBus          (schedule.trigger)