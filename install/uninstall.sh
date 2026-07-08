#!/usr/bin/env bash
# ETHAN clean systemd uninstaller.

set -euo pipefail

ETHAN_USER="ethan"
ETHAN_GROUP="ethan"
STATE_FILE="/var/lib/ethan/install-state.env"
SERVICES=(ethan-plugins ethan-core ethan-runtime)

log() { printf '==> %s\n' "$*"; }
ok() { printf '  OK %s\n' "$*"; }
warn() { printf '  WARN %s\n' "$*" >&2; }
fail() { printf '  ERROR %s\n' "$*" >&2; exit 1; }

require_root() {
    [ "$(id -u)" -eq 0 ] || fail "Run as root: sudo install/uninstall.sh"
}

load_state() {
    ETHAN_CREATED_USER=0
    ETHAN_CREATED_GROUP=0
    ETHAN_GENERATED_FILES="/usr/local/bin/ethan /usr/local/bin/ethan-cli /usr/local/bin/ethan-core /usr/local/bin/ethan-plugins /usr/local/bin/ethan-runtime /etc/systemd/system/ethan-runtime.service /etc/systemd/system/ethan-core.service /etc/systemd/system/ethan-plugins.service"

    if [ -f "$STATE_FILE" ]; then
        # shellcheck disable=SC1090
        . "$STATE_FILE"
        ok "Loaded install state"
    else
        warn "No install state found; using known ETHAN generated paths"
    fi
}

stop_services() {
    log "Stopping ETHAN services"
    for service in "${SERVICES[@]}"; do
        systemctl stop "$service.service" 2>/dev/null || true
    done

    local main_pid
    main_pid="$(systemctl show ethan-runtime.service -p MainPID --value 2>/dev/null || true)"
    for pid in $(pgrep ethan-runtime 2>/dev/null || true); do
        if [ -z "$main_pid" ] || [ "$pid" != "$main_pid" ]; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    ok "Services stopped"
}

remove_systemd_units() {
    log "Removing systemd units"
    for service in ethan-runtime ethan-core ethan-plugins; do
        systemctl disable "$service.service" 2>/dev/null || true
        rm -f "/etc/systemd/system/$service.service"
        ok "Removed $service.service"
    done
    systemctl daemon-reload
    systemctl reset-failed 2>/dev/null || true
}

remove_generated_files() {
    log "Removing generated files"
    for path in $ETHAN_GENERATED_FILES; do
        case "$path" in
            /home/*/AI/Ethan/*|*/core/*|*/runtime/*|*/plugins/*|*/interfaces/*|*/infrastructure/*|*/install/*)
                warn "Skipping source path: $path"
                ;;
            *)
                rm -f "$path"
                ok "Removed $path"
                ;;
        esac
    done

    rm -rf /run/ethan
    rm -rf /var/cache/ethan
    rm -rf /var/log/ethan
    rm -rf /var/lib/ethan
    ok "Removed generated ETHAN state directories"
}

remove_user_if_created() {
    log "Removing installer-created user/group if applicable"

    if [ "${ETHAN_CREATED_USER:-0}" = "1" ] && id "$ETHAN_USER" >/dev/null 2>&1; then
        userdel "$ETHAN_USER" 2>/dev/null || warn "Could not remove user $ETHAN_USER"
        ok "Removed user $ETHAN_USER"
    else
        ok "Preserved user $ETHAN_USER"
    fi

    if [ "${ETHAN_CREATED_GROUP:-0}" = "1" ] && getent group "$ETHAN_GROUP" >/dev/null; then
        groupdel "$ETHAN_GROUP" 2>/dev/null || warn "Could not remove group $ETHAN_GROUP"
        ok "Removed group $ETHAN_GROUP"
    else
        ok "Preserved group $ETHAN_GROUP"
    fi
}

main() {
    require_root
    load_state
    stop_services
    remove_systemd_units
    remove_generated_files
    remove_user_if_created
    ok "ETHAN uninstallation complete; source code was not removed"
}

main "$@"
