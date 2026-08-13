-- =============================================================================
-- ETHAN PostgreSQL schema (version 1)
-- =============================================================================
--
-- This file is mounted at /docker-entrypoint-initdb.d/ and is executed only
-- when PostgreSQL creates a new data directory. Existing installations must
-- use deploy/postgres/migrations/*.sql; never re-run this file against a
-- populated volume.
--
-- The schema deliberately uses TEXT identifiers for events and goals. The
-- Python state backends exchange string IDs and therefore must not depend on
-- PostgreSQL UUID adaptation.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version    TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Event journal. position is nullable because the state backend writes events
-- before the replay backend assigns a monotonically increasing position.
CREATE TABLE IF NOT EXISTS events (
    id          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    type        TEXT NOT NULL DEFAULT 'generic' CHECK (length(type) > 0),
    source      TEXT NOT NULL DEFAULT 'system' CHECK (length(source) > 0),
    timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload     JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
    version     TEXT NOT NULL DEFAULT '1.0',
    reply_to    TEXT,
    position    BIGINT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_type_timestamp
    ON events (type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_source_timestamp
    ON events (source, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_timestamp
    ON events (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_position
    ON events (position);

-- Transactional outbox used by PersistentState.insert_outbox().
CREATE TABLE IF NOT EXISTS events_outbox (
    id           BIGSERIAL PRIMARY KEY,
    topic        TEXT NOT NULL CHECK (length(topic) > 0),
    payload      JSONB NOT NULL DEFAULT '{}'::jsonb,
    status       TEXT NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending', 'published', 'failed')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_events_outbox_status_created
    ON events_outbox (status, created_at);

-- Goal lifecycle and its append-only step history.
CREATE TABLE IF NOT EXISTS goals (
    id          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id     TEXT NOT NULL,
    intent      JSONB NOT NULL DEFAULT '{}'::jsonb,
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    result      JSONB,
    session_id  TEXT NOT NULL DEFAULT '',
    trace_id    TEXT NOT NULL DEFAULT '',
    error       TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_goals_user_status ON goals (user_id, status);
CREATE INDEX IF NOT EXISTS idx_goals_updated_at ON goals (updated_at DESC);

CREATE TABLE IF NOT EXISTS goal_steps (
    id           BIGSERIAL PRIMARY KEY,
    goal_id      TEXT NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    module       TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending', 'running', 'in_progress',
                                   'completed', 'failed', 'skipped')),
    result       JSONB,
    duration_ms  DOUBLE PRECISION,
    retry_count  INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    started_at   TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_goal_steps_goal_created
    ON goal_steps (goal_id, created_at);
CREATE INDEX IF NOT EXISTS idx_goal_steps_status ON goal_steps (status);

-- Optional registries used by the module and session services.
CREATE TABLE IF NOT EXISTS modules (
    id                 TEXT PRIMARY KEY,
    name               TEXT NOT NULL,
    version            TEXT NOT NULL,
    capabilities       JSONB NOT NULL DEFAULT '[]'::jsonb,
    topics_subscribed  JSONB NOT NULL DEFAULT '[]'::jsonb,
    topics_published   JSONB NOT NULL DEFAULT '[]'::jsonb,
    status             TEXT NOT NULL DEFAULT 'active'
                       CHECK (status IN ('active', 'inactive', 'dead')),
    last_heartbeat     TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL,
    metadata   JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '24 hours'
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id);

-- LLM provider configurations (managed by ProviderManager / ProviderStore).
-- ⚠️ La table ne stocke JAMAIS les clés API (secrets via core/config/secrets.py).
CREATE TABLE IF NOT EXISTS llm_providers (
    provider_id TEXT PRIMARY KEY,
    config      JSONB NOT NULL DEFAULT '{}'::jsonb,
    enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    is_default  BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_providers_enabled
    ON llm_providers (enabled);
CREATE INDEX IF NOT EXISTS idx_llm_providers_default
    ON llm_providers (is_default);

-- Durable JSON records owned by Core domain managers.  The domain-specific
-- managers validate their own types; this table supplies a small common
-- persistence boundary while keeping the API gateway stateless.
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

-- AuditStore's canonical row order is intentionally preserved: it reads rows
-- with SELECT * and reconstructs AuditEntry by position.
CREATE TABLE IF NOT EXISTS audit_log (
    id             TEXT PRIMARY KEY,
    timestamp      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    category       TEXT NOT NULL,
    decision       TEXT NOT NULL,
    action         TEXT NOT NULL DEFAULT '',
    actor          TEXT NOT NULL DEFAULT 'system',
    source         TEXT NOT NULL DEFAULT 'system',
    details        JSONB NOT NULL DEFAULT '{}'::jsonb,
    correlation_id TEXT NOT NULL DEFAULT '',
    tags           TEXT[] NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_category ON audit_log (category);
CREATE INDEX IF NOT EXISTS idx_audit_decision ON audit_log (decision);
CREATE INDEX IF NOT EXISTS idx_audit_correlation ON audit_log (correlation_id);

CREATE TABLE IF NOT EXISTS config_changes (
    change_id   TEXT PRIMARY KEY,
    component   TEXT NOT NULL,
    old_value   JSONB,
    new_value   JSONB,
    reason      TEXT NOT NULL DEFAULT '',
    checksum    TEXT NOT NULL DEFAULT '',
    applied     BOOLEAN NOT NULL DEFAULT FALSE,
    rolled_back BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS experiences (
    experience_id TEXT PRIMARY KEY,
    timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type    TEXT NOT NULL DEFAULT '',
    event_id      TEXT NOT NULL DEFAULT '',
    user_id       TEXT NOT NULL DEFAULT 'anonymous',
    goal_id       TEXT NOT NULL DEFAULT '',
    outcome       TEXT NOT NULL DEFAULT 'unknown',
    duration_ms   DOUBLE PRECISION NOT NULL DEFAULT 0,
    module_used   TEXT NOT NULL DEFAULT '',
    skill_invoked TEXT NOT NULL DEFAULT '',
    context       JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata      JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_experiences_skill_time
    ON experiences (skill_invoked, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_experiences_outcome
    ON experiences (skill_invoked, outcome);

CREATE TABLE IF NOT EXISTS cost_log (
    id            BIGSERIAL PRIMARY KEY,
    timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    scope         TEXT NOT NULL DEFAULT 'global',
    scope_id      TEXT NOT NULL DEFAULT '',
    provider      TEXT NOT NULL DEFAULT 'unknown',
    model         TEXT NOT NULL DEFAULT '',
    tokens_input  INTEGER NOT NULL DEFAULT 0 CHECK (tokens_input >= 0),
    tokens_output INTEGER NOT NULL DEFAULT 0 CHECK (tokens_output >= 0),
    cost_usd      DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (cost_usd >= 0),
    context       TEXT NOT NULL DEFAULT '',
    metadata      JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_cost_timestamp ON cost_log (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_cost_scope ON cost_log (scope, scope_id);

-- Replay backend tables (created only when that backend is selected).
CREATE TABLE IF NOT EXISTS checkpoints (
    id              TEXT PRIMARY KEY,
    subject_pattern TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    position        BIGINT NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_checkpoints_subject_time
    ON checkpoints (subject_pattern, timestamp DESC);

CREATE TABLE IF NOT EXISTS snapshots (
    id         TEXT PRIMARY KEY,
    position   BIGINT NOT NULL,
    state      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata   JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_snapshots_position ON snapshots (position DESC);

CREATE OR REPLACE FUNCTION cleanup_outbox()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM events_outbox
    WHERE status = 'published'
      AND COALESCE(processed_at, published_at, created_at)
          < NOW() - INTERVAL '7 days';
END;
$$;

INSERT INTO schema_migrations (version)
VALUES ('0001_initial_schema')
ON CONFLICT (version) DO NOTHING;

DO $$
BEGIN
    RAISE NOTICE 'ETHAN PostgreSQL schema 0001 initialized';
END
$$;
