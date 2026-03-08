"""Burst behavior — burst_max vs sustained_rate distinction."""

from __future__ import annotations

from rate_limiter import FakeClock, MemoryStore
from tests.conftest import make_limiter


class TestBurst:
    """When burst_max < sustained_rate, rapid calls are capped at burst_max."""

    def test_burst_limits_rapid_calls(self, clock: FakeClock, store: MemoryStore):
        """If burst_max=3, you can't fire more than 3 calls in rapid succession
        even if sustained_rate=10."""
        limiter = make_limiter(
            clock, store, sustained_rate=10, window_seconds=60.0, burst_max=3,
        )
        results = [limiter.check("alice") for _ in range(5)]
        allowed = [r.allowed for r in results]
        # First 3 should be allowed (burst), then rejected
        assert allowed[:3] == [True, True, True]
        assert allowed[3] is False

    def test_burst_replenishes_over_time(self, clock: FakeClock, store: MemoryStore):
        """After consuming the burst, waiting should allow more calls
        (up to the sustained rate within the window)."""
        limiter = make_limiter(
            clock, store, sustained_rate=10, window_seconds=60.0, burst_max=3,
        )
        # Exhaust burst
        for _ in range(3):
            limiter.check("alice")
        assert limiter.check("alice").allowed is False

        # Advance some time (not the full window) — burst should replenish
        clock.advance(30.0)
        assert limiter.check("alice").allowed is True

    def test_no_burst_distinction_when_equal(self, clock: FakeClock, store: MemoryStore):
        """When burst_max == sustained_rate, all calls up to the limit are allowed
        in rapid succession."""
        limiter = make_limiter(
            clock, store, sustained_rate=5, window_seconds=60.0, burst_max=5,
        )
        results = [limiter.check("alice") for _ in range(5)]
        assert all(r.allowed for r in results)
        assert limiter.check("alice").allowed is False

    def test_sustained_rate_is_total_within_window(self, clock: FakeClock, store: MemoryStore):
        """Even with burst, total calls in the full window cannot exceed sustained_rate."""
        limiter = make_limiter(
            clock, store, sustained_rate=6, window_seconds=60.0, burst_max=3,
        )
        allowed_count = 0
        # Spread calls over the full window
        for _ in range(12):
            result = limiter.check("alice")
            if result.allowed:
                allowed_count += 1
            clock.advance(5.0)  # 12 * 5s = 60s = one full window

        # Should not exceed sustained_rate within any window
        assert allowed_count <= 6
