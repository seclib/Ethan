#!/usr/bin/env bash
# ethan migrate — Exécuter les migrations PostgreSQL
# Usage: ./ethan migrate [--offline] [--revision REV]
#
# Deux mécanismes, dans cet ordre :
#   1. Migrations SQL numérotées (deploy/postgres/migrations/*.sql) — source de
#      vérité du schéma (cf. migrations/README.md). Chaque fichier est appliqué
#      une seule fois via `psql -v ON_ERROR_STOP=1` ; le suivi est assuré par la
#      table `schema_migrations`, alimentée par le fichier SQL lui-même.
#   2. Alembic — conservé pour compatibilité ; ignoré tant qu'aucune révision
#      n'existe dans deploy/postgres/alembic/versions/.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

ALEMBIC_DIR="${SCRIPT_DIR}/../deploy/postgres/alembic"
ALEMBIC_INI="${ALEMBIC_DIR}/alembic.ini"
MIGRATIONS_DIR="${SCRIPT_DIR}/../deploy/postgres/migrations"

section "Migrations PostgreSQL"

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

# ── 1. Migrations SQL numérotées (source de vérité) ───────────────────
if [ -n "$OFFLINE" ]; then
    info "Mode --offline : migrations SQL ignorées (elles s'appliquent en ligne)."
elif [ -z "$(find "$MIGRATIONS_DIR" -maxdepth 1 -name '*.sql' -print -quit 2>/dev/null)" ]; then
    info "Aucun fichier SQL dans deploy/postgres/migrations — étape ignorée."
else
    if ! docker_compose ps postgres 2>/dev/null | grep -q "Up"; then
        error "Le conteneur 'postgres' doit être en cours d'exécution. Lancez './ethan up' d'abord."
        exit 1
    fi

    APPLIED_FILE="$(mktemp)"
    SQL_INPUT="$(mktemp)"
    trap 'rm -f "$APPLIED_FILE" "$SQL_INPUT"' EXIT

    if ! docker_compose exec -T postgres \
        psql -U ethan -d ethan -qtAc "SELECT version FROM schema_migrations" \
        > "$APPLIED_FILE" 2>/dev/null; then
        error "Impossible de lire schema_migrations (base non initialisée ?)"
        exit 1
    fi

    SQL_APPLIED=0
    while IFS= read -r file; do
        # La version fait foi : elle est déclarée DANS le fichier SQL (le numéro
        # du nom de fichier peut ne pas correspondre, ex. 001_* → 0002_*).
        version="$(grep -A1 'INSERT INTO schema_migrations' "$file" \
            | sed -n "s/.*VALUES ('\([^']*\)').*/\1/p" | head -1)"
        if [ -z "$version" ]; then
            warn "Version introuvable dans $(basename "$file") — fichier ignoré"
            continue
        fi
        if grep -qx "$version" "$APPLIED_FILE"; then
            info "  = $version (déjà appliquée)"
            continue
        fi
        info "  -> application de $version"
        # psql lit le fichier sur stdin : les inclusions psql (`\ir ../init.sql`,
        # cf. 001_stabilize_legacy_schema.sql) ne peuvent pas être résolues côté
        # serveur (le dossier migrations n'est pas monté dans le conteneur).
        # On les inligne ici, résolues relativement au fichier de migration.
        while IFS= read -r line || [ -n "$line" ]; do
            if [[ "$line" =~ ^[[:space:]]*\\(i|ir)[[:space:]]+([^[:space:]]+) ]]; then
                include="$(cd "$(dirname "$file")" && realpath -m "${BASH_REMATCH[2]}")"
                if [ -f "$include" ]; then
                    cat "$include"
                else
                    warn "Inclusion introuvable : ${BASH_REMATCH[2]} (dans $(basename "$file"))"
                    printf '%s\n' "$line"
                fi
            else
                printf '%s\n' "$line"
            fi
        done < "$file" > "$SQL_INPUT"

        if ! docker_compose exec -T postgres \
            psql -U ethan -d ethan -v ON_ERROR_STOP=1 -q < "$SQL_INPUT"; then
            error "Échec de la migration $version — arrêt (schéma non modifié)"
            exit 1
        fi
        SQL_APPLIED=$((SQL_APPLIED + 1))
    done < <(find "$MIGRATIONS_DIR" -maxdepth 1 -name '*.sql' | sort)

    success "${SQL_APPLIED} migration(s) SQL appliquée(s)"
fi

# ── 2. Alembic (compatibilité — aucune révision aujourd'hui) ───────────
if [ -z "$(find "${ALEMBIC_DIR}/versions" -name '*.py' -print -quit 2>/dev/null)" ]; then
    info "Aucune révision Alembic — étape ignorée."
else
    if ! docker_compose ps api 2>/dev/null | grep -q "Up"; then
        error "Le conteneur 'api' doit être en cours d'exécution. Lancez './ethan up api' d'abord."
        exit 1
    fi

    ALEMBIC_CMD="docker_compose exec -T api alembic"

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
fi

success "Migrations appliquées"