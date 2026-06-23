# ETHAN Shell Integration Layer — zsh adapter
# Idempotent.
if [[ -n "$ETHAN_SHELL_LOADED" ]]; then return; fi
export ETHAN_SHELL_LOADED=1

_ethan_api() {
  local base="${ETHAN_API:-http://localhost:8000}"
  curl -s --max-time 10 -X POST "$base/message" \
    -H "Content-Type: application/json" \
    -d "{\"content\":\"$*\"}" 2>/dev/null
}

_ethan_send() {
  local out
  out="$(_ethan_api "$*")" || true
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

ethan() {
  local cmd="$1"; shift
  case "$cmd" in
    send|"")
      if [[ $# -eq 0 ]]; then
        echo "usage: ethan <message>"
        return 1
      fi
      _ethan_send "$@"
      ;;
    chat)
      if command -v ethan-cli >/dev/null 2>&1; then
        ethan-cli chat
      else
        echo "ethan-cli not found — please install ethan-cli"
      fi
      ;;
    status)
      _ethan_status | python3 -c "
import sys, json
s=json.load(sys.stdin)
print(f\"Mode:       {s.get('mode','?')}\")
print(f\"Goal:       {s.get('active_goal','none')}\")
print(f\"Tasks:      {s.get('running_tasks',0)}\")
" 2>/dev/null || _ethan_status
      ;;
    suggest)
      if command -v ethan-cli >/dev/null 2>&1; then
        ethan-cli suggest "$@"
      else
        echo "ethan-cli not found"
      fi
      ;;
    daemon)
      if command -v ethan-cli >/dev/null 2>&1; then
        ethan-cli daemon "$@"
      else
        echo "ethan-cli not found"
      fi
      ;;
    --help|-h|help)
      echo "ETHAN Shell — native command"
      echo "  ethan <message>  Send message"
      echo "  ethan chat       Interactive mode"
      echo "  ethan status     System status"
      echo "  ethan suggest    Show suggestions"
      echo "  ethan daemon     Background cache"
      ;;
    *)
      _ethan_send "$cmd $*"
      ;;
  esac
}

# Completion
_ethan_complete() {
  local -a subcmds
  subcmds=(chat status suggest daemon --help help)
  if [[ $CURRENT -eq 1 ]]; then
    compadd "$@" "${subcmds[@]}"
    return
  fi
  case "$words[2]" in
    suggest) compadd -S '' {1..20} ;;
    daemon)  compadd start stop status ;;
  esac
}
compdef _ethan_complete ethan