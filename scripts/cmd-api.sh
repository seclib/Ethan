#!/usr/bin/env bash
# ethan api — Lancer l'API Gateway en mode développement
# Usage: ./ethan api [--port=8000] [--reload]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

timer_start
require_python

PORT="${PORT:-8000}"
RELOAD=false

for arg in "$@"; do
    case "$arg" in
        --reload) RELOAD=true ;;
        --port=*) PORT="${arg#*=}" ;;
    esac
done

section "API Gateway ETHAN"

# Vérifier les dépendances
if [ ! -d "${ETHAN_ROOT}/.venv" ]; then
    info "Installation des dépendances Python..."
    cd "$ETHAN_ROOT"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[server,dev]" 2>&1 | tail -1
    success "Dépendances installées"
fi

# Activer le venv
source "${ETHAN_ROOT}/.venv/bin/activate" 2>/dev/null || true

cd "$API_DIR"

RELOAD_FLAG=""
if [ "$RELOAD" = true ]; then
    RELOAD_FLAG="--reload"
    info "Mode rechargement actif"
fi

info "Démarrage sur http://localhost:${PORT}"
info "NATS : ${NATS_URL:-nats://localhost:4222}"

PYTHONPATH="${ETHAN_ROOT}/core:${API_DIR}:${ETHAN_ROOT}" \
    uvicorn api.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    $RELOAD_FLAG \
    --log-level "${LOG_LEVEL:-info}"

cd "$ETHAN_ROOT"
metadata "$(timer_end)"