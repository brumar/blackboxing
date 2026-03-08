"""Async interface — acheck mirrors check behavior exactly."""

from __future__ import annotations

import pytest

from rate_limiter import FakeClock, MemoryStore
from tests.conftest import make_limiter


class TestAsyncCheck:

    @pytest.mark.asyncio
    async def test_acheck_allows_within_limit(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=3, window_seconds=60.0)
        for _ in range(3):
            result = await limiter.acheck("alice")
            assert result.allowed is True

    @pytest.mark.asyncio
    async def test_acheck_rejects_beyond_limit(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=2, window_seconds=60.0)
        await limiter.acheck("alice")
        await limiter.acheck("alice")
        result = await limiter.acheck("alice")
        assert result.allowed is False

    @pytest.mark.asyncio
    async def test_acheck_returns_correct_remaining(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=3, window_seconds=60.0)
        r1 = await limiter.acheck("alice")
        r2 = await limiter.acheck("alice")
        assert r1.remaining == 2
        assert r2.remaining == 1

    @pytest.mark.asyncio
    async def test_acheck_retry_after_zero_when_allowed(self, clock: FakeClock, store: MemoryStore):
        limiter = make_limiter(clock, store, sustained_rate=5, window_seconds=60.0)
        result = await limiter.acheck("alice")
        assert result.retry_after == 0.0

    @pytest.mark.asyncio
    async def test_sync_and_async_share_state(self, clock: FakeClock, store: MemoryStore):
        """Mixing check() and acheck() on the same key sees the same quota."""
        limiter = make_limiter(clock, store, sustained_rate=2, window_seconds=60.0)
        limiter.check("alice")                      # sync: 1 used
        result = await limiter.acheck("alice")       # async: 2 used
        assert result.allowed is True
        assert result.remaining == 0

        result = limiter.check("alice")              # sync: rejected
        assert result.allowed is False
