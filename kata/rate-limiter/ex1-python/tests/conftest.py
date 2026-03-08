"""Shared fixtures for rate limiter tests."""

from __future__ import annotations

import pytest

from rate_limiter import (
    RateLimiter,
    RateLimiterConfig,
    FakeClock,
    MemoryStore,
)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(start=1_000_000.0)


@pytest.fixture
def store(clock: FakeClock) -> MemoryStore:
    return MemoryStore(clock=clock)


def make_limiter(
    clock: FakeClock,
    store: MemoryStore,
    *,
    sustained_rate: int = 10,
    window_seconds: float = 60.0,
    burst_max: int | None = None,
) -> RateLimiter:
    """Helper to build a limiter with less boilerplate."""
    if burst_max is None:
        burst_max = sustained_rate
    return RateLimiter(
        config=RateLimiterConfig(
            sustained_rate=sustained_rate,
            window_seconds=window_seconds,
            burst_max=burst_max,
        ),
        store=store,
        clock=clock,
    )
