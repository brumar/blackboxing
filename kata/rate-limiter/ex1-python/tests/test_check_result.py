"""CheckResult metadata — remaining count and retry_after accuracy."""

from __future__ import annotations

from rate_limiter import FakeClock, MemoryStore
from tests.conftest import make_limiter


class TestRemaining:
    """The 'remaining' field tracks how many calls are left."""

    def test_remaining_decreases_with_each_call(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=3, window_seconds=60.0)
        assert limiter.check("alice").remaining == 2
        assert limiter.check("alice").remaining == 1
        assert limiter.check("alice").remaining == 0

    def test_remaining_is_zero_when_rejected(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=1, window_seconds=60.0)
        limiter.check("alice")
        result = limiter.check("alice")
        assert result.allowed is False
        assert result.remaining == 0

    def test_remaining_resets_after_window(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=3, window_seconds=10.0)
        limiter.check("alice")
        limiter.check("alice")
        limiter.check("alice")

        clock.advance(10.0)
        result = limiter.check("alice")
        assert result.allowed is True
        assert result.remaining == 2


class TestRetryAfter:
    """The 'retry_after' field tells the caller when to come back."""

    def test_retry_after_is_zero_when_allowed(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=5, window_seconds=60.0)
        result = limiter.check("alice")
        assert result.retry_after == 0.0

    def test_retry_after_is_positive_when_rejected(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=1, window_seconds=10.0)
        limiter.check("alice")
        result = limiter.check("alice")
        assert result.allowed is False
        assert result.retry_after > 0.0

    def test_retry_after_does_not_exceed_window(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=1, window_seconds=10.0)
        limiter.check("alice")
        result = limiter.check("alice")
        assert result.retry_after <= 10.0

    def test_retry_after_decreases_as_time_passes(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=1, window_seconds=10.0)
        limiter.check("alice")

        r1 = limiter.check("alice")
        clock.advance(3.0)
        r2 = limiter.check("alice")

        assert r2.retry_after < r1.retry_after
