#!/usr/bin/env bash
# ethan watchdog — Surveiller les conteneurs en échec (one-shot)
# Appelé par ethan-watchdog.service (déclenché par ethan-watchdog.timer toutes les 30s).
#
# Circuit breaker par service :
#   - Détecte les états exited / restarting / dead. Sous `restart: unless-stopped`,
#     un crash-loop apparaît en `restarting` (jamais `exited`) : l'ancienne
#     version ne filtrait que `status=exited` et était aveugle à ce cas.
#   - Tant que les échecs consécutifs restent <= MAX_RESTARTS : redémarrage
#     via `docker compose up -d <service>`.
#   - Au-delà : circuit OUVERT — plus aucun redémarrage automatique (fin des
#     boucles infinies) + alerte dans le journal systemd.
#   - Un cycle stable décrémente le compteur d'un cran par service (réarmement
#     progressif après environ MAX_RESTARTS x 30s de stabilité).
#
# Variables (surchargeables) :
#   ETHAN_WATCHDOG_MAX_RESTARTS  échecs consécutifs avant ouverture (défaut 5)
#   ETHAN_WATCHDOG_STATE         fichier d'état (défaut /tmp/ethan-watchdog-state)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

MAX_RESTARTS="${ETHAN_WATCHDOG_MAX_RESTARTS:-5}"
STATE_FILE="${ETHAN_WATCHDOG_STATE:-/tmp/ethan-watchdog-state}"

require_docker

# ── États en échec : exited / restarting / dead ───────────────────────────
# NOTE: `compose ps` sans `--all` ne montre QUE les conteneurs running —
# un conteneur stoppé/crashé y est invisible (l'ancien watchdog était donc
# aveugle aussi aux exited). Toujours interroger avec `--all`.
if ! PS_OUTPUT="$(docker_compose ps --all --format json 2>/dev/null)"; then
    error "Impossible d'interroger Docker Compose (COMPOSE_FILE=${COMPOSE_FILE})"
    exit 1
fi

if ! FAILED_SVCS="$(printf '%s\n' "$PS_OUTPUT" | python3 -c '
import json, sys
failed = []
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        row = json.loads(line)
    except json.JSONDecodeError:
        continue
    if str(row.get("State", "")).lower() in ("exited", "restarting", "dead"):
        failed.append(str(row.get("Service", "?")))
print(" ".join(failed))
')"; then
    error "Analyse de l'état Docker Compose impossible"
    exit 1
fi

# ── État persistant : lignes « service compteur » ─────────────────────────
declare -A COUNTS=()
if [[ -f "$STATE_FILE" ]]; then
    while read -r svc cnt; do
        [[ -n "$svc" && "$cnt" =~ ^[0-9]+$ ]] && COUNTS["$svc"]="$cnt"
    done < "$STATE_FILE"
fi

# ── Cycle : incrément puis restart, ou circuit ouvert ─────────────────────
OPEN_CIRCUITS=0
declare -A FAILED_SET=()
# shellcheck disable=SC2086 — $FAILED_SVCS est une liste à découper volontairement
for svc in $FAILED_SVCS; do
    FAILED_SET["$svc"]=1
    cnt=$(( ${COUNTS[$svc]:-0} + 1 ))
    COUNTS["$svc"]="$cnt"

    if (( cnt > MAX_RESTARTS )); then
        OPEN_CIRCUITS=$((OPEN_CIRCUITS + 1))
        if (( cnt == MAX_RESTARTS + 1 )); then
            error "Circuit ouvert pour ${svc} — ${cnt} échecs consécutifs"
            error "Redémarrages automatiques suspendus pour ce service."
            info "Diagnostiquer : docker compose logs ${svc}"
        else
            error "Circuit toujours ouvert pour ${svc} (${cnt} échecs consécutifs)"
        fi
    else
        warn "${svc} en échec (tentative ${cnt}/${MAX_RESTARTS}) — redémarrage"
        docker_compose up -d "$svc" >/dev/null 2>&1 || true
    fi
done

# ── Réarmement progressif : un cran de moins par cycle stable ─────────────
for svc in "${!COUNTS[@]}"; do
    [[ -n "${FAILED_SET[$svc]:-}" ]] && continue
    cnt=$(( ${COUNTS[$svc]} - 1 ))
    if (( cnt <= 0 )); then
        unset 'COUNTS[$svc]'
    else
        COUNTS["$svc"]="$cnt"
    fi
done

# ── Persistance de l'état ─────────────────────────────────────────────────
if (( ${#COUNTS[@]} > 0 )); then
    : > "$STATE_FILE"
    for svc in "${!COUNTS[@]}"; do
        echo "${svc} ${COUNTS[$svc]}" >> "$STATE_FILE"
    done
else
    rm -f "$STATE_FILE"
fi

# Défaillance persistante (circuit ouvert) → exit 1 pour systemd/metrics.
if (( OPEN_CIRCUITS > 0 )); then
    exit 1
fi
exit 0
