# C4 Architecture — Level 1: System Context

## Vue d'ensemble

ETHAN Cognitive OS est un système d'exploitation cognitif événementiel. Cette vue montre le système dans son contexte global avec ses utilisateurs et systèmes externes.

## Diagramme ASCII

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ETHAN COGNITIVE OS                          │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │ API Gateway  │    │  Cognitive  │    │   Modules    │         │
│  │  (FastAPI)   │◄──►│   Kernel    │◄──►│  (Pluggable) │         │
│  │  :8000       │    │  (Async)    │    │  (Python)    │         │
│  └──────────────┘    └──────┬───────┘    └──────────────┘         │
│                              │                                     │
│                    ┌─────────▼──────────┐                          │
│                    │    Event Bus       │                          │
│                    │     (NATS)         │                          │
│                    └─────────┬──────────┘                          │
│                              │                                     │
│  ┌──────────────┐    ┌────────▼────────┐   ┌──────────────────┐  │
│  │    Redis     │    │   PostgreSQL    │   │   Scheduler      │  │
│  │  (Sessions,  │    │  (Events, Goals,│   │  (Cron, Background│  │
│  │    Goals)    │    │   Modules)      │   │   Tasks)         │  │
│  └──────────────┘    └─────────────────┘   └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
        ▲                    ▲                    ▲
        │                    │                    │
        │                    │                    │
   ┌────┴────┐          ┌────┴────┐         ┌────┴────┐
   │  User   │          │  NATS   │         │ Postgres│
   │ (Human/ │          │ (Message│         │ (Persist│
   │  API)   │          │  Broker)│         │  Storage│
   └─────────┘          └─────────┘         └─────────┘
```

## PlantUML

```plantuml
@startuml C4_SystemContext
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml

title System Context Diagram — ETHAN Cognitive OS

Person(user, "User", "Interacts via CLI, API, or GUI")
System(ethan, "ETHAN Cognitive OS", "Event-driven cognitive operating system")

System_Ext(nats, "NATS JetStream", "Message broker, pub/sub, request-reply")
System_Ext(redis, "Redis", "Live state, sessions, caching")
System_Ext(postgres, "PostgreSQL", "Persistent storage, events, goals, audit")

Rel(user, ethan, "Sends intents / receives responses", "HTTPS / WebSocket")
Rel(ethan, nats, "Publishes and subscribes to events", "TCP :4222")
Rel(ethan, redis, "Reads/writes live state", "TCP :6379")
Rel(ethan, postgres, "Persists events and goals", "TCP :5432")

@enduml
```

## Acteurs et systèmes externes

| Élément | Type | Description |
|---------|------|-------------|
| **User** | Acteur humain | Utilisateur final interagissant via CLI, API REST, ou interface desktop |
| **API externe** | Acteur système | Intégrations tierces (Slack, Twitter, outils métier) |
| **NATS JetStream** | Infrastructure | Broker de messages événementiel, garantit la livraison |
| **Redis** | Infrastructure | Cache volatile, sessions, heartbeats modules |
| **PostgreSQL** | Infrastructure | Stockage persistant des événements, goals, modules, audit |

## Flux principal

```
User → POST /v1/message → API Gateway → NATS → Cognitive Kernel
Cognitive Kernel → Redis (session) + PostgreSQL (event)
Cognitive Kernel → NATS → Modules
Modules → NATS → Cognitive Kernel → PostgreSQL (goal status)
Cognitive Kernel → User (response)