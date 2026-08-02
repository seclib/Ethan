#!/usr/bin/env bash
# ethan migrate — Exécuter les migrations PostgreSQL
# Usage: ./ethan migrate [--offline] [--revision REV]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

ALEMBIC_DIR="${SCRIPT_DIR}/../deploy/postgres/alembic"
ALEMBIC_INI="${ALEMBIC_DIR}/alembic.ini"

section "Migrations PostgreSQL"

# Utilise le conteneur API pour exécuter alembic (pas de dépendance host)
if ! docker compose ps api | grep -q "Up"; then
    error "Le conteneur 'api' doit être en cours d'exécution. Lancez './ethan up api' d'abord."
    exit 1
fi

ALEMBIC_CMD="docker compose exec api alembic"

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
if [ -f "$ALEMBIC_INI" ]; then
    $CMD
else
    warn "Aucun alembic.ini trouvé (Migrations non initialisées). Ignoré."
fi

success "Migrations appliquées"