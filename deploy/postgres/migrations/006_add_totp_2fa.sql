-- Migration 006 — Two-factor authentication (TOTP) columns on users.
-- ETHAN Core owns the TOTP secret lifecycle (core/auth/totp.py).

ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret text NOT NULL DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_enabled boolean NOT NULL DEFAULT false;

INSERT INTO schema_migrations (version)
VALUES ('006_add_totp_2fa')
ON CONFLICT (version) DO NOTHING;
