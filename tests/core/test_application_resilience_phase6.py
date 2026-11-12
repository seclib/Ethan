import time

from core.applications import (
    ApplicationLifecycleManager,
    CircuitBreaker,
    CircuitBreakerConfig,
    ErrorKind,
    LifecycleState,
    LifecycleTransitionError,
    OperationResult,
    ResilientExecutor,
    RetryPolicy,
    classify_error,
)


def test_allowed_and_denied_transitions() -> None:
    manager = ApplicationLifecycleManager()
    manager.set_initial("app", "instance")
    manager.transition("app", "instance", LifecycleState.VALIDATED)
    manager.transition("app", "instance", LifecycleState.READY)
    try:
        manager.transition("app", "instance", LifecycleState.STOPPED)
        raise AssertionError("unexpected transition allowed")
    except LifecycleTransitionError:
        pass
    assert manager.get_state("app", "instance") == LifecycleState.READY


def test_unknown_state_remains_unknown_then_resolvable() -> None:
    manager = ApplicationLifecycleManager()
    manager.mark_unknown("app", "instance", reason="supervisor timeout")
    assert manager.get_state("app", "instance") == LifecycleState.UNKNOWN
    manager.transition("app", "instance", LifecycleState.REGISTERED)
    assert manager.get_state("app", "instance") == LifecycleState.REGISTERED


def test_transient_retry_and_non_idempotent_no_retry() -> None:
    clock = [0.0]
    def now() -> float:
        return clock[0]
    def sleep(delay: float) -> None:
        clock[0] += delay

    calls = {"count": 0}
    def operation() -> str:
        calls["count"] += 1
        if calls["count"] < 3:
            raise ConnectionError("temporary failure")
        return "ok"

    executor = ResilientExecutor(
        policy=RetryPolicy(max_attempts=3, base_delay=0.01),
        clock=now,
        sleeper=sleep,
    )
    result = executor.run(operation, idempotent=True)
    assert result.success is True
    assert result.value == "ok"
    assert result.attempts == 3

    calls2 = {"count": 0}
    def permanent_operation() -> str:
        calls2["count"] += 1
        raise ConnectionError("temporary failure")
    result2 = ResilientExecutor(
        policy=RetryPolicy(max_attempts=3, base_delay=0.01),
        clock=now,
        sleeper=sleep,
    ).run(permanent_operation, idempotent=False)
    assert result2.success is False
    assert result2.attempts == 1


def test_permanent_error_classification() -> None:
    assert classify_error(ValueError("invalid permission")) == ErrorKind.PERMANENT


def test_circuit_breaker_opens_and_recovers() -> None:
    clock = [0.0]
    def now() -> float:
        return clock[0]
    breaker = CircuitBreaker(config=CircuitBreakerConfig(failure_threshold=2, recovery_timeout=5.0), clock=now)
    assert breaker.allow_request() is True
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state.value == "open"
    assert breaker.allow_request() is False
    clock[0] = 5.0
    assert breaker.allow_request() is True
    assert breaker.state.value == "half_open"
    breaker.record_success()
    assert breaker.state.value == "closed"


def test_idempotency_cache_returns_cached_result() -> None:
    clock = [0.0]
    def now() -> float:
        return clock[0]
    from core.applications import IdempotencyRegistry
    registry = IdempotencyRegistry(ttl=10.0, clock=now)
    result = OperationResult(success=True, value="cached", attempts=1)
    registry.set("op-1", result)
    assert registry.get("op-1") is result
    clock[0] = 20.0
    assert registry.get("op-1") is None


def test_cancellation_is_reported() -> None:
    from core.applications import CancellationToken
    token = CancellationToken()
    token.cancel()
    assert token.is_cancelled() is True
    try:
        token.check()
        raise AssertionError("cancellation not detected")
    except BaseException:
        pass


def test_application_failure_isolation() -> None:
    manager = ApplicationLifecycleManager()
    manager.set_initial("app-a", "instance-a")
    manager.set_initial("app-b", "instance-b")
    manager.mark_unknown("app-a", "instance-a", reason="failure")
    assert manager.get_state("app-a", "instance-a") == LifecycleState.UNKNOWN
    assert manager.get_state("app-b", "instance-b") == LifecycleState.REGISTERED


def test_no_real_operation_or_permission_side_effect() -> None:
    executor = ResilientExecutor(policy=RetryPolicy(max_attempts=1))
    result = executor.run(lambda: "value", idempotent=True)
    assert result.success is True
    assert result.value == "value"
