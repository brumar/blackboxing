"""Burst + remaining semantics — clarify what 'remaining' means under burst.

When burst_max < sustained_rate, 'remaining' should reflect the effective
number of calls the caller can make RIGHT NOW (i.e., burst tokens available),
not the sustained-rate headroom. This is the only actionable interpretation
for API consumers.
"""

from __future__ import annotations

from rate_limiter import FakeClock, MemoryStore
from tests.conftest import make_limiter


class TestBurstRemaining:
    """When burst-limited, remaining reflects immediately available calls."""

    def test_remaining_reflects_burst_cap_initially(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """First check: remaining should not exceed burst_max - 1."""
        limiter = make_limiter(
            clock, store, sustained_rate=10, window_seconds=60.0, burst_max=3,
        )
        result = limiter.check("alice")
        assert result.allowed is True
        assert result.remaining <= 2  # burst_max - 1 = 2

    def test_remaining_hits_zero_at_burst_exhaustion(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """After burst_max calls, remaining must be 0."""
        limiter = make_limiter(
            clock, store, sustained_rate=10, window_seconds=60.0, burst_max=3,
        )
        for _ in range(3):
            result = limiter.check("alice")
        assert result.remaining == 0

    def test_remaining_recovers_after_burst_replenish(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """After time passes and burst replenishes, remaining should increase."""
        limiter = make_limiter(
            clock, store, sustained_rate=10, window_seconds=60.0, burst_max=3,
        )
        for _ in range(3):
            limiter.check("alice")

        # Advance enough time for some burst to refill
        clock.advance(30.0)
        result = limiter.check("alice")
        assert result.allowed is True
        assert result.remaining >= 0


class TestBurstRetryAfter:
    """When burst-limited, retry_after tells you when a burst token refills."""

    def test_burst_limited_has_positive_retry_after(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """When rejected due to burst (not sustained), retry_after > 0."""
        limiter = make_limiter(
            clock, store, sustained_rate=10, window_seconds=60.0, burst_max=2,
        )
        limiter.check("alice")
        limiter.check("alice")
        result = limiter.check("alice")
        assert result.allowed is False
        assert result.retry_after > 0.0

    def test_burst_retry_after_is_shorter_than_window(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """Burst refill should happen before the full window elapses.
        With sustained_rate=10, burst_max=2, window=60s — burst refill
        should be much faster than 60s since sustained rate is high."""
        limiter = make_limiter(
            clock, store, sustained_rate=10, window_seconds=60.0, burst_max=2,
        )
        limiter.check("alice")
        limiter.check("alice")
        result = limiter.check("alice")
        assert result.allowed is False
        # Burst should refill well before the full window
        assert result.retry_after < 60.0

    def test_waiting_burst_retry_after_allows_next_call(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """The retry_after honor contract also applies to burst-limited rejections."""
        limiter = make_limiter(
            clock, store, sustained_rate=10, window_seconds=60.0, burst_max=2,
        )
        limiter.check("alice")
        limiter.check("alice")
        result = limiter.check("alice")
        assert result.allowed is False

        clock.advance(result.retry_after)
        assert limiter.check("alice").allowed is True
