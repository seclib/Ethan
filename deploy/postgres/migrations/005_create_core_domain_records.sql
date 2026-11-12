-- ETHAN PostgreSQL migration 005
-- Durable records for Core-owned agents, missions, knowledge and RAG data.

\set ON_ERROR_STOP on
BEGIN;

CREATE TABLE IF NOT EXISTS core_domain_records (
    domain      TEXT NOT NULL CHECK (length(domain) > 0),
    record_id   TEXT NOT NULL CHECK (length(record_id) > 0),
    record      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (domain, record_id)
);

CREATE INDEX IF NOT EXISTS idx_core_domain_records_domain_updated
    ON core_domain_records (domain, updated_at DESC);

INSERT INTO schema_migrations (version)
VALUES ('005_create_core_domain_records')
ON CONFLICT (version) DO NOTHING;

COMMIT;
