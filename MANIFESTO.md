# ETHAN Manifesto

## The problem

We build AI systems the same way we build websites.

A chatbot answers when you prompt. An agent runs until you stop it. An assistant waits for instructions.

These are not architectures. They are limitations disguised as products.

The industry optimizes for conversation quality. It measures engagement, coherence, user satisfaction. These metrics produce better chatbots, not better intelligence.

A chatbot that answers well is still a chatbot.

## Assistants are the wrong abstraction

An assistant is a reactive loop:

> Listen → Think → Respond → Wait

This pattern dominates because it is easy to ship. It requires no state, no persistence, no autonomy. It is web-scale request-response with a language model behind it.

The assistant abstraction assumes a human is always in control. It assumes intelligence should be synchronous. It assumes cognition only happens when someone asks.

These assumptions are wrong.

Intelligence does not pause when nobody is watching. Reasoning is not a request-response cycle. Goals exist independently of prompts.

A cognitive system must outlive any single conversation.

## What a cognitive runtime is

A runtime is not a product. It is not an interface. It is not a model.

A runtime is a substrate.

A cognitive runtime provides:

- **Event-driven execution** — processes run when conditions are met, not when a user types
- **Persistent state** — memory survives restarts, conversations are not the unit of persistence
- **Modular reasoning** — no monolithic model call; reasoning is a pipeline of specialized modules
- **Autonomous goals** — the system can hold and pursue goals across arbitrary timeframes
- **Replaceable models** — no dependency on any single provider or architecture

ETHAN provides this substrate. Modules provide intelligence. Interfaces connect users. The kernel orchestrates nothing more than what needs to run and what needs to know.

## The three layers

### Kernel

The kernel does one thing: maintain system integrity. It routes events, schedules modules, stores state, and ensures nothing bypasses the bus.

The kernel does not reason. It does not decide. It does not have opinions.

This is not a limitation. It is a firewall against centralised control.

### Modules

Modules are where intelligence lives. Each module is an independent process with a single responsibility: executive function, planning, memory, reflection, learning, metacognition.

Modules do not call each other. They emit events. The kernel routes them. No module knows how another works internally.

This is not overhead. It is decoupling. A module can be rewritten, replaced, or removed without touching anything else.

### Interfaces

Interfaces are replaceable. CLI, Web UI, VSCode, API — none of them contain logic. They are windows into the runtime, not the runtime itself.

ETHAN does not have a primary interface. ETHAN has many interfaces, and none is privileged.

## Persistence of intelligence

When you talk to a chatbot, the conversation ends when you close the tab. The memory is a context window. The identity resets.

A cognitive runtime does not forget when you stop talking. State persists in PostgreSQL and Redis, not in a prompt. Goals continue to be evaluated. Learning continues to run.

This is not a technical detail. It is a fundamental difference between a tool that answers questions and a system that maintains cognition.

The system is not defined by the last message. It is defined by its entire history, its current state, and its active goals. None of these reset when an interface disconnects.

## Modular cognition

A single LLM call is not reasoning. It is pattern completion.

Real reasoning requires:

- A planner that decomposes problems
- An executive that coordinates execution
- A memory that stores and retrieves context
- A reflective module that evaluates outcomes
- A learning engine that improves over time

Each of these is a separate module with a separate responsibility. Together they form a cognitive pipeline. No single model can replace this pipeline because no single model can be an architect, a librarian, a critic, and a teacher simultaneously.

Modular cognition is not a performance tradeoff. It is an architectural necessity. Intelligence is not monolithic. The system that hosts it should not be either.

## What ETHAN is not

ETHAN is not a chatbot.

ETHAN is not an agent framework.

ETHAN is not a prompt engineering platform.

ETHAN is not a wrapper around an API.

ETHAN is a cognitive runtime. It does not answer questions. It runs cognition.

## What ETHAN is

ETHAN is a substrate for autonomous intelligence.

It does not wait for prompts. It observes, reflects, and acts.

It does not forget when the conversation ends. It maintains state across time.

It does not depend on a single model. It supports multiple providers and treats them as replaceable engines.

It does not centralize control. The kernel orchestrates. Modules reason. Interfaces connect.

ETHAN provides the structure. The intelligence comes from how you use it.

That is the difference between a tool and a runtime.