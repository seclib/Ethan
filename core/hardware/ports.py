"""Gestionnaire d'allocation et de vérification des ports TCP locaux.

Évite les collisions de ports entre services et vérifie la disponibilité
avant tout bind ou lancement de serveur local.
"""

from __future__ import annotations

import socket


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Vérifie si un port TCP est actuellement en écoute."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.25)
        try:
            s.connect((host, port))
            return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            return False


def find_free_port(start_port: int = 8000, max_offset: int = 30, host: str = "127.0.0.1") -> int:
    """Trouve le premier port TCP libre dans la plage [start_port, start_port + max_offset].

    Args:
        start_port: Port de départ
        max_offset: Nombre d'incréments à tester
        host: Hôte local

    Returns:
        Numéro du premier port libre trouvé.

    Raises:
        RuntimeError: Si aucun port libre n'est disponible dans la plage.
    """
    for offset in range(max_offset + 1):
        port = start_port + offset
        if not is_port_in_use(port, host=host):
            return port

    raise RuntimeError(
        f"Aucun port libre trouvé entre {start_port} et {start_port + max_offset} sur {host}."
    )
