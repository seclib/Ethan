#!/usr/bin/env bash
# ethan down — Arrêter les services ETHAN
# Usage: ./ethan down [service...]
#
# Arrêt progressif :
#   1. SIGTERM avec timeout 30s (grace period)
#   2. Attente 5s pour finalisation
#   3. docker compose down (nettoie réseaux, volumes orphelins)

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

timer_start
require_docker

SERVICES="${*:-}"

section "Arrêt des services ETHAN"

if [ -n "$SERVICES" ]; then
    info "Arrêt progressif de : $SERVICES"
    docker_compose stop --timeout=30 $SERVICES
    sleep 2
    info "Nettoyage final"
    docker_compose down --remove-orphans $SERVICES
else
    info "Arrêt progressif de tous les services"
    docker_compose stop --timeout=30
    sleep 5
    info "Nettoyage final"
    docker_compose down --remove-orphans
fi

success "Services arrêtés"
metadata "$(timer_end)"
