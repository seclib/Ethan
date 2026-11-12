# Isolated PostgreSQL Test Environment — Knowledge/RAG

## Existing environment observed
- PostgreSQL production/test-shared service in ETHAN: ethan-postgres (Up, healthy, 5432)
- Database: ethan
- User: ethan
- Password source: POSTGRES_PASSWORD (default ethan_dev_pass if unset)
- RAG domains stored in `core_domain_records`: knowledge, knowledge-collections, rag-documents, files, files_content, folders, folder-memberships
- Isolated PostgreSQL test database validated for Knowledge/RAG integration testing:
  - PostgreSQL version: 16.15
  - Database: ethan_knowledge_test
  - User: ethan_test
  - Host port: 5433 (`docker-compose.postgres-test.yml`)

## Proposed isolated test service
Create in dedicated compose override only after human validation:
- container name: ethan-postgres-test
- image: postgres:16-alpine
- volume: ethan-postgres-test-db
- host port: 5433 (avoid conflict with 5432)
- database name: ethan_knowledge_test
- user: ethan_test
- credential only via secret manager / env
- no productionvolume

## Safety checks in test
- ETHAN_TEST_POSTGRES_URL required
- ETHAN_TEST_POSTGRES_SAFE=1 required
- explicit ALLOW_TEST only if both
- expected DB name = ethan_knowledge_test
- expected user = ethan_test
- PostgreSQL identity verified with SQL (`current_database()`, `current_user`)
- failure before connect
- cleanup only test-owned IDs linked by current insertion
- never fallback DATABASE_URL

## Provisioning command

```bash
export ETHAN_TEST_POSTGRES_URL=postgresql://ethan_test:***@localhost:5433/ethan_knowledge_test
export ETHAN_TEST_POSTGRES_SAFE=1
.venv/bin/python -m pytest tests/integration/knowledge/test_rag_postgres_persistence.py -q
```

Observed result:

- 1 passed

## Status

- Optional fixture `docker-compose.postgres-test.yml` defines `ethan-postgres-test` (`postgres:16-alpine`) with database `ethan_knowledge_test`, user `ethan_test`, and host port `5433`.
- The isolated test database has been provisioned and validated for the scope documented in `knowledge-postgres-validation.md`.
- PostgreSQL version observed during validation: 16.15.
- Phase 2.4 isolated persistence scope: validated (1 passed).
- Not yet validated: PostgreSQL performance, heavy load, and end-to-end API tests.
- No Docker, database, volume, or migration operation was performed as part of this documentation update.
