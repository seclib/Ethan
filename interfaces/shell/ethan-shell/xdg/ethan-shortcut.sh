#!/bin/bash
# ESIL XDG desktop shortcuts — XFCE / GNOME / generic
set -e

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAUNCHER="$SRC/launcher/ethan-launcher.sh"
CHAT="ethan chat"

install_xdg() {
  # Generic .desktop launcher
  local desktop_file="$1"
  mkdir -p "$(dirname "$desktop_file")"
  cat > "$desktop_file" <<EOF
[Desktop Entry]
Type=Application
Name=ETHAN Launcher
Exec=$LAUNCHER
Icon=utilities-terminal
Terminal=true
Categories=Utility;AI;System;
EOF
  chmod 644 "$desktop_file"
  echo "Desktop entry: $desktop_file"
}

install_xfce() {
  local dir="$HOME/.config/xfce4"
  mkdir -p "$dir"
  # xfconf-query hotkey
  if command -v xfconf-query >/dev/null 2>&1; then
    xfconf-query -c xfce4-keyboard-shortcuts \
      -n -t string \
      -p "/commands/custom/<Super>space" \
      -s "$LAUNCHER" >/dev/null 2>&1 || true
    echo "XFCE hotkey set: Super+Space → launcher"
  fi
  install_xdg "$dir/xfce/ethan-launcher.desktop"
}

install_gnome() {
  local dir="$HOME/.local/share/applications"
  install_xdg "$dir/ethan-launcher.desktop"
  if command -v gsettings >/dev/null 2>&1; then
    gsettings set org.gnome.settings-daemon.plugins.media-keys \
      custom-keybindings \
      "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/']" >/dev/null 2>&1 || true
    echo "GNOME custom keybinding registered (manual path edit required)"
  fi
}

echo "== ETHAN XDG shortcuts =="
echo "DE: ${XDG_CURRENT_DESKTOP:-unknown}"
echo

case "${XDG_CURRENT_DESKTOP:-}" in
  *XFCE*)   install_xfce ;;
  *GNOME*)  install_gnome ;;
  *)        install_xdg "$HOME/.local/share/applications/ethan-launcher.desktop" ;;
esac

echo
echo "Done."
echo "  Launcher: ethan-launcher"
echo "  Chat:     ethan chat"
echo "  Shortcut: Super+Space (XFCE) or custom shortcut (GNOME)"