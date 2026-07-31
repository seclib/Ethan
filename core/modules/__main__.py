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
from core.telemetry.logger import setup_logging

logger = logging.getLogger(__name__)


async def main():
    nats_url = os.getenv("NATS_URL", "nats://nats:4222")
    log_level = os.getenv("LOG_LEVEL", "INFO")

    setup_logging(log_level)

    logger.info("Modules service connecting to NATS: %s", nats_url)

    bus = NatsEventBus(servers=nats_url)

    # Retry NATS connection.  Each attempt is bounded and the final
    # connection error is propagated so Docker can restart the service.
    connect_attempts = int(os.getenv("CONNECT_ATTEMPTS", "10"))
    connect_timeout = float(os.getenv("CONNECT_TIMEOUT", "10"))
    if connect_attempts < 1:
        raise ValueError("CONNECT_ATTEMPTS must be >= 1")
    if connect_timeout <= 0:
        raise ValueError("CONNECT_TIMEOUT must be > 0")
    startup_deadline = asyncio.get_running_loop().time() + float(
        os.getenv("DEPENDENCY_STARTUP_TIMEOUT", "180")
    )
    for attempt in range(1, connect_attempts + 1):
        try:
            remaining = startup_deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise asyncio.TimeoutError("Modules dependency startup deadline exceeded")
            await asyncio.wait_for(bus.connect(), timeout=min(connect_timeout, remaining))
            logger.info("Modules service connected to NATS")
            break
        except Exception as exc:
            if attempt == connect_attempts:
                logger.error("Modules service could not connect to NATS", exc_info=True)
                try:
                    await asyncio.wait_for(bus.disconnect(), timeout=5)
                except Exception:
                    logger.exception("NATS cleanup failed after connection error")
                raise
            wait = min(attempt * 2, 10)
            wait = min(wait, max(0.0, startup_deadline - asyncio.get_running_loop().time()))
            logger.warning(
                "NATS connection failed (%s), retry %s/%s in %ss",
                exc, attempt, connect_attempts, wait,
            )
            await asyncio.sleep(wait)

    # Readiness is only granted once every configured module has initialized
    # and its own NATS/Redis clients are usable.  A process with a live NATS
    # connection but a failed cognitive module must remain unhealthy.
    health_state: dict[str, object] = {
        "initializing": True,
        "module_status": {},
        "ready": False,
    }
    modules = []

    # ── Health server (port 8081) for Docker healthcheck ──────────────
    async def _health_handler(reader, writer):
        """Serve liveness and readiness probes over HTTP."""
        import json

        request = await reader.read(1024)
        try:
            path = request.decode("ascii", errors="replace").split(" ", 2)[1]
        except (IndexError, UnicodeDecodeError):
            path = "/"

        if path == "/health/live":
            payload = {"status": "ok", "service": "modules"}
            code = 200
        elif path in {"/health", "/health/ready"}:
            module_status = health_state["module_status"]
            module_ok = bool(health_state["ready"])
            nats_ok = bus.is_connected
            redis_ok = True
            for module in modules:
                redis_client = getattr(module, "redis", None)
                if redis_client is None:
                    continue
                try:
                    await asyncio.wait_for(redis_client.ping(), timeout=2)
                except Exception:
                    redis_ok = False
            module_nats_ok = all(
                getattr(module, "nc", None) is not None
                and getattr(module.nc, "is_connected", False)
                for module in modules
                if module_status.get(getattr(module, "module_id", "")) == "ready"
            )
            ready = module_ok and nats_ok and redis_ok and module_nats_ok
            payload = {
                "status": "ok" if ready else "degraded",
                "service": "modules",
                "nats_connected": nats_ok,
                "module_nats_connected": module_nats_ok,
                "redis_connected": redis_ok,
                "modules": module_status,
            }
            code = 200 if ready else 503
        else:
            payload = {"error": "not found"}
            code = 404

        body = json.dumps(payload, separators=(",", ":"))
        reason = "OK" if code == 200 else "Service Unavailable" if code == 503 else "Not Found"
        response = (
            f"HTTP/1.1 {code} {reason}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(body.encode())}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{body}"
        )
        writer.write(response.encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    health_server = await asyncio.start_server(_health_handler, "0.0.0.0", 8081)
    logger.info("Modules health server listening on :8081")

    # ── Wire cognitive modules ───────────────────────────────────────
    from core.modules.executive.main import ExecutiveModule
    from core.modules.planner.main import PlannerModule
    from core.modules.memory.main import MemoryModule
    from core.modules.reflective.main import ReflectiveModule
    from core.ethan_types.sdk.module import ModuleContext

    modules.extend([
        ExecutiveModule(),
        PlannerModule(),
        MemoryModule(),
        ReflectiveModule(),
    ])

    for mod in modules:
        manifest = mod.get_manifest()
        module_key = manifest.id
        try:
            ctx = ModuleContext(
                module_id=manifest.id,
                nats_url=nats_url,
                config={"redis_url": os.getenv("REDIS_URL", "redis://localhost:6379/0")},
            )
            await asyncio.wait_for(mod.initialize(ctx), timeout=10)
            health_state["module_status"][module_key] = "ready"
            logger.info("Module registered: %s capabilities=%s", manifest.name, manifest.capabilities)
        except Exception as exc:
            health_state["module_status"][module_key] = f"error: {type(exc).__name__}"
            mod_name = manifest.name
            logger.error("Module registration failed: %s (%s)", mod_name, exc, exc_info=True)
            # A cognitive module is a critical dependency of this service.
            # Do not leave a live process that can only ever be unhealthy;
            # clean up and propagate the original exception to the supervisor.
            health_server.close()
            await health_server.wait_closed()
            for started in reversed(modules):
                try:
                    await asyncio.wait_for(started.shutdown(), timeout=10)
                except Exception:
                    logger.exception("Module cleanup failed: %s", type(started).__name__)
            try:
                await asyncio.wait_for(bus.disconnect(), timeout=10)
            except Exception:
                logger.exception("NATS cleanup failed after module startup error")
            raise RuntimeError(f"Module {mod_name} failed to start") from exc

    health_state["initializing"] = False
    health_state["ready"] = all(
        status == "ready" for status in health_state["module_status"].values()
    ) and len(health_state["module_status"]) == len(modules)

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
    health_server.close()
    await health_server.wait_closed()
    for mod in reversed(modules):
        try:
            await asyncio.wait_for(mod.shutdown(), timeout=10)
        except Exception as exc:
            logger.warning("Module shutdown failed: %s", exc)
    await asyncio.wait_for(bus.disconnect(), timeout=10)
    logger.info("Modules service stopped")


if __name__ == "__main__":
    asyncio.run(main())
