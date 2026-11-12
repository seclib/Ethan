# ETHAN — Technical Roadmap Proposal

## Priorities

1. Stabiliser profiles/service lifecycle HROT stores under PostgreSQL.
2. Formalize authentication authority via ADR.
3. Fix scheduler/terminal WS discrepancy.
4. Prepare minimal WIPs:
   - implement outbox audit
   - verify multi-instance atomicity
   - document production config
5. Stabilize WebUI / API integration via .env.

## Lots independants

- TRUST-SERVICE finalization.
- infra deployment.
- web login consistency.
- tests and docs reconciliation.

## Acceptance

- all targeted tests clean except known tasks
- documented baseline
- no destructive operations.
