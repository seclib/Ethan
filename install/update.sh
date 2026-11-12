#!/bin/bash
# ETHAN Update Script
# Version: 1.0.0
# Usage: sudo ./update.sh
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────
ETHAN_SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ETHAN_VERSION="$(cat "$ETHAN_SOURCE_DIR/VERSION" 2>/dev/null || echo "0.2.0")"
MANIFEST_FILE="/var/lib/ethan/.install-manifest.json"
ROLLBACK_DIR="/var/lib/ethan/.rollback"
INSTALL_LOG="/var/log/ethan/install.log"
ETHAN_USER="ethan"
ETHAN_GROUP="ethan"

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
log_step()  { echo -e "\n${DIM}──${NC} ${GREEN}$1${NC}"; }

die() {
    log_error "$1"
    exit 1
}

log_update() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$INSTALL_LOG"
}

check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        die "update.sh must be run as root. Use: sudo ./update.sh"
    fi
}

# ── Snapshot ──────────────────────────────────────────────────────────

create_snapshot() {
    log_step "Creating pre-update snapshot"

    local timestamp
    timestamp=$(date '+%Y%m%d_%H%M%S')
    local snapshot_dir="$ROLLBACK_DIR/$timestamp"

    mkdir -p "$snapshot_dir"

    # Snapshot binaries
    for bin in /usr/local/bin/ethan /usr/local/bin/ethan-cli /usr/local/bin/ethan-runtime; do
        if [ -f "$bin" ]; then
            cp "$bin" "$snapshot_dir/"
            log_ok "Snapshot: $bin"
        fi
    done

    # Snapshot configs
    if [ -d /etc/ethan ]; then
        cp -r /etc/ethan "$snapshot_dir/configs"
        log_ok "Snapshot: /etc/ethan"
    fi

    # Snapshot systemd units
    mkdir -p "$snapshot_dir/systemd"
    for unit in ethan-runtime.service ethan-core.service ethan-plugins.service; do
        if [ -f "/etc/systemd/system/$unit" ]; then
            cp "/etc/systemd/system/$unit" "$snapshot_dir/systemd/"
        fi
    done
    log_ok "Snapshot: systemd units"

    # Snapshot compose files
    if [ -d /usr/local/share/ethan/compose ]; then
        cp -r /usr/local/share/ethan/compose "$snapshot_dir/compose"
        log_ok "Snapshot: compose files"
    fi

    # Save manifest
    if [ -f "$MANIFEST_FILE" ]; then
        cp "$MANIFEST_FILE" "$snapshot_dir/manifest.json"
    fi

    # Save version metadata
    cat > "$snapshot_dir/meta" <<EOF
version_before=$(python3 -c "import json; d=json.load(open('$MANIFEST_FILE')); print(d.get('version','unknown'))" 2>/dev/null || echo "unknown")
version_after=$ETHAN_VERSION
timestamp=$timestamp
source_dir=$ETHAN_SOURCE_DIR
EOF

    echo "$timestamp" > "$ROLLBACK_DIR/latest"
    log_ok "Snapshot saved: $timestamp"
    log_update "Snapshot created: $timestamp"
}

# ── Rollback ──────────────────────────────────────────────────────────

perform_rollback() {
    local snapshot_dir
    snapshot_dir="$ROLLBACK_DIR/$(cat "$ROLLBACK_DIR/latest" 2>/dev/null || echo "")"

    if [ ! -d "$snapshot_dir" ]; then
        log_error "No snapshot found for rollback"
        return 1
    fi

    log_warn "Performing rollback from snapshot..."

    # Restore binaries
    for bin in ethan ethan-cli ethan-runtime; do
        if [ -f "$snapshot_dir/$bin" ]; then
            cp "$snapshot_dir/$bin" "/usr/local/bin/$bin"
            chmod 755 "/usr/local/bin/$bin"
            log_ok "Restored: $bin"
        fi
    done

    # Restore configs
    if [ -d "$snapshot_dir/configs" ]; then
        rm -rf /etc/ethan
        cp -r "$snapshot_dir/configs" /etc/ethan
        chown -R "$ETHAN_USER:$ETHAN_GROUP" /etc/ethan 2>/dev/null || true
        log_ok "Restored: /etc/ethan"
    fi

    # Restore systemd
    if [ -d "$snapshot_dir/systemd" ]; then
        for unit_file in "$snapshot_dir/systemd"/*.service; do
            [ -f "$unit_file" ] && cp "$unit_file" /etc/systemd/system/
        done
        systemctl daemon-reload
        log_ok "Restored: systemd units"
    fi

    # Restore compose
    if [ -d "$snapshot_dir/compose" ]; then
        rm -rf /usr/local/share/ethan/compose
        cp -r "$snapshot_dir/compose" /usr/local/share/ethan/compose
        log_ok "Restored: compose files"
    fi

    # Restore manifest
    if [ -f "$snapshot_dir/manifest.json" ]; then
        cp "$snapshot_dir/manifest.json" "$MANIFEST_FILE"
    fi

    log_ok "Rollback complete"
    log_update "Rollback performed from snapshot"
}

# ── Stop Services ─────────────────────────────────────────────────────

stop_services() {
    log_info "Stopping ETHAN services..."

    for unit in ethan-plugins ethan-core ethan-runtime; do
        if systemctl is-active "$unit.service" &>/dev/null; then
            systemctl stop "$unit.service" 2>/dev/null || true
            log_ok "Stopped: $unit"
        fi
    done

    # Stop Docker stack
    if [ -f /usr/local/share/ethan/compose/docker-compose.yml ]; then
        docker compose -f /usr/local/share/ethan/compose/docker-compose.yml down 2>/dev/null || true
        log_ok "Docker stack stopped"
    fi

    pkill -f "ethan-runtime" 2>/dev/null || true
    pkill -f "ethan-cli" 2>/dev/null || true
    sleep 1
}

# ── Deploy New Binaries ──────────────────────────────────────────────

deploy_binaries() {
    log_info "Building and deploying new binaries..."

    # Build Go Runtime
    log_info "Building ethan-runtime..."
    (cd "$ETHAN_SOURCE_DIR/runtime" && go build -o /tmp/ethan-runtime ./cmd/ethan-runtime/) 2>&1 | tail -3 || die "Go build failed"
    install -m 755 /tmp/ethan-runtime /usr/local/bin/ethan-runtime
    rm -f /tmp/ethan-runtime
    log_ok "Updated: ethan-runtime"

    # Update launcher
    install -m 755 "$ETHAN_SOURCE_DIR/ethan-launcher.sh" /usr/local/bin/ethan
    log_ok "Updated: ethan (launcher)"

    # Update CLI
    install -m 755 "$ETHAN_SOURCE_DIR/interfaces/cli/main.py" /usr/local/bin/ethan-cli
    log_ok "Updated: ethan-cli"

    # Update Python dependencies
    log_info "Updating Python dependencies..."
    pip3 install -r "$ETHAN_SOURCE_DIR/interfaces/cli/requirements.txt" 2>&1 | tail -1 || log_warn "pip install had warnings"
    log_ok "Python dependencies updated"
}

# ── Merge Configs ────────────────────────────────────────────────────

merge_configs() {
    log_info "Merging configuration files..."

    local configs=(
        "runtime.yaml"
        "core.yaml"
        "plugins.yaml"
    )

    for cfg in "${configs[@]}"; do
        local src="$ETHAN_SOURCE_DIR/infrastructure/config/$cfg"
        local dst="/etc/ethan/$cfg"

        if [ ! -f "$src" ]; then
            continue
        fi

        if [ -f "$dst" ]; then
            # Backup existing
            cp "$dst" "${dst}.bak"
            # Install new version
            install -m 644 -o "$ETHAN_USER" -g "$ETHAN_GROUP" "$src" "$dst"
            log_info "Merged: $cfg (backup at ${cfg}.bak)"
        else
            install -m 644 -o "$ETHAN_USER" -g "$ETHAN_GROUP" "$src" "$dst"
            log_ok "Installed: $cfg"
        fi
    done

    # Update compose files
    for compose_file in docker-compose.yml docker-compose.dev.yml docker-compose.prod.yml; do
        if [ -f "$ETHAN_SOURCE_DIR/$compose_file" ]; then
            install -m 644 -o "$ETHAN_USER" -g "$ETHAN_GROUP" "$ETHAN_SOURCE_DIR/$compose_file" "/usr/local/share/ethan/compose/$compose_file"
        fi
    done
    log_ok "Compose files updated"
}

# ── Update Systemd ───────────────────────────────────────────────────

update_systemd() {
    log_info "Updating systemd units..."

    local units=(
        "ethan-runtime.service"
        "ethan-core.service"
        "ethan-plugins.service"
    )

    for unit in "${units[@]}"; do
        local src="$ETHAN_SOURCE_DIR/infrastructure/systemd/$unit"
        if [ -f "$src" ]; then
            install -m 644 "$src" "/etc/systemd/system/$unit"
            log_ok "Updated: $unit"
        fi
    done

    systemctl daemon-reload
    log_ok "systemd daemon reloaded"
}

# ── Update Docker Stack ──────────────────────────────────────────────

update_docker() {
    log_info "Updating Docker stack..."

    local compose_file="/usr/local/share/ethan/compose/docker-compose.yml"

    if [ ! -f "$compose_file" ]; then
        log_warn "Compose file not found, skipping"
        return 0
    fi

    # Pull new images
    log_info "Pulling new Docker images..."
    docker compose -f "$compose_file" pull 2>&1 | tail -3 || log_warn "Docker pull had issues"

    # Recreate containers
    log_info "Recreating containers..."
    docker compose -f "$compose_file" up -d --force-recreate 2>&1 | tail -3 || log_warn "Docker recreate had issues"

    log_ok "Docker stack updated"
}

# ── Health Check ─────────────────────────────────────────────────────

health_check() {
    log_info "Running health check..."

    local failures=0

    # Check binaries
    for bin in /usr/local/bin/ethan /usr/local/bin/ethan-cli /usr/local/bin/ethan-runtime; do
        if [ ! -x "$bin" ]; then
            log_error "Binary missing: $bin"
            ((failures++))
        fi
    done

    # Check systemd
    for unit in ethan-runtime.service ethan-core.service ethan-plugins.service; do
        if ! systemctl is-enabled "$unit" &>/dev/null; then
            log_warn "Unit not enabled: $unit"
            ((failures++))
        fi
    done

    # Check Docker
    if ! docker info &>/dev/null; then
        log_error "Docker daemon not reachable"
        ((failures++))
    fi

    if [ "$failures" -eq 0 ]; then
        log_ok "Health check passed"
        return 0
    else
        log_warn "Health check: $failures issues found"
        return "$failures"
    fi
}

# ── Update Manifest ──────────────────────────────────────────────────

update_manifest() {
    log_info "Updating install manifest..."

    local tmp
    tmp=$(mktemp)

    if [ -f "$MANIFEST_FILE" ]; then
        python3 -c "
import json
d = json.load(open('$MANIFEST_FILE'))
d['version'] = '$ETHAN_VERSION'
d['updated_at'] = '$(date -u '+%Y-%m-%dT%H:%M:%SZ')'
d['source_dir'] = '$ETHAN_SOURCE_DIR'
json.dump(d, open('$tmp', 'w'), indent=2)
" 2>/dev/null
        mv "$tmp" "$MANIFEST_FILE"
        chown "$ETHAN_USER:$ETHAN_GROUP" "$MANIFEST_FILE" 2>/dev/null || true
        log_ok "Manifest updated to v$ETHAN_VERSION"
    fi
}

# ── Main ─────────────────────────────────────────────────────────────

main() {
    local skip_health=false
    local force=false

    for arg in "$@"; do
        case "$arg" in
            --skip-health) skip_health=true ;;
            --force|-f) force=true ;;
            --help|-h)
                echo "ETHAN Update"
                echo ""
                echo "Usage: sudo ./update.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-health   Skip health check after update"
                echo "  --force, -f     Skip version check"
                echo "  --help, -h      Show this help"
                exit 0
                ;;
        esac
    done

    echo ""
    echo -e "${GREEN}◆${NC}  ETHAN Update v${ETHAN_VERSION}"
    echo ""

    check_root

    # Check if installed
    if [ ! -f "$MANIFEST_FILE" ]; then
        die "ETHAN is not installed. Run install.sh first."
    fi

    local current_version
    current_version=$(python3 -c "import json; d=json.load(open('$MANIFEST_FILE')); print(d.get('version',''))" 2>/dev/null || echo "")

    if [ "$current_version" = "$ETHAN_VERSION" ] && [ "$force" = false ]; then
        log_ok "Already at version $ETHAN_VERSION"
        log_info "Use --force to reinstall"
        exit 0
    fi

    log_info "Updating: $current_version → $ETHAN_VERSION"
    log_update "=== ETHAN Update: $current_version → $ETHAN_VERSION ==="

    # 1. Snapshot
    create_snapshot

    # 2. Stop services
    stop_services

    # 3. Deploy new binaries
    deploy_binaries

    # 4. Merge configs
    merge_configs

    # 5. Update systemd
    update_systemd

    # 6. Update Docker
    update_docker

    # 7. Health check
    if [ "$skip_health" = false ]; then
        if ! health_check; then
            log_warn "Health check failed — initiating rollback"
            perform_rollback
            die "Update failed, rolled back to $current_version"
        fi
    fi

    # 8. Update manifest
    update_manifest

    # 9. Cleanup old rollback snapshots (keep last 3)
    log_info "Cleaning old rollback snapshots..."
    ls -t "$ROLLBACK_DIR" 2>/dev/null | tail -n +4 | while IFS= read -r snap; do
        [ -n "$snap" ] && [ "$snap" != "latest" ] && rm -rf "$ROLLBACK_DIR/$snap" 2>/dev/null || true
    done
    log_ok "Old snapshots cleaned"

    echo ""
    echo -e "${GREEN}◆${NC}  ETHAN updated to v$ETHAN_VERSION"
    echo -e "  ${CYAN}→${NC} Previous version backed up in rollback"
    echo -e "  ${CYAN}→${NC} Run 'sudo ./doctor.sh' for full diagnostics"
    echo ""

    log_update "=== ETHAN Update complete: $ETHAN_VERSION ==="
}

main "$@"