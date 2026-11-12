# Security Program Charter — ETHAN

## Scope

This charter governs security work for the ETHAN repository: backend runtime, API gateway, WebUI, Core services, Docker and deployment support, scripts, documentation and release hygiene.

ETHAN must be treated as a future Internet-exposed system.

## Authority

Security changes follow architecture review before implementation.

## Core objectives

1. Establish a verifiable authentication and authorization model.
2. Separate user identity from browser/UI visibility.
3. Enforce resource ownership server-side.
4. Make bootstrap of privileged accounts deterministic and non-reusable.
5. Isolate WebSocket and async event paths.
6. Prevent accidental exposure of secrets, infrastructure and data.
7. Maintain compatibility with existing deployments before any destructive change.

## Controls required

- Authentication
- Authorization / ownership
- Bootstrap security
- Secret hygiene
- Docker and deployment hygiene
- Public repository hygiene
- Documentation and audit traceability
- Test verification

## Status methodology

- VERIFIED: direct source or config evidence
- INFERRED: plausible operational implication
- UNKNOWN: uninspected
- FIXED: corrected and re-tested
- ACCEPTED: accepted residual risk

## Security baseline rule

A feature is not considered secure merely because it exists. It must be backed by implementation evidence, tests, and a documented risk status.
