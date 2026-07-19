#!/usr/bin/env bash
# ethan down — Arrêter les services ETHAN
# Usage: ./ethan down [service...]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

timer_start
require_docker

SERVICES="${*:-}"

section "Arrêt des services ETHAN"

if [ -n "$SERVICES" ]; then
    info "Arrêt de : $SERVICES"
    docker_compose stop $SERVICES
else
    info "Tous les services"
    docker_compose down
fi

success "Services arrêtés"
metadata "$(timer_end)"