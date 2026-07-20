#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"
section "Attente services HTTP"
TIMEOUT="${1:-60}"
FAIL=0
for entry in "API:http://localhost:8000/v1/health" "WebUI:http://localhost:3000/"; do
  name="${entry%%:*}"
  url="${entry##*:}"
  info "Attente $name -> $url"
  if ! wait_for_http "$url" "$TIMEOUT"; then
    error "$name injoignable"
    FAIL=1
  else
    success "$name pret"
  fi
done
if [ "$FAIL" -ne 0 ]; then
  error "Certains services ne sont pas prets"
  exit 1
fi
success "Services HTTP prets"