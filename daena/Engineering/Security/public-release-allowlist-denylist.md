# Public Release Allowlist / Denylist

## Allowlist (source candidates)

- `core/`
- `runtime/`
- `services/`
- `sdk/`
- `interfaces/api/` after secret/template review
- `interfaces/webui/src/` after removing runtime-only and private-data paths
- `tests/` after removal of real credentials or environment-specific assumptions
- `docs/` after documentation scrub for internal addresses and credentials
- `.github/workflows/` only after Actions are SHA-pinned
- `.env.example`
- Deployment templates that use placeholders only

## Denylist (never publish as-is)

- `.env`
- `.env.*` except `.env.example`
- `.secrets/`
- private keys, certificates and credential stores
- logs, SQLite databases, SQL dumps and generated reports
- `.next/`, build outputs and cache directories
- local IDE, OS and editor settings
- internal host-only network configurations unless intentionally documented as examples
- Docker runtime volumes
- database dumps and user data
- default-admin SQL bootstrap with password `admin`
- Playwright, test-result and coverage artifacts

## Governance

- Review every PR for runtime topology and credentials before merge.
- Keep production WebUI behavior unchanged in non-demo work.
- Use the dedicated GitHub Pages demo plan before building any public demonstration.
