#!/bin/bash
# ESIL core — shared shell functions
# No side-effects. Safe to source multiple times.
#
# CONTRAT API (vérifié vivant le 30/09/2026 — ne pas diverger) :
#   - POST ${ETHAN_API}/v1/message  champ REQUIS « input » (MessageRequest)
#   - GET  ${ETHAN_API}/v1/state
#   - les deux exigent un JWT (401 sinon) : lu dans ETHAN_TOKEN, jamais en dur.
# Ces trois règles sont figées par tests/interfaces/test_shell_contract.py.

_ethan_base() {
  printf '%s' "${ETHAN_API:-http://localhost:8000}"
}

# En-têtes d'auth en tableau global. Vide si aucun token configuré : on
# n'invente pas de secret, on laisse l'API répondre 401 et on le dit.
_ETHAN_AUTH=()
_ethan_auth_args() {
  _ETHAN_AUTH=()
  if [[ -n "${ETHAN_TOKEN:-}" ]]; then
    _ETHAN_AUTH=(-H "Authorization: Bearer ${ETHAN_TOKEN}")
  fi
}

# Charge utile JSON construite par python3 : un message contenant des guillemets,
# un antislash ou un saut de ligne ne peut plus casser le -d de curl.
_ethan_json_payload() {
  python3 -c 'import json,sys; print(json.dumps({"input": sys.argv[1]}))' "$*"
}

_ethan_api() {
  local base payload
  base="$(_ethan_base)"
  payload="$(_ethan_json_payload "$*")" || return 1
  _ethan_auth_args
  curl -s --max-time 10 -X POST "${base%/}/v1/message" \
    -H "Content-Type: application/json" \
    ${_ETHAN_AUTH[@]+"${_ETHAN_AUTH[@]}"} \
    -d "$payload" -w $'\n%{http_code}' 2>/dev/null
}

# Émet le corps JSON sur stdout ; sur stderr la cause racine de l'échec.
# Un 401 n'est pas « API unreachable » : le dire honnêtement.
_ethan_api_raw() {
  local raw code out
  raw="$(_ethan_api "$*")" || true
  if [[ -z "$raw" ]]; then
    echo "ERR: API injoignable ($(_ethan_base))" >&2
    return 1
  fi
  code="${raw##*$'\n'}"
  out="${raw%$'\n'*}"
  case "$code" in
    2*)
      printf '%s\n' "$out"
      ;;
    000|"")
      # curl n'a pas pu etablir la connexion : 000 n'est pas un code HTTP recu
      # par ETHAN, c'est l'absence de reponse. Le dire avec l'URL concernee.
      echo "ERR: API injoignable ($(_ethan_base)) — ETHAN_API ? ethan up ?" >&2
      return 1
      ;;
    401|403)
      echo "ERR: authentification requise (HTTP $code) — export ETHAN_TOKEN=<jwt>" >&2
      return 1
      ;;
    404)
      echo "ERR: /v1/message introuvable (HTTP 404) — ETHAN_API=$(_ethan_base) ?" >&2
      return 1
      ;;
    422)
      echo "ERR: requête rejetée (HTTP 422) — charge utile non conforme au schéma Core" >&2
      return 1
      ;;
    503)
      echo "ERR: NATS non connecté (HTTP 503) — l'API ne peut pas émettre d'événement" >&2
      return 1
      ;;
    *)
      echo "ERR: HTTP $code — $out" >&2
      return 1
      ;;
  esac
}

_ethan_status() {
  local base body code rc fallback
  base="$(_ethan_base)"
  _ethan_auth_args
  fallback='{"mode":"offline","active_goal":null,"running_tasks":0,"modules_active":[]}'
  body="$(mktemp)"

  # -o dans un fichier, -w pour le code : VERIFIE VIVANT le 30/09/2026, un
  # 401 sans token renvoie un corps JSON {"detail": "..."} non vide. L'ancien
  # `curl || echo fallback` le prenait pour l'etat reel et l'affichait tel quel.
  code="$(curl -s --max-time 5 "${base%/}/v1/state" \
    ${_ETHAN_AUTH[@]+"${_ETHAN_AUTH[@]}"} -o "$body" -w '%{http_code}' 2>/dev/null)"
  rc=$?

  case "$code" in
    2*)
      cat "$body"
      ;;
    401|403)
      echo "ERR: authentification requise (HTTP $code) — export ETHAN_TOKEN=<jwt>" >&2
      printf '%s\n' "$fallback"
      ;;
    *)
      # Un etat inconnu s'affiche « offline », jamais invente. Et on le dit.
      if [[ "$rc" -ne 0 || -z "$code" || "$code" == "000" ]]; then
        echo "INFO: API injoignable ($base) — état affiché offline" >&2
      else
        echo "INFO: HTTP $code sur /v1/state — état affiché offline" >&2
      fi
      printf '%s\n' "$fallback"
      ;;
  esac
  rm -f "$body"
}

# Nom du binaire CLI réel. Deux pièges :
#  1. `ethan-cli` est l'ancien nom — interfaces/cli/pyproject.toml déclare
#     `[project.scripts] ethan`. On accepte les deux, sans supposer.
#  2. Dans les adaptateurs, `ethan` est une FONCTION shell qui masquerait le
#     binaire : `type -P` ne résout que sur le disque.
_ethan_cli() {
  local candidate
  for candidate in ethan-cli ethan; do
    if [[ -n "$(type -P "$candidate" 2>/dev/null)" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

_ethan_history_record() {
  local type="$1"
  local text="$2"
  local cli
  cli="$(_ethan_cli 2>/dev/null)" || return 0
  "$cli" suggest --record "$type" "$text" >/dev/null 2>&1 || true
}