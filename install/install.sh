#!/bin/bash
# ETHAN Installation Script
# Version: 1.0.0
# Usage: sudo ./install.sh
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────
ETHAN_VERSION="$(cat "$(dirname "$0")/../VERSION" 2>/dev/null || echo "0.2.0")"
ETHAN_SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL_LOG="/var/log/ethan/install.log"
MANIFEST_FILE="/var/lib/ethan/.install-manifest.json"
ROLLBACK_DIR="/var/lib/ethan/.rollback"
ETHAN_USER="ethan"
ETHAN_GROUP="ethan"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
DIM='\033[2m'
NC='\033[0m'

# ── Helper Functions ──────────────────────────────────────────────────

log_info()  { echo -e "  ${CYAN}→${NC} $1"; }
log_ok()    { echo -e "  ${GREEN}✓${NC} $1"; }
log_warn()  { echo -e "  ${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "  ${RED}✗${NC} $1"; }
log_step()  { echo -e "\n${DIM}──${NC} ${GREEN}$1${NC}"; }

die() {
    log_error "$1"
    exit 1
}

# Log to file
log_install() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$INSTALL_LOG"
}

# Check if running as root
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        die "install.sh must be run as root. Use: sudo ./install.sh"
    fi
}

# Check for old installations and remove conflicting binaries
check_old_installations() {
    local old_paths=(
        "$HOME/.local/bin/ethan"
        "$HOME/.local/bin/ethan-cli"
        "/usr/local/bin/ethan-old"
    )

    for old_path in "${old_paths[@]}"; do
        if [ -f "$old_path" ]; then
            log_warn "Removing old installation: $old_path"
            rm -f "$old_path"
            log_ok "Removed: $old_path"
        fi
    done
}

# Check if already installed
check_installed() {
    local force="${1:-false}"
    if [ -f "$MANIFEST_FILE" ]; then
        local installed_version
        installed_version=$(python3 -c "import json; d=json.load(open('$MANIFEST_FILE')); print(d.get('version',''))" 2>/dev/null || echo "")
        if [ "$installed_version" = "$ETHAN_VERSION" ] && [ "$force" = false ]; then
            log_ok "ETHAN $ETHAN_VERSION is already installed"
            log_info "Run 'sudo ./install.sh --force' to reinstall"
            exit 0
        elif [ -n "$installed_version" ] && [ "$force" = false ]; then
            log_warn "ETHAN $installed_version is installed (current: $ETHAN_VERSION)"
            log_info "Run 'sudo ./update.sh' to upgrade"
            exit 0
        fi
    fi
}

# Write manifest entry
write_manifest() {
    local phase="$1"
    local tmp
    tmp=$(mktemp)
    if [ -f "$MANIFEST_FILE" ]; then
        python3 -c "
import json, sys
d = json.load(open('$MANIFEST_FILE'))
if '$phase' not in d.get('phases_completed', []):
    d.setdefault('phases_completed', []).append('$phase')
json.dump(d, open('$tmp', 'w'), indent=2)
" 2>/dev/null || cat "$MANIFEST_FILE" > "$tmp"
    else
        cat > "$tmp" <<EOF
{
  "version": "$ETHAN_VERSION",
  "installed_at": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "updated_at": null,
  "install_method": "source",
  "source_dir": "$ETHAN_SOURCE_DIR",
  "phases_completed": ["$phase"],
  "files": {},
  "systemd_units": [],
  "docker_images": []
}
EOF
    fi
    mv "$tmp" "$MANIFEST_FILE"
    chown "$ETHAN_USER:$ETHAN_GROUP" "$MANIFEST_FILE" 2>/dev/null || true
}

# Add file to manifest
manifest_add_file() {
    local path="$1"
    local checksum
    checksum=$(sha256sum "$path" 2>/dev/null | cut -d' ' -f1 || echo "unknown")
    local mode
    mode=$(stat -c "%a" "$path" 2>/dev/null || echo "644")
    local tmp
    tmp=$(mktemp)
    python3 -c "
import json
d = json.load(open('$MANIFEST_FILE'))
d.setdefault('files', {})['$path'] = {'checksum': 'sha256:$checksum', 'mode': '$mode'}
json.dump(d, open('$tmp', 'w'), indent=2)
" 2>/dev/null
    mv "$tmp" "$MANIFEST_FILE"
}

# Add systemd unit to manifest
manifest_add_unit() {
    local unit="$1"
    local tmp
    tmp=$(mktemp)
    python3 -c "
import json
d = json.load(open('$MANIFEST_FILE'))
if '$unit' not in d.setdefault('systemd_units', []):
    d['systemd_units'].append('$unit')
json.dump(d, open('$tmp', 'w'), indent=2)
" 2>/dev/null
    mv "$tmp" "$MANIFEST_FILE"
}

# Rollback function — restore from snapshot
rollback() {
    local phase="$1"
    log_warn "Rolling back phase: $phase"
    log_install "ROLLBACK: phase $phase failed"

    case "$phase" in
        preflight)    return 0 ;;  # read-only, nothing to rollback
        user)
            userdel "$ETHAN_USER" 2>/dev/null || true
            groupdel "$ETHAN_GROUP" 2>/dev/null || true
            log_ok "Removed system user"
            ;;
        directories)
            rm -rf /var/lib/ethan /var/run/ethan /var/log/ethan /etc/ethan /usr/local/share/ethan 2>/dev/null || true
            log_ok "Removed directories"
            ;;
        binaries)
            rm -f /usr/local/bin/ethan /usr/local/bin/ethan-cli /usr/local/bin/ethan-runtime 2>/dev/null || true
            log_ok "Removed binaries"
            ;;
        configs)
            rm -rf /etc/ethan 2>/dev/null || true
            log_ok "Removed configs"
            ;;
        shell)
            # Remove shell integration lines
            for profile in /etc/bash.bashrc /etc/zsh/zshrc /etc/skel/.bashrc /etc/skel/.zshrc; do
                [ -f "$profile" ] && sed -i '/ETHAN Shell Integration/d; /ethan\.sh/d; /ethan\/shell/d' "$profile" 2>/dev/null || true
            done
            log_ok "Removed shell integration"
            ;;
        systemd)
            for unit in ethan-runtime ethan-core ethan-plugins; do
                systemctl disable "$unit.service" 2>/dev/null || true
                rm -f "/etc/systemd/system/$unit.service" 2>/dev/null || true
            done
            systemctl daemon-reload 2>/dev/null || true
            log_ok "Removed systemd units"
            ;;
        docker)
            docker compose -f /usr/local/share/ethan/compose/docker-compose.yml down -v 2>/dev/null || true
            log_ok "Stopped Docker stack"
            ;;
        verify)       return 0 ;;  # read-only
    esac
}

# ── Preflight Checks ──────────────────────────────────────────────────

phase_preflight() {
    log_step "Phase 1/9: Preflight Checks"

    # OS Check
    if [ ! -f /etc/os-release ]; then
        die "Unsupported OS: only Linux with systemd is supported"
    fi
    log_ok "OS: $(grep -oP 'PRETTY_NAME="\K[^"]+' /etc/os-release 2>/dev/null || echo 'Linux')"

    # systemd
    if ! command -v systemctl &>/dev/null; then
        die "systemd not found. ETHAN requires systemd."
    fi
    log_ok "systemd detected"

    # Docker
    if ! command -v docker &>/dev/null; then
        die "Docker not found. Install Docker first: https://docs.docker.com/engine/install/"
    fi
    log_ok "Docker: $(docker --version 2>/dev/null || echo 'installed')"
    if ! docker info &>/dev/null; then
        die "Docker daemon not running. Start with: systemctl start docker"
    fi
    log_ok "Docker daemon running"

    # Docker Compose
    if ! docker compose version &>/dev/null; then
        die "Docker Compose not found. Install Docker Compose plugin."
    fi
    log_ok "Docker Compose: $(docker compose version 2>/dev/null)"

    # Go (needed for Runtime build)
    if ! command -v go &>/dev/null; then
        die "Go not found. Install Go ≥1.23: https://go.dev/dl/"
    fi
    local go_version
    go_version=$(go version | grep -oP 'go\K[0-9]+\.[0-9]+' || echo "0")
    if [ "$(echo "$go_version" | cut -d. -f1)" -lt 1 ] || { [ "$(echo "$go_version" | cut -d. -f1)" -eq 1 ] && [ "$(echo "$go_version" | cut -d. -f2)" -lt 23 ]; }; then
        die "Go ≥1.23 required (found: $go_version)"
    fi
    log_ok "Go: $(go version)"

    # Python
    if ! command -v python3 &>/dev/null; then
        die "Python 3 not found. Install Python ≥3.10."
    fi
    local py_version
    py_version=$(python3 --version | grep -oP 'Python \K[0-9]+\.[0-9]+' || echo "0")
    if [ "$(echo "$py_version" | cut -d. -f1)" -lt 3 ] || { [ "$(echo "$py_version" | cut -d. -f1)" -eq 3 ] && [ "$(echo "$py_version" | cut -d. -f2)" -lt 10 ]; }; then
        die "Python ≥3.10 required (found: $py_version)"
    fi
    log_ok "Python: $(python3 --version)"

    # Pip
    if ! command -v pip3 &>/dev/null; then
        die "pip3 not found. Install python3-pip."
    fi
    log_ok "pip3: $(pip3 --version 2>/dev/null | head -1)"

    # Check available disk space
    local available_kb
    available_kb=$(df /var/lib/ethan 2>/dev/null | tail -1 | awk '{print $4}' || echo "0")
    if [ "$available_kb" -gt 0 ] && [ "$available_kb" -lt 1048576 ]; then
        log_warn "Low disk space: $(( available_kb / 1024 )) MB available (recommended: ≥1GB)"
    fi

    log_install "Preflight checks passed"
    write_manifest "preflight"
    log_ok "Preflight checks complete"
    return 0
}

# ── Phase 2: System User ─────────────────────────────────────────────

phase_user() {
    log_step "Phase 2/9: System User"

    if getent group "$ETHAN_GROUP" &>/dev/null; then
        log_ok "Group '$ETHAN_GROUP' already exists"
    else
        groupadd --system "$ETHAN_GROUP"
        log_ok "Created group: $ETHAN_GROUP"
    fi

    if id "$ETHAN_USER" &>/dev/null; then
        log_ok "User '$ETHAN_USER' already exists"
    else
        useradd --system --gid "$ETHAN_GROUP" --home-dir /var/lib/ethan --no-create-home --shell /usr/sbin/nologin "$ETHAN_USER"
        log_ok "Created user: $ETHAN_USER"
    fi

    # Add to docker group
    usermod -aG docker "$ETHAN_USER" 2>/dev/null || log_warn "Could not add user to docker group"
    log_ok "User added to docker group"

    log_install "System user created"
    write_manifest "user"
    return 0
}

# ── Phase 3: Directory Scaffold ──────────────────────────────────────

phase_directories() {
    log_step "Phase 3/9: Directory Scaffold"

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
        mkdir -p "$dir"
        chown "$ETHAN_USER:$ETHAN_GROUP" "$dir"
        chmod 755 "$dir"
    done

    # Run socket directory needs special permissions
    chmod 775 /var/run/ethan

    log_ok "Created directory structure"
    log_install "Directory scaffold created"
    write_manifest "directories"
    return 0
}

# ── Phase 4: Deploy Binaries ─────────────────────────────────────────

phase_binaries() {
    log_step "Phase 4/9: Deploy Binaries"

    # Build Go Runtime
    log_info "Building ethan-runtime..."
    (cd "$ETHAN_SOURCE_DIR/runtime" && go mod tidy && go build -o /tmp/ethan-runtime ./cmd/ethan-runtime/) 2>&1 | while IFS= read -r line; do log_info "  go: $line"; done
    if [ ! -x /tmp/ethan-runtime ]; then
        die "Go build failed — check runtime/go.mod and runtime/go.sum"
    fi
    install -m 755 /tmp/ethan-runtime /usr/local/bin/ethan-runtime
    rm -f /tmp/ethan-runtime
    log_ok "Built and installed: ethan-runtime"
    manifest_add_file "/usr/local/bin/ethan-runtime"

    # Install launcher as 'ethan' command
    install -m 755 "$ETHAN_SOURCE_DIR/ethan-launcher.sh" /usr/local/bin/ethan
    log_ok "Installed launcher: /usr/local/bin/ethan"
    manifest_add_file "/usr/local/bin/ethan"

    # Install CLI wrapper
    install -m 755 "$ETHAN_SOURCE_DIR/interfaces/cli/main.py" /usr/local/bin/ethan-cli
    log_ok "Installed CLI: /usr/local/bin/ethan-cli"
    manifest_add_file "/usr/local/bin/ethan-cli"

    # Install Python dependencies
    log_info "Installing Python dependencies..."
    if [ -f "$ETHAN_SOURCE_DIR/interfaces/cli/requirements.txt" ]; then
        pip3 install --break-system-packages -r "$ETHAN_SOURCE_DIR/cli/requirements.txt" 2>&1 | tail -1 || log_warn "pip install had warnings"
        log_ok "Python dependencies installed"
    else
        log_warn "No requirements.txt found at cli/requirements.txt — skipping Python deps"
    fi

    log_install "Binaries deployed"
    write_manifest "binaries"
    return 0
}

# ── Phase 5: Deploy Configs ──────────────────────────────────────────

phase_configs() {
    log_step "Phase 5/9: Deploy Configs"

    # Copy config files from infrastructure/config/
    local configs=(
        "runtime.yaml"
        "core.yaml"
        "plugins.yaml"
    )

    for cfg in "${configs[@]}"; do
        local src="$ETHAN_SOURCE_DIR/infrastructure/config/$cfg"
        local dst="/etc/ethan/$cfg"
        if [ -f "$src" ]; then
            if [ -f "$dst" ]; then
                # Preserve existing config, backup
                cp "$dst" "${dst}.bak"
                log_info "Backed up existing: $cfg"
            fi
            install -m 644 -o "$ETHAN_USER" -g "$ETHAN_GROUP" "$src" "$dst"
            manifest_add_file "$dst"
            log_ok "Installed: $cfg"
        fi
    done

    # Copy docker-compose files
    for compose_file in docker-compose.yml docker-compose.dev.yml docker-compose.prod.yml; do
        if [ -f "$ETHAN_SOURCE_DIR/$compose_file" ]; then
            install -m 644 -o "$ETHAN_USER" -g "$ETHAN_GROUP" "$ETHAN_SOURCE_DIR/$compose_file" "/usr/local/share/ethan/compose/$compose_file"
            manifest_add_file "/usr/local/share/ethan/compose/$compose_file"
        fi
    done
    log_ok "Docker Compose files installed"

    # Copy postgres init
    if [ -f "$ETHAN_SOURCE_DIR/deploy/postgres/init.sql" ]; then
        install -m 644 -o "$ETHAN_USER" -g "$ETHAN_GROUP" "$ETHAN_SOURCE_DIR/deploy/postgres/init.sql" "/usr/local/share/ethan/deploy/postgres/init.sql"
        manifest_add_file "/usr/local/share/ethan/deploy/postgres/init.sql"
    fi

    log_install "Configs deployed"
    write_manifest "configs"
    return 0
}

# ── Phase 6: Shell Integration ───────────────────────────────────────

phase_shell() {
    log_step "Phase 6/9: Shell Integration"

    # Copy shell integration files
    install -m 644 -o "$ETHAN_USER" -g "$ETHAN_GROUP" "$ETHAN_SOURCE_DIR/infrastructure/shell/ethan.sh" /etc/ethan/shell/ethan.sh
    install -m 644 -o "$ETHAN_USER" -g "$ETHAN_GROUP" "$ETHAN_SOURCE_DIR/infrastructure/shell/completion.sh" /etc/ethan/shell/completion.sh 2>/dev/null || true
    manifest_add_file "/etc/ethan/shell/ethan.sh"

    # Install to system-wide bashrc
    local bashrc_lines=(
        ""
        "# ETHAN Shell Integration"
        'export ETHAN_HOME="${ETHAN_HOME:-$HOME/.ethan}"'
        'export PATH="$ETHAN_HOME/bin:$PATH"'
        '[ -f /etc/ethan/shell/ethan.sh ] && source /etc/ethan/shell/ethan.sh'
    )
    local bashrc_file="/etc/bash.bashrc"
    if [ -f "$bashrc_file" ]; then
        if ! grep -q "ETHAN Shell Integration" "$bashrc_file" 2>/dev/null; then
            printf '%s\n' "${bashrc_lines[@]}" >> "$bashrc_file"
            log_ok "Added shell integration to $bashrc_file"
        else
            log_ok "Shell integration already in $bashrc_file"
        fi
    fi

    # Also add to /etc/skel for new users
    local skel_file="/etc/skel/.bashrc"
    if [ -f "$skel_file" ]; then
        if ! grep -q "ETHAN Shell Integration" "$skel_file" 2>/dev/null; then
            printf '%s\n' "${bashrc_lines[@]}" >> "$skel_file"
        fi
    fi

    log_install "Shell integration deployed"
    write_manifest "shell"
    return 0
}

# ── Phase 7: Systemd Units ───────────────────────────────────────────

phase_systemd() {
    log_step "Phase 7/9: Systemd Units"

    local units=(
        "ethan-runtime.service"
        "ethan-core.service"
        "ethan-plugins.service"
    )

    for unit in "${units[@]}"; do
        local src="$ETHAN_SOURCE_DIR/infrastructure/systemd/$unit"
        local dst="/etc/systemd/system/$unit"
        if [ -f "$src" ]; then
            install -m 644 "$src" "$dst"
            manifest_add_file "$dst"
            manifest_add_unit "$unit"
            log_ok "Installed unit: $unit"
        else
            log_warn "Unit not found: $unit"
        fi
    done

    systemctl daemon-reload
    log_ok "systemd daemon reloaded"

    # Enable units
    for unit in "${units[@]}"; do
        if [ -f "/etc/systemd/system/$unit" ]; then
            systemctl enable "$unit" 2>/dev/null || log_warn "Could not enable $unit"
            log_ok "Enabled: $unit"
        fi
    done

    log_install "Systemd units deployed"
    write_manifest "systemd"
    return 0
}

# ── Phase 8: Docker Stack Init ───────────────────────────────────────

phase_docker() {
    log_step "Phase 8/9: Docker Stack Init"

    local compose_file="/usr/local/share/ethan/compose/docker-compose.yml"

    if [ ! -f "$compose_file" ]; then
        log_warn "Docker Compose file not found, skipping"
        write_manifest "docker"
        return 0
    fi

    # Pull images
    log_info "Pulling Docker images..."
    docker compose -f "$compose_file" pull 2>&1 | while IFS= read -r line; do
        if [[ "$line" == *"Pulled"* ]] || [[ "$line" == *"Downloaded"* ]]; then
            log_info "  $line"
        fi
    done
    log_ok "Docker images pulled"

    # Start services
    log_info "Starting Docker stack..."
    docker compose -f "$compose_file" up -d 2>&1 | while IFS= read -r line; do
        if [[ "$line" == *"Started"* ]] || [[ "$line" == *"Running"* ]]; then
            log_info "  $line"
        fi
    done

    # Record images in manifest
    local tmp
    tmp=$(mktemp)
    docker compose -f "$compose_file" images -q 2>/dev/null | while IFS= read -r image_id; do
        if [ -n "$image_id" ]; then
            local repo_tag
            repo_tag=$(docker inspect "$image_id" --format '{{range .RepoTags}}{{.}}{{"\n"}}{{end}}' 2>/dev/null | head -1)
            if [ -n "$repo_tag" ]; then
                python3 -c "
import json
d = json.load(open('$MANIFEST_FILE'))
if '$repo_tag' not in d.setdefault('docker_images', []):
    d['docker_images'].append('$repo_tag')
json.dump(d, open('$tmp', 'w'), indent=2)
" 2>/dev/null
                mv "$tmp" "$MANIFEST_FILE"
            fi
        fi
    done

    log_ok "Docker stack initialized"
    log_install "Docker stack initialized"
    write_manifest "docker"
    return 0
}

# ── Phase 9: Health Verify ───────────────────────────────────────────

phase_verify() {
    log_step "Phase 9/9: Health Verification"

    # Run doctor checks
    local failures=0

    # Check Runtime binary
    if [ -x /usr/local/bin/ethan-runtime ]; then
        log_ok "Runtime binary exists"
    else
        log_error "Runtime binary missing"
        ((failures++))
    fi

    # Check CLI binary
    if [ -x /usr/local/bin/ethan-cli ]; then
        log_ok "CLI binary exists"
    else
        log_error "CLI binary missing"
        ((failures++))
    fi

    # Check launcher
    if [ -x /usr/local/bin/ethan ]; then
        log_ok "Launcher exists"
    else
        log_error "Launcher missing"
        ((failures++))
    fi

    # Check configs
    for cfg in runtime.yaml core.yaml plugins.yaml; do
        if [ -f "/etc/ethan/$cfg" ]; then
            log_ok "Config exists: $cfg"
        else
            log_warn "Config missing: $cfg"
            ((failures++))
        fi
    done

    # Check systemd units
    for unit in ethan-runtime.service ethan-core.service ethan-plugins.service; do
        if systemctl is-enabled "$unit" &>/dev/null; then
            log_ok "Systemd unit enabled: $unit"
        else
            log_warn "Systemd unit not enabled: $unit"
            ((failures++))
        fi
    done

    # Check Docker
    if docker info &>/dev/null; then
        log_ok "Docker daemon reachable"
    else
        log_error "Docker daemon not reachable"
        ((failures++))
    fi

    # Check Python packages
    if python3 -c "import nats, redis, asyncpg, fastapi, uvicorn" 2>/dev/null; then
        log_ok "Python dependencies available"
    else
        log_warn "Some Python dependencies missing (run: pip3 install -r requirements.txt)"
    fi

    if [ "$failures" -eq 0 ]; then
        log_ok "All checks passed"
    else
        log_warn "$failures checks failed — review above"
    fi

    log_install "Health verification complete ($failures failures)"
    write_manifest "verify"
    return "$failures"
}

# ── Main ─────────────────────────────────────────────────────────────

main() {
    local force=false

    for arg in "$@"; do
        case "$arg" in
            --force|-f) force=true ;;
            --help|-h)
                echo "ETHAN Installation"
                echo ""
                echo "Usage: sudo ./install.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --force, -f     Force reinstall even if same version"
                echo "  --help, -h      Show this help"
                exit 0
                ;;
        esac
    done

    echo ""
    echo -e "${GREEN}◆${NC}  ETHAN Installation v${ETHAN_VERSION}"
    echo ""

    check_root
    check_old_installations
    check_installed "$force"

    # Create log directory
    mkdir -p /var/log/ethan 2>/dev/null || true

    log_install "=== ETHAN Installation v$ETHAN_VERSION ==="
    log_install "Source: $ETHAN_SOURCE_DIR"

    # Execute phases with rollback on failure
    phases=(
        "preflight:phase_preflight"
        "user:phase_user"
        "directories:phase_directories"
        "binaries:phase_binaries"
        "configs:phase_configs"
        "shell:phase_shell"
        "systemd:phase_systemd"
        "docker:phase_docker"
        "verify:phase_verify"
    )

    for phase_entry in "${phases[@]}"; do
        local phase_name="${phase_entry%%:*}"
        local phase_func="${phase_entry##*:}"

        if ! $phase_func; then
            log_error "Phase '$phase_name' failed"
            rollback "$phase_name"
            die "Installation failed at phase: $phase_name. Run 'sudo ./repair.sh' for diagnostics."
        fi
    done

    echo ""
    echo -e "${GREEN}◆${NC}  ETHAN v$ETHAN_VERSION installed successfully"
    echo ""
    echo -e "  ${CYAN}→${NC} Type 'ethan' to start"
    echo -e "  ${CYAN}→${NC} Type 'ethan --help' for options"
    echo -e "  ${CYAN}→${NC} Logs: journalctl --user -u ethan-runtime -f"
    echo ""

    log_install "=== Installation complete ==="
}

main "$@"