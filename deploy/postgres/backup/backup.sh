#!/bin/bash
set -euo pipefail
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/ethan"
mkdir -p "$BACKUP_DIR"
pg_dump -U "$PGUSER" -d "$PGDATABASE" | gzip > "${BACKUP_DIR}/ethan_${TIMESTAMP}.sql.gz"
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
echo "Backup complete: ethan_${TIMESTAMP}.sql.gz"