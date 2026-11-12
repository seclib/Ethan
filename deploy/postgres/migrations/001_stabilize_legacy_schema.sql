-- ETHAN PostgreSQL migration 001
--
-- Run with psql against an existing volume:
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f 001_stabilize_legacy_schema.sql
--
-- init.sql is intentionally not re-run by Docker after the first volume
-- creation. This migration imports the same canonical definitions, then
-- reconciles columns and constraints that existed in the original schema.

\set ON_ERROR_STOP on
BEGIN;

-- The first schema version predates a few columns that are referenced by the
-- canonical init script. Add those columns before importing it so its indexes
-- can be created on an existing volume. The migration is intentionally for an
-- initialized ETHAN database; a new volume should use init.sql directly.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE events
    ADD COLUMN IF NOT EXISTS reply_to TEXT,
    ADD COLUMN IF NOT EXISTS position BIGINT,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

ALTER TABLE events_outbox
    ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ;

ALTER TABLE goals
    ADD COLUMN IF NOT EXISTS result JSONB,
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

\ir ../init.sql

ALTER TABLE events
    ALTER COLUMN created_at SET DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_events_type_timestamp
    ON events (type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_source_timestamp
    ON events (source, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_timestamp
    ON events (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_position ON events (position);

-- Remove indexes left by the pre-0001 schema when their composite successor
-- provides the same leading-key lookup.
DROP INDEX IF EXISTS idx_events_type;
DROP INDEX IF EXISTS idx_events_source;
DROP INDEX IF EXISTS idx_goals_user;
DROP INDEX IF EXISTS idx_outbox_status;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'events'::regclass
          AND conname = 'events_type_nonempty'
    ) THEN
        ALTER TABLE events ADD CONSTRAINT events_type_nonempty
            CHECK (length(type) > 0);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'events'::regclass
          AND conname = 'events_source_nonempty'
    ) THEN
        ALTER TABLE events ADD CONSTRAINT events_source_nonempty
            CHECK (length(source) > 0);
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_events_outbox_status_created
    ON events_outbox (status, created_at);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'events_outbox'::regclass
          AND conname = 'events_outbox_status_check'
    ) THEN
        ALTER TABLE events_outbox ADD CONSTRAINT events_outbox_status_check
            CHECK (status IN ('pending', 'published', 'failed'));
    END IF;
END
$$;

UPDATE goals
SET session_id = COALESCE(session_id, ''),
    trace_id = COALESCE(trace_id, ''),
    error = COALESCE(error, '');

ALTER TABLE goals
    ALTER COLUMN session_id SET DEFAULT '',
    ALTER COLUMN trace_id SET DEFAULT '',
    ALTER COLUMN error SET DEFAULT '',
    ALTER COLUMN session_id SET NOT NULL,
    ALTER COLUMN trace_id SET NOT NULL,
    ALTER COLUMN error SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'goals'::regclass
          AND conname = 'goals_status_check'
    ) THEN
        ALTER TABLE goals ADD CONSTRAINT goals_status_check
            CHECK (status IN ('pending', 'in_progress', 'completed', 'failed'));
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_goals_user_status ON goals (user_id, status);
CREATE INDEX IF NOT EXISTS idx_goals_updated_at ON goals (updated_at DESC);

INSERT INTO schema_migrations (version)
VALUES ('0002_stabilize_legacy_schema')
ON CONFLICT (version) DO NOTHING;

COMMIT;
