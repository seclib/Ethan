-- ETHAN PostgreSQL migration 004
-- Table des configurations de providers LLM gérés par ProviderManager.
--
-- La table ne stocke JAMAIS les clés API : celles-ci proviennent des
-- secrets (Vault/env/Docker secrets) via core/config/secrets.py et sont
-- injectées en mémoire au runtime par ProviderManager._inject_secrets().
-- La colonne `config` (JSONB) contient le reste de la configuration
-- (type, base_url, default_model, display_name, enabled, ...).

\set ON_ERROR_STOP on
BEGIN;

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

INSERT INTO schema_migrations (version)
VALUES ('004_create_llm_providers_table')
ON CONFLICT (version) DO NOTHING;

COMMIT;
