"""Default dependencies — limiter works out of the box with no store/clock."""

from __future__ import annotations

from rate_limiter import RateLimiter, RateLimiterConfig


class TestDefaults:

    def test_limiter_works_without_explicit_store_and_clock(self):
        """When store and clock are omitted, the limiter uses built-in defaults."""
        limiter = RateLimiter(config=RateLimiterConfig(
            sustained_rate=5, window_seconds=60.0, burst_max=5,
        ))
        result = limiter.check("alice")
        assert result.allowed is True

    def test_default_limiter_rejects_beyond_limit(self):
        limiter = RateLimiter(config=RateLimiterConfig(
            sustained_rate=2, window_seconds=60.0, burst_max=2,
        ))
        limiter.check("alice")
        limiter.check("alice")
        assert limiter.check("alice").allowed is False
