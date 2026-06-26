#!/bin/bash
# ETHAN Uninstallation Script
# Version: 1.0.0
# Usage: sudo ./uninstall.sh [--purge]
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────
MANIFEST_FILE="/var/lib/ethan/.install-manifest.json"
ETHAN_USER="ethan"
ETHAN_GROUP="ethan"
UNINSTALL_LOG="/var/log/ethan/install.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
DIM='\033[2m'
NC='\033[0m'

# ── Helpers ───────────────────────────────────────────────────────────

log_info()  { echo -e "  ${CYAN}→${NC} $1"; }
log_ok()    { echo -e "  ${GREEN}✓${NC} $1"; }
log_warn()  { echo -e "  ${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "  ${RED}✗${NC} $1"; }

die() {
    log_error "$1"
    exit 1
}

log_uninstall() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$UNINSTALL_LOG"
}

check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        die "uninstall.sh must be run as root. Use: sudo ./uninstall.sh"
    fi
}

# ── Stop Services ─────────────────────────────────────────────────────

stop_services() {
    log_info "Stopping ETHAN services..."

    # Stop systemd units
    for unit in ethan-plugins ethan-core ethan-runtime; do
        if systemctl is-active "$unit.service" &>/dev/null; then
            systemctl stop "$unit.service" 2>/dev/null || true
            log_ok "Stopped: $unit"
        fi
    done

    # Stop Docker stack
    if [ -f /usr/local/share/ethan/compose/docker-compose.yml ]; then
        log_info "Stopping Docker stack..."
        docker compose -f /usr/local/share/ethan/compose/docker-compose.yml down -v 2>/dev/null || true
        log_ok "Docker stack stopped"
    fi

    # Kill any remaining ethan processes
    pkill -f "ethan-runtime" 2>/dev/null || true
    pkill -f "ethan-cli" 2>/dev/null || true
    sleep 1
    log_ok "All services stopped"
}

# ── Remove Systemd Units ─────────────────────────────────────────────

remove_systemd() {
    log_info "Removing systemd units..."

    for unit in ethan-runtime ethan-core ethan-plugins; do
        systemctl disable "$unit.service" 2>/dev/null || true
        rm -f "/etc/systemd/system/$unit.service" 2>/dev/null || true
        log_ok "Removed: $unit.service"
    done

    systemctl daemon-reload 2>/dev/null || true
    log_ok "systemd daemon reloaded"
}

# ── Remove Binaries ──────────────────────────────────────────────────

remove_binaries() {
    log_info "Removing binaries..."

    local binaries=(
        "/usr/local/bin/ethan"
        "/usr/local/bin/ethan-cli"
        "/usr/local/bin/ethan-runtime"
        "$HOME/.local/bin/ethan"
        "$HOME/.local/bin/ethan-cli"
    )

    for bin in "${binaries[@]}"; do
        if [ -f "$bin" ]; then
            rm -f "$bin"
            log_ok "Removed: $bin"
        fi
    done
}

# ── Remove Configs ───────────────────────────────────────────────────

remove_configs() {
    log_info "Removing configuration files..."

    if [ -d /etc/ethan ]; then
        rm -rf /etc/ethan
        log_ok "Removed: /etc/ethan"
    fi

    if [ -d /usr/local/share/ethan ]; then
        rm -rf /usr/local/share/ethan
        log_ok "Removed: /usr/local/share/ethan"
    fi
}

# ── Remove Shell Integration ─────────────────────────────────────────

remove_shell() {
    log_info "Removing shell integration..."

    local profiles=(
        "/etc/bash.bashrc"
        "/etc/zsh/zshrc"
        "/etc/skel/.bashrc"
        "/etc/skel/.zshrc"
    )

    for profile in "${profiles[@]}"; do
        if [ -f "$profile" ]; then
            sed -i '/ETHAN Shell Integration/d; /ETHAN_HOME/d; /ethan\/shell\/ethan\.sh/d; /ethan\/shell\/completion/d' "$profile" 2>/dev/null || true
            log_ok "Cleaned: $profile"
        fi
    done
}

# ── Remove Docker Images (optional) ──────────────────────────────────

remove_docker_images() {
    log_info "Removing ETHAN Docker images..."

    # Read images from manifest
    if [ -f "$MANIFEST_FILE" ]; then
        local images
        images=$(python3 -c "
import json
d = json.load(open('$MANIFEST_FILE'))
for img in d.get('docker_images', []):
    print(img)
" 2>/dev/null || true)

        if [ -n "$images" ]; then
            echo "$images" | while IFS= read -r img; do
                if [ -n "$img" ]; then
                    docker rmi "$img" 2>/dev/null || true
                    log_ok "Removed image: $img"
                fi
            done
        fi
    fi

    # Also remove by label
    docker images --filter "label=com.ethan.app=core" -q 2>/dev/null | while IFS= read -r id; do
        [ -n "$id" ] && docker rmi "$id" 2>/dev/null || true
    done

    log_ok "Docker images cleaned"
}

# ── Remove System User ───────────────────────────────────────────────

remove_user() {
    log_info "Removing system user..."

    if id "$ETHAN_USER" &>/dev/null; then
        userdel "$ETHAN_USER" 2>/dev/null || log_warn "Could not remove user (may have running processes)"
        log_ok "Removed user: $ETHAN_USER"
    fi

    if getent group "$ETHAN_GROUP" &>/dev/null; then
        groupdel "$ETHAN_GROUP" 2>/dev/null || true
        log_ok "Removed group: $ETHAN_GROUP"
    fi
}

# ── Remove Data Directories ──────────────────────────────────────────

remove_data() {
    log_info "Removing data directories..."

    # Remove everything except user data
    for dir in /var/cache/ethan /var/log/ethan /var/run/ethan; do
        rm -rf "$dir" 2>/dev/null || true
        log_ok "Removed: $dir"
    done

    # Remove manifest
    rm -f "$MANIFEST_FILE" 2>/dev/null || true
    rm -rf "/var/lib/ethan/.rollback" 2>/dev/null || true

    log_ok "System directories cleaned"
}

remove_data_purge() {
    log_info "Purging ALL data..."

    rm -rf /var/lib/ethan 2>/dev/null || true
    log_ok "Removed: /var/lib/ethan (all data purged)"
}

# ── Main ─────────────────────────────────────────────────────────────

main() {
    local purge=false
    local force=false

    # Parse args
    for arg in "$@"; do
        case "$arg" in
            --purge|-p) purge=true ;;
            --force|-f) force=true ;;
            --help|-h)
                echo "ETHAN Uninstall"
                echo ""
                echo "Usage: sudo ./uninstall.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --purge, -p     Remove ALL data including user files"
                echo "  --force, -f     Skip confirmation prompts"
                echo "  --help, -h      Show this help"
                echo ""
                echo "Default: removes system files, preserves /var/lib/ethan/data/"
                exit 0
                ;;
        esac
    done

    echo ""
    echo -e "${YELLOW}◆${NC}  ETHAN Uninstallation"
    echo ""

    check_root

    # Confirmation
    if [ "$force" = false ]; then
        if [ "$purge" = true ]; then
            echo -e "  ${RED}⚠ WARNING: --purge will DELETE ALL user data${NC}"
        fi
        echo -n "  Uninstall ETHAN? [y/N] "
        read -r response
        case "$response" in
            [yY]|[yY][eE][sS]) ;;
            *) die "Uninstall cancelled" ;;
        esac
    fi

    log_uninstall "=== ETHAN Uninstall started (purge=$purge) ==="

    # Execute steps
    stop_services
    remove_systemd
    remove_shell
    remove_binaries
    remove_configs
    remove_docker_images
    remove_user
    remove_data

    if [ "$purge" = true ]; then
        remove_data_purge
    else
        log_info "User data preserved: /var/lib/ethan/data/"
    fi

    # Ensure log directory exists for final log entry
    mkdir -p /var/log/ethan 2>/dev/null || true

    echo ""
    echo -e "${GREEN}◆${NC}  ETHAN uninstalled"
    if [ "$purge" = false ]; then
        echo -e "  ${CYAN}→${NC} User data preserved at /var/lib/ethan/data/"
        echo -e "  ${CYAN}→${NC} Run with --purge to remove all data"
    fi
    echo ""

    log_uninstall "=== ETHAN Uninstall complete (purge=$purge) ==="
}

main "$@"