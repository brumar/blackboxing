# Challenge — 2026-03-08

## Issue 1: Race Condition in `check()` — Non-Atomic Read-Compute-Write

### What I Found
`check()` does `store.get()` → `_compute()` → `store.set()` as three separate calls. Two concurrent calls for the same key can both read the same state, both compute "allowed", and both write back — bypassing the limit.

### Evidence
- `_impl.py:129-132` (`do_check`): `get` → `_compute` → `set` with no atomicity
- `_impl.py:142-145` (`do_acheck`): same pattern, async
- `interface.py:68-102` (`Store` protocol): no `cas()`, `lock()`, or atomic-update primitive

### Recommendation
Add an atomic update mechanism to the `Store` protocol. Options:
1. **`cas(key, expected, new, ttl)` (compare-and-swap)** — optimistic concurrency, retry on conflict
2. **`lock(key)` / `unlock(key)`** — pessimistic locking, simpler but higher contention
3. **`update(key, fn, ttl)`** — store executes the function atomically (like Redis EVAL)

Option 3 is cleanest but hardest to implement across backends. Option 1 is the most portable.

### Severity
**warning** — Single-process use with `MemoryStore` is fine (GIL + lock). Only matters for multi-process/distributed deployments with shared stores (Redis, SQL). Can work around it but spec needs attention before a production `RedisStore` is viable.

---

## Issue 2: Memory Growth with High `sustained_rate`

### What I Found
The sliding window stores one timestamp (8 bytes) per allowed call. For `sustained_rate=100_000, window_seconds=60`, that's up to 800KB of state per key. With many keys, this could become significant.

### Evidence
- `_impl.py:19-22`: state layout stores N doubles for N timestamps
- `_impl.py:94`: each allowed call appends `now` to the timestamp list
- No upper bound on state size besides `sustained_rate`

### Recommendation
For typical rates (≤1000/window) this is fine. For very high rates, consider:
1. **Document the trade-off** in DOCS.md (memory per key ≈ `sustained_rate × 8 bytes`)
2. **Alternative representation** — approximate sliding window using sub-buckets (e.g., 10 fixed sub-windows) instead of individual timestamps. Trades precision for O(1) memory.
3. **Do nothing** — if very high `sustained_rate` isn't a real use case, just document the limit.

### Severity
**warning** — Not a correctness issue. Only matters for extreme configurations. Option 3 (document it) is likely sufficient.
