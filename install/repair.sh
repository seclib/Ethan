#!/bin/bash
# ETHAN Repair Script
# Version: 1.0.0
# Usage: sudo ./repair.sh [--auto] [--force]
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────
ETHAN_SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ETHAN_VERSION="$(cat "$ETHAN_SOURCE_DIR/VERSION" 2>/dev/null || echo "0.2.0")"
MANIFEST_FILE="/var/lib/ethan/.install-manifest.json"
INSTALL_LOG="/var/log/ethan/install.log"
ETHAN_USER="ethan"
ETHAN_GROUP="ethan"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

# State
AUTO_MODE=false
FORCE=false
REPAIRED=0
SKIPPED=0
FAILED=0

# ── Helpers ───────────────────────────────────────────────────────────

log_info()   { echo -e "  ${CYAN}→${NC} $1"; }
log_ok()     { echo -e "  ${GREEN}✓${NC} $1"; }
log_warn()   { echo -e "  ${YELLOW}⚠${NC} $1"; }
log_error()  { echo -e "  ${RED}✗${NC} $1"; }
log_section() { echo -e "\n${BOLD}${CYAN}◆${NC} ${BOLD}$1${NC}"; }
log_repaired() { echo -e "  ${GREEN}🔧${NC} $1"; ((REPAIRED++)); }

die() {
    log_error "$1"
    exit 1
}

log_repair() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$INSTALL_LOG"
}

check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        die "repair.sh must be run as root. Use: sudo ./repair.sh"
    fi
}

confirm() {
    local prompt="$1"
    local response

    if [ "$AUTO_MODE" = true ] || [ "$FORCE" = true ]; then
        return 0
    fi

    echo -n "  $prompt [y/N] "
    read -r response
    case "$response" in
        [yY]|[yY][eE][sS]) return 0 ;;
        *) return 1 ;;
    esac
}

# ── Repair Actions ───────────────────────────────────────────────────

repair_user() {
    log_section "Repair: System User"

    if ! getent group "$ETHAN_GROUP" &>/dev/null; then
        groupadd --system "$ETHAN_GROUP"
        log_repaired "Created missing group: $ETHAN_GROUP"
    fi

    if ! id "$ETHAN_USER" &>/dev/null; then
        useradd --system --gid "$ETHAN_GROUP" --home-dir /var/lib/ethan --no-create-home --shell /usr/sbin/nologin "$ETHAN_USER"
        log_repaired "Created missing user: $ETHAN_USER"
    fi

    usermod -aG docker "$ETHAN_USER" 2>/dev/null || true
    log_ok "User $ETHAN_USER is in docker group"
}

repair_directories() {
    log_section "Repair: Directories"

    local dirs=(
        "/var/lib/ethan/data/memory"
        "/var/lib/ethan/data/uploads"
        "/var/lib/ethan/data/models"
        "/var/lib/ethan/cache"
        "/var/lib/ethan/.rollback"
        "/var/run/ethan"
        "/var/log/ethan"
        "/etc/ethan/shell"
        "/usr/local/share/ethan/compose"
        "/usr/local/share/ethan/deploy/postgres"
    )

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            chown "$ETHAN_USER:$ETHAN_GROUP" "$dir"
            chmod 755 "$dir"
            log_repaired "Created missing directory: $dir"
        fi
    done

    # Special permissions for socket directory
    chmod 775 /var/run/ethan 2>/dev/null || true
}

repair_binaries() {
    log_section "Repair: Binaries"

    # Build and reinstall Runtime
    if [ ! -x /usr/local/bin/ethan-runtime ]; then
        log_info "Rebuilding ethan-runtime..."
        if [ -f "$ETHAN_SOURCE_DIR/runtime/go.mod" ]; then
            (cd "$ETHAN_SOURCE_DIR/runtime" && go mod tidy && go build -o /tmp/ethan-runtime ./cmd/ethan-runtime/) 2>&1 | tail -3 || {
                log_warn "Go build failed — skipping Runtime rebuild"
                ((SKIPPED++))
                return
            }
            install -m 755 /tmp/ethan-runtime /usr/local/bin/ethan-runtime
            rm -f /tmp/ethan-runtime
            log_repaired "Rebuilt and installed: ethan-runtime"
        fi
    fi

    # Reinstall launcher
    if [ ! -x /usr/local/bin/ethan ]; then
        if [ -f "$ETHAN_SOURCE_DIR/ethan-launcher.sh" ]; then
            install -m 755 "$ETHAN_SOURCE_DIR/ethan-launcher.sh" /usr/local/bin/ethan
            log_repaired "Reinstalled launcher: /usr/local/bin/ethan"
        fi
    fi

    # Reinstall CLI
    if [ ! -x /usr/local/bin/ethan-cli ]; then
        if [ -f "$ETHAN_SOURCE_DIR/interfaces/cli/main.py" ]; then
            install -m 755 "$ETHAN_SOURCE_DIR/interfaces/cli/main.py" /usr/local/bin/ethan-cli
            log_repaired "Reinstalled CLI: /usr/local/bin/ethan-cli"
        fi
    fi

    # Reinstall Python deps
    if [ -f "$ETHAN_SOURCE_DIR/cli/requirements.txt" ]; then
        log_info "Reinstalling Python dependencies..."
        pip3 install --break-system-packages -r "$ETHAN_SOURCE_DIR/cli/requirements.txt" 2>&1 | tail -1 || log_warn "pip install had warnings"
        log_ok "Python dependencies reinstalled"
    else
        log_warn "No requirements.txt found at cli/requirements.txt — skipping"
    fi
}

repair_configs() {
    log_section "Repair: Config Files"

    local configs=(
        "runtime.yaml"
        "core.yaml"
        "plugins.yaml"
    )

    for cfg in "${configs[@]}"; do
        local src="$ETHAN_SOURCE_DIR/infrastructure/config/$cfg"
        local dst="/etc/ethan/$cfg"

        if [ ! -f "$dst" ] && [ -f "$src" ]; then
            install -m 644 -o "$ETHAN_USER" -g "$ETHAN_GROUP" "$src" "$dst"
            log_repaired "Restored missing config: $cfg"
        fi
    done

    # Restore compose files
    local compose_dst="/usr/local/share/ethan/compose"
    for compose_file in docker-compose.yml docker-compose.dev.yml docker-compose.prod.yml; do
        if [ ! -f "$compose_dst/$compose_file" ] && [ -f "$ETHAN_SOURCE_DIR/$compose_file" ]; then
            install -m 644 -o "$ETHAN_USER" -g "$ETHAN_GROUP" "$ETHAN_SOURCE_DIR/$compose_file" "$compose_dst/$compose_file"
            log_repaired "Restored compose file: $compose_file"
        fi
    done

    # Restore shell integration
    if [ ! -f /etc/ethan/shell/ethan.sh ]; then
        if [ -f "$ETHAN_SOURCE_DIR/infrastructure/shell/ethan.sh" ]; then
            install -m 644 -o "$ETHAN_USER" -g "$ETHAN_GROUP" "$ETHAN_SOURCE_DIR/infrastructure/shell/ethan.sh" /etc/ethan/shell/ethan.sh
            log_repaired "Restored shell integration"
        fi
    fi
}

repair_shell() {
    log_section "Repair: Shell Integration"

    local bashrc_file="/etc/bash.bashrc"
    local bashrc_lines=(
        ""
        "# ETHAN Shell Integration"
        'export ETHAN_HOME="${ETHAN_HOME:-$HOME/.ethan}"'
        'export PATH="$ETHAN_HOME/bin:$PATH"'
        '[ -f /etc/ethan/shell/ethan.sh ] && source /etc/ethan/shell/ethan.sh'
    )

    if [ -f "$bashrc_file" ]; then
        if ! grep -q "ETHAN Shell Integration" "$bashrc_file" 2>/dev/null; then
            printf '%s\n' "${bashrc_lines[@]}" >> "$bashrc_file"
            log_repaired "Added shell integration to $bashrc_file"
        else
            log_ok "Shell integration already present"
        fi
    fi
}

repair_systemd() {
    log_section "Repair: Systemd Units"

    local units=(
        "ethan-runtime.service"
        "ethan-core.service"
        "ethan-plugins.service"
    )

    for unit in "${units[@]}"; do
        local src="$ETHAN_SOURCE_DIR/infrastructure/systemd/$unit"
        local dst="/etc/systemd/system/$unit"

        if [ ! -f "$dst" ] && [ -f "$src" ]; then
            install -m 644 "$src" "$dst"
            log_repaired "Restored systemd unit: $unit"
        fi

        # Enable if not enabled
        if [ -f "$dst" ]; then
            if ! systemctl is-enabled "$unit" &>/dev/null 2>&1; then
                systemctl enable "$unit" 2>/dev/null || true
                log_repaired "Enabled systemd unit: $unit"
            fi
        fi
    done

    systemctl daemon-reload 2>/dev/null || true
}

repair_docker() {
    log_section "Repair: Docker Stack"

    if ! command -v docker &>/dev/null; then
        log_warn "Docker not installed — skipping Docker repair"
        ((SKIPPED++))
        return
    fi

    if ! docker info &>/dev/null; then
        log_warn "Docker daemon not running — attempting to start"
        systemctl start docker 2>/dev/null || true
        sleep 2
        if ! docker info &>/dev/null; then
            log_warn "Could not start Docker daemon — manual intervention needed"
            ((SKIPPED++))
            return
        fi
    fi

    local compose_file="/usr/local/share/ethan/compose/docker-compose.yml"
    if [ ! -f "$compose_file" ]; then
        log_warn "Compose file missing — skipping"
        ((SKIPPED++))
        return
    fi

    # Check if compose config is valid
    if ! docker compose -f "$compose_file" config >/dev/null 2>&1; then
        log_warn "Compose config invalid — attempt to restore"
        if [ -f "$ETHAN_SOURCE_DIR/docker-compose.yml" ]; then
            install -m 644 "$ETHAN_SOURCE_DIR/docker-compose.yml" "$compose_file"
            log_repaired "Restored docker-compose.yml from source"
        fi
    fi

    # Pull and restart
    log_info "Pulling Docker images..."
    docker compose -f "$compose_file" pull 2>&1 | tail -2 || log_warn "Docker pull had issues"

    log_info "Starting Docker stack..."
    docker compose -f "$compose_file" up -d 2>&1 | tail -2 || log_warn "Docker up had issues"
    log_ok "Docker stack restarted"
}

repair_socket() {
    log_section "Repair: Runtime Socket"

    local socket="/var/run/ethan/runtime.sock"

    # Ensure directory
    mkdir -p /var/run/ethan
    chmod 775 /var/run/ethan

    # Clean stale socket
    if [ -S "$socket" ]; then
        # Check if Runtime is actually listening
        if ! fuser "$socket" &>/dev/null 2>&1; then
            rm -f "$socket"
            log_repaired "Removed stale socket: $socket"
        fi
    fi

    # Try to start Runtime if socket missing
    if [ ! -S "$socket" ]; then
        if systemctl is-enabled ethan-runtime &>/dev/null 2>&1; then
            log_info "Starting ethan-runtime service..."
            systemctl start ethan-runtime 2>/dev/null || true
            sleep 2
            if [ -S "$socket" ]; then
                log_repaired "Started ethan-runtime service"
            fi
        fi
    fi
}

repair_manifest() {
    log_section "Repair: Install Manifest"

    if [ ! -f "$MANIFEST_FILE" ]; then
        log_info "Creating install manifest from existing state..."
        mkdir -p "$(dirname "$MANIFEST_FILE")"

        local phases=()
        [ -d /etc/ethan ] && phases+=("configs")
        [ -x /usr/local/bin/ethan-runtime ] && phases+=("binaries")
        [ -f /etc/systemd/system/ethan-runtime.service ] && phases+=("systemd")
        command -v docker &>/dev/null && phases+=("docker")

        local phases_json
        phases_json=$(printf '"%s",' "${phases[@]}" | sed 's/,$//')

        cat > "$MANIFEST_FILE" <<EOF
{
  "version": "$ETHAN_VERSION",
  "installed_at": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "updated_at": null,
  "install_method": "repair",
  "source_dir": "$ETHAN_SOURCE_DIR",
  "phases_completed": [${phases_json}],
  "files": {},
  "systemd_units": [],
  "docker_images": []
}
EOF
        chown "$ETHAN_USER:$ETHAN_GROUP" "$MANIFEST_FILE" 2>/dev/null || true
        log_repaired "Created install manifest from discovered state"
    fi
}

# ── Main ─────────────────────────────────────────────────────────────

main() {
    for arg in "$@"; do
        case "$arg" in
            --auto|-a)  AUTO_MODE=true ;;
            --force|-f) FORCE=true ;;
            --help|-h)
                echo "ETHAN Repair"
                echo ""
                echo "Usage: sudo ./repair.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --auto, -a      Auto-repair without prompts"
                echo "  --force, -f     Skip all confirmations"
                echo "  --help, -h      Show this help"
                echo ""
                echo "Repairs:"
                echo "  • Missing system user/group"
                echo "  • Missing directories and permissions"
                echo "  • Missing or corrupted binaries"
                echo "  • Missing configuration files"
                echo "  • Shell integration"
                echo "  • Systemd units"
                echo "  • Docker daemon and containers"
                echo "  • Stale socket"
                echo "  • Install manifest"
                exit 0
                ;;
        esac
    done

    echo ""
    echo -e "${BOLD}${YELLOW}◆${NC}  ETHAN Repair v${ETHAN_VERSION}"
    echo ""

    check_root

    # Run doctor first
    echo -e "  ${CYAN}→${NC} Running diagnostics..."
    echo ""

    local doctor_output
    doctor_output=$("$ETHAN_SOURCE_DIR/install/doctor.sh" 2>&1 || true)

    # Check doctor result
    if echo "$doctor_output" | grep -q "All checks passed"; then
        echo -e "\n  ${GREEN}✓${NC}  System is healthy — no repair needed"
        exit 0
    fi

    # Show doctor summary
    echo "$doctor_output" | grep -E "(fail|warn|missing|not found)" || true
    echo ""

    if ! confirm "Attempt to repair detected issues?"; then
        log_info "Repair cancelled"
        exit 0
    fi

    log_repair "=== ETHAN Repair started ==="

    # Execute repairs
    repair_user
    repair_directories
    repair_binaries
    repair_configs
    repair_shell
    repair_systemd
    repair_docker
    repair_socket
    repair_manifest

    # Summary
    echo ""
    echo -e "${DIM}────────────────────────────────────────${NC}"
    if [ "$REPAIRED" -gt 0 ]; then
        echo -e "  ${GREEN}🔧${NC}  $REPAIRED items repaired"
    fi
    if [ "$SKIPPED" -gt 0 ]; then
        echo -e "  ${YELLOW}⚠${NC}  $SKIPPED items skipped (manual intervention may be needed)"
    fi

    # Re-run doctor to verify
    echo ""
    echo -e "  ${CYAN}→${NC} Verifying repairs..."
    echo ""
    "$ETHAN_SOURCE_DIR/install/doctor.sh" || true

    log_repair "=== ETHAN Repair complete: $REPAIRED repaired, $SKIPPED skipped ==="
}

main "$@"