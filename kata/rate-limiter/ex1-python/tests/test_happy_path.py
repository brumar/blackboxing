"""Happy path — core allow/reject behavior."""

from __future__ import annotations

from rate_limiter import FakeClock, MemoryStore
from tests.conftest import make_limiter


class TestBasicAllowReject:
    """Calls within the limit are allowed; calls beyond are rejected."""

    def test_first_call_is_allowed(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=5, window_seconds=60.0)
        result = limiter.check("alice")
        assert result.allowed is True

    def test_calls_up_to_limit_are_allowed(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=3, window_seconds=60.0)
        for _ in range(3):
            result = limiter.check("alice")
            assert result.allowed is True

    def test_call_beyond_limit_is_rejected(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=3, window_seconds=60.0)
        for _ in range(3):
            limiter.check("alice")
        result = limiter.check("alice")
        assert result.allowed is False

    def test_single_call_limit(self, clock: FakeClock, store: MemoryStore):
        """Edge case: sustained_rate=1 allows exactly one call."""
        limiter = make_limiter(clock, store, sustained_rate=1, window_seconds=60.0)
        assert limiter.check("alice").allowed is True
        assert limiter.check("alice").allowed is False


class TestWindowRollover:
    """After the window elapses, the caller gets a fresh quota."""

    def test_calls_allowed_after_window_expires(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=2, window_seconds=10.0)
        limiter.check("alice")
        limiter.check("alice")
        assert limiter.check("alice").allowed is False

        clock.advance(10.0)
        assert limiter.check("alice").allowed is True

    def test_partial_window_advance_still_rejected(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=2, window_seconds=10.0)
        limiter.check("alice")
        limiter.check("alice")

        clock.advance(5.0)  # half the window
        assert limiter.check("alice").allowed is False

    def test_multiple_windows(self, clock: FakeClock, store: MemoryStore):
        """Limiter works correctly across several consecutive windows."""
        limiter = make_limiter(clock, store, sustained_rate=1, window_seconds=5.0)
        for _ in range(10):
            assert limiter.check("alice").allowed is True
            assert limiter.check("alice").allowed is False
            clock.advance(5.0)


class TestCallerIsolation:
    """Different keys are independent — one caller's usage doesn't affect another."""

    def test_different_keys_have_separate_quotas(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=1, window_seconds=60.0)
        assert limiter.check("alice").allowed is True
        assert limiter.check("bob").allowed is True

    def test_exhausting_one_key_does_not_affect_another(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=2, window_seconds=60.0)
        limiter.check("alice")
        limiter.check("alice")
        assert limiter.check("alice").allowed is False
        assert limiter.check("bob").allowed is True
