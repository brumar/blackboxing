"""Edge cases — boundaries, unusual inputs, rapid sequences."""

from __future__ import annotations

from rate_limiter import FakeClock, MemoryStore
from tests.conftest import make_limiter


class TestEdgeCases:

    def test_empty_string_key(self, clock: FakeClock, store: MemoryStore):
        """Empty string is a valid key."""
        limiter = make_limiter(clock, store, sustained_rate=1, window_seconds=60.0)
        assert limiter.check("").allowed is True
        assert limiter.check("").allowed is False

    def test_very_long_key(self, clock: FakeClock, store: MemoryStore):
        """Long keys should work without error."""
        limiter = make_limiter(clock, store, sustained_rate=1, window_seconds=60.0)
        key = "x" * 10_000
        assert limiter.check(key).allowed is True

    def test_unicode_key(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=1, window_seconds=60.0)
        assert limiter.check("用户-42").allowed is True
        assert limiter.check("用户-42").allowed is False

    def test_very_small_window(self, clock: FakeClock, store: MemoryStore):
        """Sub-second windows should work."""
        limiter = make_limiter(clock, store, sustained_rate=2, window_seconds=0.1)
        limiter.check("alice")
        limiter.check("alice")
        assert limiter.check("alice").allowed is False

        clock.advance(0.1)
        assert limiter.check("alice").allowed is True

    def test_large_sustained_rate(self, clock: FakeClock, store: MemoryStore):
        """High limits should not cause errors."""
        limiter = make_limiter(clock, store, sustained_rate=100_000, window_seconds=60.0)
        # Spot check — first and last within limit
        assert limiter.check("alice").allowed is True

    def test_check_result_is_frozen(self, clock: FakeClock, store: MemoryStore):
        """CheckResult is immutable (frozen dataclass)."""
        limiter = make_limiter(clock, store, sustained_rate=5, window_seconds=60.0)
        result = limiter.check("alice")
        with __import__("pytest").raises(AttributeError):
            result.allowed = False  # type: ignore[misc]

    def test_many_distinct_keys(self, clock: FakeClock, store: MemoryStore):
        """Many independent callers should each get their own quota."""
        limiter = make_limiter(clock, store, sustained_rate=1, window_seconds=60.0)
        for i in range(1000):
            assert limiter.check(f"user-{i}").allowed is True

    def test_exact_boundary_timing(self, clock: FakeClock, store: MemoryStore):
        """Check at exactly the window boundary."""
        limiter = make_limiter(clock, store, sustained_rate=1, window_seconds=10.0)
        limiter.check("alice")

        # Advance to exactly the boundary
        clock.advance(10.0)
        assert limiter.check("alice").allowed is True
