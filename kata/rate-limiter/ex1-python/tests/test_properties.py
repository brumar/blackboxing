"""Property-based tests — invariants that must hold for all valid inputs."""

from __future__ import annotations

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from rate_limiter import (
    RateLimiter,
    RateLimiterConfig,
    CheckResult,
    FakeClock,
    MemoryStore,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

valid_config = st.builds(
    RateLimiterConfig,
    sustained_rate=st.integers(min_value=1, max_value=200),
    window_seconds=st.floats(min_value=0.1, max_value=3600.0),
    burst_max=st.integers(min_value=1, max_value=200),
).filter(lambda c: c.burst_max <= c.sustained_rate)

caller_key = st.text(min_size=1, max_size=50)


def _make(config: RateLimiterConfig) -> tuple[RateLimiter, FakeClock]:
    clock = FakeClock(start=1_000_000.0)
    store = MemoryStore(clock=clock)
    return RateLimiter(config=config, store=store, clock=clock), clock


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

class TestInvariants:

    @given(config=valid_config, key=caller_key)
    @settings(max_examples=100)
    def test_first_check_is_always_allowed(self, config: RateLimiterConfig, key: str):
        """A fresh key is never rejected on its first check."""
        limiter, _ = _make(config)
        assert limiter.check(key).allowed is True

    @given(config=valid_config, key=caller_key)
    @settings(max_examples=100)
    def test_allowed_implies_retry_after_zero(self, config: RateLimiterConfig, key: str):
        """If allowed=True, retry_after must be 0.0."""
        limiter, _ = _make(config)
        result = limiter.check(key)
        if result.allowed:
            assert result.retry_after == 0.0

    @given(config=valid_config, key=caller_key)
    @settings(max_examples=100)
    def test_rejected_implies_positive_retry_after(self, config: RateLimiterConfig, key: str):
        """If allowed=False, retry_after must be > 0."""
        limiter, _ = _make(config)
        # Exhaust the limit
        for _ in range(config.sustained_rate + 1):
            result = limiter.check(key)
        # The last call should be rejected
        if not result.allowed:
            assert result.retry_after > 0.0

    @given(config=valid_config, key=caller_key)
    @settings(max_examples=100)
    def test_remaining_is_never_negative(self, config: RateLimiterConfig, key: str):
        """Remaining count must be ≥ 0, even after many rejections."""
        limiter, _ = _make(config)
        for _ in range(config.sustained_rate + 5):
            result = limiter.check(key)
            assert result.remaining >= 0

    @given(config=valid_config, key=caller_key)
    @settings(max_examples=100)
    def test_remaining_does_not_increase_without_time_passing(
        self, config: RateLimiterConfig, key: str,
    ):
        """Without advancing time, remaining can only stay the same or decrease."""
        limiter, _ = _make(config)
        prev = config.sustained_rate
        for _ in range(config.sustained_rate + 2):
            result = limiter.check(key)
            assert result.remaining <= prev
            prev = result.remaining

    @given(config=valid_config)
    @settings(max_examples=50)
    def test_independent_keys_do_not_interfere(self, config: RateLimiterConfig):
        """Exhausting key A does not affect key B."""
        limiter, _ = _make(config)
        for _ in range(config.sustained_rate + 1):
            limiter.check("key-a")
        assert limiter.check("key-b").allowed is True

    @given(config=valid_config, key=caller_key)
    @settings(max_examples=50)
    def test_reset_then_check_behaves_as_fresh(self, config: RateLimiterConfig, key: str):
        """After reset, the key behaves as if never seen."""
        limiter, _ = _make(config)
        for _ in range(config.sustained_rate):
            limiter.check(key)
        limiter.reset(key)
        result = limiter.check(key)
        assert result.allowed is True
        assert result.remaining == config.burst_max - 1 or result.remaining == config.sustained_rate - 1

    @given(config=valid_config, key=caller_key)
    @settings(max_examples=50)
    def test_full_window_advance_restores_quota(self, config: RateLimiterConfig, key: str):
        """Advancing past the full window always allows the next call."""
        limiter, clock = _make(config)
        for _ in range(config.sustained_rate + 1):
            limiter.check(key)
        clock.advance(config.window_seconds)
        assert limiter.check(key).allowed is True

    @given(config=valid_config, key=caller_key)
    @settings(max_examples=50)
    def test_retry_after_never_exceeds_window(self, config: RateLimiterConfig, key: str):
        """retry_after should never be longer than the window itself."""
        limiter, _ = _make(config)
        for _ in range(config.sustained_rate + 1):
            result = limiter.check(key)
        if not result.allowed:
            assert result.retry_after <= config.window_seconds
