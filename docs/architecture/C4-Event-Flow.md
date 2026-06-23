# C4 Architecture — Event Flow

## Vue d'ensemble

Cette vue documente les flux événementiels principaux dans ETHAN Cognitive OS.

## Scénario 1: Traitement d'une intention utilisateur

```
┌─────────────────────────────────────────────────────────────────────┐
│  User → POST /v1/message {"input": "Analyze Q3 report"}            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  API Gateway                                                        │
│  - Crée Event(id=uuid, type="intent.user", source="api-gateway")   │
│  - Bus.publish("ethan.intent.user", event)                          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  NATS JetStream                                                    │
│  - Route vers toutes les subscriptions                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
            ┌────────────────┴─────────────────┐
            │                                   │
            ▼                                   ▼
┌──────────────────────────┐       ┌────────────────────────────────┐
│ Cognitive Kernel         │       │ Module Executive               │
│ _on_intent_event(event)  │       │ (si abonné à ethan.intent.user)│
│                          │       └────────────────────────────────┘
│ 1. goals.create() → Goal │
│ 2. event.data["goal_id"] │
│    = goal.id             │
│ 3. dispatch_event(event) │
│    → registry.find_by_   │
│      capability("handle  │
│      .intent")           │
│ 4. bus.publish("module   │
│    .dispatch.intent      │
│    .user", event)        │
└──────────┬───────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  NATS → module.dispatch.intent.user                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Module Executive                                                   │
│  - Reçoit: module.dispatch.intent.user                             │
│  - Extrait intent.user_input = "Analyze Q3 report"               │
│  - Classifie: "analyze" → type = "analysis"                       │
│  - Crée task:                                                      │
│    {                                                                │
│      "task_id": uuid,                                               │
│      "type": "analysis",                                            │
│      "source": "text",                                              │
│      "input": "Analyze Q3 report",                                  │
│      "priority": "normal"                                           │
│    }                                                                │
│  - Publie: ethan.task.created                                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  NATS → ethan.task.created                                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┬────────────────────────┐
              │                             │                        │
              ▼                             ▼                        ▼
┌──────────────────────────┐     ┌─────────────────────┐   ┌────────────────────┐
│ Module Planner           │     │ Module Memory       │   │ Cognitive Kernel   │
│ _on_task_created(event)  │     │ (store.event)       │   │ (goal tracking)    │
│                          │     └─────────────────────┘   └────────────────────┘
│ - Récupère task.type     │     - Stocke event dans Redis│ - goals.update_step │
│ - Génère steps:          │       memory:{event_id}     │   ("planner",       │
│   [understand_request,   │     - Émet memory.stored     │    "running")       │
│    gather_data, process, │                              │                    │
│    generate_report,      │                              │                    │
│    summarize_result]     │                              │                    │
│ - Publie: ethan.task.plan│                              │                    │
└──────────────────────────┘                              │                    │
              │                                           │                    │
              ▼                                           │                    │
┌──────────────────────────┐                              │                    │
│ NATS → ethan.task.plan   │                              │                    │
└──────────────────────────┘                              │                    │
              │                                           │                    │
              ▼                                           │                    │
┌──────────────────────────┐                              │                    │
│ Module Memory (suite)    │                              │                    │
│ - Stocke le plan         │                              │                    │
│ - Émet memory.stored     │                              │                    │
└──────────────────────────┘                              │                    │
              │                                           │                    │
              ▼                                           │                    │
┌──────────────────────────┐                              │                    │
│ NATS → ethan.memory.stored                              │                    │
└──────────────────────────┘                              │                    │
              │                                           │                    │
              ▼                                           │                    │
┌─────────────────────────────────────────────────────────────────────┐  │
│ Cognitive Kernel                                                    │  │
│ - Reçoit memory.stored                                              │  │
│ - Émet goal.completed                                               │  │
│ - goals.complete(goal_id)                                           │  │
└────────────────────────────┬────────────────────────────────────────┘  │
                             │                                            │
                             ▼                                            │
┌─────────────────────────────────────────────────────────────────────┐  │
│ Module Reflective                                                   │  │
│ - Reçoit goal.completed                                             │  │
│ - Log + summary: "Processed task of type 'analysis' with success" │  │
│ - Émet: ethan.reflection.done                                      │  │
└─────────────────────────────────────────────────────────────────────┘  │
```

## Scénario 2: Événement planifié (cron)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Scheduler                                                          │
│  - schedule_cron("health-check", 60, "ethan.health.check")         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  NATS → ethan.health.check                                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Module abonné (ex: system-monitor)                                │
│  - Traite l'événement                                               │
│  - Publie résultat                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Scénario 3: Module en erreur

```
┌─────────────────────────────────────────────────────────────────────┐
│  Module Executive (en erreur)                                       │
│  - Exception lors du traitement                                     │
│  - Catch + log                                                      │
│  - N'émet PAS de réponse                                            │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Cognitive Kernel                                                   │
│  - Timeout après retry                                              │
│  - bus.publish("system.error", ...)                                │
│  - goals.fail(goal_id, "Executive timed out")                      │
└─────────────────────────────────────────────────────────────────────┘
```

## États des Events

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Created    │────►│  Published   │────►│  Dispatched  │
│  (API)      │     │  (NATS)      │     │  (Module)    │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                │
                                                ▼
                                        ┌──────────────┐
                                        │  Completed   │
                                        │  (Response)  │
                                        └──────┬───────┘
                                                │
                                                ▼
                                        ┌──────────────┐
                                        │  Failed      │
                                        │  (Error)     │
                                        └──────────────┘
```

## Topics NATS et leur rôle

| Topic | Publisher | Subscribers | Description |
|----------|-----------|-------------|-------------|
| `ethan.intent.user` | API Gateway | Executive, Kernel | Intentions utilisateur brutes |
| `ethan.task.created` | Executive | Planner, Memory, Kernel | Tâche structurée créée |
| `ethan.task.plan` | Planner | Memory, Kernel | Plan d'exécution |
| `ethan.memory.stored` | Memory | Kernel | Confirmation stockage |
| `ethan.task.completed` | Kernel | Reflective | Tâche terminée |
| `ethan.reflection.done` | Reflective | Kernel | Réflexion émise |
| `module.dispatch.*` | Kernel | Modules cibles | Dispatch par capability |
| `system.kernel.*` | Kernel | Monitoring | Events système |
| `goal.*` | GoalManager | Kernel | Lifecycle des goals |
| `schedule.trigger` | Scheduler | Modules | Triggers cron |