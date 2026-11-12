-- ETHAN PostgreSQL migration 009
-- Durable records for HROT approvals backed by PostgreSQL.

\set ON_ERROR_STOP on
BEGIN;

CREATE TABLE IF NOT EXISTS hrot_approvals (
    approval_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    requester TEXT NOT NULL,
    requester_type TEXT NOT NULL,
    service_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'APPROVED', 'DENIED', 'EXPIRED', 'CONSUMED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    approver TEXT,
    decided_at TIMESTAMPTZ,
    consumed_id TEXT,
    consumed_at TIMESTAMPTZ,
    reason TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_hrot_approvals_service_id
    ON hrot_approvals(service_id);
CREATE INDEX IF NOT EXISTS idx_hrot_approvals_status
    ON hrot_approvals(status);
CREATE INDEX IF NOT EXISTS idx_hrot_approvals_expires_at
    ON hrot_approvals(expires_at);

INSERT INTO schema_migrations (version)
VALUES ('009_create_hrot_approvals')
ON CONFLICT (version) DO NOTHING;

COMMIT;
