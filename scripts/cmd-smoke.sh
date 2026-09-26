#!/usr/bin/env bash
# ethan smoke — Vérification E2E d'une stack ETHAN déployée.
# Usage: ./ethan smoke [--skip-llm] [--timeout SECONDS]
#
# Étapes :
#   1. Stack     — les conteneurs Compose sont healthy
#   2. Santé     — API /health + /health/ready, WebUI, /v1/version
#   3. Ollama    — joignable depuis le conteneur api (host.docker.internal)
#   4. Auth      — POST /auth/register puis POST /auth/login (JWT réel)
#   5. Chat      — POST /v1/chat/completions (inférence réelle via Ollama)
#   6. Chats     — création, message persisté, suppression (/chats)
#   7. Projects  — CRUD complet (/v1/projects)
#
# Variables :
#   ETHAN_SMOKE_USER / ETHAN_SMOKE_PASSWORD — compte de test
#   (défauts : ethan-smoke / smoke-ethan-2026 ; le compte est créé en base
#    au premier run et réutilisé ensuite — il sert d'identité de smoke).
#   Ollama/hôte : OLLAMA_BASE_URL (défaut http://host.docker.internal:11434).
#
# Exit codes :
#   0 — toutes les étapes conformes
#   1 — au moins une étape a échoué
#   2 — stack hors ligne (API injoignable)
#   3 — prérequis manquant (python3)

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/ethan-lib.sh"
timer_start

usage() {
    cat <<'EOF'
Usage: ./ethan smoke [--skip-llm] [--timeout SECONDS]

  --skip-llm      Ne pas vérifier Ollama ni l'inférence (étapes 3 et 5)
  --timeout N     Timeout de l'appel d'inférence en secondes (défaut 180,
                  couvre le premier chargement (cold start) d'un modèle)
  --help, -h      Afficher cette aide

Vérifie la stack déployée de bout en bout : health, Ollama externe,
register/login JWT, chat completions réel, persistance /chats, CRUD
/v1/projects. Voir docs/installation.md.
EOF
}

# ── Options ───────────────────────────────────────────────────────
SKIP_LLM=0
CHAT_TIMEOUT=180
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-llm)   SKIP_LLM=1; shift ;;
        --timeout)    CHAT_TIMEOUT="$2"; shift 2 ;;
        --help|-h)    usage; exit 0 ;;
        *)            warn "Option inconnue : $1 (ignorée)"; shift ;;
    esac
done

API_URL="http://localhost:${ETHAN_API_PORT}"
UI_URL="http://localhost:${ETHAN_WEBUI_PORT}"
SMOKE_USER="${ETHAN_SMOKE_USER:-ethan-smoke}"
SMOKE_PASSWORD="${ETHAN_SMOKE_PASSWORD:-smoke-ethan-2026}"

# ── Prérequis ─────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    error "python3 est requis pour parser les réponses JSON du smoke."
    info "Installe-le : sudo apt install python3"
    exit 3
fi
require_docker

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
RESP="${TMP_DIR}/resp.json"
HTTP_CODE=""
HTTP_BODY=""

PASS=0; FAILN=0; WARNS=0
ok()   { success "$*"; PASS=$((PASS + 1)); }
bad()  { error "$*"; FAILN=$((FAILN + 1)); }
soft() { warn "$*"; WARNS=$((WARNS + 1)); }

# ── Helpers HTTP ──────────────────────────────────────────────────
# http_call MÉTHODE URL [json] [token] [timeout]
# → HTTP_CODE (000 = injoignable), HTTP_BODY.
http_call() {
    local method="$1" url="$2" json="${3:-}" token="${4:-}" tmo="${5:-30}"
    local args=(-sS -X "$method" -o "$RESP" -w '%{http_code}'
                --max-time "$tmo" -H 'Content-Type: application/json')
    [[ -n "$token" ]] && args+=(-H "Authorization: Bearer ${token}")
    [[ -n "$json" ]] && args+=(-d "$json")
    HTTP_CODE="$(curl "${args[@]}" "$url" 2>"${TMP_DIR}/curl.err" || true)"
    HTTP_CODE="${HTTP_CODE:-000}"
    HTTP_BODY="$(cat "$RESP" 2>/dev/null || true)"
}

# _jget FICHIER CHEMIN — extraction d'un champ JSON (a.b.c) via python3.
_jget() {
    python3 - "$1" "$2" <<'PY' 2>/dev/null
import json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as fh:
        data = json.load(fh)
except Exception:
    sys.exit(1)
cur = data
for part in sys.argv[2].split("."):
    if isinstance(cur, list):
        try:
            cur = cur[int(part)]
        except (ValueError, IndexError):
            sys.exit(1)
    elif isinstance(cur, dict) and part in cur:
        cur = cur[part]
    else:
        sys.exit(1)
if isinstance(cur, (dict, list)):
    print(json.dumps(cur, ensure_ascii=False))
elif cur is True:
    print("true")
elif cur is False:
    print("false")
elif cur is None:
    sys.exit(1)
else:
    print(cur)
PY
}

# _jlen FICHIER — longueur d'un tableau JSON (0 si invalide).
_jlen() {
    python3 -c 'import json,sys
try:
    d=json.load(open(sys.argv[1],encoding="utf-8"))
    print(len(d) if isinstance(d,list) else 0)
except Exception:
    print(0)' "$1" 2>/dev/null || echo 0
}

_trunc() { # aperçu du corps d'erreur (200 caractères max)
    head -c 200 <<<"${HTTP_BODY:-<vide>}" | tr '\n' ' '
}

# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 1 — Stack
# ═══════════════════════════════════════════════════════════════════
section "1/7 — État des conteneurs"

STACK_OK=1
for container in ethan-nats ethan-redis ethan-postgres ethan-api \
                 ethan-kernel ethan-modules ethan-ui ethan-pg_backup; do
    health="$(docker inspect "$container" \
        --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' \
        2>/dev/null || echo absent)"
    case "$health" in
        healthy)  ok "$container : healthy" ;;
        starting) soft "$container : healthcheck en cours (starting)" ;;
        none)     soft "$container : running sans healthcheck" ;;
        absent)   bad "$container : absent (stack arrêtée ? ./ethan up)"; STACK_OK=0 ;;
        *)        bad "$container : $health" ;;
    esac
done

# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 2 — Santé HTTP
# ═══════════════════════════════════════════════════════════════════
section "2/7 — API / WebUI"

http_call GET "${API_URL}/health"
if [ "$HTTP_CODE" != "200" ]; then
    error "API /health : HTTP ${HTTP_CODE} (${API_URL})"
    error "La stack semble hors ligne — lancer : ./ethan up puis ./ethan wait-for-services"
    exit 2
fi
[ "$(_jget "$RESP" status)" = "ok" ] \
    && ok "API /health → status=ok" \
    || bad "API /health : status inattendu ($(_trunc))"

http_call GET "${API_URL}/health/ready"
[ "$HTTP_CODE" = "200" ] && [ "$(_jget "$RESP" status)" = "ok" ] \
    && ok "API /health/ready → status=ok" \
    || bad "API /health/ready : HTTP ${HTTP_CODE} ($(_trunc))"

http_call GET "${API_URL}/v1/version"
[ "$HTTP_CODE" = "200" ] \
    && ok "API /v1/version → 200 (version $(_jget "$RESP" version))" \
    || bad "API /v1/version : HTTP ${HTTP_CODE}"

http_call GET "${UI_URL}/"
case "$HTTP_CODE" in
    200|30[1278]) ok "WebUI ${UI_URL}/ → HTTP ${HTTP_CODE}" ;;
    000)         bad "WebUI injoignable sur ${UI_URL} (port ETHAN_WEBUI_PORT=${ETHAN_WEBUI_PORT})" ;;
    *)           bad "WebUI : HTTP ${HTTP_CODE}" ;;
esac

# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 3 — Ollama externe (vu depuis le conteneur api)
# ═══════════════════════════════════════════════════════════════════
OLLAMA_MODEL=""
if [ "$SKIP_LLM" = "1" ]; then
    section "3/7 — Ollama (ignoré : --skip-llm)"
else
    section "3/7 — Ollama externe (depuis le conteneur api)"

    OLLAMA_MODEL="$(docker_compose exec -T api printenv OLLAMA_DEFAULT_MODEL 2>/dev/null \
        | tr -d '\r' || true)"
    OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.1}"

    if docker_compose exec -T api curl -sf --max-time 5 \
        "http://host.docker.internal:11434/api/tags" > "${TMP_DIR}/ollama.json" 2>/dev/null; then
        ok "Ollama joignable depuis api (host.docker.internal:11434)"
        _model_base="${OLLAMA_MODEL%%:*}"
        if grep -q "\"name\":\"${_model_base}:" "${TMP_DIR}/ollama.json" \
            || grep -q "\"name\":\"${_model_base}\"" "${TMP_DIR}/ollama.json"; then
            ok "Modèle '${OLLAMA_MODEL}' présent dans Ollama"
        else
            bad "Modèle '${OLLAMA_MODEL}' absent d'Ollama (tags: $(_jget "${TMP_DIR}/ollama.json" 0.name 2>/dev/null || echo '?'))"
        fi
    else
        bad "Ollama injoignable depuis api (OLLAMA_BASE_URL attendu : http://host.docker.internal:11434 — voir docs/installation.md)"
    fi
fi

# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 4 — Auth (register + login)
# ═══════════════════════════════════════════════════════════════════
section "4/7 — Authentification"

TOKEN=""
http_call POST "${API_URL}/auth/register" \
    "{\"username\":\"${SMOKE_USER}\",\"password\":\"${SMOKE_PASSWORD}\"}"
if [ "$HTTP_CODE" = "200" ]; then
    TOKEN="$(_jget "$RESP" access_token)"
    ok "POST /auth/register → 200 (user=${SMOKE_USER}, role=$(_jget "$RESP" user.role))"
else
    bad "POST /auth/register : HTTP ${HTTP_CODE} ($(_trunc))"
fi

http_call POST "${API_URL}/auth/login" \
    "{\"username\":\"${SMOKE_USER}\",\"password\":\"${SMOKE_PASSWORD}\"}"
if [ "$HTTP_CODE" = "200" ]; then
    _login_token="$(_jget "$RESP" access_token)"
    [ -n "$_login_token" ] && TOKEN="$_login_token"
    ok "POST /auth/login → 200 (role=$(_jget "$RESP" user.role))"
elif [ -z "$TOKEN" ]; then
    bad "POST /auth/login : HTTP ${HTTP_CODE} ($(_trunc)) — et aucun token de register"
else
    # Le compte peut préexister avec un autre mot de passe (register est
    # idempotent) : le token register suffit pour la suite.
    soft "POST /auth/login : HTTP ${HTTP_CODE} — on réutilise le token register"
fi

if [ -z "$TOKEN" ]; then
    error "Aucun JWT — impossible de poursuivre (étapes 5 à 7 protégées)."
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 5 — Chat completions (inférence réelle via Ollama)
# ═══════════════════════════════════════════════════════════════════
if [ "$SKIP_LLM" = "1" ]; then
    section "5/7 — Chat completions (ignoré : --skip-llm)"
else
    section "5/7 — Chat completions (inférence réelle)"
    http_call POST "${API_URL}/v1/chat/completions" \
        '{"message":"Reponds uniquement par : ETHAN SMOKE OK"}' \
        "$TOKEN" "$CHAT_TIMEOUT"
    if [ "$HTTP_CODE" = "200" ]; then
        _reply="$(_jget "$RESP" message)"
        if [ -n "$_reply" ]; then
            ok "POST /v1/chat/completions → 200 — réponse : \"$(head -c 80 <<<"$_reply")\""
        else
            bad "POST /v1/chat/completions : 200 mais champ 'message' vide ($(_trunc))"
        fi
    else
        bad "POST /v1/chat/completions : HTTP ${HTTP_CODE} ($(_trunc))"
        arrow "Vérifier OLLAMA_DEFAULT_MODEL et les logs : docker compose logs api --tail 50"
    fi
fi

# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 6 — Conversations (/chats) : création, persistance, suppression
# ═══════════════════════════════════════════════════════════════════
section "6/7 — Conversations (/chats)"

CHAT_ID=""
http_call POST "${API_URL}/chats" \
    "{\"title\":\"smoke-$(date +%s)\"}" "$TOKEN"
if [ "$HTTP_CODE" = "200" ]; then
    CHAT_ID="$(_jget "$RESP" id)"
    [ -n "$CHAT_ID" ] && ok "POST /chats → 200 (id=${CHAT_ID})" \
        || bad "POST /chats : 200 mais champ 'id' absent ($(_trunc))"
else
    bad "POST /chats : HTTP ${HTTP_CODE} ($(_trunc))"
fi

if [ -n "$CHAT_ID" ]; then
    http_call GET "${API_URL}/chats/${CHAT_ID}" "" "$TOKEN"
    [ "$HTTP_CODE" = "200" ] && ok "GET /chats/{id} → 200" \
        || bad "GET /chats/{id} : HTTP ${HTTP_CODE}"

    http_call POST "${API_URL}/chats/${CHAT_ID}/messages" \
        '{"role":"user","content":"message de persistance smoke"}' "$TOKEN"
    if [[ "$HTTP_CODE" =~ ^2 ]]; then
        ok "POST /chats/{id}/messages → HTTP ${HTTP_CODE}"
    else
        bad "POST /chats/{id}/messages : HTTP ${HTTP_CODE} ($(_trunc))"
    fi

    http_call GET "${API_URL}/chats/${CHAT_ID}/messages" "" "$TOKEN"
    _msg_count="$(_jlen "$RESP")"
    if [ "$HTTP_CODE" = "200" ] && [ "$_msg_count" -ge 1 ] 2>/dev/null; then
        ok "GET /chats/{id}/messages → 200 (${_msg_count} message(s) persisté(s))"
    else
        bad "GET /chats/{id}/messages : HTTP ${HTTP_CODE}, ${_msg_count} message(s) (persistance absente ?)"
    fi

    http_call DELETE "${API_URL}/chats/${CHAT_ID}" "" "$TOKEN"
    [ "$HTTP_CODE" = "200" ] && [ "$(_jget "$RESP" status)" = "deleted" ] \
        && ok "DELETE /chats/{id} → status=deleted" \
        || bad "DELETE /chats/{id} : HTTP ${HTTP_CODE} ($(_trunc))"
fi

# ═══════════════════════════════════════════════════════════════════
# ÉTAPE 7 — Projets (/v1/projects) : CRUD complet
# ═══════════════════════════════════════════════════════════════════
section "7/7 — Projets (/v1/projects)"

http_call GET "${API_URL}/v1/projects" "" "$TOKEN"
[ "$HTTP_CODE" = "200" ] && ok "GET /v1/projects → 200" \
    || bad "GET /v1/projects : HTTP ${HTTP_CODE} ($(_trunc))"

PROJ_ID=""
PROJ_NAME="smoke-$(date +%s)"
http_call POST "${API_URL}/v1/projects" \
    "{\"name\":\"${PROJ_NAME}\",\"description\":\"auto créé par ./ethan smoke\"}" "$TOKEN"
if [ "$HTTP_CODE" = "200" ]; then
    PROJ_ID="$(_jget "$RESP" id)"
    [ -n "$PROJ_ID" ] && ok "POST /v1/projects → 200 (id=${PROJ_ID})" \
        || bad "POST /v1/projects : 200 mais champ 'id' absent ($(_trunc))"
else
    bad "POST /v1/projects : HTTP ${HTTP_CODE} ($(_trunc))"
    arrow "Rôle insuffisant ? Le rôle 'standard' doit avoir la permission MEMORY"
fi

if [ -n "$PROJ_ID" ]; then
    http_call GET "${API_URL}/v1/projects/${PROJ_ID}" "" "$TOKEN"
    [ "$HTTP_CODE" = "200" ] && [ "$(_jget "$RESP" name)" = "$PROJ_NAME" ] \
        && ok "GET /v1/projects/{id} → 200 (name=${PROJ_NAME})" \
        || bad "GET /v1/projects/{id} : HTTP ${HTTP_CODE} ($(_trunc))"

    http_call PATCH "${API_URL}/v1/projects/${PROJ_ID}" \
        '{"description":"mise à jour smoke"}' "$TOKEN"
    [ "$HTTP_CODE" = "200" ] && ok "PATCH /v1/projects/{id} → 200" \
        || bad "PATCH /v1/projects/{id} : HTTP ${HTTP_CODE} ($(_trunc))"

    http_call DELETE "${API_URL}/v1/projects/${PROJ_ID}" "" "$TOKEN"
    [ "$HTTP_CODE" = "200" ] && [ "$(_jget "$RESP" status)" = "deleted" ] \
        && ok "DELETE /v1/projects/{id} → status=deleted" \
        || bad "DELETE /v1/projects/{id} : HTTP ${HTTP_CODE} ($(_trunc))"

    http_call GET "${API_URL}/v1/projects/${PROJ_ID}" "" "$TOKEN"
    [ "$HTTP_CODE" = "404" ] && ok "GET après suppression → 404 (bien supprimé)" \
        || bad "GET après suppression : HTTP ${HTTP_CODE} (404 attendu)"
fi

# ═══════════════════════════════════════════════════════════════════
# Résumé
# ═══════════════════════════════════════════════════════════════════
section "Résumé du smoke"
metadata "${PASS} conforme(s) · ${FAILN} échec(s) · ${WARNS} avertissement(s)"
[ "$STACK_OK" = "1" ] || warn "Conteneurs absents — démarrer avec ./ethan up"
timer_end

if [ "$FAILN" -gt 0 ]; then
    error "SMOKE ÉCHEC — ${FAILN} étape(s) non conforme(s)"
    exit 1
fi
success "SMOKE OK — stack vérifiée de bout en bout"
exit 0

