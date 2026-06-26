#!/bin/bash
# ETHAN Launcher — orchestrates Runtime bootstrap, then attaches to CLI
# No AI logic. No business logic. Pure orchestration.

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────
RUNTIME_PID="/run/ethan/runtime.pid"
RUNTIME_SOCK="/run/ethan/runtime.sock"
RUNTIME_BIN="/usr/local/bin/ethan-runtime"
CLI_BIN="/usr/local/bin/ethan-cli"
TIMEOUT=30  # seconds
POLL_INTERVAL=0.5  # seconds

# ── Helper Functions ──────────────────────────────────────────────────

log_info() {
    echo "  $1" >&2
}

log_error() {
    echo "  ✗ $1" >&2
}

log_success() {
    echo "  ✓ $1" >&2
}

# Check if Runtime is running
is_runtime_running() {
    # Check PID file exists
    if [ ! -f "$RUNTIME_PID" ]; then
        return 1
    fi

    # Check process exists
    local pid
    pid=$(cat "$RUNTIME_PID" 2>/dev/null || echo "")
    if [ -z "$pid" ]; then
        return 1
    fi

    if ! kill -0 "$pid" 2>/dev/null; then
        return 1
    fi

    # Check socket exists
    if [ ! -S "$RUNTIME_SOCK" ]; then
        return 1
    fi

    return 0
}

# Start Runtime
start_runtime() {
    log_info "Starting Runtime..."

    # Method 1: systemd user service (preferred)
    if command -v systemctl >/dev/null 2>&1; then
        if systemctl --user is-enabled ethan-runtime >/dev/null 2>&1; then
            systemctl --user start ethan-runtime
            sleep 2
            if is_runtime_running; then
                log_success "Runtime started (systemd)"
                return 0
            fi
        fi
    fi

    # Method 2: Direct binary (fallback)
    if [ -x "$RUNTIME_BIN" ]; then
        nohup "$RUNTIME_BIN" > /var/log/ethan/runtime.log 2>&1 &
        local pid=$!
        echo "$pid" > "$RUNTIME_PID"
        sleep 1
        if is_runtime_running; then
            log_success "Runtime started (direct)"
            return 0
        fi
    fi

    return 1
}

# Wait for Runtime to be ready
wait_for_runtime() {
    local elapsed=0
    log_info "Waiting for Runtime..."

    while [ "$elapsed" -lt "$TIMEOUT" ]; do
        if is_runtime_running; then
            log_success "Runtime ready"
            return 0
        fi

        sleep "$POLL_INTERVAL"
        elapsed=$(echo "$elapsed + $POLL_INTERVAL" | bc)
    done

    return 1
}

# ── Main Logic ────────────────────────────────────────────────────────

# Handle special flags
case "${1:-}" in
    --version|-v)
        echo "ethan 1.0.0"
        exit 0
        ;;
    --help|-h)
        echo "ETHAN — Cognitive Runtime"
        echo ""
        echo "Usage: ethan [OPTIONS] [COMMAND]"
        echo ""
        echo "Options:"
        echo "  --version, -v    Show version"
        echo "  --help, -h       Show this help"
        echo "  --no-runtime     Skip Runtime auto-start"
        echo ""
        echo "Commands:"
        echo "  chat             Interactive chat (default)"
        echo "  run <task>       One-shot task execution"
        echo "  status           Show system status"
        echo "  logs [service]   Show logs"
        echo "  config <action>  Manage configuration"
        echo "  help             Show command help"
        echo ""
        echo "Documentation: https://www.github.io/Ethan/"
        exit 0
        ;;
    --no-runtime)
        # Skip Runtime check, go directly to CLI
        shift
        exec "$CLI_BIN" "$@"
        ;;
esac

# Check if Runtime is running
if ! is_runtime_running; then
    # Try to start Runtime
    if ! start_runtime; then
        log_error "Failed to start Runtime"
        log_error "Try: systemctl --user start ethan-runtime"
        exit 1
    fi

    # Wait for Runtime to be ready
    if ! wait_for_runtime; then
        log_error "Runtime did not become ready in time"
        log_error "Check logs: journalctl --user -u ethan-runtime -n 50"
        exit 1
    fi
fi

# Execute CLI, forwarding all arguments
export ETHAN_SOURCE_DIR="${ETHAN_SOURCE_DIR:-/home/fatsio/AI/Ethan}"
export PYTHONPATH="$ETHAN_SOURCE_DIR:$PYTHONPATH"
exec "$CLI_BIN" "$@"
