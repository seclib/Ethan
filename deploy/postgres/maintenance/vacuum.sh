#!/bin/bash
# PostgreSQL maintenance — VACUUM ANALYZE + REINDEX
# Run weekly via cron or docker exec
set -euo pipefail

PGHOST="${PGHOST:-postgres}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-ethan}"
PGDATABASE="${PGDATABASE:-ethan}"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting PostgreSQL maintenance..."

# VACUUM ANALYZE — reclaim dead tuples, update planner stats
echo "  → VACUUM ANALYZE..."
psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "VACUUM ANALYZE;" 2>&1

# REINDEX — rebuild indexes to reduce bloat
echo "  → REINDEX DATABASE CONCURRENTLY..."
psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "REINDEX DATABASE CONCURRENTLY \"$PGDATABASE\";" 2>&1 || true

# Check table sizes for monitoring
echo "  → Table sizes:"
psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "
  SELECT schemaname || '.' || relname AS table,
         pg_size_pretty(pg_total_relation_size(relid)) AS total_size
  FROM pg_catalog.pg_statio_user_tables
  ORDER BY pg_total_relation_size(relid) DESC
  LIMIT 10;
" 2>&1

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Maintenance complete."