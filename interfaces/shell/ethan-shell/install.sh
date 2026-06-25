#!/bin/bash
# ETHAN Shell Integration Layer — installer
set -e

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF="${HOME}/.config/ethan-shell"

echo "== ETHAN Shell Integration Layer =="
echo

# 1. Detect shell
detect_shell() {
  local sh="${SHELL##*/}"
  case "$sh" in
    bash) echo bash ;;
    zsh)  echo zsh  ;;
    fish) echo fish ;;
    *)    echo bash ;;  # default
  esac
}

SHELL_NAME="$(detect_shell)"
echo "Detected shell: $SHELL_NAME"

# 2. Create config dirs
mkdir -p "$CONF/adapters"
mkdir -p "${HOME}/.local/bin"

# 3. Copy adapter
ADAPTER="$SRC/adapters/$SHELL_NAME/ethan.$SHELL_NAME"
if [ ! -f "$ADAPTER" ]; then
  echo "ERROR: adapter not found: $ADAPTER"
  exit 1
fi
cp "$ADAPTER" "$CONF/adapters/ethan.$SHELL_NAME"

# 4. Symlink cli tools
for f in "$SRC"/cli/*.sh; do
  name="$(basename "${f%.sh}")"
  ln -sf "$f" "${HOME}/.local/bin/$name"
done

# 5. Source line
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

# 6. Wrapper command
ln -sf "$SRC/cli/send.sh" "${HOME}/.local/bin/ethan"

echo
echo "Installation complete."
echo "  Config:     $CONF"
echo "  RC file:    $RC_FILE"
echo "  Wrapper:    ~/.local/bin/ethan"
echo
echo "Run: source $RC_FILE"
echo "Then: ethan \"hello\""