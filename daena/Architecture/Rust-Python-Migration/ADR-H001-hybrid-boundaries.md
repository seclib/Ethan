# ADR-H001 — Boundary between Python and Rust

Status: proposed

## Context

ETHAN now has Rust diagnostics and JSON-contract helpers.

## Decision

Keep Python as the source of truth and use Rust through explicit façades.

## Consequences

- Rust stays subordinate to HROT.
- no direct permissions in Rust;
- all contracts remain traceable.
