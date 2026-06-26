#!/bin/bash
# ETHAN Diagnostic Script
# Version: 1.0.0
# Usage: ./doctor.sh [--verbose] [--json]
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────
MANIFEST_FILE="/var/lib/ethan/.install-manifest.json"
DOCTOR_LOG="/var/log/ethan/doctor.log"
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
VERBOSE=false
JSON_OUTPUT=false
FAILURES=0
WARNINGS=0
RESULTS=()

# ── Helpers ───────────────────────────────────────────────────────────

log_info()  { echo -e "  ${CYAN}→${NC} $1"; }
log_ok()    { echo -e "  ${GREEN}✓${NC} $1"; }
log_warn()  { echo -e "  ${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "  ${RED}✗${NC} $1"; }
log_section() { echo -e "\n${BOLD}${CYAN}◆${NC} ${BOLD}$1${NC}"; }
log_detail() { [ "$VERBOSE" = true ] && echo -e "  ${DIM}$1${NC}"; }

check() {
    local name="$1"
    local status="$2"  # pass, fail, warn
    local message="$3"
    local detail="${4:-}"

    case "$status" in
        pass)
            RESULTS+=("{\"check\":\"$name\",\"status\":\"pass\",\"message\":\"$message\"}")
            log_ok "$message"
            ;;
        fail)
            RESULTS+=("{\"check\":\"$name\",\"status\":\"fail\",\"message\":\"$message\"}")
            log_error "$message"
            ((FAILURES++))
            ;;
        warn)
            RESULTS+=("{\"check\":\"$name\",\"status\":\"warn\",\"message\":\"$message\"}")
            log_warn "$message"
            ((WARNINGS++))
            ;;
    esac
    [ -n "$detail" ] && log_detail "$detail"
}

log_diagnostic() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$DOCTOR_LOG"
}

# ── Checks ───────────────────────────────────────────────────────────

check_os() {
    log_section "OS & Platform"

    if [ ! -f /etc/os-release ]; then
        check "os-release" "fail" "OS detection file (/etc/os-release) missing"
    else
        local os_name
        os_name=$(grep -oP 'PRETTY_NAME="\K[^"]+' /etc/os-release 2>/dev/null || echo "unknown")
        check "os" "pass" "OS: $os_name"
    fi

    local kernel
    kernel=$(uname -r)
    check "kernel" "pass" "Kernel: $kernel"

    # architecture
    local arch
    arch=$(uname -m)
    if [ "$arch" = "x86_64" ] || [ "$arch" = "aarch64" ]; then
        check "architecture" "pass" "Architecture: $arch"
    else
        check "architecture" "warn" "Untested architecture: $arch"
    fi
}

check_dependencies() {
    log_section "System Dependencies"

    # systemd
    if command -v systemctl &>/dev/null; then
        check "systemd" "pass" "systemd detected"
    else
        check "systemd" "fail" "systemd not found — ETHAN requires systemd"
    fi

    # Docker
    if command -v docker &>/dev/null; then
        local docker_version
        docker_version=$(docker --version 2>/dev/null || echo "unknown")
        check "docker" "pass" "Docker: $docker_version"
        if docker info &>/dev/null; then
            check "docker-daemon" "pass" "Docker daemon running"
        else
            check "docker-daemon" "fail" "Docker daemon not running"
        fi
    else
        check "docker" "fail" "Docker not found"
    fi

    # Docker Compose
    if docker compose version &>/dev/null; then
        local compose_version
        compose_version=$(docker compose version 2>/dev/null)
        check "docker-compose" "pass" "Docker Compose: $compose_version"
    else
        check "docker-compose" "fail" "Docker Compose not found"
    fi

    # Go
    if command -v go &>/dev/null; then
        local go_version
        go_version=$(go version)
        check "go" "pass" "$go_version"
    else
        check "go" "warn" "Go not found (needed for building Runtime)"
    fi

    # Python
    if command -v python3 &>/dev/null; then
        local py_version
        py_version=$(python3 --version 2>/dev/null || echo "unknown")
        check "python3" "pass" "$py_version"
    else
        check "python3" "fail" "Python 3 not found"
    fi

    # Pip
    if command -v pip3 &>/dev/null; then
        check "pip3" "pass" "pip3 available"
    else
        check "pip3" "fail" "pip3 not found"
    fi
}

check_ethan_user() {
    log_section "ETHAN System User"

    if id "$ETHAN_USER" &>/dev/null; then
        local uid
        uid=$(id -u "$ETHAN_USER")
        check "ethan-user" "pass" "User '$ETHAN_USER' exists (UID: $uid)"

        # Check docker group membership
        if groups "$ETHAN_USER" 2>/dev/null | grep -q docker; then
            check "docker-group" "pass" "User is in docker group"
        else
            check "docker-group" "warn" "User not in docker group — Runtime may not access Docker"
        fi
    else
        check "ethan-user" "fail" "User '$ETHAN_USER' does not exist"
    fi

    if getent group "$ETHAN_GROUP" &>/dev/null; then
        check "ethan-group" "pass" "Group '$ETHAN_GROUP' exists"
    else
        check "ethan-group" "fail" "Group '$ETHAN_GROUP' does not exist"
    fi
}

check_directories() {
    log_section "Directory Structure"

    local dirs=(
        "/var/lib/ethan/data/memory"
        "/var/lib/ethan/data/uploads"
        "/var/lib/ethan/data/models"
        "/var/lib/ethan/cache"
        "/var/run/ethan"
        "/var/log/ethan"
        "/etc/ethan"
        "/usr/local/share/ethan/compose"
        "/usr/local/share/ethan/deploy/postgres"
    )

    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            local owner
            owner=$(stat -c "%U:%G" "$dir" 2>/dev/null || echo "unknown")
            local perms
            perms=$(stat -c "%a" "$dir" 2>/dev/null || echo "?")
            check "dir:$dir" "pass" "$dir ($owner, $perms)"
        else
            check "dir:$dir" "fail" "$dir — missing"
        fi
    done
}

check_binaries() {
    log_section "Binary Integrity"

    local binaries=(
        "/usr/local/bin/ethan"
        "/usr/local/bin/ethan-cli"
        "/usr/local/bin/ethan-runtime"
    )

    for bin in "${binaries[@]}"; do
        if [ -x "$bin" ]; then
            local size
            size=$(stat -c "%s" "$bin" 2>/dev/null || echo "?")
            size="$(( size / 1024 )) KB"

            # Check hash against manifest
            local expected_hash=""
            if [ -f "$MANIFEST_FILE" ]; then
                expected_hash=$(python3 -c "
import json
d = json.load(open('$MANIFEST_FILE'))
f = d.get('files', {}).get('$bin', {})
print(f.get('checksum', ''))
" 2>/dev/null || echo "")
            fi

            if [ -n "$expected_hash" ] && [ "$expected_hash" != "sha256:unknown" ]; then
                local actual_hash
                actual_hash=$(sha256sum "$bin" 2>/dev/null | cut -d' ' -f1 || echo "")
                if [ "sha256:$actual_hash" = "$expected_hash" ]; then
                    check "bin:$bin" "pass" "$bin ($size, checksum OK)"
                else
                    check "bin:$bin" "warn" "$bin ($size, checksum MISMATCH — may have been modified)"
                fi
            else
                check "bin:$bin" "pass" "$bin ($size)"
            fi
        else
            check "bin:$bin" "fail" "$bin — missing or not executable"
        fi
    done

    # Check Python packages
    log_section "Python Dependencies"
    local py_packages=("nats" "redis" "asyncpg" "fastapi" "uvicorn")
    for pkg in "${py_packages[@]}"; do
        if python3 -c "import $pkg" 2>/dev/null; then
            check "pkg:$pkg" "pass" "Python package: $pkg"
        else
            check "pkg:$pkg" "warn" "Python package: $pkg — not installed"
        fi
    done
}

check_configs() {
    log_section "Configuration Files"

    local configs=(
        "/etc/ethan/runtime.yaml"
        "/etc/ethan/core.yaml"
        "/etc/ethan/plugins.yaml"
        "/etc/ethan/shell/ethan.sh"
    )

    for cfg in "${configs[@]}"; do
        if [ -f "$cfg" ]; then
            # Basic YAML validation (Python)
            if [[ "$cfg" == *.yaml ]]; then
                if python3 -c "import yaml; yaml.safe_load(open('$cfg'))" 2>/dev/null; then
                    check "cfg:$cfg" "pass" "$cfg (valid YAML)"
                else
                    check "cfg:$cfg" "warn" "$cfg (invalid YAML)"
                fi
            else
                check "cfg:$cfg" "pass" "$cfg"
            fi
        else
            check "cfg:$cfg" "warn" "$cfg — missing"
        fi
    done

    # Check compose files
    local compose_file="/usr/local/share/ethan/compose/docker-compose.yml"
    if [ -f "$compose_file" ]; then
        # Validate with docker compose
        if docker compose -f "$compose_file" config >/dev/null 2>&1; then
            check "compose" "pass" "Docker Compose config is valid"
        else
            check "compose" "warn" "Docker Compose config has issues"
        fi
    else
        check "compose" "warn" "Docker Compose file missing"
    fi
}

check_systemd() {
    log_section "Systemd Units"

    local units=(
        "ethan-runtime.service"
        "ethan-core.service"
        "ethan-plugins.service"
    )

    for unit in "${units[@]}"; do
        if [ -f "/etc/systemd/system/$unit" ]; then
            # Check is-enabled (may fail if not enabled)
            local enabled_status="disabled"
            systemctl is-enabled "$unit" &>/dev/null && enabled_status="enabled"

            # Check is-active
            local active_status="inactive"
            systemctl is-active "$unit" &>/dev/null && active_status="active"

            if [ "$active_status" = "active" ]; then
                check "unit:$unit" "pass" "$unit ($enabled_status, $active_status)"
            else
                check "unit:$unit" "warn" "$unit ($enabled_status, $active_status)"
            fi
        else
            check "unit:$unit" "warn" "$unit — unit file missing"
        fi
    done
}

check_docker_containers() {
    log_section "Docker Containers"

    if ! docker info &>/dev/null; then
        check "docker-ps" "warn" "Docker daemon not reachable — skipping container checks"
        return
    fi

    # Check for ethan containers
    local containers
    containers=$(docker ps -a --filter "name=ethan" --format "{{.Names}}" 2>/dev/null || true)

    if [ -z "$containers" ]; then
        check "docker-containers" "warn" "No ETHAN containers running"
        return
    fi

    echo "$containers" | while IFS= read -r container; do
        [ -z "$container" ] && continue
        local status
        status=$(docker inspect "$container" --format "{{.State.Status}}" 2>/dev/null || echo "unknown")
        local health
        health=$(docker inspect "$container" --format "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}" 2>/dev/null || echo "none")

        if [ "$status" = "running" ]; then
            if [ "$health" = "healthy" ] || [ "$health" = "none" ]; then
                check "container:$container" "pass" "$container ($status)"
            else
                check "container:$container" "warn" "$container ($status, health: $health)"
            fi
        else
            check "container:$container" "warn" "$container ($status)"
        fi
    done
}

check_ports() {
    log_section "Port Availability"

    local ports_map=(
        "4222:NATS"
        "6379:Redis"
        "5432:PostgreSQL"
        "8000:API"
        "8002:Runtime HTTP"
    )

    for entry in "${ports_map[@]}"; do
        local port="${entry%%:*}"
        local service="${entry##*:}"

        if ss -tlnp "sport = :$port" 2>/dev/null | grep -q ":$port"; then
            check "port:$port" "pass" "Port $port ($service) — in use"
        else
            check "port:$port" "warn" "Port $port ($service) — not listening"
        fi
    done
}

check_socket() {
    log_section "Socket Connectivity"

    local socket="/var/run/ethan/runtime.sock"

    if [ -S "$socket" ]; then
        local perms
        perms=$(stat -c "%a" "$socket" 2>/dev/null || echo "?")
        local owner
        owner=$(stat -c "%U:%G" "$socket" 2>/dev/null || echo "?")
        check "socket" "pass" "Runtime socket: $socket ($perms, $owner)"

        # Test connectivity with socat or python
        if command -v socat &>/dev/null; then
            if echo '{"type":"status.get","session_id":"doctor","payload":{}}' | socat - UNIX-CONNECT:"$socket" - 2>/dev/null | head -1 | grep -q "response"; then
                check "socket-comm" "pass" "Socket communication works"
            else
                check "socket-comm" "warn" "Socket exists but communication failed"
            fi
        else
            check "socket-comm" "warn" "Cannot test socket (socat not installed)"
        fi
    else
        check "socket" "warn" "Runtime socket not found — Runtime may not be running"
    fi
}

check_disk() {
    log_section "Disk Space"

    local targets=(
        "/var/lib/ethan:ETHAN data"
        "/var/log/ethan:ETHAN logs"
    )

    for target in "${targets[@]}"; do
        local dir="${target%%:*}"
        local label="${target##*:}"

        if [ -d "$dir" ]; then
            local usage
            usage=$(df -h "$dir" 2>/dev/null | tail -1 | awk '{print $4, "free of", $2}')
            local pct
            pct=$(df "$dir" 2>/dev/null | tail -1 | awk '{print $5}' | tr -d '%')
            if [ "$pct" -lt 80 ]; then
                check "disk:$label" "pass" "$label: $usage"
            elif [ "$pct" -lt 95 ]; then
                check "disk:$label" "warn" "$label: $usage (${pct}% used)"
            else
                check "disk:$label" "fail" "$label: $usage (CRITICAL: ${pct}% used)"
            fi
        fi
    done
}

check_manifest() {
    log_section "Install Manifest"

    if [ -f "$MANIFEST_FILE" ]; then
        local version
        version=$(python3 -c "import json; d=json.load(open('$MANIFEST_FILE')); print(d.get('version','unknown'))" 2>/dev/null || echo "corrupt")
        local installed_at
        installed_at=$(python3 -c "import json; d=json.load(open('$MANIFEST_FILE')); print(d.get('installed_at','unknown'))" 2>/dev/null || echo "corrupt")
        local phases
        phases=$(python3 -c "
import json
d = json.load(open('$MANIFEST_FILE'))
print(', '.join(d.get('phases_completed', [])))
" 2>/dev/null || echo "corrupt")

        check "manifest" "pass" "Manifest: v$version (installed: $installed_at)"
        check "manifest-phases" "pass" "Completed phases: $phases"

        # Verify all files in manifest still exist
        local missing_files=0
        python3 -c "
import json
d = json.load(open('$MANIFEST_FILE'))
for path in d.get('files', {}):
    import os
    if not os.path.exists(path):
        print(path)
" 2>/dev/null | while IFS= read -r missing; do
            [ -n "$missing" ] && check "manifest-file" "warn" "Manifest file missing: $missing"
        done
    else
        check "manifest" "warn" "Install manifest not found — ETHAN may not be installed"
    fi
}

# ── Main ─────────────────────────────────────────────────────────────

main() {
    for arg in "$@"; do
        case "$arg" in
            --verbose|-v) VERBOSE=true ;;
            --json|-j) JSON_OUTPUT=true ;;
            --help|-h)
                echo "ETHAN Doctor — Diagnostics"
                echo ""
                echo "Usage: ./doctor.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --verbose, -v   Show detailed output"
                echo "  --json, -j      Output as JSON"
                echo "  --help, -h      Show this help"
                exit 0
                ;;
        esac
    done

    # Create log directory
    mkdir -p /var/log/ethan 2>/dev/null || true

    log_diagnostic "=== ETHAN Doctor started ==="

    if [ "$JSON_OUTPUT" = true ]; then
        # Run all checks, output JSON
        check_os
        check_dependencies
        check_ethan_user
        check_directories
        check_binaries
        check_configs
        check_systemd
        check_docker_containers
        check_ports
        check_socket
        check_disk
        check_manifest

        # JSON output
        echo "{"
        echo "  \"timestamp\": \"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\","
        echo "  \"failures\": $FAILURES,"
        echo "  \"warnings\": $WARNINGS,"
        echo "  \"results\": ["
        local first=true
        for result in "${RESULTS[@]}"; do
            if [ "$first" = true ]; then
                first=false
            else
                echo ","
            fi
            echo "    $result"
        done
        echo ""
        echo "  ]"
        echo "}"
    else
        # Terminal output
        echo ""
        echo -e "${BOLD}${CYAN}◆${NC}  ETHAN Diagnostics"
        echo -e "  ${DIM}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
        echo ""

        check_os
        check_dependencies
        check_ethan_user
        check_directories
        check_binaries
        check_configs
        check_systemd
        check_docker_containers
        check_ports
        check_socket
        check_disk
        check_manifest

        # Summary
        echo ""
        echo -e "${DIM}────────────────────────────────────────${NC}"
        if [ "$FAILURES" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
            echo -e "  ${GREEN}✓${NC}  All checks passed — system healthy"
        elif [ "$FAILURES" -eq 0 ]; then
            echo -e "  ${YELLOW}⚠${NC}  $WARNINGS warnings (no failures)"
            echo -e "  ${CYAN}→${NC}  Run 'sudo ./repair.sh' to auto-fix warnings"
        else
            echo -e "  ${RED}✗${NC}  $FAILURES failures, $WARNINGS warnings"
            echo -e "  ${CYAN}→${NC}  Run 'sudo ./repair.sh' to attempt auto-repair"
        fi
        echo ""
    fi

    log_diagnostic "=== ETHAN Doctor complete: $FAILURES failures, $WARNINGS warnings ==="
    exit "$FAILURES"
}

main "$@"