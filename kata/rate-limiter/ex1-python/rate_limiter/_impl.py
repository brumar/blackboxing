"""Rate Limiter — implementation (black box).

Hybrid algorithm:
- Fixed window counter for sustained rate (resets when window expires)
- Token bucket for burst limiting (refills continuously)
"""

from __future__ import annotations

import struct

from rate_limiter.interface import (
    CheckResult,
    Clock,
    RateLimiterConfig,
    Store,
)

# State: (window_start, call_count, burst_tokens, last_burst_time)
_STATE_FMT = "!dddd"


def _pack(window_start: float, count: float, burst: float, burst_time: float) -> bytes:
    return struct.pack(_STATE_FMT, window_start, count, burst, burst_time)


def _unpack(raw: bytes) -> tuple[float, float, float, float]:
    return struct.unpack(_STATE_FMT, raw)


def validate_config(config: RateLimiterConfig) -> None:
    if config.sustained_rate < 1:
        raise ValueError(f"sustained_rate must be >= 1, got {config.sustained_rate}")
    if config.window_seconds <= 0:
        raise ValueError(f"window_seconds must be > 0, got {config.window_seconds}")
    if config.burst_max < 1:
        raise ValueError(f"burst_max must be >= 1, got {config.burst_max}")
    if config.burst_max > config.sustained_rate:
        raise ValueError(
            f"burst_max ({config.burst_max}) cannot exceed "
            f"sustained_rate ({config.sustained_rate})"
        )


def _compute(
    now: float, config: RateLimiterConfig, raw: bytes | None,
) -> tuple[bool, int, float, bytes]:
    """Core logic. Returns (allowed, remaining, retry_after, new_state)."""
    if raw is None:
        window_start = now
        count = 0.0
        burst = float(config.burst_max)
        burst_time = now
    else:
        window_start, count, burst, burst_time = _unpack(raw)

    # Reset window if expired
    if now >= window_start + config.window_seconds:
        window_start = now
        count = 0.0

    # Refill burst tokens
    elapsed = now - burst_time
    if elapsed > 0:
        burst_rate = config.burst_max / config.window_seconds
        burst = min(config.burst_max, burst + elapsed * burst_rate)
    burst_time = now

    sustained_remaining = config.sustained_rate - int(count)
    burst_available = burst >= 1.0

    if sustained_remaining >= 1 and burst_available:
        count += 1.0
        burst -= 1.0
        new_sustained = config.sustained_rate - int(count)
        remaining = min(int(burst), new_sustained)
        state = _pack(window_start, count, burst, burst_time)
        return True, remaining, 0.0, state

    # Rejected
    burst_wait = (
        (1.0 - burst) / (config.burst_max / config.window_seconds)
        if burst < 1.0
        else 0.0
    )
    sustained_wait = (
        (window_start + config.window_seconds - now)
        if sustained_remaining < 1
        else 0.0
    )
    retry_after = min(max(burst_wait, sustained_wait), config.window_seconds)
    state = _pack(window_start, count, burst, burst_time)
    return False, 0, retry_after, state


def do_check(
    key: str,
    config: RateLimiterConfig,
    store: Store,
    clock: Clock,
) -> CheckResult:
    now = clock.now()
    raw = store.get(key)
    allowed, remaining, retry_after, state = _compute(now, config, raw)
    store.set(key, state, config.window_seconds)
    return CheckResult(allowed=allowed, remaining=remaining, retry_after=retry_after)


async def do_acheck(
    key: str,
    config: RateLimiterConfig,
    store: Store,
    clock: Clock,
) -> CheckResult:
    now = await clock.anow()
    raw = await store.aget(key)
    allowed, remaining, retry_after, state = _compute(now, config, raw)
    await store.aset(key, state, config.window_seconds)
    return CheckResult(allowed=allowed, remaining=remaining, retry_after=retry_after)
