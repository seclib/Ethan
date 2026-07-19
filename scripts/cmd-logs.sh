#!/usr/bin/env bash
# ethan logs — Afficher les logs des services ETHAN
# Usage: ./ethan logs [service...] [-f] [--tail=N]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

require_docker

SERVICES="${*:-}"

section "Logs ETHAN"

if [ -n "$SERVICES" ]; then
    docker_compose logs "$@"
else
    docker_compose logs --tail=50 "$@"
fi