#!/usr/bin/env bash
# DEPRECATED — Utilisez ./ethan install

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ETHAN_ROOT="$(dirname "$SCRIPT_DIR")"

echo "⚠  Ce script est déprécié. Redirection vers ./ethan install..."
echo

if [ ! -x "${ETHAN_ROOT}/ethan" ]; then
    chmod +x "${ETHAN_ROOT}/ethan"
fi

exec "${ETHAN_ROOT}/ethan" install "$@"