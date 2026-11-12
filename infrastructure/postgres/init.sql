-- Compatibility entrypoint for deployments that still reference the
-- infrastructure/postgres path. The runtime compose stack uses
-- deploy/postgres/init.sql directly. Keep one schema source of truth so the
-- two deployment paths cannot silently drift.
\ir ../../deploy/postgres/init.sql
