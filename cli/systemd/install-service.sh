#!/bin/bash
set -e
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== ETHAN systemd service installer =="
read -p "Install as (u)ser or (s)ystem? [u/s]: " -r mode

case "$mode" in
  s)
    DEST="/etc/systemd/system"
    echo "Installing system-wide service..."
    sudo install -m 644 "$SRC/ethan.service" "$DEST/ethan.service"
    sudo systemctl daemon-reload
    echo "Done. Enable with:"
    echo "  sudo systemctl enable ethan.service"
    echo "  sudo systemctl start ethan.service"
    echo "  sudo systemctl status ethan.service"
    ;;
  *)
    DEST="${HOME}/.config/systemd/user"
    mkdir -p "$DEST"
    install -m 644 "$SRC/ethan.service" "$DEST/ethan.service"
    systemctl --user daemon-reload
    echo "Done. Enable with:"
    echo "  systemctl --user enable ethan.service"
    echo "  systemctl --user start ethan.service"
    echo "  systemctl --user status ethan.service"
    ;;
esac