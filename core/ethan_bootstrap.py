"""Bootstrap — Entry point for the Cognitive Kernel service."""

from __future__ import annotations

import asyncio
import logging
import os
import signal

from core.autonomy.controller import AutonomyLoopController
from core.bootstrap.bootstrapper import SystemBootstrapper
from core.bus.nats_bus import EventBus as NatsEventBus
from core.goals.manager import GoalManager
from core.kernel import CognitiveKernel
from core.learning.engine import LearningEngine
from core.learning.detector import PatternDetector
from core.learning.generator import RuleGenerator
from core.learning.modeler import SelfModelUpdater
from core.learning.store import ExperienceStore
from core.metacognition.engine import MetaCognitionEngine
from core.metacognition.load import CognitiveLoadManager
from core.metacognition.prioritizer import ModulePrioritizer
from core.metacognition.strategy import DecisionStrategySelector
from core.metacognition.trace import ThoughtTraceAnalyzer
from core.registry.capability import CapabilityRegistry
from core.registry.module import ModuleRegistry
from core.scheduler.scheduler import Scheduler
from core.state.composite_backend import CompositeStateBackend
from core.state.postgres_state import PostgresPersistentState
from core.state.redis_state import RedisLiveState
from core.telemetry.logger import setup_logging

logger = logging.getLogger(__name__)


async def _connect_with_retries(
    name: str,
    operation,
    *,
    timeout: float,
    attempts: int,
    retry_delay: float,
    deadline: float | None = None,
):
    """Run one critical dependency connection with bounded retries.

    Every attempt has an actual ``wait_for`` deadline.  The sleep is only a
    bounded backoff between attempts; it never substitutes for an operation
    timeout.  The last exception is chained and re-raised unchanged.
    """
    if attempts < 1:
        raise ValueError(f"{name} connection attempts must be >= 1")
    if timeout <= 0:
        raise ValueError(f"{name} connection timeout must be > 0")

    for attempt in range(1, attempts + 1):
        try:
            remaining = None if deadline is None else deadline - asyncio.get_running_loop().time()
            if remaining is not None and remaining <= 0:
                raise asyncio.TimeoutError(f"{name} startup deadline exceeded")
            return await asyncio.wait_for(
                operation(), timeout=timeout if remaining is None else min(timeout, remaining)
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if attempt == attempts:
                logger.error("%s connection failed after %s attempts", name, attempts)
                raise
            delay = min(retry_delay * attempt, 10.0)
            if deadline is not None:
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    raise
                delay = min(delay, remaining)
            logger.warning(
                "%s connection failed (%s), retry %s/%s in %.1fs",
                name,
                exc,
                attempt,
                attempts,
                delay,
            )
            await asyncio.sleep(delay)


async def _close_startup_dependencies(bus, redis, pg) -> None:
    """Best-effort cleanup when a dependency/bootstrap step aborts startup.

    Cleanup is bounded and never replaces the original startup exception.  A
    partially-connected client is still closed so retries/restarts do not
    inherit sockets or pools from a failed attempt.
    """
    for name, resource in (("PostgreSQL", pg), ("Redis", redis), ("NATS", bus)):
        close = getattr(resource, "close", None)
        if close is None:
            continue
        try:
            await asyncio.wait_for(close(), timeout=5)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("%s cleanup failed after startup error", name)


async def main():
    """Start the Cognitive Kernel with optional Learning + Meta-Cognition + Autonomy + Bootstrap."""
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://ethan:ethan_dev_pass@localhost:5432/ethan",
    )
    log_level = os.getenv("LOG_LEVEL", "INFO")
    enable_learning = os.getenv("ENABLE_LEARNING", "false").lower() == "true"
    enable_metacognition = os.getenv("ENABLE_METACOGNITION", "false").lower() == "true"
    enable_autonomy = os.getenv("ENABLE_AUTONOMY", "false").lower() == "true"
    connect_timeout = int(os.getenv("CONNECT_TIMEOUT", "10"))
    connect_attempts = int(os.getenv("CONNECT_ATTEMPTS", "10"))
    dependency_deadline = asyncio.get_running_loop().time() + float(
        os.getenv("DEPENDENCY_STARTUP_TIMEOUT", "180")
    )

    setup_logging(log_level)
    logger.info("Cognitive Kernel bootstrapping... learning=%s metacognition=%s autonomy=%s",
                enable_learning, enable_metacognition, enable_autonomy)

    bus = NatsEventBus(servers=nats_url)
    redis = RedisLiveState(redis_url)
    pg = PostgresPersistentState(database_url)

    # ── Résilience : retry borné + timeout par tentative ─────────────
    try:
        await _connect_with_retries(
            "NATS", bus.connect, timeout=connect_timeout,
            attempts=connect_attempts, retry_delay=2,
            deadline=dependency_deadline,
        )
        logger.info("NATS connection established")
        await _connect_with_retries(
            "Redis", redis.connect, timeout=connect_timeout,
            attempts=connect_attempts, retry_delay=2,
            deadline=dependency_deadline,
        )
        logger.info("Redis connection established")
        await _connect_with_retries(
            "PostgreSQL", pg.connect, timeout=connect_timeout,
            attempts=connect_attempts, retry_delay=2,
            deadline=dependency_deadline,
        )
        logger.info("PostgreSQL connection established")
    except BaseException:
        await _close_startup_dependencies(bus, redis, pg)
        raise

    # Run system bootstrap (integrity check + repair) with timeout
    bootstrapper = SystemBootstrapper(bus, redis, pg)
    bootstrap_ok = True
    bootstrap_timeout = float(os.getenv("BOOTSTRAP_TIMEOUT", "120"))
    try:
        bootstrap_ok = await asyncio.wait_for(
            bootstrapper.run(), timeout=bootstrap_timeout
        )
    except BaseException:
        await _close_startup_dependencies(bus, redis, pg)
        raise
    if not bootstrap_ok:
        await _close_startup_dependencies(bus, redis, pg)
        raise RuntimeError("Bootstrap integrity checks failed")

    scheduler = Scheduler(bus)
    capability_registry = CapabilityRegistry()
    registry = ModuleRegistry(bus, capability_registry)
    goals = GoalManager(bus, pg, redis)

    learning = None
    if enable_learning:
        store = ExperienceStore(redis, pg)
        detector = PatternDetector(threshold=3)
        generator = RuleGenerator()
        modeler = SelfModelUpdater(redis)
        learning = LearningEngine(bus, store, detector, generator, modeler)
        logger.info("Learning Engine initialized")

    metacognition = None
    if enable_metacognition:
        strategy = DecisionStrategySelector()
        load_manager = CognitiveLoadManager()
        prioritizer = ModulePrioritizer()
        trace_analyzer = ThoughtTraceAnalyzer()
        metacognition = MetaCognitionEngine(
            bus=bus,
            redis=redis,
            strategy=strategy,
            load_manager=load_manager,
            prioritizer=prioritizer,
            trace_analyzer=trace_analyzer,
        )
        logger.info("Meta-Cognition Engine initialized")

    autonomy = None
    if enable_autonomy:
        autonomy = AutonomyLoopController(bus=bus, redis=redis)
        logger.info("Autonomy Loop Controller initialized")

    # Create composite state backend for Kernel (Clean Architecture)
    state = CompositeStateBackend(redis, pg)
    
    kernel = CognitiveKernel(
        bus=bus,
        state=state,
        registry=registry,
        goals=goals,
        scheduler=scheduler,
        learning=learning,
        metacognition=metacognition,
        autonomy=autonomy,
    )

    try:
        await asyncio.wait_for(kernel.start(), timeout=30)
    except asyncio.TimeoutError as exc:
        logger.error("Kernel start timed out after 30s")
        raise RuntimeError("Kernel failed to start within timeout") from exc
    # ── Health server (port 8080) for Docker healthcheck ──────────────
    async def _health_handler(reader, writer):
        """Serve liveness and readiness probes for the kernel."""
        request = await reader.read(1024)
        try:
            path = request.decode("ascii", errors="replace").split(" ", 2)[1]
        except (IndexError, UnicodeDecodeError):
            path = "/"

        if path == "/health/live":
            body = '{"status":"ok","service":"kernel"}'
            code = 200
            reason = "OK"
        elif path in {"/health", "/health/ready"}:
            nats_ok = bus.is_connected if hasattr(bus, 'is_connected') else False
            redis_ok = False
            try:
                if hasattr(redis, '_redis') and redis._redis is not None:
                    await asyncio.wait_for(redis._redis.ping(), timeout=2)
                    redis_ok = True
            except Exception:
                redis_ok = False
            pg_ok = False
            try:
                if hasattr(pg, '_pool') and pg._pool is not None:
                    conn = await asyncio.wait_for(pg._pool.acquire(), timeout=2)
                    try:
                        await asyncio.wait_for(conn.execute("SELECT 1"), timeout=2)
                    finally:
                        await asyncio.wait_for(pg._pool.release(conn), timeout=2)
                    pg_ok = True
            except Exception:
                pg_ok = False
            running = kernel._running if hasattr(kernel, '_running') else False
            all_ok = running and bootstrap_ok and nats_ok and redis_ok and pg_ok
            status = "ok" if all_ok else "degraded"
            code = 200 if all_ok else 503
            reason = 'OK' if code == 200 else 'Service Unavailable'
            body = (
                '{"status":"' + status + '","service":"kernel","running":' + str(running).lower()
                + ',"nats":' + str(nats_ok).lower() + ',"redis":' + str(redis_ok).lower()
                + ',"postgresql":' + str(pg_ok).lower() + ',"bootstrap":' + str(bootstrap_ok).lower() + '}'
            )
        else:
            body = '{"error":"not found"}'
            code = 404
            reason = "Not Found"

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

    health_server = await asyncio.start_server(_health_handler, "0.0.0.0", 8080)
    logger.info("Kernel health server listening on :8080")

    # ── Gestion des signaux (asyncio.get_event_loop() déprécié depuis 3.10) ──
    stop = asyncio.get_running_loop().create_future()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop = asyncio.get_running_loop()
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(_shutdown(kernel, stop)),
            )
        except NotImplementedError:
            signal.signal(sig, lambda s, f: asyncio.create_task(_shutdown(kernel, stop)))

    await stop
    health_server.close()
    await health_server.wait_closed()
    logger.info("Kernel bootstrap complete, awaiting shutdown")


async def _shutdown(kernel: CognitiveKernel, stop: asyncio.Future):
    logger.info("Shutdown signal received")
    try:
        await asyncio.wait_for(kernel.stop(), timeout=15)
    except asyncio.TimeoutError:
        logger.error("Kernel stop timed out after 15s")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    if not stop.done():
        stop.set_result(None)


if __name__ == "__main__":
    asyncio.run(main())
