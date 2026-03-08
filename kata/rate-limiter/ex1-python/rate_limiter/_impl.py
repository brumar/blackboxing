"""Rate Limiter — implementation (black box).

Sliding window log + token bucket:
- Sliding window: stores timestamps of each allowed call, prunes expired ones
- Token bucket: burst tokens refill continuously, cap rapid-fire calls
"""

from __future__ import annotations

import struct

from rate_limiter.interface import (
    CheckResult,
    Clock,
    RateLimiterConfig,
    Store,
)

# State layout: [burst_tokens: double, last_burst_time: double, N timestamps: double...]
_HEADER_FMT = "!dd"
_HEADER_SIZE = struct.calcsize(_HEADER_FMT)
_TS_SIZE = struct.calcsize("!d")


def _pack(burst: float, burst_time: float, timestamps: list[float]) -> bytes:
    header = struct.pack(_HEADER_FMT, burst, burst_time)
    body = struct.pack(f"!{len(timestamps)}d", *timestamps) if timestamps else b""
    return header + body


def _unpack(raw: bytes) -> tuple[float, float, list[float]]:
    burst, burst_time = struct.unpack(_HEADER_FMT, raw[:_HEADER_SIZE])
    n = (len(raw) - _HEADER_SIZE) // _TS_SIZE
    timestamps = list(struct.unpack(f"!{n}d", raw[_HEADER_SIZE:])) if n else []
    return burst, burst_time, timestamps


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
        burst = float(config.burst_max)
        burst_time = now
        timestamps: list[float] = []
    else:
        burst, burst_time, timestamps = _unpack(raw)

    # Prune timestamps outside the current window
    window_start = now - config.window_seconds
    timestamps = [t for t in timestamps if t > window_start]

    # Refill burst tokens
    elapsed = now - burst_time
    if elapsed > 0:
        burst_rate = config.burst_max / config.window_seconds
        burst = min(float(config.burst_max), burst + elapsed * burst_rate)
    burst_time = now

    count = len(timestamps)
    sustained_remaining = config.sustained_rate - count
    burst_available = burst >= 1.0

    if sustained_remaining >= 1 and burst_available:
        timestamps.append(now)
        burst -= 1.0
        new_sustained = sustained_remaining - 1
        remaining = min(int(burst), new_sustained)
        state = _pack(burst, burst_time, timestamps)
        return True, remaining, 0.0, state

    # Rejected — compute retry_after
    if sustained_remaining < 1:
        # Earliest timestamp will expire first, opening a slot
        oldest = min(timestamps)
        sustained_wait = oldest + config.window_seconds - now
    else:
        sustained_wait = 0.0

    if burst < 1.0:
        burst_rate = config.burst_max / config.window_seconds
        burst_wait = (1.0 - burst) / burst_rate
    else:
        burst_wait = 0.0

    retry_after = min(max(burst_wait, sustained_wait), config.window_seconds)
    state = _pack(burst, burst_time, timestamps)
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
