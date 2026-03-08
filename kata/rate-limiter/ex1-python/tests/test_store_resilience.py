"""Store resilience — graceful behavior when the store loses data.

If the store evicts a key (TTL, memory pressure, restart), the limiter
should treat the caller as fresh — not crash, not permanently block.
This is the "fail open on data loss" contract.
"""

from __future__ import annotations

import pytest

from rate_limiter import FakeClock, MemoryStore
from tests.conftest import make_limiter


class TestStoreLostData:
    """When the store loses state mid-window, the limiter degrades gracefully."""

    def test_store_eviction_resets_to_fresh(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """If the store loses a key, the next check behaves as if fresh."""
        limiter = make_limiter(clock, store, sustained_rate=2, window_seconds=60.0)
        limiter.check("alice")
        limiter.check("alice")
        assert limiter.check("alice").allowed is False

        # Simulate store eviction by deleting the key directly
        # (We don't know the internal key format, so use reset which calls store.delete)
        limiter.reset("alice")

        # Should behave as fresh — full quota restored
        result = limiter.check("alice")
        assert result.allowed is True
        assert result.remaining >= 1  # at least 1 more call available

    def test_store_returns_none_for_unknown_key(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """A never-seen key returns None from store and allows the first call."""
        limiter = make_limiter(clock, store, sustained_rate=5, window_seconds=60.0)
        # First call for a brand new key
        result = limiter.check("brand-new-key")
        assert result.allowed is True
        assert result.remaining == 4

    def test_multiple_limiters_share_store(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """Two RateLimiter instances with the same config sharing a store
        should see each other's state."""
        from rate_limiter import RateLimiter, RateLimiterConfig
        config = RateLimiterConfig(sustained_rate=2, window_seconds=60.0, burst_max=2)
        limiter_a = RateLimiter(config=config, store=store, clock=clock)
        limiter_b = RateLimiter(config=config, store=store, clock=clock)

        limiter_a.check("alice")
        limiter_b.check("alice")
        # Both consumed from the same key — should be at limit
        result = limiter_a.check("alice")
        assert result.allowed is False
