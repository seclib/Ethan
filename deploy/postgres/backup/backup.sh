#!/bin/bash
# =============================================================================
# ETHAN — PostgreSQL Backup Script
# =============================================================================
# Production-grade pg_dump avec :
#   - Rotation automatique par rétention configurable
#   - Vérification de l'intégrité du dump (pg_restore --list)
#   - Rapport de taille et durée
#   - Signal SIGUSR1 pour backup manuel immédiat depuis l'hôte
# =============================================================================
set -euo pipefail

# ── Configuration (depuis les variables d'environnement) ─────────────────────
BACKUP_DIR="${BACKUP_DIR:-/var/backups/ethan}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
COMPRESS="${BACKUP_COMPRESS:-true}"
DB="${PGDATABASE:-ethan}"
LOG_PREFIX="[ethan-backup]"

# ── Fonctions utilitaires ─────────────────────────────────────────────────────
log()  { echo "$(date -Iseconds) ${LOG_PREFIX} INFO  $*"; }
warn() { echo "$(date -Iseconds) ${LOG_PREFIX} WARN  $*" >&2; }
die()  { echo "$(date -Iseconds) ${LOG_PREFIX} ERROR $*" >&2; exit 1; }

# ── Vérification de la connexion PostgreSQL ───────────────────────────────────
wait_for_pg() {
    local retries=30
    log "Waiting for PostgreSQL at ${PGHOST}:${PGPORT:-5432}..."
    until pg_isready -q -h "${PGHOST}" -p "${PGPORT:-5432}" -U "${PGUSER}"; do
        retries=$((retries - 1))
        [ $retries -le 0 ] && die "PostgreSQL not reachable after 30 retries"
        sleep 2
    done
    log "PostgreSQL is ready."
}

# ── Exécution du backup ───────────────────────────────────────────────────────
run_backup() {
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/ethan_${timestamp}"
    local start_ts
    start_ts=$(date +%s)

    mkdir -p "${BACKUP_DIR}"

    log "Starting backup of database '${DB}'..."

    if [ "${COMPRESS}" = "true" ]; then
        backup_file="${backup_file}.dump.gz"
        pg_dump \
            -h "${PGHOST}" \
            -p "${PGPORT:-5432}" \
            -U "${PGUSER}" \
            -d "${DB}" \
            --format=custom \
            --no-password \
        | gzip -9 > "${backup_file}"
    else
        backup_file="${backup_file}.dump"
        pg_dump \
            -h "${PGHOST}" \
            -p "${PGPORT:-5432}" \
            -U "${PGUSER}" \
            -d "${DB}" \
            --format=custom \
            --no-password \
            -f "${backup_file}"
    fi

    # ── Vérification de l'intégrité ──────────────────────────────────────────
    if [ "${COMPRESS}" = "true" ]; then
        # Vérifier que le fichier gzip est lisible
        gzip -t "${backup_file}" || die "Backup file integrity check failed: ${backup_file}"
    else
        pg_restore --list "${backup_file}" > /dev/null || die "Backup restore-list check failed: ${backup_file}"
    fi

    local duration=$(( $(date +%s) - start_ts ))
    local size
    size=$(du -sh "${backup_file}" | cut -f1)

    log "Backup complete: $(basename "${backup_file}") [${size}] in ${duration}s"

    # ── Rotation : supprimer les backups trop anciens ─────────────────────────
    local deleted
    deleted=$(find "${BACKUP_DIR}" \( -name "*.dump.gz" -o -name "*.dump" \) -mtime "+${RETENTION_DAYS}" -print -delete | wc -l)
    [ "${deleted}" -gt 0 ] && log "Rotation: deleted ${deleted} backup(s) older than ${RETENTION_DAYS} days"

    # ── Résumé des backups disponibles ────────────────────────────────────────
    local count
    count=$(find "${BACKUP_DIR}" \( -name "*.dump.gz" -o -name "*.dump" \) | wc -l)
    local total_size
    total_size=$(du -sh "${BACKUP_DIR}" 2>/dev/null | cut -f1 || echo "?")
    log "Backup directory: ${count} file(s), total ${total_size}"

    # ── Upload déporté (S3 ou équivalent) ─────────────────────────────────────
    if [ -n "${AWS_ACCESS_KEY_ID:-}" ] && [ -n "${AWS_SECRET_ACCESS_KEY:-}" ] && [ -n "${S3_BACKUP_BUCKET:-}" ]; then
        log "Uploading backup to S3 bucket ${S3_BACKUP_BUCKET}..."
        # Utilisation de aws-cli si disponible
        if command -v aws >/dev/null 2>&1; then
            aws s3 cp "${backup_file}" "s3://${S3_BACKUP_BUCKET}/ethan/$(basename "${backup_file}")" >/dev/null
            log "S3 upload complete."
        else
            warn "AWS CLI not found. S3 upload skipped."
        fi
    fi
}

# ── Handler pour SIGUSR1 (backup manuel) ─────────────────────────────────────
trap 'log "Received SIGUSR1 — running manual backup"; run_backup' SIGUSR1

# ── Mode scheduler interne (évite la dépendance à cron dans le conteneur) ─────
# Le Dockerfile utilise une boucle sleep; ici on prend en charge le cas
# où BACKUP_SCHEDULE est défini (via supercronic ou fcron si disponible).
main() {
    wait_for_pg

    # Premier backup au démarrage
    run_backup

    # Boucle de backup périodique (intervalle en secondes)
    # BACKUP_INTERVAL_SECONDS peut être défini pour override la planification
    local interval="${BACKUP_INTERVAL_SECONDS:-21600}"  # 6h par défaut
    log "Next backup in ${interval}s (use SIGUSR1 for immediate backup)"

    while true; do
        sleep "${interval}" &
        wait $!
        run_backup
        log "Next backup in ${interval}s"
    done
}

main "$@"