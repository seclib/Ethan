#!/bin/bash
# ETHAN systemd service installer
set -e

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== ETHAN systemd service installer =="
echo "  1) User service (~/.config/systemd/user/)"
echo "  2) System service (/etc/systemd/system/) — requires sudo"
read -p "Choice [1/2]: " -r mode

case "$mode" in
  2)
    DEST="/etc/systemd/system"
    echo "Installing system-wide service..."
    sudo install -m 644 "$SRC/ethan.service" "$DEST/ethan.service"
    sudo systemctl daemon-reload
    echo "Done. Enable with:"
    echo "  sudo systemctl enable ethan.service"
    echo "  sudo systemctl start ethan.service"
    echo "  sudo systemctl status ethan.service"
    echo "  journalctl -u ethan.service -f"
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
    echo "  journalctl --user -u ethan.service -f"
    ;;
esac