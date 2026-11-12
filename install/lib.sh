#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# ETHAN Installation Library — Shared functions for all lifecycle scripts
# ═══════════════════════════════════════════════════════════════════════════════
# This file is sourced (not executed) by install.sh, uninstall.sh, update.sh,
# doctor.sh, and repair.sh.  It provides:
#   • Logging with severity levels
#   • Color output helpers
#   • Root/dependency guards
#   • Manifest read/write
#   • Checksum utilities
#   • Rollback snapshot helpers
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Constants ─────────────────────────────────────────────────────────────────
readonly ETHAN_VERSION="0.2.0"
readonly ETHAN_USER="ethan"
readonly ETHAN_GROUP="ethan"

# Filesystem roots
readonly ETHAN_BIN_DIR="/usr/local/bin"
readonly ETHAN_ETC_DIR="/etc/ethan"
readonly ETHAN_SHARE_DIR="/usr/local/share/ethan"
readonly ETHAN_LIB_DIR="/var/lib/ethan"
readonly ETHAN_DATA_DIR="/var/lib/ethan/data"
readonly ETHAN_CACHE_DIR="/var/lib/ethan/cache"
readonly ETHAN_RUN_DIR="/var/run/ethan"
readonly ETHAN_LOG_DIR="/var/log/ethan"

# Control files
readonly ETHAN_MANIFEST="${ETHAN_LIB_DIR}/.install-manifest.json"
readonly ETHAN_ROLLBACK_DIR="${ETHAN_LIB_DIR}/.rollback"
readonly ETHAN_INSTALL_LOG="${ETHAN_LOG_DIR}/install.log"

# Systemd
readonly ETHAN_SYSTEMD_DIR="/etc/systemd/system"

# Docker
readonly ETHAN_COMPOSE_DIR="${ETHAN_SHARE_DIR}/compose"

# Port range for Osiris-Lab port allocation
readonly ETHAN_PORT_RANGE_START=3000
readonly ETHAN_PORT_RANGE_END=9000

# Required binaries
readonly REQUIRED_BINS=(docker python3 git)
readonly OPTIONAL_BINS=(go jq curl nc)

# ── Colors ────────────────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
    readonly C_RESET='\033[0m'
    readonly C_RED='\033[0;31m'
    readonly C_GREEN='\033[0;32m'
    readonly C_YELLOW='\033[0;33m'
    readonly C_BLUE='\033[0;34m'
    readonly C_CYAN='\033[0;36m'
    readonly C_BOLD='\033[1m'
    readonly C_DIM='\033[2m'
else
    readonly C_RESET='' C_RED='' C_GREEN='' C_YELLOW=''
    readonly C_BLUE='' C_CYAN='' C_BOLD='' C_DIM=''
fi

# ── Logging ───────────────────────────────────────────────────────────────────

_log() {
    local level="$1" icon="$2" color="$3"
    shift 3
    local ts
    ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    printf "${color}  %s %s${C_RESET}\n" "$icon" "$*" >&2
    # Also append to install log if the directory exists
    if [[ -d "${ETHAN_LOG_DIR}" ]]; then
        printf "%s [%s] %s\n" "$ts" "$level" "$*" >> "${ETHAN_INSTALL_LOG}" 2>/dev/null || true
    fi
}

log_info()    { _log "INFO"    "◆" "$C_BLUE"   "$@"; }
log_ok()      { _log "OK"      "✓" "$C_GREEN"  "$@"; }
log_warn()    { _log "WARN"    "⚠" "$C_YELLOW" "$@"; }
log_error()   { _log "ERROR"   "✗" "$C_RED"    "$@"; }
log_step()    { _log "STEP"    "▸" "$C_CYAN"   "$@"; }
log_section() {
    echo "" >&2
    printf "${C_BOLD}  ── %s ──${C_RESET}\n" "$*" >&2
    echo "" >&2
}

# ── Guards ────────────────────────────────────────────────────────────────────

require_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

require_linux() {
    if [[ "$(uname -s)" != "Linux" ]]; then
        log_error "ETHAN installation is only supported on Linux"
        exit 1
    fi
}

require_systemd() {
    if ! command -v systemctl &>/dev/null; then
        log_error "systemd is required but not found"
        exit 1
    fi
    if ! pidof systemd &>/dev/null && ! pidof /sbin/init &>/dev/null; then
        log_warn "systemd does not appear to be PID 1 — service management may fail"
    fi
}

check_dependency() {
    local bin="$1"
    if command -v "$bin" &>/dev/null; then
        return 0
    fi
    return 1
}

require_dependencies() {
    local missing=()
    for bin in "${REQUIRED_BINS[@]}"; do
        if ! check_dependency "$bin"; then
            missing+=("$bin")
        fi
    done
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing[*]}"
        log_error "Install them and re-run the installer"
        exit 1
    fi
}

check_docker_version() {
    local docker_version
    docker_version="$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "0")"
    local major
    major="$(echo "$docker_version" | cut -d. -f1)"
    if [[ "$major" -lt 24 ]]; then
        log_warn "Docker >= 24 recommended (found: ${docker_version})"
        return 1
    fi
    return 0
}

check_python_version() {
    local py_version
    py_version="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")"
    local major minor
    major="$(echo "$py_version" | cut -d. -f1)"
    minor="$(echo "$py_version" | cut -d. -f2)"
    if [[ "$major" -lt 3 ]] || { [[ "$major" -eq 3 ]] && [[ "$minor" -lt 10 ]]; }; then
        log_warn "Python >= 3.10 required (found: ${py_version})"
        return 1
    fi
    return 0
}

# ── Source Directory Detection ────────────────────────────────────────────────

detect_source_dir() {
    # The source directory is where THIS script lives, two levels up
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}")" && pwd)"
    # If we're in infrastructure/install/, go up two levels
    if [[ "$script_dir" == */infrastructure/install ]]; then
        echo "$(cd "$script_dir/../.." && pwd)"
    elif [[ "$script_dir" == */scripts ]]; then
        echo "$(cd "$script_dir/.." && pwd)"
    else
        echo "$script_dir"
    fi
}

# ── Manifest Operations ──────────────────────────────────────────────────────

manifest_exists() {
    [[ -f "${ETHAN_MANIFEST}" ]]
}

manifest_read() {
    if manifest_exists; then
        cat "${ETHAN_MANIFEST}"
    else
        echo "{}"
    fi
}

manifest_get_version() {
    if manifest_exists && check_dependency jq; then
        jq -r '.version // "unknown"' "${ETHAN_MANIFEST}" 2>/dev/null || echo "unknown"
    else
        echo "unknown"
    fi
}

manifest_write() {
    local version="$1"
    local source_dir="$2"
    local phases_json="$3"
    local files_json="$4"
    local units_json="$5"
    local images_json="$6"

    if ! check_dependency jq; then
        # Fallback: write raw JSON without jq
        cat > "${ETHAN_MANIFEST}" <<MANIFEST_EOF
{
  "version": "${version}",
  "installed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "updated_at": null,
  "install_method": "source",
  "source_dir": "${source_dir}",
  "phases_completed": ${phases_json},
  "files": ${files_json},
  "systemd_units": ${units_json},
  "docker_images": ${images_json}
}
MANIFEST_EOF
    else
        jq -n \
            --arg ver "$version" \
            --arg src "$source_dir" \
            --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
            --argjson phases "$phases_json" \
            --argjson files "$files_json" \
            --argjson units "$units_json" \
            --argjson images "$images_json" \
            '{
                version: $ver,
                installed_at: $ts,
                updated_at: null,
                install_method: "source",
                source_dir: $src,
                phases_completed: $phases,
                files: $files,
                systemd_units: $units,
                docker_images: $images
            }' > "${ETHAN_MANIFEST}"
    fi
}

manifest_record_file() {
    local filepath="$1"
    local mode="$2"
    # Append to a temp file list — caller aggregates at the end
    echo "${filepath}|${mode}" >> "${ETHAN_LIB_DIR}/.install-files.tmp"
}

# ── Checksum Utilities ────────────────────────────────────────────────────────

file_checksum() {
    local filepath="$1"
    sha256sum "$filepath" 2>/dev/null | awk '{print "sha256:" $1}'
}

verify_checksum() {
    local filepath="$1"
    local expected="$2"
    local actual
    actual="$(file_checksum "$filepath")"
    [[ "$actual" == "$expected" ]]
}

# ── Rollback Snapshot ─────────────────────────────────────────────────────────

create_rollback_snapshot() {
    local tag="$1"  # e.g. "update-0.2.0"
    local snapshot_dir="${ETHAN_ROLLBACK_DIR}/${tag}-$(date +%s)"

    mkdir -p "$snapshot_dir"

    # Snapshot binaries
    for bin in ethan ethan-cli ethan-runtime; do
        if [[ -f "${ETHAN_BIN_DIR}/${bin}" ]]; then
            cp -a "${ETHAN_BIN_DIR}/${bin}" "$snapshot_dir/" 2>/dev/null || true
        fi
    done

    # Snapshot configs
    if [[ -d "${ETHAN_ETC_DIR}" ]]; then
        cp -a "${ETHAN_ETC_DIR}" "$snapshot_dir/etc-ethan" 2>/dev/null || true
    fi

    # Snapshot manifest
    if [[ -f "${ETHAN_MANIFEST}" ]]; then
        cp -a "${ETHAN_MANIFEST}" "$snapshot_dir/manifest.json" 2>/dev/null || true
    fi

    # Snapshot systemd units
    mkdir -p "$snapshot_dir/systemd"
    for unit in ethan-runtime.service ethan-core.service ethan-plugins.service; do
        if [[ -f "${ETHAN_SYSTEMD_DIR}/${unit}" ]]; then
            cp -a "${ETHAN_SYSTEMD_DIR}/${unit}" "$snapshot_dir/systemd/" 2>/dev/null || true
        fi
    done

    # Write metadata
    cat > "$snapshot_dir/meta.json" <<META_EOF
{
  "tag": "${tag}",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "version": "$(manifest_get_version)",
  "hostname": "$(hostname)"
}
META_EOF

    log_ok "Rollback snapshot created: ${snapshot_dir}"
    echo "$snapshot_dir"
}

restore_rollback_snapshot() {
    local snapshot_dir="$1"

    if [[ ! -d "$snapshot_dir" ]]; then
        log_error "Rollback snapshot not found: ${snapshot_dir}"
        return 1
    fi

    log_step "Restoring from rollback snapshot..."

    # Restore binaries
    for bin in ethan ethan-cli ethan-runtime; do
        if [[ -f "${snapshot_dir}/${bin}" ]]; then
            cp -a "${snapshot_dir}/${bin}" "${ETHAN_BIN_DIR}/" 2>/dev/null || true
        fi
    done

    # Restore configs
    if [[ -d "${snapshot_dir}/etc-ethan" ]]; then
        cp -a "${snapshot_dir}/etc-ethan/"* "${ETHAN_ETC_DIR}/" 2>/dev/null || true
    fi

    # Restore systemd units
    if [[ -d "${snapshot_dir}/systemd" ]]; then
        cp -a "${snapshot_dir}/systemd/"* "${ETHAN_SYSTEMD_DIR}/" 2>/dev/null || true
        systemctl daemon-reload 2>/dev/null || true
    fi

    # Restore manifest
    if [[ -f "${snapshot_dir}/manifest.json" ]]; then
        cp -a "${snapshot_dir}/manifest.json" "${ETHAN_MANIFEST}" 2>/dev/null || true
    fi

    log_ok "Rollback restore complete"
}

cleanup_old_rollbacks() {
    local keep="${1:-3}"  # Keep N most recent snapshots
    if [[ -d "${ETHAN_ROLLBACK_DIR}" ]]; then
        local count
        count="$(find "${ETHAN_ROLLBACK_DIR}" -maxdepth 1 -mindepth 1 -type d | wc -l)"
        if [[ "$count" -gt "$keep" ]]; then
            find "${ETHAN_ROLLBACK_DIR}" -maxdepth 1 -mindepth 1 -type d \
                | sort | head -n "$((count - keep))" \
                | xargs rm -rf
            log_info "Cleaned up old rollback snapshots (kept ${keep})"
        fi
    fi
}

# ── Service Control ───────────────────────────────────────────────────────────

stop_ethan_services() {
    log_step "Stopping ETHAN services..."
    for unit in ethan-plugins ethan-core ethan-runtime; do
        if systemctl is-active "${unit}.service" &>/dev/null; then
            systemctl stop "${unit}.service" 2>/dev/null || true
            log_ok "Stopped ${unit}"
        fi
    done
}

start_ethan_services() {
    log_step "Starting ETHAN services..."
    for unit in ethan-runtime ethan-core ethan-plugins; do
        if systemctl is-enabled "${unit}.service" &>/dev/null; then
            systemctl start "${unit}.service" 2>/dev/null || true
            log_ok "Started ${unit}"
        fi
    done
}

# ── Docker Helpers ────────────────────────────────────────────────────────────

is_docker_running() {
    docker info &>/dev/null 2>&1
}

docker_compose_down() {
    local compose_dir="${1:-${ETHAN_COMPOSE_DIR}}"
    if [[ -f "${compose_dir}/docker-compose.yml" ]]; then
        docker compose -f "${compose_dir}/docker-compose.yml" down 2>/dev/null || true
    fi
}

docker_compose_up() {
    local compose_dir="${1:-${ETHAN_COMPOSE_DIR}}"
    if [[ -f "${compose_dir}/docker-compose.yml" ]]; then
        docker compose -f "${compose_dir}/docker-compose.yml" up -d 2>/dev/null || true
    fi
}

# ── Port Helpers (Osiris-Lab integration) ─────────────────────────────────────

is_port_in_use() {
    local port="$1"
    ss -tlnp 2>/dev/null | grep -q ":${port} " && return 0
    return 1
}

find_free_port() {
    local start="${1:-${ETHAN_PORT_RANGE_START}}"
    local end="${2:-${ETHAN_PORT_RANGE_END}}"
    for ((port=start; port<=end; port++)); do
        if ! is_port_in_use "$port"; then
            echo "$port"
            return 0
        fi
    done
    return 1
}

# ── Banner ────────────────────────────────────────────────────────────────────

print_banner() {
    local action="${1:-ETHAN}"
    cat >&2 <<'BANNER_EOF'

  ███████╗████████╗██╗  ██╗ █████╗ ███╗   ██╗
  ██╔════╝╚══██╔══╝██║  ██║██╔══██╗████╗  ██║
  █████╗     ██║   ███████║███████║██╔██╗ ██║
  ██╔══╝     ██║   ██╔══██║██╔══██║██║╚██╗██║
  ███████╗   ██║   ██║  ██║██║  ██║██║ ╚████║
  ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝

BANNER_EOF
    printf "${C_BOLD}  %s — v%s${C_RESET}\n" "$action" "$ETHAN_VERSION" >&2
    echo "" >&2
}
