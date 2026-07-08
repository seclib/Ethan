#!/usr/bin/env bash
# ETHAN clean systemd installer.

set -euo pipefail

ETHAN_USER="ethan"
ETHAN_GROUP="ethan"
STATE_FILE="/var/lib/ethan/install-state.env"
SYSTEMD_DIR="/etc/systemd/system"
SERVICES=(ethan-runtime ethan-core ethan-plugins)

log() { printf '==> %s\n' "$*"; }
ok() { printf '  OK %s\n' "$*"; }
warn() { printf '  WARN %s\n' "$*" >&2; }
fail() { printf '  ERROR %s\n' "$*" >&2; exit 1; }

require_root() {
    [ "$(id -u)" -eq 0 ] || fail "Run as root: sudo install/install.sh"
}

detect_root() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    ETHAN_ROOT="$(cd "$script_dir/.." && pwd)"

    [ -d "$ETHAN_ROOT/core" ] || fail "Missing core/ in $ETHAN_ROOT"
    [ -d "$ETHAN_ROOT/runtime" ] || fail "Missing runtime/ in $ETHAN_ROOT"
    [ -d "$ETHAN_ROOT/plugins" ] || fail "Missing plugins/ in $ETHAN_ROOT"
    [ -d "$ETHAN_ROOT/interfaces" ] || fail "Missing interfaces/ in $ETHAN_ROOT"
    [ -d "$ETHAN_ROOT/infrastructure" ] || fail "Missing infrastructure/ in $ETHAN_ROOT"
    [ -d "$ETHAN_ROOT/install/systemd" ] || fail "Missing install/systemd/ in $ETHAN_ROOT"
}

ensure_user() {
    CREATED_GROUP=0
    CREATED_USER=0

    if ! getent group "$ETHAN_GROUP" >/dev/null; then
        groupadd --system "$ETHAN_GROUP"
        CREATED_GROUP=1
        ok "Created group $ETHAN_GROUP"
    else
        ok "Group $ETHAN_GROUP exists"
    fi

    if ! id "$ETHAN_USER" >/dev/null 2>&1; then
        useradd --system \
            --gid "$ETHAN_GROUP" \
            --home-dir /var/lib/ethan \
            --shell /usr/sbin/nologin \
            "$ETHAN_USER"
        CREATED_USER=1
        ok "Created user $ETHAN_USER"
    else
        ok "User $ETHAN_USER exists"
    fi

    if getent group docker >/dev/null; then
        usermod -aG docker "$ETHAN_USER" || true
    fi
}

ensure_directories() {
    install -d -o "$ETHAN_USER" -g "$ETHAN_GROUP" -m 0750 /var/lib/ethan
    install -d -o "$ETHAN_USER" -g "$ETHAN_GROUP" -m 0750 /var/log/ethan
    install -d -o "$ETHAN_USER" -g "$ETHAN_GROUP" -m 0750 /var/cache/ethan
    install -d -o root -g "$ETHAN_GROUP" -m 0770 /run/ethan
    ok "Created runtime directories"
}

build_runtime() {
    command -v go >/dev/null 2>&1 || fail "Go is required to build ethan-runtime"

    log "Building ethan-runtime"
    (
        cd "$ETHAN_ROOT/runtime"
        go build -o /tmp/ethan-runtime ./cmd/ethan-runtime
    )
    install -o root -g root -m 0755 /tmp/ethan-runtime /usr/local/bin/ethan-runtime
    rm -f /tmp/ethan-runtime
    ok "Installed /usr/local/bin/ethan-runtime"
}

install_wrappers() {
    log "Installing command wrappers"

    cat >/usr/local/bin/ethan-core <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$ETHAN_ROOT"
export PYTHONPATH="$ETHAN_ROOT:\${PYTHONPATH:-}"
export PYTHONDONTWRITEBYTECODE=1
exec /usr/bin/python3 -m core.main
EOF
    chmod 0755 /usr/local/bin/ethan-core

    cat >/usr/local/bin/ethan-plugins <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$ETHAN_ROOT"
export PYTHONPATH="$ETHAN_ROOT:\${PYTHONPATH:-}"
export PYTHONDONTWRITEBYTECODE=1
exec /usr/bin/python3 -m plugins.sandbox.runtime
EOF
    chmod 0755 /usr/local/bin/ethan-plugins

    cat >/usr/local/bin/ethan-cli <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$ETHAN_ROOT"
export PYTHONPATH="$ETHAN_ROOT:\${PYTHONPATH:-}"
export PYTHONDONTWRITEBYTECODE=1
exec /usr/bin/python3 "$ETHAN_ROOT/interfaces/cli/main.py" "\$@"
EOF
    chmod 0755 /usr/local/bin/ethan-cli

    cat >/usr/local/bin/ethan <<EOF
#!/usr/bin/env bash
set -euo pipefail
export ETHAN_SOURCE_DIR="\${ETHAN_SOURCE_DIR:-$ETHAN_ROOT}"
export PYTHONPATH="\$ETHAN_SOURCE_DIR:\${PYTHONPATH:-}"
export PYTHONDONTWRITEBYTECODE=1
if [ "\${1:-}" = "--no-runtime" ]; then
    shift
    exec /usr/local/bin/ethan-cli "\$@"
fi
if [ ! -S /run/ethan/runtime.sock ]; then
    systemctl start ethan-runtime.service
fi
exec /usr/local/bin/ethan-cli "\$@"
EOF
    chmod 0755 /usr/local/bin/ethan

    ok "Installed /usr/local/bin/ethan* wrappers"
}

install_systemd_units() {
    log "Installing systemd units from $ETHAN_ROOT/install/systemd"

    for service in "${SERVICES[@]}"; do
        local src="$ETHAN_ROOT/install/systemd/$service.service"
        local dst="$SYSTEMD_DIR/$service.service"
        [ -f "$src" ] || fail "Missing unit source: $src"
        sed "s|@ETHAN_ROOT@|$ETHAN_ROOT|g" "$src" >"$dst"
        chown root:root "$dst"
        chmod 0644 "$dst"
        ok "Installed $dst"
    done
}

write_state() {
    cat >"$STATE_FILE" <<EOF
ETHAN_ROOT='$ETHAN_ROOT'
ETHAN_CREATED_USER='$CREATED_USER'
ETHAN_CREATED_GROUP='$CREATED_GROUP'
ETHAN_INSTALLED_AT='$(date -u +%Y-%m-%dT%H:%M:%SZ)'
ETHAN_GENERATED_FILES='/usr/local/bin/ethan /usr/local/bin/ethan-cli /usr/local/bin/ethan-core /usr/local/bin/ethan-plugins /usr/local/bin/ethan-runtime /etc/systemd/system/ethan-runtime.service /etc/systemd/system/ethan-core.service /etc/systemd/system/ethan-plugins.service'
EOF
    chown "$ETHAN_USER:$ETHAN_GROUP" "$STATE_FILE"
    chmod 0640 "$STATE_FILE"
}

enable_and_start() {
    log "Reloading systemd"
    systemctl daemon-reload

    log "Enabling services"
    systemctl enable ethan-runtime.service ethan-core.service ethan-plugins.service

    log "Starting ETHAN"
    systemctl restart ethan-runtime.service
    systemctl restart ethan-core.service
    systemctl restart ethan-plugins.service
}

final_test() {
    log "Running final test"

    for service in "${SERVICES[@]}"; do
        systemctl is-active --quiet "$service.service" || {
            systemctl status "$service.service" --no-pager || true
            fail "$service.service is not active"
        }
        ok "$service.service active"
    done

    [ -S /run/ethan/runtime.sock ] || fail "Missing /run/ethan/runtime.sock"
    ok "Runtime socket exists"

    sudo -u "$ETHAN_USER" env PYTHONPATH="$ETHAN_ROOT" /usr/bin/python3 - <<'PY'
import json
import socket

req = {"type": "services.status", "session_id": "install-test", "payload": {}}
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.settimeout(5)
sock.connect("/run/ethan/runtime.sock")
sock.sendall((json.dumps(req) + "\n").encode())
resp = json.loads(sock.recv(65536).decode())
sock.close()
if resp.get("type") != "services.status.result":
    raise SystemExit(f"unexpected runtime response: {resp}")
PY
    ok "Runtime socket responds for user $ETHAN_USER"
}

main() {
    require_root
    detect_root

    log "Installing ETHAN from $ETHAN_ROOT"
    ensure_user
    ensure_directories
    build_runtime
    install_wrappers
    install_systemd_units
    write_state
    enable_and_start
    final_test

    ok "ETHAN installation complete"
}

main "$@"
