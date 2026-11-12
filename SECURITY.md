# Security Policy

ETHAN is a multi-component AI runtime with Docker, database, agent and provider capabilities.

## Reporting a vulnerability

Please do not open public issues containing exploit details, secrets, tokens, user data or internal infrastructure information.

Report vulnerabilities privately through the repository's GitHub security advisories feature once this repository is public. For private coordination, contact the maintainer through the repository owner account.

## Scope

This policy covers:

- `core/`
- `runtime/`
- `services/`
- `interfaces/api/`
- `interfaces/webui/`
- Docker Compose and deployment support files
- scripts used by ETHAN runtime operations

## Not in scope

The following require coordinated handling because they touch production data or infrastructure:

- Live Docker socket access
- PostgreSQL, Redis or NATS data stores
- Ollama, Odin and Frames integrations
- Provider credentials
- Active sessions and tokens

## Secret hygiene

Never commit `.env`, `.env.*` except `.env.example`, `.secrets/`, private keys, certificates or generated credentials.

Use `Obsidian/Architecture/System/10-secret-hygiene.md` and the public release allowlist/denylist as guidance.

See `Obsidian/Architecture/System/10-secret-hygiene.md` for secret management.

AUDIT ONLY / initial baseline: public-release hygiene is still in progress. Do not report a vulnerability by exposing real credentials.
