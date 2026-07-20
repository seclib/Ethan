#!/usr/bin/env bash
# ethan pull-images — Pré-télécharger les images Docker de base
# Usage: ./ethan pull-images [--parallel]
#
# En mode séquentiel (défaut) : évite la saturation réseau sur un système vierge
# En mode parallèle (--parallel) : plus rapide si le réseau le permet
#
# POURQUOI SÉQUENTIEL PAR DÉFAUT ?
# Sur un système vierge, 6 pulls simultanés peuvent saturer la connexion
# et provoquer des timeouts. Le séquentiel garantit la reproductibilité.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"

PARALLEL_MODE="${1:-}"

timer_start
section "Téléchargement des images Docker de base"

# Images de base (ordre : infrastructure d'abord, puis application)
# Toutes les images utilisées dans docker-compose.yml ET les Dockerfiles
BASE_IMAGES=(
    "nats:2.10-alpine"
    "redis:7-alpine"
    "postgres:16-alpine"
    "prom/prometheus:latest"
    "python:3.12-slim"
    "node:20-alpine"
)

info "Mode : $([ "$PARALLEL_MODE" = "--parallel" ] && echo "parallèle" || echo "séquentiel")"
info "Images à vérifier : ${#BASE_IMAGES[@]}"

# Vérifier la connectivité Docker Hub avant de commencer
if ! docker info &>/dev/null 2>&1; then
    error "Docker daemon non disponible"
    exit 1
fi

# ── Pull séquentiel (défaut) ────────────────────────────────────

pull_image() {
    local image="$1"
    local start
    start=$(date +%s)

    info "Pull : ${image}..."
    if docker pull "$image" 2>&1 | tail -3; then
        local elapsed=$(( $(date +%s) - start ))
        success "✓ ${image} (${elapsed}s)"
        return 0
    else
        error "✗ ${image} : pull échoué"
        return 1
    fi
}

FAILED_IMAGES=()

if [[ "$PARALLEL_MODE" == "--parallel" ]]; then
    # ── Pull parallèle ──────────────────────────────────────────
    warn "Mode parallèle : ${#BASE_IMAGES[@]} pulls simultanés (risque de timeout réseau)"
    PIDS=()
    RESULTS=()

    for image in "${BASE_IMAGES[@]}"; do
        (
            if docker pull "$image" &>/dev/null 2>&1; then
                echo "OK:${image}"
            else
                echo "FAIL:${image}"
            fi
        ) &
        PIDS+=($!)
    done

    for pid in "${PIDS[@]}"; do
        wait "$pid"
    done

    # Vérification finale
    for image in "${BASE_IMAGES[@]}"; do
        if docker image inspect "$image" &>/dev/null 2>&1; then
            success "$image : OK"
        else
            error "$image : échec"
            FAILED_IMAGES+=("$image")
        fi
    done

else
    # ── Pull séquentiel (recommandé) ───────────────────────────
    for image in "${BASE_IMAGES[@]}"; do
        # Vérifier si déjà en cache (évite un pull inutile)
        if docker image inspect "$image" &>/dev/null 2>&1; then
            # Vérifier l'âge de l'image — mettre à jour si > 7 jours
            image_date="$(docker image inspect "$image" --format '{{.Created}}' 2>/dev/null | cut -d'T' -f1 || echo '1970-01-01')"
            if [[ -n "$image_date" ]]; then
                image_epoch="$(date -d "$image_date" +%s 2>/dev/null || echo 0)"
                now_epoch="$(date +%s)"
                age_days=$(( (now_epoch - image_epoch) / 86400 ))
                if (( age_days > 7 )); then
                    warn "$image : en cache mais ${age_days}j — mise à jour..."
                    pull_image "$image" || FAILED_IMAGES+=("$image")
                else
                    success "$image : en cache (${age_days}j) — skip"
                fi
            else
                success "$image : en cache — skip"
            fi
        else
            pull_image "$image" || FAILED_IMAGES+=("$image")
        fi
    done
fi

# ── Résumé ──────────────────────────────────────────────────────

echo
section "Résumé"

total="${#BASE_IMAGES[@]}"
failed="${#FAILED_IMAGES[@]}"
success_count=$(( total - failed ))

if (( failed == 0 )); then
    success "Toutes les images disponibles ($success_count/$total)"
    metadata "$(timer_end)"
    exit 0
else
    error "$failed/$total images en échec :"
    for img in "${FAILED_IMAGES[@]}"; do
        arrow "$img"
    done
    info "Vérifier la connectivité : curl -sf https://registry-1.docker.io/v2/"
    info "Ou utiliser un registry mirror dans /etc/docker/daemon.json"
    metadata "$(timer_end)"
    exit 1
fi
