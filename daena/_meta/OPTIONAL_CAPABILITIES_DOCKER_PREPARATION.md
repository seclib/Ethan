# OPTIONAL CAPABILITIES DOCKER PREPARATION — Phase 10

Date : 2026-11-04

## Sources officielles et preparations deja presentes

- Qdrant declaration exists in core/capability_manager/builtin.py.
- ChromaDB declaration exists in core/capability_manager/builtin.py.
- LangChain and LangGraph were added as optional `python_package` capabilities.
- Reusable Docker Compose profiles exist in core/deployment/docker/docker-compose.dev.yml and the production docker-compose.yml.

## Docker preparation status

- Qdrant : official upstream project is compatible with a containerized runtime, but official Docker Compose packaging remains to be verified. Security profile and HROT must match existing capabilities.
- ChromaDB : official upstream project is compatible with a containerized runtime and an existing compose profile is already referenced for development.
- LangChain / LangGraph : Python libraries, no dedicated service expected. Their preparation is limited to package isolation and tutor guidance.

## Security

- HROT and limited networks remain mandatory.
- No Docker socket mounting is added.
- No unnecessary database or volume expansion is proposed.
- No real install or run was performed.

## Limits

- Build/run of official images not verified in this phase.
- Settings UI behavior for these capabilities is already declarative, but concrete availability depends on install and HROT flow.
