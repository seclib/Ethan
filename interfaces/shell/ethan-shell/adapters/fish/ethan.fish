# ETHAN Shell Integration Layer — fish adapter
# Idempotent.
if set -q ETHAN_SHELL_LOADED
    exit
end
set -gx ETHAN_SHELL_LOADED 1

# core.sh est du bash : fish ne peut pas le sourcer, on porte donc le contrat
# API ici. Toute modification doit être répercutée dans cli/core.sh (le test
# tests/interfaces/test_shell_contract.py compare les deux).
#   - POST $ETHAN_API/v1/message  champ REQUIS « input »
#   - GET  $ETHAN_API/v1/state
#   - JWT obligatoire, lu dans ETHAN_TOKEN (jamais en dur)

function _ethan_base
    if set -q ETHAN_API; and test -n "$ETHAN_API"
        echo "$ETHAN_API"
    else
        echo "http://localhost:8000"
    end
end

function _ethan_auth_flags
    if set -q ETHAN_TOKEN; and test -n "$ETHAN_TOKEN"
        echo -H "Authorization: Bearer $ETHAN_TOKEN"
    end
end

function _ethan_json_payload
    python3 -c 'import json,sys; print(json.dumps({"input": sys.argv[1]}))' "$argv"
end

function _ethan_api_raw
    set -l base (_ethan_base | string replace -r '/+$' '')
    set -l payload (_ethan_json_payload (string join ' ' -- $argv))
    or return 1

    # -o dans un fichier, -w sur stdout : le code HTTP ne se melange JAMAIS
    # au corps de la reponse. Une substitution de commande fish decouperait
    # sur les sauts de ligne, donc on ne passe jamais par la stdout.
    set -l body (mktemp)
    set -l code (curl -s --max-time 10 -X POST "$base/v1/message" \
        -H "Content-Type: application/json" \
        (_ethan_auth_flags) \
        -d "$payload" -o "$body" -w '%{http_code}' 2>/dev/null)
    set -l rc $status

    if test $rc -ne 0 -o -z "$code"
        rm -f "$body"
        echo "ERR: API injoignable ($base) — ETHAN_API ? ethan up ?" >&2
        return 1
    end

    switch "$code"
        case '2*'
            cat "$body"
            rm -f "$body"
            return 0
            ;;
        case 000
            echo "ERR: API injoignable ($base) — ETHAN_API ? ethan up ?" >&2
            return 1
            ;;
        case 401 403
            rm -f "$body"
            echo "ERR: authentification requise (HTTP $code) — export ETHAN_TOKEN=<jwt>" >&2
            return 1
            ;;
        case 404
            rm -f "$body"
            echo "ERR: /v1/message introuvable (HTTP $code) — ETHAN_API=$base ?" >&2
            return 1
            ;;
        case 422
            rm -f "$body"
            echo "ERR: requête rejetée (HTTP $code) — charge utile non conforme au schéma Core" >&2
            return 1
            ;;
        case 503
            rm -f "$body"
            echo "ERR: NATS non connecté (HTTP $code) — l'API ne peut pas émettre d'événement" >&2
            return 1
            ;;
        case '*'
            set -l detail (cat "$body")
            rm -f "$body"
            echo "ERR: HTTP $code — $detail" >&2
            return 1
            ;;
    end
end

function _ethan_status
    set -l base (_ethan_base | string replace -r '/+$' '')
    set -l body (mktemp)
    set -l code (curl -s --max-time 5 "$base/v1/state" (_ethan_auth_flags) \
        -o "$body" -w '%{http_code}' 2>/dev/null)
    set -l rc $status
    set -l fallback '{"mode":"offline","active_goal":null,"running_tasks":0,"modules_active":[]}'

    switch "$code"
        case '2*'
            cat "$body"
            ;;
        case 401 403
            echo "ERR: authentification requise (HTTP $code) — export ETHAN_TOKEN=<jwt>" >&2
            echo "$fallback"
            ;;
        case '*'
            # Un etat inconnu s'affiche « offline », jamais invente. On le dit.
            if test $rc -ne 0 -o -z "$code"
                echo "INFO: API injoignable ($base) — etat affiche offline" >&2
            else
                echo "INFO: HTTP $code sur /v1/state — etat affiche offline" >&2
            end
            echo "$fallback"
            ;;
    end
    rm -f "$body"
end

function _ethan_cli
    if command -q ethan-cli
        echo ethan-cli
    else if command -q ethan
        echo ethan
    else
        return 1
    end
end

function _ethan_cli_or_die
    set -l cli (_ethan_cli)
    or begin
        echo "ethan CLI not found — installez interfaces/cli (binaire « ethan »)" >&2
        return 1
    end
    echo "$cli"
end

function ethan
    set -l cmd $argv[1]; set -e argv[1]
    switch "$cmd"
        case "send" ""
            if test (count $argv) -eq 0
                echo "usage: ethan <message>"
                return 1
            end
            _ethan_api_raw $argv
        case "chat"
            _ethan_cli_or_die | read -l cli; and eval "$cli chat"
        case "status"
            _ethan_status | python3 -c "
import sys, json
s=json.load(sys.stdin)
print(f\"Mode:       {s.get('mode','?')}\")
print(f\"Goal:       {s.get('active_goal') or 'none'}\")
print(f\"Tasks:      {s.get('running_tasks',0)}\")
print(f\"Modules:    {', '.join(s.get('modules_active') or []) or '-'}\")
" 2>/dev/null; or _ethan_status
        case "suggest"
            _ethan_cli_or_die | read -l cli; and eval "$cli suggest $argv"
        case "daemon"
            _ethan_cli_or_die | read -l cli; and eval "$cli daemon $argv"
        case "--help" "-h" "help"
            echo "ETHAN Shell — native command"
            echo "  ethan <message>  Send message (POST \$ETHAN_API/v1/message)"
            echo "  ethan chat       Interactive mode"
            echo "  ethan status     System status (GET \$ETHAN_API/v1/state)"
            echo "  ethan daemon     Background cache"
            echo
            echo "Env: ETHAN_API (défaut http://localhost:8000) · ETHAN_TOKEN (JWT requis)"
        case "*"
            _ethan_api_raw "$cmd $argv"
    end
end