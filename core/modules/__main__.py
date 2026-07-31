"""Entry point for the modules service.

This allows running: python -m core.modules
The kernel loads builtin modules; this service provides additional module processes.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal

from core.bus.nats_bus import EventBus as NatsEventBus

logger = logging.getLogger(__name__)


async def main():
    nats_url = os.getenv("NATS_URL", "nats://nats:4222")
    log_level = os.getenv("LOG_LEVEL", "INFO")

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logger.info("Modules service connecting to NATS: %s", nats_url)

    bus = NatsEventBus(servers=nats_url)
    await bus.connect()
    logger.info("Modules service connected to NATS")

    # Keep running until SIGTERM/SIGINT
    stop = asyncio.get_running_loop().create_future()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop = asyncio.get_running_loop()
            loop.add_signal_handler(
                sig,
                lambda: stop.set_result(None),
            )
        except NotImplementedError:
            signal.signal(sig, lambda s, f: stop.set_result(None))

    await stop
    await bus.disconnect()
    logger.info("Modules service stopped")


if __name__ == "__main__":
    asyncio.run(main())