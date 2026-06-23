# ETHAN — Roadmap

## Phase 1: CLI + API Foundation

**Goal:** Establish the primary interface and basic backend connectivity.

Deliverables:
- Unified CLI with command registry
- REST API gateway
- Basic configuration system
- Docker Compose deployment

Outcome: Users can interact with ETHAN through a terminal. The system has a stable entry point.

---

## Phase 2: Kernel + Capability System

**Goal:** Introduce the orchestrator and module contract.

Deliverables:
- Kernel service (Go binary)
- Capability registry
- Event bus integration (NATS)
- Module lifecycle management

Outcome: Modules can register capabilities. The kernel routes events without containing business logic. The foundation for modularity is in place.

---

## Phase 3: Memory + Persistence

**Goal:** Make intelligence durable and queryable.

Deliverables:
- Redis integration for live state
- PostgreSQL integration for persistent storage
- Event sourcing for state transitions
- Memory module (short-term and long-term)

Outcome: System state survives restarts. Goals, events, and learned patterns persist across sessions. Intelligence is no longer tied to a single conversation.

---

## Phase 4: Plugin System

**Goal:** Allow extension without core modification.

Deliverables:
- Plugin discovery and validation
- CLI plugin manager (install, remove, list)
- Version compatibility checks
- Built-in example plugins

Outcome: External developers can add commands and modules. The ecosystem can grow without forking the core repository.

---

## Phase 5: Multi-Interface

**Goal:** Provide multiple access patterns to the same runtime.

Deliverables:
- Web UI (Textual-based terminal interface)
- VSCode extension (Tauri desktop)
- Shell integration (bash/zsh completion)
- Enhanced API surface

Outcome: ETHAN is accessible through CLI, browser, editor, and shell. Interfaces remain thin clients with no business logic.

---

## Phase 6: Autonomous Behaviors

**Goal:** Enable goal-driven, self-directed operation.

Deliverables:
- Goal manager (create, track, evaluate)
- Planner module (decompose goals into tasks)
- Executive module (coordinate execution)
- Learning engine (evaluate outcomes, propose improvements)
- Reflective module (self-assessment)

Outcome: ETHAN pursues goals without continuous user prompting. It observes, reflects, and acts. The system demonstrates sustained autonomous cognition.

---

## Progression Criteria

Each phase depends on the previous one. A phase is complete when:
- All deliverables are merged to main
- Documentation is updated
- The system passes integration tests
- The next phase's prerequisites are satisfied