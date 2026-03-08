# Rate Limiter — Developer Guide

## What It Does

Controls how many operations a caller (identified by a string key) can perform
within a rolling time window. Supports both sustained rate limits and burst
allowances.

## Quick Start

Three lines to get going:

```python
from rate_limiter import RateLimiter, RateLimiterConfig

limiter = RateLimiter(config=RateLimiterConfig(
    sustained_rate=100,    # 100 calls …
    window_seconds=60.0,   # … per minute
    burst_max=20,          # up to 20 in a quick burst
))

result = limiter.check("user-42")
if result.allowed:
    do_work()
else:
    print(f"Slow down — retry in {result.retry_after:.1f}s")
    print(f"Remaining quota: {result.remaining}")
```

When `store` and `clock` are omitted, the limiter uses sensible defaults:
- **Clock**: `SystemClock` — real wall time via `time.time()`
- **Store**: `MemoryStore` — in-memory with TTL expiration

> **Warning**: The default `MemoryStore` is **single-process only**. State is
> not shared across instances and is lost on restart. For production deployments
> with multiple processes or hosts, inject a shared store (see below).

## Async Usage

Same limiter, use `acheck` instead:

```python
result = await limiter.acheck("user-42")
if not result.allowed:
    raise TooManyRequests(retry_after=result.retry_after)
```

## Explicit Dependencies

You can always inject your own clock and store:

```python
from rate_limiter import (
    RateLimiter, RateLimiterConfig, SystemClock, MemoryStore,
)

clock = SystemClock()
store = MemoryStore(clock=clock)

limiter = RateLimiter(
    config=RateLimiterConfig(sustained_rate=100, window_seconds=60.0, burst_max=20),
    store=store,
    clock=clock,
)
```

## Resetting a Caller

Admin override, account upgrade, support escalation — sometimes you need to
wipe the slate:

```python
limiter.reset("user-42")
# Next check behaves as if user-42 was never seen

await limiter.areset("user-42")  # async variant
```

## Writing a Custom Store (e.g., Redis)

Implement the `Store` protocol — six methods (sync + async pairs for
get/set/delete):

```python
import redis.asyncio as aioredis
import redis as sync_redis


class RedisStore:
    """Example Redis-backed store for shared state across instances."""

    def __init__(self, sync_client: sync_redis.Redis,
                 async_client: aioredis.Redis) -> None:
        self._sync = sync_client
        self._async = async_client

    def get(self, key: str) -> bytes | None:
        return self._sync.get(key)

    async def aget(self, key: str) -> bytes | None:
        return await self._async.get(key)

    def set(self, key: str, value: bytes, ttl_seconds: float) -> None:
        self._sync.set(key, value, px=int(ttl_seconds * 1000))

    async def aset(self, key: str, value: bytes, ttl_seconds: float) -> None:
        await self._async.set(key, value, px=int(ttl_seconds * 1000))

    def delete(self, key: str) -> None:
        self._sync.delete(key)

    async def adelete(self, key: str) -> None:
        await self._async.delete(key)
```

Then plug it in:

```python
limiter = RateLimiter(
    config=config,
    store=RedisStore(sync_client, async_client),
)
```

## Testing with Fake Time

Use `FakeClock` to write deterministic tests without sleeps:

```python
from rate_limiter import (
    RateLimiter, RateLimiterConfig, FakeClock, MemoryStore,
)

clock = FakeClock(start=1000.0)
store = MemoryStore(clock=clock)
limiter = RateLimiter(
    config=RateLimiterConfig(sustained_rate=2, window_seconds=10.0, burst_max=2),
    store=store,
    clock=clock,
)

assert limiter.check("alice").allowed       # 1st — ok
assert limiter.check("alice").allowed       # 2nd — ok
assert not limiter.check("alice").allowed   # 3rd — rejected

clock.advance(10.0)                         # window rolls over
assert limiter.check("alice").allowed       # ok again
```

## Configuration Reference

| Field            | Type    | Meaning                                      |
|------------------|---------|----------------------------------------------|
| `sustained_rate` | `int`   | Max calls allowed within the window           |
| `window_seconds` | `float` | Rolling window duration in seconds             |
| `burst_max`      | `int`   | Max calls in a short burst (≤ `sustained_rate`) |

When `burst_max == sustained_rate`, no burst distinction is made — the limiter
behaves as a simple "N per window" policy.

## CheckResult Reference

Every call to `check` / `acheck` returns a `CheckResult`:

| Field         | Type    | Meaning                                       |
|---------------|---------|-----------------------------------------------|
| `allowed`     | `bool`  | Whether this call is permitted                 |
| `remaining`   | `int`   | Calls available right now (see below)          |
| `retry_after` | `float` | Seconds until next allowed call (0.0 if allowed) |

### `retry_after` honor contract

**If `retry_after` says wait X seconds, waiting X seconds guarantees the next call is
allowed.** This is a hard contract, not advisory. Callers can set timers, sleep, or
schedule retries based on this value with confidence.

### `remaining` under burst

When `burst_max < sustained_rate`, `remaining` reflects the number of calls you can make
**right now** — i.e., available burst tokens, not sustained-rate headroom. This is the
only actionable interpretation for API consumers deciding whether to proceed or back off.

## Sliding Window Semantics

The limiter uses a **sliding window**: each call expires individually at its own
`timestamp + window_seconds`. This prevents the classic fixed-window exploit where
callers get 2x throughput by timing calls across window boundaries.

Example with `sustained_rate=3, window=10s`:
- Calls at t=0, t=3, t=7 → 3 used, limit reached
- At t=10: only the t=0 call expires → 1 slot opens
- At t=13: the t=3 call also expires → 2 slots open

## Store Data Loss

If the store loses a key (TTL expiry, eviction, restart), the limiter treats the caller
as fresh — full quota restored. The limiter never crashes or permanently blocks due to
missing store data. This is "fail open on data loss" behavior.

## Error Handling

- **Invalid config** (e.g., `burst_max > sustained_rate`, non-positive values):
  Raises `ValueError` at construction time. The limiter is never in an invalid
  state.
- **Store failures**: Propagated as-is. The limiter does not swallow store
  exceptions — the caller decides how to handle infrastructure errors (fail open,
  fail closed, retry, etc.).

## Thread Safety

The limiter itself holds no mutable state — all state lives in the injected
store. The bundled `MemoryStore` is thread-safe (uses a lock). For custom stores,
thread safety is your responsibility.

## Roadmap

Planned evolutions for the library:

- **`RedisStore`** — First-party Redis-backed store shipped with the module,
  so users don't have to write their own for multi-instance deployments.
