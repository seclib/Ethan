#!/usr/bin/env bash
# ethan restart — Redémarrer les services ETHAN
# Usage: ./ethan restart [service...]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

timer_start
require_docker

SERVICES="${*:-}"

section "Redémarrage des services ETHAN"

if [ -n "$SERVICES" ]; then
    info "Redémarrage de : $SERVICES"
    docker_compose restart $SERVICES
else
    info "Tous les services"
    docker_compose restart
fi

success "Services redémarrés"
metadata "$(timer_end)"