"""Plugin Sandbox Runtime — Point d'entrée pour le service systemd."""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

logger = logging.getLogger(__name__)


class PluginRuntime:
    """Runtime principal pour l'exécution des plugins."""

    def __init__(self):
        self.running = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Configure les gestionnaires de signaux pour un arrêt propre."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Gestionnaire de signal pour l'arrêt propre."""
        logger.info(f"Signal reçu: {signum}")
        self.running = False

    async def start(self):
        """Démarre le runtime des plugins."""
        logger.info("◆ ETHAN Plugin Runtime")
        logger.info("  Initializing plugin sandbox...")
        
        self.running = True
        logger.info("  ✓ Plugin runtime ready")
        logger.info("  Listening for plugin requests...")

        # Boucle principale
        while self.running:
            await asyncio.sleep(1)

    async def stop(self):
        """Arrête le runtime proprement."""
        logger.info("  Shutting down plugin runtime...")
        self.running = False


def main():
    """Point d'entrée principal."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    runtime = PluginRuntime()
    
    try:
        asyncio.run(runtime.start())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        asyncio.run(runtime.stop())
        logger.info("✓ Plugin runtime stopped")


if __name__ == "__main__":
    main()