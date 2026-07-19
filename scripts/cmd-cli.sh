#!/usr/bin/env bash
# ethan cli — Lancer le CLI ETHAN
# Usage: ./ethan cli [arguments...]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

require_python

section "CLI ETHAN"

if [ -f "${CLI_DIR}/main.py" ]; then
    cd "$ETHAN_ROOT"
    PYTHONPATH="${ETHAN_ROOT}:${ETHAN_ROOT}/core:${ETHAN_ROOT}/interfaces/cli${PYTHONPATH:+:$PYTHONPATH}" \
    python3 -m cli.main "$@"
elif [ -f "${CLI_DIR}/ethan" ]; then
    "${CLI_DIR}/ethan" "$@"
elif [ -f "${CLI_DIR}/ethan.py" ]; then
    python3 "${CLI_DIR}/ethan.py" "$@"
else
    error "CLI introuvable dans ${CLI_DIR}"
    info "Vérifie le chemin ou implémente interfaces/cli/"
    exit 1
fi