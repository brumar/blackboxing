"""Rate Limiter — Public Interface.

This file defines the complete public API. Implementation is a black box.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Value types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RateLimiterConfig:
    """Policy that governs rate limiting behavior.

    Attributes:
        sustained_rate: Maximum number of allowed calls within ``window_seconds``.
        window_seconds: The rolling time window in seconds.
        burst_max: Maximum calls allowed in a short burst (≥1).
                   Must be ≤ sustained_rate.  When equal to sustained_rate
                   no burst distinction is made.
    """

    sustained_rate: int
    window_seconds: float
    burst_max: int


@dataclass(frozen=True)
class CheckResult:
    """Outcome of a rate-limit check.

    Always returned — callers pick which fields they care about.

    Attributes:
        allowed: Whether the call is permitted.
        remaining: How many calls are left in the current window.
        retry_after: Seconds until the caller can retry (0.0 if allowed).
    """

    allowed: bool
    remaining: int
    retry_after: float


# ---------------------------------------------------------------------------
# Dependency protocols
# ---------------------------------------------------------------------------

@runtime_checkable
class Clock(Protocol):
    """Time source — inject for deterministic testing."""

    def now(self) -> float:
        """Return current time as a Unix timestamp (seconds)."""
        ...

    async def anow(self) -> float:
        """Async variant of ``now``."""
        ...


@runtime_checkable
class Store(Protocol):
    """Backend for shared rate-limit state.

    Implementations might be in-memory, Redis, SQL, etc.
    Each method pair provides sync + async variants.
    Keys are opaque strings produced by the limiter.
    Values are opaque bytes — the store must not interpret them.
    """

    def get(self, key: str) -> bytes | None:
        """Retrieve state for *key*, or ``None`` if absent."""
        ...

    async def aget(self, key: str) -> bytes | None:
        """Async variant of ``get``."""
        ...

    def set(self, key: str, value: bytes, ttl_seconds: float) -> None:
        """Store *value* under *key* with a time-to-live.

        The store MUST expire the entry after *ttl_seconds*.
        """
        ...

    async def aset(self, key: str, value: bytes, ttl_seconds: float) -> None:
        """Async variant of ``set``."""
        ...

    def delete(self, key: str) -> None:
        """Remove *key* from the store. No-op if absent."""
        ...

    async def adelete(self, key: str) -> None:
        """Async variant of ``delete``."""
        ...


# ---------------------------------------------------------------------------
# Core module
# ---------------------------------------------------------------------------

class RateLimiter:
    """Controls how many operations a caller can perform within a time window.

    Usage::

        limiter = RateLimiter(config=config, store=store, clock=clock)

        # Sync
        result = limiter.check("user-42")

        # Async
        result = await limiter.acheck("user-42")

    The algorithm used internally is an implementation detail.
    """

    def __init__(
        self,
        config: RateLimiterConfig,
        store: Store | None = None,
        clock: Clock | None = None,
    ) -> None:
        """Create a rate limiter.

        Args:
            config: The rate-limiting policy.
            store: Backend for state. Defaults to an in-memory ``MemoryStore``.
                   **Warning**: the default store is single-process only — state
                   is not shared across instances and is lost on restart.
            clock: Time source. Defaults to ``SystemClock`` (real wall time).

        Raises:
            ValueError: If *config* is invalid (non-positive values,
                        burst_max > sustained_rate, etc.).
        """
        from rate_limiter._impl import validate_config
        from rate_limiter.defaults import MemoryStore, SystemClock

        validate_config(config)
        self._config = config
        self._clock: Clock = clock if clock is not None else SystemClock()
        if store is not None:
            self._store: Store = store
        else:
            self._store = MemoryStore(clock=self._clock)

    def check(self, key: str) -> CheckResult:
        """Check (and consume) a call for *key*.

        Returns a ``CheckResult`` with the decision and metadata.
        """
        from rate_limiter._impl import do_check

        return do_check(key, self._config, self._store, self._clock)

    async def acheck(self, key: str) -> CheckResult:
        """Async variant of ``check``."""
        from rate_limiter._impl import do_acheck

        return await do_acheck(key, self._config, self._store, self._clock)

    def reset(self, key: str) -> None:
        """Clear all rate-limit state for *key*.

        After reset, the next ``check`` for this key behaves as if
        the caller has never been seen.
        """
        self._store.delete(key)

    async def areset(self, key: str) -> None:
        """Async variant of ``reset``."""
        await self._store.adelete(key)
