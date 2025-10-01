"""Circuit breaker pattern implementation for service resilience."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, TypeVar

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: int = 60  # Seconds before trying half-open
    success_threshold: int = 3  # Successes needed to close from half-open
    timeout: int = 30  # Request timeout in seconds
    expected_exception: type = Exception


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""

    failure_count: int = 0
    success_count: int = 0
    total_requests: int = 0
    last_failure_time: datetime | None = None
    last_success_time: datetime | None = None
    state_changed_at: datetime = field(default_factory=datetime.utcnow)


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""

    def __init__(self, message: str, circuit_name: str, state: CircuitState) -> None:
        super().__init__(message)
        self.circuit_name = circuit_name
        self.state = state


class CircuitBreaker:
    """Circuit breaker implementation with async support."""

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None) -> None:
        """Initialize circuit breaker."""
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            await self._check_state()

        if self.state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN", self.name, self.state
            )

        try:
            # Execute with timeout
            func_result = func(*args, **kwargs)
            if asyncio.iscoroutine(func_result):
                result: T = await asyncio.wait_for(
                    func_result, timeout=self.config.timeout
                )
            else:
                result = func_result

            await self._on_success()
            return result

        except Exception as e:
            if isinstance(e, self.config.expected_exception):
                await self._on_failure()
                raise
            elif isinstance(e, TimeoutError):
                await self._on_failure()
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' timeout", self.name, self.state
                ) from e
            else:
                # Unexpected exception, also trigger failure
                await self._on_failure()
                raise

    async def _check_state(self) -> None:
        """Check and update circuit breaker state."""
        now = datetime.utcnow()

        if self.state == CircuitState.OPEN:
            if (
                self.stats.last_failure_time
                and now - self.stats.last_failure_time
                >= timedelta(seconds=self.config.recovery_timeout)
            ):
                await self._transition_to_half_open()

        elif self.state == CircuitState.HALF_OPEN:
            if self.stats.success_count >= self.config.success_threshold:
                await self._transition_to_closed()

    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            self.stats.success_count += 1
            self.stats.total_requests += 1
            self.stats.last_success_time = datetime.utcnow()

            if self.state == CircuitState.HALF_OPEN:
                if self.stats.success_count >= self.config.success_threshold:
                    await self._transition_to_closed()

            logger.debug(
                "Circuit breaker success",
                name=self.name,
                state=self.state.value,
                success_count=self.stats.success_count,
            )

    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            self.stats.failure_count += 1
            self.stats.total_requests += 1
            self.stats.last_failure_time = datetime.utcnow()

            if self.state == CircuitState.CLOSED:
                if self.stats.failure_count >= self.config.failure_threshold:
                    await self._transition_to_open()

            elif self.state == CircuitState.HALF_OPEN:
                await self._transition_to_open()

            logger.warning(
                "Circuit breaker failure",
                name=self.name,
                state=self.state.value,
                failure_count=self.stats.failure_count,
            )

    async def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        self.state = CircuitState.OPEN
        self.stats.state_changed_at = datetime.utcnow()

        logger.error(
            "Circuit breaker opened",
            name=self.name,
            failure_count=self.stats.failure_count,
            threshold=self.config.failure_threshold,
        )

    async def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.stats.success_count = 0  # Reset success count
        self.stats.state_changed_at = datetime.utcnow()

        logger.info(
            "Circuit breaker half-opened",
            name=self.name,
            recovery_timeout=self.config.recovery_timeout,
        )

    async def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.stats.failure_count = 0  # Reset failure count
        self.stats.success_count = 0  # Reset success count
        self.stats.state_changed_at = datetime.utcnow()

        logger.info(
            "Circuit breaker closed",
            name=self.name,
            success_threshold=self.config.success_threshold,
        )

    async def force_open(self) -> None:
        """Manually force circuit breaker to OPEN state."""
        async with self._lock:
            await self._transition_to_open()
            logger.warning(f"Circuit breaker '{self.name}' manually forced OPEN")

    async def force_close(self) -> None:
        """Manually force circuit breaker to CLOSED state."""
        async with self._lock:
            await self._transition_to_closed()
            logger.info(f"Circuit breaker '{self.name}' manually forced CLOSED")

    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_requests": self.stats.total_requests,
            "failure_rate": (
                self.stats.failure_count / self.stats.total_requests
                if self.stats.total_requests > 0
                else 0
            ),
            "last_failure_time": self.stats.last_failure_time.isoformat()
            if self.stats.last_failure_time
            else None,
            "last_success_time": self.stats.last_success_time.isoformat()
            if self.stats.last_success_time
            else None,
            "state_changed_at": self.stats.state_changed_at.isoformat(),
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
            },
        }


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self) -> None:
        """Initialize circuit breaker registry."""
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    async def get_breaker(
        self, name: str, config: CircuitBreakerConfig | None = None
    ) -> CircuitBreaker:
        """Get or create circuit breaker."""
        async with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config)
            return self._breakers[name]

    async def call_with_breaker(
        self,
        name: str,
        func: Callable[..., T],
        config: CircuitBreakerConfig | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute function with circuit breaker protection."""
        breaker = await self.get_breaker(name, config)
        return await breaker.call(func, *args, **kwargs)

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}

    async def force_open_all(self) -> None:
        """Force all circuit breakers to OPEN state."""
        for breaker in self._breakers.values():
            await breaker.force_open()

    async def force_close_all(self) -> None:
        """Force all circuit breakers to CLOSED state."""
        for breaker in self._breakers.values():
            await breaker.force_close()

    def get_breaker_names(self) -> list[str]:
        """Get names of all registered circuit breakers."""
        return list(self._breakers.keys())


# Global circuit breaker registry
circuit_breaker_registry = CircuitBreakerRegistry()


# Decorator for easy circuit breaker usage
def circuit_breaker(
    name: str, config: CircuitBreakerConfig | None = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to add circuit breaker protection to async functions."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await circuit_breaker_registry.call_with_breaker(
                name, func, config, *args, **kwargs
            )

        return wrapper

    return decorator
