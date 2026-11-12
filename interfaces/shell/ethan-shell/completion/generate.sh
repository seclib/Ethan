#!/bin/bash
# Generate shell completion scripts from CLI commands
# Not called at runtime — used by install.sh or updated manually

generate_bash() {
  local out="$1/ethan-completion.bash"
  cat > "$out" <<'EOF'
_ethan_complete() {
  local cur="${COMP_WORDS[COMP_CWORD]}"
  local prev="${COMP_WORDS[COMP_CWORD-1]}"
  local cmds="chat status suggest daemon send --help help"
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
EOF
  echo "bash → $out"
}

generate_zsh() {
  local out="$1/ethan-completion.zsh"
  cat > "$out" <<'EOF'
#compdef ethan
_ethan_complete() {
  local -a subcmds
  subcmds=(chat status suggest daemon send --help help)
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
EOF
  echo "zsh → $out"
}

generate_fish() {
  local out="$1/ethan-completion.fish"
  cat > "$out" <<'EOF'
function _ethan_complete
  set -l cmds chat status suggest daemon send --help help
  set -l cur (commandline -t)
  set -l prev (commandline -cp | head -1)
  switch (count (commandline -opc))
    case 1
      printf '%s\n' $cmds
    case '*'
      switch "$prev"
        case "suggest"; printf '%s\n' (seq 1 20)
        case "daemon";  printf '%s\n' start stop status
      end
  end
end
complete -c ethan -f -a '(_ethan_complete)'
EOF
  echo "fish → $out"
}

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$SRC/completions"
mkdir -p "$DEST"

generate_bash "$DEST"
generate_zsh "$DEST"
generate_fish "$DEST"

echo "Completions generated in $DEST"