# ETHAN — Matrice exigences → implémentation → tests → preuves (P1)

| ID | Exigence | Implémentation cible | Test cible | Preuve requise |
|---|---|---|---|---|
| R-01 | Core source de vérité | core/* managers | import-linter + unit | ADR-4006 + CI |
| R-02 | API thin gateway | interfaces/api routers | contract tests | shapes JSON |
| R-03 | Hybrid Rust event store | parity backend | Python/Rust shadow tests | diff count/hash |
| R-04 | Licence Open WebUI gate | docs/ADR-4007 | revue légale | décision écrite |
| R-05 | Données préservées | backups/restore | restore test | checksum/volume |
| R-06 | OID (= human trust) | core/human_root | approval tests | audit log |
| R-07 | Skills validation | core/skills | skill validation tests | rapport import |
| R-08 | MCP sandbox | env allowlist + Core runner | integration tests | logs |
| R-09 | Observabilité | logs/metrics/traces | e2e health | dashboards |
| R-10 | Non-régression | test suites P0 | pytest/jest/playwright | CI |
