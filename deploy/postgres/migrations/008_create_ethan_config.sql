-- ETHAN PostgreSQL migration 008
-- Durable configuration domains owned by core/config (ConfigStore).
--
-- Context: ConfigStore writes to `ethan_config` (JSONB per domain) but the
-- table was never created by any schema (init.sql, migrations 001-007 or
-- alembic).  Every configuration write therefore failed silently and the
-- value only lived in process memory — losing user/system configuration on
-- any container restart.  This migration materialises the missing table so
-- the configuration chain (UI → API → ConfigurationService → ConfigStore →
-- PostgreSQL) is durable.
--
-- Secrets are never stored here: api keys live in core/config/secrets.py
-- (env / Vault / Docker secrets).  See docs/security/10-secret-hygiene.md.

\set ON_ERROR_STOP on
BEGIN;

CREATE TABLE IF NOT EXISTS ethan_config (
    domain_name TEXT PRIMARY KEY CHECK (length(domain_name) > 0),
    config      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ConfigStore reads the full table on every load; the primary key on
-- domain_name already serves point lookups.  A recency index keeps the
-- "list all domains, newest first" pattern cheap if it is ever added.
CREATE INDEX IF NOT EXISTS idx_ethan_config_updated
    ON ethan_config (updated_at DESC);

INSERT INTO schema_migrations (version)
VALUES ('008_create_ethan_config')
ON CONFLICT (version) DO NOTHING;

COMMIT;