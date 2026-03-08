"""Sliding window semantics — calls expire individually, not in batches.

A fixed-window algorithm resets all counters at window boundaries, allowing
up to 2x throughput if a caller times calls across the boundary. A sliding
window tracks each call's timestamp and expires them individually.

These tests ONLY pass with a true sliding window. They are designed to fail
with a fixed-window counter.
"""

from __future__ import annotations

from rate_limiter import FakeClock, MemoryStore
from tests.conftest import make_limiter


class TestSlidingWindowExpiry:
    """Individual calls expire at their own timestamp + window_seconds."""

    def test_early_call_expires_before_late_call(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """With sustained_rate=2, window=10s:
        - Call at t=0, call at t=6 → 2 used, rejected at t=6
        - At t=10, the t=0 call expires → 1 slot opens
        - But the t=6 call is still live → only 1 slot, not 2
        """
        limiter = make_limiter(clock, store, sustained_rate=2, window_seconds=10.0)

        limiter.check("alice")         # t=0, call 1
        clock.advance(6.0)
        limiter.check("alice")         # t=6, call 2
        assert limiter.check("alice").allowed is False  # t=6, at limit

        clock.advance(4.0)             # t=10 — call 1 expires
        result = limiter.check("alice")
        assert result.allowed is True  # 1 slot opened (call 1 expired)
        assert result.remaining == 0   # call 2 (t=6) still live + this call

    def test_no_double_throughput_at_boundary(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """Classic fixed-window exploit: fire N calls just before the boundary,
        then N more just after. With sliding window, the first N are still
        in the window, so the second batch is rejected.

        sustained_rate=3, window=10s:
        - 3 calls at t=9 (just before boundary at t=10)
        - at t=10, a fixed window would reset → allow 3 more (6 in 2 seconds!)
        - sliding window: the 3 calls at t=9 expire at t=19, so at t=10
          all 3 are still live → next call is rejected.
        """
        limiter = make_limiter(clock, store, sustained_rate=3, window_seconds=10.0)

        clock.advance(9.0)
        for _ in range(3):
            assert limiter.check("alice").allowed is True

        clock.advance(1.0)  # t=10
        # With sliding window, those 3 calls are still in [t=0+10=10, ...=19]
        # so we should be rejected
        assert limiter.check("alice").allowed is False

    def test_gradual_slot_recovery(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """Calls made at different times free up slots at different times.

        sustained_rate=3, window=10s:
        - call at t=0, t=3, t=7 → 3 used
        - t=10: call at t=0 expires → 1 slot
        - t=13: call at t=3 expires → 2 slots
        - t=17: call at t=7 expires → 3 slots (full reset)
        """
        limiter = make_limiter(clock, store, sustained_rate=3, window_seconds=10.0)

        limiter.check("alice")    # t=0
        clock.advance(3.0)
        limiter.check("alice")    # t=3
        clock.advance(4.0)
        limiter.check("alice")    # t=7
        assert limiter.check("alice").allowed is False  # full

        # t=10: only the t=0 call expired
        clock.advance(3.0)  # now at t=10
        assert limiter.check("alice").allowed is True   # 1 slot freed
        assert limiter.check("alice").allowed is False   # full again (t=3 still live)

        # t=13: the t=3 call also expires
        clock.advance(3.0)  # now at t=13
        assert limiter.check("alice").allowed is True

    def test_sliding_window_with_burst(
        self, clock: FakeClock, store: MemoryStore,
    ):
        """Sliding expiry should also interact correctly with burst limits.

        sustained_rate=6, burst_max=2, window=10s:
        - Fire 2 calls (burst limit) at t=0 → burst exhausted
        - At t=5, some burst should have replenished
        - At t=10, the t=0 calls expire from sustained window
        """
        limiter = make_limiter(
            clock, store, sustained_rate=6, window_seconds=10.0, burst_max=2,
        )

        limiter.check("alice")  # t=0
        limiter.check("alice")  # t=0 — burst exhausted
        assert limiter.check("alice").allowed is False  # burst-limited

        # Advance enough for burst to partially replenish
        clock.advance(5.0)
        result = limiter.check("alice")
        assert result.allowed is True  # burst replenished, sustained still has room
