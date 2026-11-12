-- Migration 007 — Password reset tokens (forgot-password flow).
-- ETHAN Core owns the token lifecycle (core/auth/password_reset.py).
-- Only SHA-256 hashes of tokens are stored — never the raw token.

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id          bigserial PRIMARY KEY,
    token_hash  text NOT NULL UNIQUE,
    username    text NOT NULL,
    expires_at  timestamptz NOT NULL,
    used        boolean NOT NULL DEFAULT false,
    consumed_at timestamptz,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_username
    ON password_reset_tokens (username);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires
    ON password_reset_tokens (expires_at);

INSERT INTO schema_migrations (version)
VALUES ('007_password_reset_tokens')
ON CONFLICT (version) DO NOTHING;