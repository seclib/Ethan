#!/usr/bin/env bash
# ethan migrate — Exécuter les migrations PostgreSQL
# Usage: ./ethan migrate [--offline] [--revision REV]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

ALEMBIC_DIR="${SCRIPT_DIR}/../deploy/postgres/alembic"
ALEMBIC_INI="${ALEMBIC_DIR}/alembic.ini"

section "Migrations PostgreSQL"

# Check if alembic is installed
if ! command -v alembic &>/dev/null; then
    error "alembic non installé. Installer avec: pip install alembic sqlalchemy"
    exit 1
fi

# Check if alembic directory exists
if [ ! -f "$ALEMBIC_INI" ]; then
    warn "Aucun fichier alembic.ini trouvé, génération..."
    cd "${SCRIPT_DIR}/.."
    alembic init deploy/postgres/alembic
fi

# Build alembic command
ALEMBIC_CMD="alembic -c ${ALEMBIC_INI}"

# Parse options
OFFLINE=""
REVISION=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --offline)
            OFFLINE="--offline"
            shift
            ;;
        --revision)
            REVISION="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        -*)
            warn "Option inconnue: $1"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Build command based on revision
if [ -n "$REVISION" ]; then
    if [ -n "$OFFLINE" ]; then
        CMD="${ALEMBIC_CMD} upgrade ${REVISION} --offline"
    else
        CMD="${ALEMBIC_CMD} upgrade ${REVISION}"
    fi
else
    CMD="${ALEMBIC_CMD} upgrade head"
fi

info "Exécution : $CMD"
cd "${SCRIPT_DIR}/.."
$CMD

success "Migrations appliquées"