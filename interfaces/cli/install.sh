#!/bin/bash
# Installe le CLI ETHAN comme commande locale `ethan-cli`.
# Le CLI est un client de l'API Core : il s'exécute avec la racine du dépôt
# dans PYTHONPATH (imports interfaces.cli.*).
set -e
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${SRC}/../.." && pwd)"
DEST="${HOME}/.local/bin"
mkdir -p "${DEST}"

cat > "${DEST}/ethan-cli" <<WRAPPER
#!/usr/bin/env bash
export PYTHONPATH="${REPO}:\${PYTHONPATH:-}"
exec python3 -m interfaces.cli.main "\$@"
WRAPPER
chmod 755 "${DEST}/ethan-cli"

echo "Installed: ${DEST}/ethan-cli"
echo
echo "Add to PATH if needed:"
echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""