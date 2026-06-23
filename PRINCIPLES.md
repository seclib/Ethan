# ETHAN — Engineering Principles

## 1. Kernel and Interfaces are separate

The kernel orchestrates. Interfaces connect. No interface contains business logic. No kernel code knows about UI.

## 2. No intelligence in UI layers

Interfaces translate input to events and state to output. They do not reason, plan, or decide. Intelligence lives in modules only.

## 3. Persistence over stateless design

All critical state is external. Redis for live state. PostgreSQL for permanent state. No in-memory state that cannot be rebuilt.

## 4. Modular capabilities only

Every module exposes a versioned capability contract. Modules do not call each other directly. They declare inputs, outputs, and state access.

## 5. Plugin-first architecture

Extension happens through plugins, not core modification. If you touch core code to add functionality, you are doing it wrong.

## 6. Model-agnostic design

No hard dependency on any LLM provider or model. Models are replaceable inference engines accessed through capability interfaces.

## 7. Event-driven thinking

All communication is events on the bus. No direct calls between components. If you are passing a function pointer, stop and emit an event instead.

## 8. Failure is normal

Modules crash. The bus partitions. Networks fail. Design for recovery, not perfection. The kernel restarts modules. State survives restarts.

## 9. Observability by default

Every event is logged. Every state change is recorded. No silent mutations. If it happened, it is traceable.

## 10. No secrets in code

Secrets live in environment variables, Docker secrets, or a dedicated vault. Never in source. Never in events. Never in logs.

## 11. Namespace isolation

No module touches another module's state keys without explicit capability declaration. Isolation is enforced at the infrastructure level.

## 12. Immutable history

Events and memory entries are immutable once persisted. Updates create new entries with parent references. History is never overwritten.