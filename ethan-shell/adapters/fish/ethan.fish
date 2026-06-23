# ETHAN Shell Integration Layer — fish adapter
# Idempotent.
if set -q ETHAN_SHELL_LOADED
    exit
end
set -gx ETHAN_SHELL_LOADED 1

function _ethan_api
    set -l base "$ETHAN_API"
    if test -z "$base"; set base "http://localhost:8000"; end
    curl -s --max-time 10 -X POST "$base/message" \
        -H "Content-Type: application/json" \
        -d "{\"content\":\"$argv\"}" 2>/dev/null
end

function _ethan_send
    set -l out (_ethan_api $argv)
    if test -z "$out"
        echo "ERR: API unreachable" >&2
        return 1
    end
    echo "$out"
end

function _ethan_status
    set -l base "$ETHAN_API"
    if test -z "$base"; set base "http://localhost:8000"; end
    curl -s --max-time 5 "$base/state" 2>/dev/null \
        || echo '{"mode":"offline","active_goal":"none","running_tasks":0}'
end

function ethan
    set -l cmd $argv[1]; set -e argv[1]
    switch "$cmd"
        case "send" ""
            if test (count $argv) -eq 0
                echo "usage: ethan <message>"
                return 1
            end
            _ethan_send $argv
        case "chat"
            if command -v ethan-cli >/dev/null 2>&1
                ethan-cli chat
            else
                echo "ethan-cli not found"
            end
        case "status"
            _ethan_status | python3 -c "
import sys, json
s=json.load(sys.stdin)
print(f\"Mode:       {s.get('mode','?')}\")
print(f\"Goal:       {s.get('active_goal','none')}\")
print(f\"Tasks:      {s.get('running_tasks',0)}\")
" 2>/dev/null; or _ethan_status
        case "suggest"
            if command -v ethan-cli >/dev/null 2>&1
                ethan-cli suggest $argv
            else
                echo "ethan-cli not found"
            end
        case "daemon"
            if command -v ethan-cli >/dev/null 2>&1
                ethan-cli daemon $argv
            else
                echo "ethan-cli not found"
            end
        case "--help" "-h" "help"
            echo "ETHAN Shell — native command"
            echo "  ethan <message>  Send message"
            echo "  ethan chat       Interactive mode"
            echo "  ethan status     System status"
            echo "  ethan daemon     Background cache"
        case "*"
            _ethan_send "$cmd $argv"
    end
end