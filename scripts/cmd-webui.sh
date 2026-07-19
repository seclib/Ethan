#!/usr/bin/env bash
# ethan webui — Lancer l'interface web en mode développement
# Usage: ./ethan webui [--build] [--port=3000]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

timer_start
require_node

PORT="${PORT:-3000}"
BUILD=false

for arg in "$@"; do
    case "$arg" in
        --build) BUILD=true ;;
        --port=*) PORT="${arg#*=}" ;;
    esac
done

section "Interface Web ETHAN"

if [ ! -d "${WEBUI_DIR}/node_modules" ]; then
    info "Installation des dépendances frontend..."
    cd "$WEBUI_DIR" && npm install && cd "$ETHAN_ROOT"
    success "Dépendances installées"
fi

# S'assurer que l'API backend est disponible
API_PORT="${API_PORT:-8000}"
if ! curl -sf "http://localhost:${API_PORT}/api/v1/version" >/dev/null 2>&1; then
    info "Démarrage de l'API backend sur le port ${API_PORT}..."
    nohup "${ETHAN_ROOT}/scripts/cmd-api.sh" --port="${API_PORT}" > "$LOG_DIR/api.log" 2>&1 &
    info "API lancée, attente du healthcheck..."
    for i in {1..30}; do
        if curl -sf "http://localhost:${API_PORT}/api/v1/version" >/dev/null 2>&1; then
            success "API prête sur http://localhost:${API_PORT}"
            break
        fi
        sleep 1
    done
else
    success "API déjà disponible sur http://localhost:${API_PORT}"
fi

cd "$WEBUI_DIR"

if [ "$BUILD" = true ]; then
    info "Build production..."
    npm run build
    success "Build terminé"
    info "Frontend : http://localhost:${PORT}"
    info "API      : http://localhost:${API_PORT}"
    npx next start -p "$PORT"
else
    info "Mode développement sur http://localhost:${PORT}"
    info "API disponible sur http://localhost:${API_PORT}"
    npx next dev -p "$PORT"
fi

cd "$ETHAN_ROOT"
metadata "$(timer_end)"