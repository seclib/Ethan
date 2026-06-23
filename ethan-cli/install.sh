#!/bin/bash
set -e

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="${HOME}/.local/bin"
APPS="${HOME}/.local/share/applications"

mkdir -p "$BIN" "$APPS"

# Install the ethan command
install -m 755 "$SRC/ethan" "$BIN/ethan"

# Install Python src modules
DEST_SRC="$BIN/src"
mkdir -p "$DEST_SRC"
for f in "$SRC"/src/__init__.py "$SRC/src/client.py" "$SRC/src/cli.py" "$SRC/src/daemon.py" "$SRC/src/memory.py"; do
  install -m 644 "$f" "$DEST_SRC/$(basename "$f")"
done

# Install desktop entry
install -m 644 "$SRC/xfce/ethan.desktop" "$APPS/ethan.desktop"

echo "ETHAN CLI installed to $BIN/ethan"
echo "  Run: ethan --help"
echo
echo "Make sure $BIN is in your PATH:"
echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""