-- ETHAN PostgreSQL migration 003
-- Creates the users table to replace in-memory authentication

\set ON_ERROR_STOP on
BEGIN;

CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    roles         TEXT[] NOT NULL DEFAULT '{user}',
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    metadata      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);

-- Create a default admin user (password is 'admin')
-- Password hashed with bcrypt (passlib default rounds)
-- Note: In production this should be changed immediately!
INSERT INTO users (id, username, password_hash, roles)
VALUES (
    'user_admin_00000000',
    'admin',
    '$2b$12$IMasHHKJXSeiAxx6kYiGf.8zkx.ueVl6/oWo61VnT0mGCbv9.CQzK',
    '{admin}'
) ON CONFLICT (username) DO NOTHING;

INSERT INTO schema_migrations (version)
VALUES ('0003_create_users_table')
ON CONFLICT (version) DO NOTHING;

COMMIT;
