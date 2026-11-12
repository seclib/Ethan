# ETHAN — Technical Debt

## P0 — Critique

- WebUI login historically broken due missing API DNS / ENV; resolved by starting API and adding vars, but configuration reproducibility still fragile.
- HROT source of truth remains dual (PG + JSONL fallback), which can lead to divergent approvals in local mode.
- HumanRoot still lacks durable audit settlement and private key separation in a stronger cryptographic design.

## P1 — Prioritaires

- Audit terminal WS failures remain ambiguous: simulate in isolated manner.
- Many test fixtures share PostgreSQL HROT state without cleanup; requires care.
- Duplicate function definitions / helper drift in `interfaces/api/routers/internal.py` around `_require_hrot_approval`, `PrincipalType` and HROT calls.
- `fetch_user_record` depends on env auto loading; possible in dedicated test setups.
- Documentation partly outruns implementation (service lifecycle, HROT, MIG).

## P2 — Importants

- WebUI/API hostnames tightly coupled to Docker DNS.
- CoreRecordStore fallback may pollute unit testing assumptions.
- Agent harness / AgentManager/ToolContext untouched by this baseline.
- Wallet/CEX/API connectors may require additional governance.

## P3 — Amélioration

- WebUI proxy and auth UI test coverage currently limited.
- Test orchestration can be refined to remove flaky provider catalog ordering.
- Code style and import organization.

- Large untracked changes make review burden high; recommend organized PRs after stabilization.

## Recommandation

- First restore `.env` non-secret additions and keep API service running.
- Second migrate HROT strictly to PostgreSQL.
- Third consolidate identity provisions with strong tests.
- Keep terminal WS test as a separate concern.
