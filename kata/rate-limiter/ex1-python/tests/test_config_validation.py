"""Config validation — invalid configs must fail at construction time."""

from __future__ import annotations

import pytest

from rate_limiter import RateLimiter, RateLimiterConfig


class TestConfigValidation:
    """The limiter must never be in an invalid state."""

    def test_sustained_rate_must_be_positive(self):
        with pytest.raises(ValueError):
            RateLimiter(config=RateLimiterConfig(
                sustained_rate=0, window_seconds=60.0, burst_max=0,
            ))

    def test_negative_sustained_rate(self):
        with pytest.raises(ValueError):
            RateLimiter(config=RateLimiterConfig(
                sustained_rate=-1, window_seconds=60.0, burst_max=1,
            ))

    def test_window_seconds_must_be_positive(self):
        with pytest.raises(ValueError):
            RateLimiter(config=RateLimiterConfig(
                sustained_rate=10, window_seconds=0.0, burst_max=10,
            ))

    def test_negative_window_seconds(self):
        with pytest.raises(ValueError):
            RateLimiter(config=RateLimiterConfig(
                sustained_rate=10, window_seconds=-1.0, burst_max=10,
            ))

    def test_burst_max_must_be_positive(self):
        with pytest.raises(ValueError):
            RateLimiter(config=RateLimiterConfig(
                sustained_rate=10, window_seconds=60.0, burst_max=0,
            ))

    def test_burst_max_cannot_exceed_sustained_rate(self):
        with pytest.raises(ValueError):
            RateLimiter(config=RateLimiterConfig(
                sustained_rate=10, window_seconds=60.0, burst_max=11,
            ))

    def test_valid_config_does_not_raise(self):
        # Should not raise
        RateLimiter(config=RateLimiterConfig(
            sustained_rate=10, window_seconds=60.0, burst_max=5,
        ))

    def test_burst_max_equal_to_sustained_rate_is_valid(self):
        # Should not raise — means "no burst distinction"
        RateLimiter(config=RateLimiterConfig(
            sustained_rate=10, window_seconds=60.0, burst_max=10,
        ))
