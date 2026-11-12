"""Resilience and lifecycle management for ETHAN application integration (MEM-014 Phase 6)."""

from __future__ import annotations

import asyncio
import random
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Callable, Iterable, Mapping, TypeVar

T = TypeVar("T")


class LifecycleState(StrEnum):
    REGISTERED = "registered"
    VALIDATED = "validated"
    READY = "ready"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


# Compatibility aliases.
ApplicationLifecycleState = LifecycleState
IntegrationLifecycleState = LifecycleState


_TRANSITIONS: dict[LifecycleState, frozenset[LifecycleState]] = {
    LifecycleState.REGISTERED: frozenset({LifecycleState.VALIDATED, LifecycleState.FAILED, LifecycleState.UNKNOWN}),
    LifecycleState.VALIDATED: frozenset({LifecycleState.READY, LifecycleState.FAILED, LifecycleState.UNKNOWN}),
    LifecycleState.READY: frozenset({LifecycleState.STARTING, LifecycleState.FAILED, LifecycleState.UNKNOWN}),
    LifecycleState.STARTING: frozenset({LifecycleState.RUNNING, LifecycleState.FAILED, LifecycleState.STOPPED, LifecycleState.UNKNOWN}),
    LifecycleState.RUNNING: frozenset({LifecycleState.DEGRADED, LifecycleState.STOPPING, LifecycleState.STOPPED, LifecycleState.FAILED, LifecycleState.UNKNOWN}),
    LifecycleState.DEGRADED: frozenset({LifecycleState.RUNNING, LifecycleState.STOPPING, LifecycleState.STOPPED, LifecycleState.FAILED, LifecycleState.UNKNOWN}),
    LifecycleState.STOPPING: frozenset({LifecycleState.STOPPED, LifecycleState.FAILED, LifecycleState.UNKNOWN}),
    LifecycleState.STOPPED: frozenset({LifecycleState.READY, LifecycleState.STARTING, LifecycleState.REGISTERED, LifecycleState.VALIDATED, LifecycleState.UNKNOWN}),
    LifecycleState.FAILED: frozenset({LifecycleState.REGISTERED, LifecycleState.VALIDATED, LifecycleState.READY, LifecycleState.UNKNOWN}),
    LifecycleState.UNKNOWN: frozenset(set(LifecycleState)),
}


class LifecycleTransitionError(ValueError):
    """Raised when a lifecycle transition is not allowed."""


class ErrorKind(StrEnum):
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


def classify_error(error: BaseException | None) -> ErrorKind:
    if error is None:
        return ErrorKind.UNKNOWN
    if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
        return ErrorKind.TIMEOUT
    if isinstance(error, (KeyboardInterrupt, asyncio.CancelledError)):
        return ErrorKind.CANCELLED
    name = type(error).__name__.lower()
    message = str(error).lower()
    permanent_markers = ("not found", "invalid", "permission", "unauthorized", "permanent", "fatal")
    transient_markers = ("timeout", "temporarily", "connection", "network", "unavailable", "busy", "rate limit")
    if any(marker in name or marker in message for marker in permanent_markers):
        return ErrorKind.PERMANENT
    if any(marker in name or marker in message for marker in transient_markers):
        return ErrorKind.TRANSIENT
    return ErrorKind.UNKNOWN


@dataclass(slots=True)
class RetryPolicy:
    """Bounded retry policy."""

    max_attempts: int = 3
    base_delay: float = 0.1
    multiplier: float = 2.0
    max_delay: float = 2.0
    jitter: float = 0.0
    retry_transient_only: bool = True
    retry_unknown: bool = True

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if self.base_delay < 0 or self.max_delay < 0:
            raise ValueError("delays must be non-negative")

    def delay_for(self, attempt: int, rng: random.Random) -> float:
        raw = self.base_delay * (self.multiplier ** max(0, attempt - 1))
        capped = min(raw, self.max_delay)
        if self.jitter > 0:
            capped += rng.random() * self.jitter
        return min(capped, self.max_delay + self.jitter)

    def should_retry(self, kind: ErrorKind, idempotent: bool, attempt: int) -> bool:
        if attempt >= self.max_attempts:
            return False
        if not idempotent:
            return False
        if kind == ErrorKind.PERMANENT or kind == ErrorKind.CANCELLED:
            return False
        if kind == ErrorKind.TRANSIENT:
            return True
        if kind == ErrorKind.TIMEOUT:
            return True
        if kind == ErrorKind.UNKNOWN:
            return self.retry_unknown
        return False


@dataclass(slots=True)
class CircuitBreakerConfig:
    failure_threshold: int = 3
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 1


class CircuitBreakerState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(slots=True)
class CircuitBreaker:
    """Deterministic circuit breaker with injectable clock."""

    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    clock: Callable[[], float] = field(default=time.monotonic)
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    opened_at: float | None = None
    half_open_calls: int = 0

    def allow_request(self) -> bool:
        now = self.clock()
        if self.state == CircuitBreakerState.CLOSED:
            return True
        if self.state == CircuitBreakerState.OPEN:
            if self.opened_at is not None and now - self.opened_at >= self.config.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
            else:
                return False
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.half_open_calls < self.config.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
        return True

    def record_success(self) -> None:
        self.failure_count = 0
        self.half_open_calls = 0
        self.opened_at = None
        self.state = CircuitBreakerState.CLOSED

    def record_failure(self) -> None:
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.opened_at = self.clock()
            self.half_open_calls = 0
            return
        self.failure_count += 1
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.opened_at = self.clock()

    def reset(self) -> None:
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.opened_at = None
        self.half_open_calls = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "opened_at": self.opened_at,
        }


@dataclass(slots=True)
class OperationResult:
    success: bool
    value: Any = None
    error: BaseException | None = None
    error_kind: ErrorKind = ErrorKind.UNKNOWN
    attempts: int = 0
    cancelled: bool = False
    elapsed: float = 0.0
    idempotent: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "error": None if self.error is None else str(self.error),
            "error_kind": self.error_kind.value,
            "attempts": self.attempts,
            "cancelled": self.cancelled,
            "elapsed": self.elapsed,
            "idempotent": self.idempotent,
        }


@dataclass(slots=True)
class CancellationToken:
    _event: threading.Event = field(default_factory=threading.Event)

    def cancel(self) -> None:
        self._event.set()

    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def check(self) -> None:
        if self.is_cancelled():
            raise asyncio.CancelledError("operation cancelled")


@dataclass(slots=True)
class OperationGuard:
    """Per-key guard for incompatible concurrent operations."""

    _locks: dict[str, threading.RLock] = field(default_factory=dict)
    _meta_lock: threading.Lock = field(default_factory=threading.Lock)

    def acquire(self, key: str) -> threading.RLock:
        with self._meta_lock:
            if key not in self._locks:
                self._locks[key] = threading.RLock()
            return self._locks[key]


@dataclass(slots=True)
class ResilientExecutor:
    """Execute operations with timeout, bounded retry and circuit breaking."""

    policy: RetryPolicy = field(default_factory=RetryPolicy)
    circuit_breaker: CircuitBreaker = field(default_factory=CircuitBreaker)
    clock: Callable[[], float] = field(default=time.monotonic)
    sleeper: Callable[[float], None] = field(default=time.sleep)
    rng: random.Random = field(default_factory=random.Random)
    timeout: float = 30.0
    token: CancellationToken | None = None
    idempotency_registry: "IdempotencyRegistry | None" = None
    guard: OperationGuard = field(default_factory=OperationGuard)

    def run(self, operation: Callable[[], T], *, idempotent: bool = True, operation_key: str | None = None) -> OperationResult:
        started = self.clock()
        if not self.circuit_breaker.allow_request():
            return OperationResult(
                success=False,
                error=RuntimeError("circuit breaker is open"),
                error_kind=ErrorKind.TRANSIENT,
                attempts=0,
                idempotent=idempotent,
                elapsed=self.clock() - started,
            )

        if self.idempotency_registry is not None and operation_key is not None:
            cached = self.idempotency_registry.get(operation_key)
            if cached is not None:
                return cached

        lock = self.guard.acquire(operation_key) if operation_key is not None else None
        if lock is not None:
            lock.acquire()

        try:
            attempts = 0
            last_error: BaseException | None = None
            last_kind = ErrorKind.UNKNOWN
            while True:
                if self.token is not None:
                    self.token.check()
                attempts += 1
                try:
                    value = operation()
                    result = OperationResult(
                        success=True,
                        value=value,
                        attempts=attempts,
                        idempotent=idempotent,
                        elapsed=self.clock() - started,
                    )
                    self.circuit_breaker.record_success()
                    if operation_key is not None and self.idempotency_registry is not None:
                        self.idempotency_registry.set(operation_key, result)
                    return result
                except BaseException as exc:  # noqa: BLE001 - classified and traced.
                    last_error = exc
                    last_kind = classify_error(exc)
                    if self.policy.should_retry(last_kind, idempotent, attempts):
                        delay = self.policy.delay_for(attempts, self.rng)
                        self.sleeper(delay)
                        continue
                    self.circuit_breaker.record_failure()
                    result = OperationResult(
                        success=False,
                        error=exc,
                        error_kind=last_kind,
                        attempts=attempts,
                        cancelled=isinstance(exc, asyncio.CancelledError),
                        idempotent=idempotent,
                        elapsed=self.clock() - started,
                    )
                    return result
        finally:
            if lock is not None:
                lock.release()

    async def run_async(self, operation: Callable[[], Any], *, idempotent: bool = True, operation_key: str | None = None) -> OperationResult:
        # Wrap synchronous callable in executor; keeps deterministic injection simple.
        return self.run(operation, idempotent=idempotent, operation_key=operation_key)


@dataclass(slots=True)
class IdempotencyRegistry:
    """Simple in-memory, TTL-based idempotency cache."""

    ttl: float = 300.0
    clock: Callable[[], float] = field(default=time.monotonic)
    _entries: dict[str, tuple[float, OperationResult]] = field(default_factory=dict)

    def get(self, key: str) -> OperationResult | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        expires_at, result = entry
        if self.clock() >= expires_at:
            self._entries.pop(key, None)
            return None
        return result

    def set(self, key: str, result: OperationResult) -> None:
        self._entries[key] = (self.clock() + self.ttl, result)

    def clear(self) -> None:
        self._entries.clear()


@dataclass(slots=True)
class ApplicationLifecycleManager:
    """Explicit lifecycle state machine for integrated applications."""

    on_transition: Callable[[str, LifecycleState, LifecycleState], None] | None = None
    store: Any | None = None
    _states: dict[str, LifecycleState] = field(default_factory=dict)
    _history: dict[str, list[tuple[datetime, LifecycleState, LifecycleState]]] = field(
        default_factory=lambda: defaultdict(list)
    )
    _locks: dict[str, threading.RLock] = field(default_factory=dict)
    _meta_lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        if self.store is not None:
            try:
                for key, state in self.store.load_lifecycle_states().items():
                    self._states[key] = LifecycleState(state)
            except Exception:
                pass

    def _key(self, app_id: str, instance_id: str) -> str:
        return f"{app_id}:{instance_id}"

    def _lock_for(self, key: str) -> threading.RLock:
        with self._meta_lock:
            if key not in self._locks:
                self._locks[key] = threading.RLock()
            return self._locks[key]

    def get_state(self, app_id: str, instance_id: str) -> LifecycleState:
        return self._states.get(self._key(app_id, instance_id), LifecycleState.UNKNOWN)

    def set_initial(self, app_id: str, instance_id: str, state: LifecycleState = LifecycleState.REGISTERED) -> LifecycleState:
        key = self._key(app_id, instance_id)
        with self._lock_for(key):
            if key not in self._states:
                self._states[key] = state
            return self._states[key]

    def can_transition(self, app_id: str, instance_id: str, target: LifecycleState) -> bool:
        current = self.get_state(app_id, instance_id)
        if current == LifecycleState.UNKNOWN and target in LifecycleState:
            # Unknown can only be resolved explicitly by the caller through a
            # registered transition target that is legal from REGISTERED.
            return target in _TRANSITIONS[LifecycleState.REGISTERED]
        return target in _TRANSITIONS.get(current, frozenset())

    def transition(self, app_id: str, instance_id: str, target: LifecycleState | str) -> LifecycleState:
        desired = target if isinstance(target, LifecycleState) else LifecycleState(str(target))
        key = self._key(app_id, instance_id)
        with self._lock_for(key):
            current = self._states.get(key, LifecycleState.UNKNOWN)
            if current == LifecycleState.UNKNOWN:
                allowed = frozenset({LifecycleState.REGISTERED, LifecycleState.VALIDATED, LifecycleState.READY, LifecycleState.FAILED, LifecycleState.UNKNOWN})
            else:
                allowed = _TRANSITIONS.get(current, frozenset())
            if desired not in allowed:
                raise LifecycleTransitionError(
                    f"transition from {current.value} to {desired.value} is not allowed"
                )
            now = datetime.now(timezone.utc)
            self._history[key].append((now, current, desired))
            self._states[key] = desired
            if self.store is not None:
                try:
                    self.store.save_lifecycle_state(key, desired.value)
                except Exception:
                    pass
            if self.on_transition is not None:
                self.on_transition(key, current, desired)
            return desired

    def mark_unknown(self, app_id: str, instance_id: str, reason: str = "") -> LifecycleState:
        key = self._key(app_id, instance_id)
        with self._lock_for(key):
            previous = self._states.get(key, LifecycleState.UNKNOWN)
            if previous != LifecycleState.UNKNOWN:
                self._history[key].append((datetime.now(timezone.utc), previous, LifecycleState.UNKNOWN))
            self._states[key] = LifecycleState.UNKNOWN
            if self.store is not None:
                try:
                    self.store.save_lifecycle_state(key, LifecycleState.UNKNOWN.value)
                except Exception:
                    pass
            return LifecycleState.UNKNOWN

    def history(self, app_id: str, instance_id: str) -> list[dict[str, Any]]:
        key = self._key(app_id, instance_id)
        return [
            {"at": when.isoformat(), "from": old.value, "to": new.value}
            for when, old, new in self._history.get(key, [])
        ]

    def reset(self, app_id: str, instance_id: str) -> None:
        key = self._key(app_id, instance_id)
        with self._lock_for(key):
            self._states.pop(key, None)
            self._history.pop(key, None)

    def to_dict(self) -> dict[str, Any]:
        return {key: state.value for key, state in self._states.items()}


# Compatibility aliases.
LifecycleManager = ApplicationLifecycleManager
ApplicationLifecycle = ApplicationLifecycleManager
ResilienceManager = ResilientExecutor
ResilienceController = ResilientExecutor
ResilienceExecutorAlias = ResilientExecutor


__all__ = [
    "ApplicationLifecycleManager",
    "CancellationToken",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerState",
    "ErrorKind",
    "IdempotencyRegistry",
    "LifecycleState",
    "LifecycleTransitionError",
    "OperationGuard",
    "OperationResult",
    "ResilientExecutor",
    "RetryPolicy",
    "classify_error",
]
