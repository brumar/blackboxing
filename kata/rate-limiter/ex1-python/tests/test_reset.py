"""Reset behavior — clearing a caller's rate-limit state."""

from __future__ import annotations

import pytest

from rate_limiter import FakeClock, MemoryStore
from tests.conftest import make_limiter


class TestReset:

    def test_reset_restores_full_quota(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=2, window_seconds=60.0)
        limiter.check("alice")
        limiter.check("alice")
        assert limiter.check("alice").allowed is False

        limiter.reset("alice")
        assert limiter.check("alice").allowed is True

    def test_reset_only_affects_target_key(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=1, window_seconds=60.0)
        limiter.check("alice")
        limiter.check("bob")

        limiter.reset("alice")
        assert limiter.check("alice").allowed is True
        assert limiter.check("bob").allowed is False

    def test_reset_nonexistent_key_is_noop(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=5, window_seconds=60.0)
        # Should not raise
        limiter.reset("nobody")

    def test_remaining_is_full_after_reset(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=3, window_seconds=60.0)
        limiter.check("alice")
        limiter.check("alice")

        limiter.reset("alice")
        result = limiter.check("alice")
        assert result.remaining == 2  # 3 - 1 (this check)


class TestAsyncReset:

    @pytest.mark.asyncio
    async def test_areset_restores_full_quota(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=2, window_seconds=60.0)
        await limiter.acheck("alice")
        await limiter.acheck("alice")
        assert (await limiter.acheck("alice")).allowed is False

        await limiter.areset("alice")
        assert (await limiter.acheck("alice")).allowed is True
