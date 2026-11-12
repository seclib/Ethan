# ETHAN Shell Completion — Générique (bash/zsh)
# Source via ethan.sh

_ethan_completion() {
    local cur prev words cword
    _init_completion -n : 2>/dev/null || return

    commands="chat status logs help config daemon version plugin plugins run think suggest"

    if [[ $cword -eq 1 ]]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
        return 0
    fi

    case "${words[1]}" in
        plugin|plugins)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "list install remove info" -- "$cur"))
            fi
            ;;
        daemon)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "start stop restart status" -- "$cur"))
            fi
            ;;
        config)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "show edit reset" -- "$cur"))
            fi
            ;;
    esac
}

complete -F _ethan_completion ethan