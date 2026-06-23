#!/bin/bash
# ESIL core — shared shell functions
# No side-effects. Safe to source multiple times.

_ethan_api() {
  local base="${ETHAN_API:-http://localhost:8000}"
  curl -s --max-time 10 -X POST "$base/message" \
    -H "Content-Type: application/json" \
    -d "{\"content\":\"$*\"}"
}

_ethan_api_raw() {
  local text="$1"
  local out
  out="$(_ethan_api "$text")" || true
  if [[ -z "$out" ]]; then
    echo "ERR: API unreachable" >&2
    return 1
  fi
  echo "$out"
}

_ethan_status() {
  local base="${ETHAN_API:-http://localhost:8000}"
  curl -s --max-time 5 "$base/state" 2>/dev/null || echo '{"mode":"offline","active_goal":"none","running_tasks":0}'
}

_ethan_history_record() {
  local type="$1"
  local text="$2"
  local cli
  cli="$(command -v ethan 2>/dev/null || echo "")"
  if [[ -n "$cli" ]]; then
    "$cli" suggest --record "$type" "$text" >/dev/null 2>&1 || true
  fi
}