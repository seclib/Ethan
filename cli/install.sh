#!/bin/bash
set -e
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${HOME}/.local/bin"
mkdir -p "$DEST"
install -m 755 "$SRC/ethan" "$DEST/ethan"
cp -r "$SRC/registry.py" "$DEST/registry.py"
cp -r "$SRC/plugin_manager.py" "$DEST/plugin_manager.py"
cp -r "$SRC/core" "$DEST/core"
cp -r "$SRC/commands" "$DEST/commands"
echo "Installed: $DEST/ethan (+ registry + plugin_manager + core + commands)"
echo
echo "Add to PATH if needed:"
echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""