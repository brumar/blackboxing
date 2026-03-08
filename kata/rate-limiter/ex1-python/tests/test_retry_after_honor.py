"""retry_after honor contract — callers can trust the value they receive.

If retry_after says "wait X seconds", then waiting X seconds and retrying
MUST succeed. This is the core usability contract of retry_after — without
it the field is advisory at best and misleading at worst.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from rate_limiter import (
    RateLimiter,
    RateLimiterConfig,
    FakeClock,
    MemoryStore,
)
from tests.conftest import make_limiter


class TestRetryAfterHonor:
    """Waiting retry_after seconds guarantees the next call is allowed."""

    def test_waiting_retry_after_allows_next_call(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """The simplest case: exhaust limit, read retry_after, wait, succeed."""
        limiter = make_limiter(clock, store, sustained_rate=2, window_seconds=10.0)
        limiter.check("alice")
        limiter.check("alice")
        result = limiter.check("alice")
        assert result.allowed is False

        clock.advance(result.retry_after)
        assert limiter.check("alice").allowed is True

    def test_waiting_retry_after_with_single_call_limit(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """sustained_rate=1 — the tightest possible config."""
        limiter = make_limiter(clock, store, sustained_rate=1, window_seconds=5.0)
        limiter.check("alice")
        result = limiter.check("alice")
        assert result.allowed is False

        clock.advance(result.retry_after)
        assert limiter.check("alice").allowed is True

    def test_retry_after_honored_after_partial_window(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """Exhaust mid-window, verify retry_after still works."""
        limiter = make_limiter(clock, store, sustained_rate=3, window_seconds=60.0)
        limiter.check("alice")
        clock.advance(10.0)
        limiter.check("alice")
        clock.advance(10.0)
        limiter.check("alice")

        result = limiter.check("alice")
        assert result.allowed is False

        clock.advance(result.retry_after)
        assert limiter.check("alice").allowed is True

    def test_waiting_less_than_retry_after_still_rejected(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """Waiting *almost* retry_after should still reject."""
        limiter = make_limiter(clock, store, sustained_rate=1, window_seconds=10.0)
        limiter.check("alice")
        result = limiter.check("alice")
        assert result.allowed is False

        # Wait 90% of retry_after — should still be rejected
        almost = result.retry_after * 0.9
        if almost > 0:
            clock.advance(almost)
            assert limiter.check("alice").allowed is False

    @pytest.mark.asyncio
    async def test_async_retry_after_honored(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """Same contract holds for acheck."""
        limiter = make_limiter(clock, store, sustained_rate=2, window_seconds=10.0)
        await limiter.acheck("alice")
        await limiter.acheck("alice")
        result = await limiter.acheck("alice")
        assert result.allowed is False

        clock.advance(result.retry_after)
        result = await limiter.acheck("alice")
        assert result.allowed is True


class TestRetryAfterHonorProperty:
    """Property-based: retry_after honor holds for all valid configs."""

    @given(
        sustained_rate=st.integers(min_value=1, max_value=50),
        window_seconds=st.floats(min_value=0.5, max_value=300.0),
    )
    @settings(max_examples=80)
    def test_retry_after_honor_property(
        self, sustained_rate: int, window_seconds: float,
    ):
        """For any valid config, waiting retry_after always unblocks."""
        clock = FakeClock(start=1_000_000.0)
        store = MemoryStore(clock=clock)
        limiter = RateLimiter(
            config=RateLimiterConfig(
                sustained_rate=sustained_rate,
                window_seconds=window_seconds,
                burst_max=sustained_rate,
            ),
            store=store,
            clock=clock,
        )

        # Exhaust the quota
        for _ in range(sustained_rate):
            limiter.check("k")
        result = limiter.check("k")
        assert result.allowed is False

        clock.advance(result.retry_after)
        assert limiter.check("k").allowed is True
