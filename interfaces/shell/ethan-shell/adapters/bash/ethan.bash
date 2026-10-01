# ETHAN Shell Integration Layer — bash adapter
# Idempotent, non-intrusif.
if [[ -n "$ETHAN_SHELL_LOADED" ]]; then return; fi
export ETHAN_SHELL_LOADED=1

# Source unique de vérité du contrat API (core.sh). Les adaptateurs ne
# redéfinissent plus _ethan_api/_ethan_status : c'est cette duplication qui
# avait laissé bash/zsh/fish diverger du préfixe /v1 et du champ « input ».
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

# Completion (minimal)
_ethan_complete() {
  local cur="${COMP_WORDS[COMP_CWORD]}"
  local prev="${COMP_WORDS[COMP_CWORD-1]}"
  local cmds="chat status suggest daemon --help help"
  if [[ $COMP_CWORD -eq 1 ]]; then
    COMPREPLY=($(compgen -W "$cmds" -- "$cur"))
    return
  fi
  case "$prev" in
    suggest) COMPREPLY=($(compgen -A number -- "$cur")) ;;
    daemon)  COMPREPLY=($(compgen -W "start stop status" -- "$cur")) ;;
    *)       COMPREPLY=() ;;
  esac
}
complete -F _ethan_complete ethan