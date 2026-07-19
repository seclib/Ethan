#!/usr/bin/env bash
# ethan desktop — Lancer l'application desktop ETHAN
# Usage: ./ethan desktop [--dev]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

DESKTOP_DIR="${ETHAN_ROOT}/interfaces/desktop"
DEV_MODE=false

for arg in "$@"; do
    case "$arg" in
        --dev) DEV_MODE=true ;;
    esac
done

section "Application Desktop ETHAN"

if [ ! -d "$DESKTOP_DIR" ]; then
    error "Application desktop introuvable : ${DESKTOP_DIR}"
    info "Le desktop n'est pas encore implémenté."
    arrow "Contribution : créer interfaces/desktop/"
    exit 1
fi

if [ "$DEV_MODE" = true ]; then
    info "Mode développement"
    cd "$DESKTOP_DIR"
    if [ -f "package.json" ]; then
        if [ ! -d "node_modules" ]; then
            npm install
        fi
        npm run dev
    elif [ -f "Cargo.toml" ]; then
        cargo run
    else
        error "Aucun projet reconnu dans interfaces/desktop"
        exit 1
    fi
else
    cd "$DESKTOP_DIR"
    if [ -f "package.json" ]; then
        npx electron .
    elif [ -f "Cargo.toml" ]; then
        cargo run --release
    else
        error "Aucun projet reconnu dans interfaces/desktop"
        exit 1
    fi
fi