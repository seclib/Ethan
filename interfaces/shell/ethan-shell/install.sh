#!/bin/bash
# ETHAN Shell Integration Layer — installer
#
# Usage :
#   bash install.sh                        # detecte le shell courant ($SHELL)
#   bash install.sh --shells bash,zsh,fish # shells choisis explicitement
#
# zsh et fish sont OPTIONNELS : ETHAN fonctionne sans. L'adaptateur s'installe
# meme si le binaire n'est pas encore present (il sera charge au prochain
# demarrage du shell) ; la commande d'installation du shell est rappelee.
# Rien n'echoue si un shell manque, rien n'est installe sans consentement.
set -e

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF="${HOME}/.config/ethan-shell"
ALL_SHELLS="bash zsh fish"

echo "== ETHAN Shell Integration Layer =="
echo

# 0. Arguments
SHELLS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --shells)
      shift
      [ $# -ge 1 ] || { echo "ERROR: --shells exige une liste (ex: bash,zsh,fish)"; exit 2; }
      SHELLS="${1//,/ }"
      ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "ERROR: option inconnue: $1"; exit 2 ;;
  esac
  shift
done

# 1. Detect shell (defaut : $SHELL)
detect_shell() {
  local sh="${SHELL##*/}"
  case "$sh" in
    bash|zsh|fish) echo "$sh" ;;
    *)             echo bash ;;  # default
  esac
}

[ -n "$SHELLS" ] || SHELLS="$(detect_shell)"

for sh in $SHELLS; do
  case " $ALL_SHELLS " in
    *" $sh "*) ;;
    *) echo "ERROR: shell inconnu: $sh (valides: $ALL_SHELLS)"; exit 2 ;;
  esac
done

echo "Shells cibles: $SHELLS"

# 2. Create config dirs
mkdir -p "$CONF/adapters"
mkdir -p "$CONF/cli"
mkdir -p "${HOME}/.local/bin"

# 3. core.sh d'abord : source unique de vérité du contrat API, sourcé par les
# adaptateurs bash/zsh. S'il manque, l'adaptateur perd ses fonctions.
cp "$SRC/cli/core.sh" "$CONF/cli/core.sh"

# 4. Symlink cli tools
for f in "$SRC"/cli/*.sh; do
  name="$(basename "${f%.sh}")"
  ln -sf "$f" "${HOME}/.local/bin/$name"
done

# 5. Adapter + source line, pour chaque shell cible. Un binaire absent ne
# bloque pas : zsh et fish sont optionnels, installables a la demande.
for SHELL_NAME in $SHELLS; do
  ADAPTER="$SRC/adapters/$SHELL_NAME/ethan.$SHELL_NAME"
  if [ ! -f "$ADAPTER" ]; then
    echo "ERROR: adapter not found: $ADAPTER"
    exit 1
  fi
  cp "$ADAPTER" "$CONF/adapters/ethan.$SHELL_NAME"

  if ! command -v "$SHELL_NAME" >/dev/null 2>&1; then
    echo "NOTE: '$SHELL_NAME' absent du systeme (optionnel). Pour l'activer : sudo apt install $SHELL_NAME"
  fi

  RC_FILE=""
  case "$SHELL_NAME" in
    bash) RC_FILE="${HOME}/.bashrc" ;;
    zsh)  RC_FILE="${HOME}/.zshrc" ;;
    fish) RC_FILE="${HOME}/.config/fish/config.fish"; mkdir -p "$(dirname "$RC_FILE")" ;;
  esac

  if ! grep -q "ethan-shell" "$RC_FILE" 2>/dev/null; then
    {
      echo ""
      echo "# ETHAN Shell Integration Layer"
      case "$SHELL_NAME" in
        bash|zsh) echo "source $CONF/adapters/ethan.$SHELL_NAME" ;;
        fish)     echo "source $CONF/adapters/ethan.fish" ;;
      esac
    } >> "$RC_FILE"
    echo "Added source line to $RC_FILE"
  fi
done

# 6. Wrapper command
# COLLISION CORRIGÉE : ce wrapper s'appelait « ethan », nom déjà détenu par
# l'entrypoint CLI (interfaces/cli/pyproject.toml : [project.scripts] ethan).
# Résultat mesuré : `.venv/bin/ethan` (CLI) et `~/.local/bin/ethan` (ESIL)
# cohabitaient, le wrapper shell masquait la CLI selon l'ordre du PATH.
# Le nom « ethan-shell-send » est sans collision ; la fonction `ethan` de
# l'adaptateur reste le point d'entrée habituel pour l'utilisateur.
ln -sf "$SRC/cli/send.sh" "${HOME}/.local/bin/ethan-shell-send"

echo
echo "Installation complete."
echo "  Config:     $CONF"
echo "  RC file:    $RC_FILE"
echo "  Wrapper:    ~/.local/bin/ethan-shell-send"
echo
echo "Run: source $RC_FILE"
echo "Then: ethan \"hello\""
echo
echo "L'API exige un JWT : export ETHAN_TOKEN=\$(...)"
echo "  (secret — ne jamais committer ; voir .env.example ou Vault)"