# Décisions Architecturale Critiques — ETHAN Core Daemon

**Statut** : Décisions prises — Prêt pour implémentation  
**Date** : Juin 2026  
**Audience** : Kernel Developers, System Architects, DevOps

---

## Résumé des décisions

Ce document résout les 7 questions critiques identifiées dans `critical-analysis.md`.

---

## 1. Interface Kernel Go ↔ Python

### Décision

**gRPC avec protobuf**

### Justification

| Critère | gRPC | HTTP REST | Shared Memory | Message Queue |
|---------|------|-----------|---------------|---------------|
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Typage fort** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Streaming** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Cross-language** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Debugging** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Complexité** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

**gRPC gagne sur** :
- Performance (protobuf binaire, HTTP/2)
- Typage fort (contrat .proto)
- Streaming bidirectionnel
- Cross-language (Go ↔ Python ↔ Rust)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              KERNEL GO (main.go)                             │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              gRPC Server (port 50051)                 │ │
│  │  Service: OrchestratorService                         │ │
│  │  Methods:                                             │ │
│  │  - ProcessEvent(event) → Response                     │ │
│  │  - GetState(request) → State                          │ │
│  │  - ExecuteTask(task) → Result                         │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ gRPC (HTTP/2 + protobuf)
                            │
┌─────────────────────────────────────────────────────────────┐
│              ORCHESTRATOR PYTHON                            │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              gRPC Client                               │ │
│  │  - Connect to localhost:50051                         │ │
│  │  - Stub: OrchestratorServiceStub                      │ │
│  │  - Calls: ProcessEvent, GetState, ExecuteTask         │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              Python Modules                            │ │
│  │  - Cognition                                           │ │
│  │  - Memory                                              │ │
│  │  - Planner                                             │ │
│  │  - Tools                                               │ │
│  │  - LLM                                                 │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Protobuf Schema

```protobuf
syntax = "proto3";

package ethan.core;

service OrchestratorService {
  rpc ProcessEvent(Event) returns (Response);
  rpc GetState(StateRequest) returns (StateResponse);
  rpc ExecuteTask(Task) returns (TaskResult);
  rpc HealthCheck(HealthRequest) returns (HealthResponse);
}

message Event {
  string id = 1;
  string type = 2;
  string source = 3;
  int64 timestamp = 4;
  map<string, bytes> payload = 5;
  map<string, string> context = 6;
}

message Response {
  string request_id = 1;
  string status = 2;  // "success", "error", "timeout"
  bytes result = 3;
  string error = 4;
}

message StateRequest {
  string module = 1;
  string key = 2;
}

message StateResponse {
  bytes value = 1;
  int64 ttl = 2;
}

message Task {
  string task_id = 1;
  string capability = 2;
  map<string, bytes> params = 3;
}

message TaskResult {
  string task_id = 1;
  string status = 2;
  bytes output = 3;
  string error = 4;
  int64 duration_ms = 5;
}

message HealthRequest {}

message HealthResponse {
  string status = 1;  // "healthy", "degraded", "unhealthy"
  int64 uptime = 2;
  map<string, string> modules = 3;
  map<string, string> connections = 4;
}
```

### Implémentation

**Kernel Go** (`kernel/main.go`) :
```go
// Démarrer le serveur gRPC
grpcServer := grpc.NewServer()
orchestratorService := NewOrchestratorService(orchestratorClient)
pb.RegisterOrchestratorServiceServer(grpcServer, orchestratorService)

listener, _ := net.Listen("tcp", ":50051")
go grpcServer.Serve(listener)
```

**Orchestrator Python** (`core/orchestrator/client.py`) :
```python
import grpc

channel = grpc.insecure_channel('localhost:50051')
stub = orchestrator_pb2_grpc.OrchestratorServiceStub(channel)

def process_event(event: Event) -> Response:
    response = stub.ProcessEvent(event.to_protobuf())
    return Response.from_protobuf(response)
```

---

## 2. Backend Event Bus par Défaut

### Décision

**NATS JetStream pour V1, avec abstraction pour migration future**

### Justification

| Critère | NATS JetStream | InMemory | Kafka | Redis Streams |
|---------|----------------|----------|-------|---------------|
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Durabilité** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Complexité ops** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Écosystème** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**NATS JetStream gagne sur** :
- Performance (latence < 1ms)
- Simplicité d'opérations (cluster en 3 nodes)
- Durabilité suffisante pour V1 (rétention 1 semaine)
- Écosystème grandissant

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EVENT BUS ABSTRACTION                     │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              EventBus (ABC)                           │ │
│  │  + publish(subject, event)                            │ │
│  │  + subscribe(subject, handler)                        │ │
│  │  + close()                                            │ │
│  └───────────────────────────────────────────────────────┘ │
│                            │                                │
│          ┌─────────────────┼─────────────────┐            │
│          │                 │                 │             │
│          ▼                 ▼                 ▼             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ NATSBus      │  │ InMemoryBus  │  │ KafkaBus     │     │
│  │ (V1 default) │  │ (tests)      │  │ (V2 future)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│          │                 │                 │             │
│          └─────────────────┼─────────────────┘            │
│                            │                                │
│                            ▼                                │
│                  ┌──────────────────┐                      │
│                  │  NATS JetStream  │                      │
│                  │  (production)    │                      │
│                  └──────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### Configuration

```yaml
# ethan.yaml
event_bus:
  backend: "nats"  # "nats" | "memory" | "kafka"
  
  nats:
    url: "nats://localhost:4222"
    jetstream: true
    retention: "7d"  # 7 jours
    max_events: 10000000  # 10M events
    
  kafka:
    brokers: ["localhost:9092"]
    topic: "ethan-events"
    retention_ms: 604800000  # 7 jours
    
  memory:
    max_events: 10000  # Pour tests uniquement
```

### Implémentation

```python
# core/bus/factory.py
class EventBusFactory:
    @staticmethod
    def create(config: EventBusConfig) -> EventBus:
        if config.backend == "nats":
            return NATSBus(config.nats)
        elif config.backend == "memory":
            return InMemoryBus(config.memory)
        elif config.backend == "kafka":
            return KafkaBus(config.kafka)
        else:
            raise ValueError(f"Unknown backend: {config.backend}")
```

---

## 3. Module vs Agent

### Décision

**Module = processus métier | Agent = module avec autonomie**

### Justification

La confusion vient du fait que `core/modules/` et `core/agents/` coexistent.

**Définitions** :

| Concept | Définition | Exemples |
|---------|------------|----------|
| **Module** | Processus métier avec responsabilité unique | Memory, Tools, LLM Router |
| **Agent** | Module capable d'initiative autonome | Executive, Autonomy, Learning |
| **Tous les Agents sont des Modules** | | |
| **Tous les Modules ne sont pas des Agents** | | |

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MODULES (tous)                            │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Module     │  │   Module     │  │   Module     │     │
│  │   Memory     │  │   Tools      │  │   LLM        │     │
│  │  (passif)    │  │  (passif)    │  │  (passif)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Agent     │  │    Agent     │  │    Agent     │     │
│  │  Executive   │  │  Autonomy    │  │  Learning    │     │
│  │ (actif)      │  │  (actif)     │  │  (actif)     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  Caractéristiques:                                          │
│  - Module = réactif (répond aux événements)                 │
│  - Agent = autonome (peut émettre des événements)           │
└─────────────────────────────────────────────────────────────┘
```

### Interface

```python
# core/modules/base.py
class Module(ABC):
    """Module de base — réactif."""
    
    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        """Traite un événement."""
        pass

# core/agents/base.py
class Agent(Module):
    """Agent — module autonome."""
    
    @abstractmethod
    async def init(self) -> None:
        """Initialisation (peut émettre des événements)."""
        pass
    
    @abstractmethod
    async def run(self) -> None:
        """Boucle principale (autonome)."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Arrêt propre."""
        pass
```

### Exemples

**Module (réactif)** :
```python
class MemoryModule(Module):
    async def handle_event(self, event: Event) -> None:
        if event.type == "memory.store.request":
            await self.store(event.payload)
        elif event.type == "memory.recall.request":
            await self.recall(event.payload)
```

**Agent (autonome)** :
```python
class AutonomyAgent(Agent):
    async def init(self) -> None:
        # Émettre un événement au démarrage
        await self.bus.publish("autonomy.agent.started", {})
    
    async def run(self) -> None:
        while self.running:
            # Analyser l'état
            goals = await self.get_active_goals()
            
            # Initier de nouveaux buts si nécessaire
            if len(goals) < 3:
                new_goal = await self.propose_goal()
                await self.bus.publish("goal.created", new_goal)
            
            # Attendre avant prochaine itération
            await asyncio.sleep(60)
    
    async def shutdown(self) -> None:
        self.running = False
```

---

## 4. Event Schema Governance

### Décision

**Registry centralisé + versioning sémantique + migration automatique**

### Justification

Les événements sont le contrat entre modules. Ils doivent être :
- **Stables** : pas de breaking change sans migration
- **Versionnés** : savoir quelle version on utilise
- **Évolutifs** : pouvoir ajouter des champs sans casser

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              EVENT SCHEMA REGISTRY                           │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  EventType: "interface.command"                       │ │
│  │  Version: "1.0.0"                                     │ │
│  │  Schema: {                                            │ │
│  │    type: "object",                                    │ │
│  │    properties: {                                      │ │
│  │      cmd: { type: "string" },                         │ │
│  │      args: { type: "array" }                          │ │
│  │    },                                                 │ │
│  │    required: ["cmd"]                                  │ │
│  │  }                                                    │ │
│  │  Migration: v1 → v2: add "session_id" field          │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Versioning

**Format** : `event_type@version`

Exemples :
- `interface.command@1.0.0`
- `interface.command@1.1.0` (ajout de `session_id`)
- `interface.command@2.0.0` (breaking change)

### Migration

```python
# core/events/migrator.py
class EventMigrator:
    def __init__(self, registry: EventSchemaRegistry):
        self.registry = registry
    
    def migrate(self, event: Event, target_version: str) -> Event:
        """Migre un événement vers une version cible."""
        current_version = event.context.get("version", "1.0.0")
        
        if current_version == target_version:
            return event
        
        # Appliquer les migrations
        migrations = self.registry.get_migrations(
            event.type,
            from_version=current_version,
            to_version=target_version
        )
        
        for migration in migrations:
            event = migration.apply(event)
        
        return event
```

### Exemple de migration

```python
# core/events/migrations/interface_command_v1_to_v2.py
class InterfaceCommandV1ToV2(Migration):
    def apply(self, event: Event) -> Event:
        # Ajouter session_id si absent
        if "session_id" not in event.payload:
            event.payload["session_id"] = "default"
        
        event.context["version"] = "2.0.0"
        return event
```

---

## 5. Module Contract

### Décision

**Interface standardisée + déclaration de capabilities + permissions explicites**

### Justification

Chaque module doit :
- **Déclarer** ce qu'il peut faire (capabilities)
- **Déclarer** ce dont il a besoin (dépendances)
- **Déclarer** ce qu'il peut lire/écrire (permissions)
- **Implémenter** une interface standard

### Interface standard

```python
# core/modules/interface.py
class ModuleInterface(ABC):
    """Interface standard pour tous les modules."""
    
    @abstractmethod
    async def initialize(self, context: ModuleContext) -> None:
        """Initialisation du module."""
        pass
    
    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        """Traite un événement."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Arrêt propre."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> list[Capability]:
        """Retourne les capabilities du module."""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> list[Dependency]:
        """Retourne les dépendances du module."""
        pass
    
    @abstractmethod
    def get_permissions(self) -> Permissions:
        """Retourne les permissions du module."""
        pass
```

### Capability

```python
# core/modules/capability.py
@dataclass
class Capability:
    name: str  # "memory.store", "llm.generate"
    version: str  # "1.0.0"
    description: str
    inputs: list[str]  # Event types consommés
    outputs: list[str]  # Event types produits
    state_reads: list[str]  # Clés Redis lues
    state_writes: list[str]  # Clés Redis écrites
```

### Dependency

```python
# core/modules/dependency.py
@dataclass
class Dependency:
    name: str  # "nats", "redis", "postgres"
    version: str  # ">=1.0.0"
    required: bool  # Si False, le module peut fonctionner sans
    fallback: str | None  # Module de fallback si indisponible
```

### Permissions

```python
# core/modules/permissions.py
@dataclass
class Permissions:
    state_read: list[str]  # ["memory:*", "planner:goals"]
    state_write: list[str]  # ["memory:session:*"]
    events_subscribe: list[str]  # ["interface.*", "planner.*"]
    events_publish: list[str]  # ["memory.*", "executive.*"]
    network: list[str]  # ["https://api.openai.com"]
    filesystem: list[str]  # ["/tmp/*", "/var/lib/ethan/*"]
```

### Exemple complet

```python
# modules/memory/memory_module.py
class MemoryModule(ModuleInterface):
    def get_capabilities(self) -> list[Capability]:
        return [
            Capability(
                name="memory.store",
                version="1.0.0",
                description="Store data in memory",
                inputs=["memory.store.request"],
                outputs=["memory.store.complete"],
                state_reads=[],
                state_writes=["memory:entry:*"]
            ),
            Capability(
                name="memory.recall",
                version="1.0.0",
                description="Recall data from memory",
                inputs=["memory.recall.request"],
                outputs=["memory.recall.complete"],
                state_reads=["memory:entry:*"],
                state_writes=[]
            )
        ]
    
    def get_dependencies(self) -> list[Dependency]:
        return [
            Dependency(name="redis", version=">=7.0", required=True),
            Dependency(name="postgres", version=">=16", required=True),
            Dependency(name="nats", version=">=2.0", required=True)
        ]
    
    def get_permissions(self) -> Permissions:
        return Permissions(
            state_read=["memory:*"],
            state_write=["memory:*"],
            events_subscribe=["memory.*", "interface.*"],
            events_publish=["memory.*"],
            network=[],
            filesystem=["/var/lib/ethan/memory/*"]
        )
```

---

## 6. Testing Strategy

### Décision

**Pyramid de tests : unitaires → intégration → E2E**

### Justification

Un système distribué est difficile à tester. Il faut :
- **Tests unitaires** : tester chaque module isolément (mocking du bus)
- **Tests d'intégration** : tester les flux entre modules (bus in-memory)
- **Tests E2E** : tester la stack complète (Docker Compose)

### Architecture des tests

```
┌─────────────────────────────────────────────────────────────┐
│                    TEST PYRAMID                               │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              E2E Tests (10%)                          │ │
│  │  - Stack complète (Docker Compose)                    │ │
│  │  - Scénarios utilisateur réels                        │ │
│  │  - Performance tests                                  │ │
│  └───────────────────────────────────────────────────────┘ │
│                            │                                │
│  ┌───────────────────────────────────────────────────────┐ │
│  │           Integration Tests (30%)                     │ │
│  │  - Flux entre modules                                 │ │
│  │  - Bus in-memory                                      │ │
│  │  - Contrats entre modules                             │ │
│  └───────────────────────────────────────────────────────┘ │
│                            │                                │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              Unit Tests (60%)                         │ │
│  │  - Module isolé                                       │ │
│  │  - Mocking du bus                                     │ │
│  │  - Logique métier                                     │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Tests unitaires (60%)

```python
# tests/unit/test_memory_module.py
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_bus():
    """Mock du bus d'événements."""
    bus = Mock()
    bus.publish = Mock()
    return bus

@pytest.fixture
def memory_module(mock_bus):
    """Module mémoire avec bus mocké."""
    module = MemoryModule()
    module.bus = mock_bus
    return module

@pytest.mark.asyncio
async def test_store(memory_module):
    """Test du stockage."""
    event = Event(
        type="memory.store.request",
        payload={"key": "test", "value": "hello"}
    )
    
    await memory_module.handle_event(event)
    
    # Vérifier que l'événement a été publié
    memory_module.bus.publish.assert_called_once()
    call_args = memory_module.bus.publish.call_args
    assert call_args[0][0] == "memory.store.complete"
```

### Tests d'intégration (30%)

```python
# tests/integration/test_memory_flow.py
import pytest
from core.bus.memory import InMemoryBus

@pytest.fixture
async def bus():
    """Bus in-memory pour tests."""
    bus = InMemoryBus()
    await bus.connect()
    yield bus
    await bus.close()

@pytest.mark.asyncio
async def test_store_and_recall(bus):
    """Test du flux store → recall."""
    # Module 1 : store
    memory_module = MemoryModule(bus)
    
    # Module 2 : recall
    recall_module = RecallModule(bus)
    
    # Publier un événement de stockage
    await bus.publish("memory.store.request", {
        "key": "test",
        "value": "hello"
    })
    
    # Attendre le traitement
    await asyncio.sleep(0.1)
    
    # Publier un événement de rappel
    response = await bus.request("memory.recall.request", {
        "key": "test"
    })
    
    assert response.payload["value"] == "hello"
```

### Tests E2E (10%)

```python
# tests/e2e/test_full_stack.py
import pytest
import docker

@pytest.fixture(scope="session")
def ethan_stack():
    """Démarre la stack complète ETHAN."""
    client = docker.from_env()
    
    # Démarrer les services
    client.containers.run("nats:latest", name="nats", detach=True)
    client.containers.run("redis:7", name="redis", detach=True)
    client.containers.run("postgres:16", name="postgres", detach=True)
    client.containers.run("ethan-core:latest", name="ethan-core", detach=True)
    
    yield
    
    # Arrêter les services
    client.containers.get("ethan-core").stop()
    client.containers.get("postgres").stop()
    client.containers.get("redis").stop()
    client.containers.get("nats").stop()

@pytest.mark.asyncio
async def test_full_chat_flow(ethan_stack):
    """Test du flux complet : CLI → Core → Modules → Response."""
    # Créer un événement CLI
    event = Event(
        type="interface.command",
        source="cli",
        payload={"cmd": "chat", "args": ["hello"]}
    )
    
    # Publier sur NATS
    bus = NATSBus("nats://localhost:4222")
    await bus.connect()
    response = await bus.request("ethan.interface.cli", event, timeout=10)
    
    assert response.type == "response.ok"
    assert "hello" in response.payload["content"].lower()
```

### Coverage

**Objectif** : 80% de couverture

```bash
# Exécuter les tests avec coverage
pytest tests/ --cov=core --cov=modules --cov=kernel --cov-report=html

# Vérifier le coverage
open htmlcov/index.html
```

---

## 7. Secret Management

### Décision

**Docker Secrets + Vault (optionnel pour V2)**

### Justification

| Critère | Docker Secrets | Vault | AWS Secrets Manager | Env Vars |
|---------|----------------|-------|---------------------|----------|
| **Sécurité** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Complexité** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Coût** | Gratuit | Gratuit | Payant | Gratuit |
| **Rotation** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |

**Docker Secrets pour V1** :
- Intégré à Docker Swarm / Compose
- Pas de dépendance externe
- Chiffré au repos
- Suffisant pour le MVP

**Vault pour V2** :
- Rotation automatique
- Audit complet
- Multi-cloud
- Nécessaire pour la production à grande échelle

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SECRET MANAGEMENT                         │
│                                                             │
│  V1 (Docker Secrets)                                       │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  docker secret create ethan-openai-key ./openai.key   │ │
│  │  docker secret create ethan-nats-password ./nats.pass │ │
│  │                                                        │ │
│  │  Dans ethan-core.service:                             │ │
│  │  secrets:                                              │ │
│  │    - ethan-openai-key                                 │ │
│  │    - ethan-nats-password                              │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  V2 (Vault)                                                │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Vault Server                                          │ │
│  │  - Stocke les secrets                                  │ │
│  │  - Rotation automatique                                │ │
│  │  - Audit logs                                          │ │
│  │                                                         │ │
│  │  ethan-core → Vault Agent → Vault Server              │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Implémentation V1 (Docker Secrets)

```yaml
# docker-compose.yml
services:
  ethan-core:
    image: ethan-core:latest
    secrets:
      - ethan-openai-key
      - ethan-nats-password
    environment:
      - OPENAI_API_KEY_FILE=/run/secrets/ethan-openai-key
      - NATS_PASSWORD_FILE=/run/secrets/ethan-nats-password

secrets:
  ethan-openai-key:
    file: ./secrets/openai.key
  ethan-nats-password:
    file: ./secrets/nats.password
```

```python
# core/config/secrets.py
class SecretManager:
    def __init__(self):
        self.secrets = {}
    
    def load(self, name: str) -> str:
        """Charge un secret depuis Docker Secrets."""
        path = f"/run/secrets/{name}"
        with open(path, "r") as f:
            return f.read().strip()
    
    def get(self, name: str) -> str:
        """Récupère un secret (avec cache)."""
        if name not in self.secrets:
            self.secrets[name] = self.load(name)
        return self.secrets[name]
```

### Implémentation V2 (Vault)

```python
# core/config/vault.py
class VaultSecretManager:
    def __init__(self, vault_addr: str, vault_token: str):
        self.client = hvac.Client(url=vault_addr, token=vault_token)
    
    async def get(self, path: str) -> str:
        """Récupère un secret depuis Vault."""
        response = self.client.secrets.kv.v2.read_secret_version(
            path=path
        )
        return response["data"]["data"]["value"]
    
    async def rotate(self, path: str) -> None:
        """Demande une rotation de secret."""
        self.client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret={"value": generate_new_secret()}
        )
```

---

## 8. Event Schema Registry

### Décision

**Registry centralisé avec validation au runtime**

### Justification

Tous les événements doivent être :
- **Validés** : schéma JSON Schema
- **Versionnés** : semver
- **Documentés** : description, exemples
- **Évolutifs** : migration automatique

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              EVENT SCHEMA REGISTRY                           │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Registry (PostgreSQL)                                │ │
│  │  - event_type (PK)                                    │ │
│  │  - version                                            │ │
│  │  - schema (JSON Schema)                               │ │
│  │  - description                                        │ │
│  │  - examples                                           │ │
│  │  - migration_rules                                    │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  API:                                                       │
│  - register(event_type, version, schema)                    │
│  - validate(event_type, version, event)                     │
│  - migrate(event_type, from_version, to_version, event)     │
│  - get_schema(event_type, version)                          │
└─────────────────────────────────────────────────────────────┘
```

### Schéma PostgreSQL

```sql
CREATE TABLE event_schemas (
    event_type VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    schema JSONB NOT NULL,
    description TEXT,
    examples JSONB,
    migration_from VARCHAR(255),
    migration_to VARCHAR(255),
    migration_code TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (event_type, version)
);

CREATE INDEX idx_event_schemas_type ON event_schemas(event_type);
```

### Exemple d'insertion

```sql
INSERT INTO event_schemas 
  (event_type, version, schema, description, examples)
VALUES (
  'interface.command',
  '1.0.0',
  '{
    "type": "object",
    "properties": {
      "cmd": {"type": "string"},
      "args": {"type": "array"}
    },
    "required": ["cmd"]
  }',
  'User command from CLI',
  '[{"cmd": "chat", "args": ["hello"]}]'
);
```

### Validation au runtime

```python
# core/events/validator.py
class EventValidator:
    def __init__(self, registry: EventSchemaRegistry):
        self.registry = registry
    
    async def validate(self, event: Event) -> bool:
        """Valide un événement contre son schéma."""
        schema = self.registry.get_schema(
            event.type,
            event.context.get("version", "1.0.0")
        )
        
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(event.payload))
        
        if errors:
            for error in errors:
                logger.error(f"Event validation error: {error.message}")
            return False
        
        return True
```

---

## Conclusion

Toutes les décisions critiques sont maintenant prises.

**Résumé** :

1. ✅ **Interface Kernel Go ↔ Python** : gRPC + protobuf
2. ✅ **Backend Event Bus** : NATS JetStream pour V1, abstraction pour migration
3. ✅ **Module vs Agent** : Module = réactif, Agent = autonome
4. ✅ **Event Schema Governance** : Registry + versioning + migration
5. ✅ **Module Contract** : Interface standard + capabilities + permissions
6. ✅ **Testing Strategy** : Pyramid (60% unit, 30% intégration, 10% E2E)
7. ✅ **Secret Management** : Docker Secrets pour V1, Vault pour V2

**Prochaine étape** : Implémentation des décisions en ACT MODE.

---

**Document approuvé par** : Architecture Team  
**Date** : Juin 2026  
**Statut** : PRÊT POUR IMPLÉMENTATION