# Agent Log

## 2026-03-08 — Implementer
**What I did:** Built the full RateLimiter implementation from scratch using a hybrid algorithm: fixed window counter for sustained rate + token bucket for burst limiting. Created `_impl.py` with core logic and wired it into `interface.py` method bodies via lazy imports.
**Test status:** 57 passing, 0 failing, 0 skipped
**For next agent:** Code is functional but could benefit from a Reviewer pass — check edge cases around window boundary resets, float precision in burst calculations, and whether the fixed-window approach (vs sliding window) creates any spec-violating blind spots. A Refactorer could also DRY up the sync/async duplication in `_compute` usage.

## 2026-03-08 — Reviewer
**What I did:** Audited `_impl.py` for correctness, float precision, edge cases, and contract violations. Checked retry_after math, burst refill clamping, division-by-zero paths, state packing round-trips, and negative-value edge cases. No code bugs found — implementation is correct for its design.
**Test status:** 57 passing, 0 failing, 0 skipped
**For next agent:** Refactorer could DRY the `do_check`/`do_acheck` pair (trivial — they differ only by sync/async calls). Or Hardener could add internal assertions on invariants (e.g., `remaining >= 0`, `retry_after >= 0`).
**For human:** Two spec-level observations:
1. **Race condition**: `check()` does non-atomic read→compute→write. Concurrent calls for the same key can bypass the limit. The `Store` protocol has no CAS/lock primitive to fix this — consider whether this matters for your use case, or whether a `lock(key)` method should be added to the Store protocol.
2. ~~**Fixed-window boundary doubling**~~ — resolved by Refactorer (see below).

## 2026-03-08 — Refactorer
**What I did:** Rewrote `_impl.py` from fixed-window counter to sliding window log + token bucket. State now stores individual call timestamps (variable-length) instead of a single counter. Eliminates the boundary-doubling issue where callers could get 2× throughput by timing calls across window edges. Also removed dead `_do` stub.
**Test status:** 57 passing, 0 failing, 0 skipped
**For next agent:** Hardener could add internal assertions and stress-test the sliding window with large sustained_rate values (state grows linearly with allowed calls — potential memory concern for very high rates). Race condition from Reviewer's notes remains unaddressed (spec-level issue).

## 2026-03-08 — Spec Phase (human + AI)
**What we did:** Audited the test suite for spec gaps and added 19 new tests across 4 new files:
- `test_retry_after_honor.py` (6 tests) — retry_after honor contract: waiting retry_after seconds MUST allow the next call. Includes property-based test across all valid configs.
- `test_sliding_window.py` (4 tests) — sliding window semantics: individual call expiry, no boundary doubling, gradual slot recovery. These tests would FAIL on a fixed-window implementation.
- `test_burst_remaining.py` (6 tests) — remaining/retry_after semantics under burst: remaining reflects burst tokens, retry_after honored for burst rejections.
- `test_store_resilience.py` (3 tests) — graceful degradation on store data loss, shared store between limiter instances.

Also updated DOCS.md with: retry_after honor contract, remaining-under-burst semantics, sliding window explanation, and store data loss behavior.

**Test status:** 76 passing, 0 failing, 0 skipped
**For next agent:** All 19 new tests pass against current impl — these lock in existing behavior, no implementation changes needed. Open items: (1) Race condition still unaddressed (spec-level — needs Store protocol change). (2) Memory growth with high sustained_rate could use a hardener pass with internal assertions or an alternative compacted representation.

## 2026-03-08 — Hardener
**What I did:** Added three defensive measures to `_impl.py`: (1) `_unpack` now returns `None` on corrupted/truncated bytes instead of crashing — `_compute` treats corrupted state as fresh (fail-open). (2) Burst tokens clamped to `[0, burst_max]` after refill to guard against float drift. (3) Internal assertions on `remaining >= 0` and `retry_after >= 0` post-computation to catch invariant violations early.
**Test status:** 76 passing, 0 failing, 0 skipped
**For next agent:** Open items remain: (1) Race condition (spec-level). (2) Memory growth with high sustained_rate (state stores one timestamp per allowed call). (3) `do_check`/`do_acheck` sync/async duplication is minor but still present.

## 2026-03-08 — Doc-gardener
**What I did:** Verified all markdown against implementation. CLAUDE.md, DOCS.md, and log.md are all accurate. Checked: sliding window logic, fail-open on corruption, retry_after honor, remaining-under-burst semantics, config validation, export list. No inaccuracies found. Cleaned stale "CLAUDE.md doesn't exist" note from Hardener entry.
**Test status:** 76 passing, 0 failing, 0 skipped
**For next agent:** Module is in excellent shape — all 5 roles have completed a pass. Remaining open items are spec-level: (1) Race condition (needs Store protocol change). (2) Memory growth for very high sustained_rate. The sync/async duplication in `do_check`/`do_acheck` is ~12 lines each and inherent to the pattern — not worth a dedicated refactor. No further agent work needed unless the human changes the spec.
