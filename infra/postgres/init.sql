-- Ethan Cognitive OS — PostgreSQL Schema
-- Phase 0.2: Goals, Modules, Audit, Outbox

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Goals ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS goals (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     TEXT NOT NULL,
    intent      JSONB NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','in_progress','completed','failed')),
    result      JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_goals_user_id ON goals(user_id);
CREATE INDEX idx_goals_status ON goals(status);

-- ── Goal Steps ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS goal_steps (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id     UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    module      TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','running','completed','failed','skipped')),
    result      JSONB,
    duration_ms FLOAT,
    retry_count INT NOT NULL DEFAULT 0,
    started_at  TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_goal_steps_goal_id ON goal_steps(goal_id);

-- ── Module Registry ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS modules (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    version         TEXT NOT NULL,
    capabilities    JSONB NOT NULL DEFAULT '[]',
    topics_subscribed JSONB NOT NULL DEFAULT '[]',
    topics_published JSONB NOT NULL DEFAULT '[]',
    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active','inactive','dead')),
    last_heartbeat  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Sessions ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at  TIMESTAMPTZ NOT NULL DEFAULT now() + INTERVAL '24 hours'
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);

-- ── Audit Log ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp   TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id     TEXT,
    action      TEXT NOT NULL,
    resource    TEXT,
    result      TEXT,
    risk_level  TEXT,
    metadata    JSONB NOT NULL DEFAULT '{}',
    trace_id    TEXT
);

CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);

-- ── Event Outbox ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS events_outbox (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic       TEXT NOT NULL,
    payload     JSONB NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','published','failed')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ
);

CREATE INDEX idx_events_outbox_status ON events_outbox(status);

-- ── Users (placeholder for auth) ────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    roles       JSONB NOT NULL DEFAULT '["user"]',
    permissions JSONB NOT NULL DEFAULT '[]',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO users (id, roles, permissions) VALUES
    ('system', '["system"]', '["*"]'),
    ('user_42', '["user"]', '["message.send", "message.read"]')
ON CONFLICT (id) DO NOTHING;

-- ── Outbox cleanup function ─────────────────────────────
CREATE OR REPLACE FUNCTION cleanup_outbox()
RETURNS void AS $$
BEGIN
    DELETE FROM events_outbox
    WHERE status = 'published'
    AND created_at < now() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;