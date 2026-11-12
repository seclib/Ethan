# Application Capability Contract

Canonical contract: `core/applications/capability_contract.py`

## Contract
- Versioned (`1.0.0`)
- Stable `capability_id`
- Owning `application_id`
- Input/output JSON schema
- Required permissions (HROT strings)
- Runtime constraints and timeout
- Activation and metadata
- Unknown fields rejected

## Validation
- Required fields.
- Supported contract version.
- Valid identifiers.
- Valid category and invocation interface.
- Valid permission strings.
- Timeout between 1 and 300.
- Application ownership controlled by `ApplicationIntegrationRegistry`.

## Registration
- Explicit approval required.
- Application must exist in registry.
- Duplicate contracts rejected if their definition differs.
- Idempotent for identical contract.
- Does not activate execution or create agents.

## API
- `POST /v1/application-capabilities/validate`
- `POST /v1/application-capabilities` (`Permission.PLUGINS`, approved=true)
- `GET /v1/application-capabilities`

## Status labels
- `IMPLEMENTED`, `INTEGRATED`, `TESTED`.
- `RUNTIME_VALIDATED` not claimed.
- `E2E_VALIDATED` not claimed.
