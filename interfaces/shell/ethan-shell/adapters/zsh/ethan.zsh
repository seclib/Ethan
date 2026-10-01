# ETHAN Shell Integration Layer — zsh adapter
# Idempotent.
if [[ -n "$ETHAN_SHELL_LOADED" ]]; then return; fi
export ETHAN_SHELL_LOADED=1

# Source unique de vérité du contrat API (core.sh) — cf. adapter bash.
_ETHAN_CORE="${ETHAN_SHELL_HOME:-${HOME}/.config/ethan-shell}/cli/core.sh"
if [[ -f "$_ETHAN_CORE" ]]; then
  . "$_ETHAN_CORE"
fi

_ethan_cli_or_die() {
  local cli
  cli="$(_ethan_cli 2>/dev/null)" || {
    echo "ethan CLI not found — installez interfaces/cli (binaire « ethan »)" >&2
    return 1
  }
  printf '%s' "$cli"
}

ethan() {
  local cmd="$1"; shift
  case "$cmd" in
    send|"")
      if [[ $# -eq 0 ]]; then
        echo "usage: ethan <message>"
        return 1
      fi
      _ethan_api_raw "$@"
      ;;
    chat)
      local cli; cli="$(_ethan_cli_or_die)" || return 1
      "$cli" chat
      ;;
    status)
      _ethan_status | python3 -c "
import sys, json
s=json.load(sys.stdin)
print(f\"Mode:       {s.get('mode','?')}\")
print(f\"Goal:       {s.get('active_goal') or 'none'}\")
print(f\"Tasks:      {s.get('running_tasks',0)}\")
print(f\"Modules:    {', '.join(s.get('modules_active') or []) or '-'}\")
" 2>/dev/null || _ethan_status
      ;;
    suggest)
      local cli; cli="$(_ethan_cli_or_die)" || return 1
      "$cli" suggest "$@"
      ;;
    daemon)
      local cli; cli="$(_ethan_cli_or_die)" || return 1
      "$cli" daemon "$@"
      ;;
    --help|-h|help)
      echo "ETHAN Shell — native command"
      echo "  ethan <message>  Send message (POST \$ETHAN_API/v1/message)"
      echo "  ethan chat       Interactive mode"
      echo "  ethan status     System status (GET \$ETHAN_API/v1/state)"
      echo "  ethan suggest    Show suggestions"
      echo "  ethan daemon     Background cache"
      echo
      echo "Env: ETHAN_API (défaut http://localhost:8000) · ETHAN_TOKEN (JWT requis)"
      ;;
    *)
      _ethan_api_raw "$cmd $*"
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