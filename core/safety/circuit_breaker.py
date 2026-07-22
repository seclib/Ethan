"""Circuit breaker pattern for external service resilience."""

from __future__ import annotations

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing fast
    HALF_OPEN = "half_open"  # Testing if recovery possible


class CircuitBreaker:
    """Circuit breaker for external connections (LLM providers, APIs, etc.).
    
    States:
    - CLOSED: Calls pass through normally
    - OPEN: All calls fail fast (returns fallback/error)
    - HALF_OPEN: Test with one call, if succeeds → CLOSED, if fails → OPEN
    
    Usage:
        breaker = CircuitBreaker(name="openai", fail_threshold=5, timeout=60)
        
        async def llm_call():
            return await breaker.call(openai_client.chat.completions.create, ...)
    """
    
    def __init__(
        self,
        name: str,
        fail_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: tuple = (Exception,),
    ):
        self.name = name
        self.fail_threshold = fail_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        
    @property
    def state(self) -> CircuitState:
        return self._state
    
    async def call(self, func: Callable, *args, fallback: Any = None, **kwargs) -> Any:
        """Execute function with circuit breaker protection.
        
        Args:
            func: Async function to call
            fallback: Value to return if circuit is open
            
        Returns:
            Result of func, or fallback if circuit open
        """
        if self._state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self._last_failure_time and (time.time() - self._last_failure_time) > self.timeout:
                self._state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker %s: HALF_OPEN (testing)", self.name)
            else:
                logger.warning("Circuit breaker %s: OPEN (failing fast)", self.name)
                return fallback
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as exc:
            self._on_failure(exc)
            return fallback
    
    def _on_success(self):
        """Reset failure count on success."""
        if self._state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker %s: CLOSED (recovered)", self.name)
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
    
    def _on_failure(self, exc: Exception):
        """Increment failure count, potentially open circuit."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self.fail_threshold:
            logger.error(
                "Circuit breaker %s: OPEN (%s failures, timeout %ss)",
                self.name, self._failure_count, self.timeout
            )
            self._state = CircuitState.OPEN
            # Emit metric for observability
            self._emit_metric()
    
    def _emit_metric(self):
        """Emit circuit breaker state metric to telemetry."""
        # Will be integrated with Prometheus/metrics later
        pass