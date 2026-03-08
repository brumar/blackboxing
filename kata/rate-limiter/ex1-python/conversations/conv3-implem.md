
╭─── Claude Code v2.1.71 ──────────────────────────────────────────────────────╮
│                                                │ Tips for getting started    │
│               Welcome back Bruno!              │ Run /init to create a CLAU… │
│                                                │ ─────────────────────────── │
│                     ▐▛███▜▌                    │ Recent activity             │
│                    ▝▜█████▛▘                   │ No recent activity          │
│                      ▘▘ ▝▝                     │                             │
│                                                │                             │
│             Opus 4.6 · Claude Max              │                             │
│   ~/blackboxing/kata/rate-limiter/ex1-python   │                             │
╰──────────────────────────────────────────────────────────────────────────────╯

❯ lets work on ex1-python. activate the agent spec and work at your discretion  
on it. I accept all changes. This is a multi-run process. Play as a teammate    
for the next agents.                                                            

● Let me first see what exists for ex1-python.

● Explore(Explore ex1-python module)
  ⎿  Done (26 tool uses · 68.8k tokens · 46s)
  (ctrl+o to expand)

● Good — ex1-python is a complete rate-limiter module with 57 passing tests. Let
   me activate the agent to do an improvement pass.

● Skill(blackboxing-agent)
  ⎿  Successfully loaded skill

● Starting the agent bootstrap. Let me orient first.

● Read 6 files (ctrl+o to expand)

● Now let me run the test suite to confirm current state.

● Bash(cd /home/bruno/blackboxing/kata/rate-limiter/ex1-python && python -m
      pytest tests/ -v --tb=short 2>&1)
  ⎿  Error: Exit code 1
     /home/bruno/bin/python: No module named pytest

● Bash(cd /home/bruno/blackboxing/kata/rate-limiter/ex1-python && cat
      pyproject.toml)
  ⎿  [project]
     name = "rate-limiter"
     version = "0.1.0"
     … +9 lines (ctrl+o to expand)

● Bash(pip install -e . 2>&1 | tail -5)
  ⎿      See /usr/share/doc/python3.12/README.venv for more information.

     note: If you believe this is a mistake, please contact your Python ins
     … +4 lines (ctrl+o to expand)

● Bash(which python3 && python3 --version && (python3 -m venv .venv && source
      .venv/bin/activate && pip install -e ".[dev]" 2>&1 || (source
      .venv/bin/activate && pip i…)
  ⎿  /usr/bin/python3
     Python 3.12.3
     Checking if build backend supports build_editable: started
     … +14 lines (ctrl+o to expand)

● Bash(source .venv/bin/activate && python -m pytest tests/ -v --tb=short 2>&1)
  ⎿  ============================= test session starts ====================
     ==========
     platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0 -- /home/b
     … +82 lines (ctrl+o to expand)

● 57/57 passing. All green. Now let me assess and choose a role.

  Orientation summary:
  - 57 tests pass, 0 fail
  - One previous agent run: Implementer (2026-03-08)
  - The log suggests: Reviewer pass (edge cases, float precision, spec-violating
   blind spots) or Refactorer (DRY sync/async)
  - Implementation is a single 120-line file — compact, not messy enough for a
  full Refactorer pass
  - Role choice: Reviewer — most valuable next step per the implementer's notes

  Let me write the plan and then execute.

● Write(.blackbox/plan.md)
  ⎿  Wrote 16 lines to .blackbox/plan.md
       1 # Plan — Reviewer — 2026-03-08
       2 
       3 ## Assessment
       4 All 57 tests pass. Implementation is a compact 120-line hybrid a
         lgorithm (fixed window + token bucket). The implementer flagged 
         float precision in burst calculations, window boundary behavior,
          and fixed-window blind spots as areas to audit.
       5 
       6 ## Goal
       7 Audit `_impl.py` for correctness bugs, edge cases the tests don'
         t cover, and contract violations that happen to pass current tes
         ts. Fix what's safe to fix; document the rest for next agents.
       8 
       9 ## Steps
      10 - [ ] Audit `_compute` for off-by-one and float precision issues
     … +6 lines (ctrl+o to expand)

● Now let me do the actual review. I've already read all the code. Let me
  analyze _impl.py systematically.

  Findings from code review of _impl.py:

  1. Retry_after calculation — potential bug when both burst and sustained are 
  exhausted

  At line 91: retry_after = min(max(burst_wait, sustained_wait), 
  config.window_seconds)

  When both limits are hit, it takes max(burst_wait, sustained_wait) — correct,
  caller needs to wait for the slower of the two. But then it clamps to
  config.window_seconds. The property test test_retry_after_never_exceeds_window
   validates this. Good.

  2. Float precision in burst refill

  The burst refill at line 66: burst = min(config.burst_max, burst + elapsed * 
  burst_rate) — the min clamp prevents overshoot. Good.

  3. Division by zero check

  burst_rate = config.burst_max / config.window_seconds — config validation
  ensures window_seconds > 0 and burst_max >= 1, so no division by zero. Good.

  Similarly in retry_after: (1.0 - burst) / (config.burst_max / 
  config.window_seconds) — same guarantees apply.

  4. Read-modify-write race condition

  The do_check function does: get → compute → set. This is NOT atomic. Two
  concurrent calls for the same key could both read the same state, both allow,
  and both write — effectively allowing double the rate. The MemoryStore lock
  only protects individual operations, not the full read-modify-write sequence.

  This is a real correctness issue but it's architectural — fixing it properly
  requires either:
  - A compare-and-swap or lock-per-key pattern in the store
  - Making the limiter hold the lock across the full operation
  - Documenting it as a known limitation

  Since the interface defines Store as a simple get/set protocol without CAS,
  this is a spec-level concern for the human.

  5. Window reset behavior — fixed window blind spot

  The fixed-window algorithm resets at window boundaries. A caller could make N
  calls at the end of one window and N calls at the start of the next,
  effectively doubling throughput in a 2x window-sized span. This is a known
  trade-off of fixed-window vs sliding-window. The interface doesn't specify
  which algorithm to use ("The algorithm used internally is an implementation
  detail"), so this is valid but worth noting.

  6. State struct uses count as float but semantically it's an int

  count is stored as a double in the struct but used as an integer counter. This
   works fine — IEEE 754 doubles represent integers exactly up to 2^53. No real
  issue, just a minor clarity thing.

  7. Burst tokens can accumulate while sustained rate is exhausted

  If a caller is blocked by sustained rate but time passes, burst tokens refill.
   When the window resets, burst tokens could already be near-max. This is
  actually correct behavior — burst should be available at window reset.

  Let me verify one edge case I'm concerned about — what happens if retry_after
  could go negative in some edge case with burst math:

● Read 1 file (ctrl+o to expand)

● 8. Potential negative retry_after edge case

  burst_wait = (1.0 - burst) / (burst_max / window_seconds) — if burst is
  between 0 and 1, this is positive. If burst is exactly 0, (1.0 - 0) / rate is
  positive. If burst is negative... can it go negative?

  Looking at the deduction: burst -= 1.0 only happens when burst >= 1.0 (line
  70-74). And refill clamps to min(burst_max, ...). But what about the initial
  state when burst starts at burst_max (float) — the sequence of subtract-1
  calls can bring it down to 0.0 at most in a single window (since burst_max
  checks prevent more subtractions).

  Actually, there's a subtle path: if burst is say 1.5 after refill, it passes
  burst >= 1.0 check, gets decremented to 0.5. Next call: burst = 0.5, fails
  burst check, gets rejected. burst_wait = (1.0 - 0.5) / rate = positive. All
  good.

  No negative retry_after bug found. The logic is sound.

  Summary of findings

  Two spec-level concerns, zero code bugs to fix:

  1. Race condition in read-modify-write — concurrent calls for the same key can
   bypass the rate limit. This is inherent to the Store protocol design (no
  CAS/locking primitive).
  2. Fixed-window boundary doubling — known trade-off, acceptable since the
  interface says algorithm is an implementation detail.

  No code changes needed — the implementation is correct for its design. Let me
  update the handoff log and clean up.

● Read 1 file (ctrl+o to expand)

● Update(.blackbox/log.md)
  ⎿  Added 8 lines
       4  **What I did:** Built the full RateLimiter implementation from 
          scratch using a hybrid algorithm: fixed window counter for sust
          ained rate + token bucket for burst limiting. Created `_impl.py
          ` with core logic and wired it into `interface.py` method bodie
          s via lazy imports.
       5  **Test status:** 57 passing, 0 failing, 0 skipped
       6  **For next agent:** Code is functional but could benefit from a
           Reviewer pass — check edge cases around window boundary resets
          , float precision in burst calculations, and whether the fixed-
          window approach (vs sliding window) creates any spec-violating 
          blind spots. A Refactorer could also DRY up the sync/async dupl
          ication in `_compute` usage.
       7 +                                                               
       8 +## 2026-03-08 — Reviewer                                       
       9 +**What I did:** Audited `_impl.py` for correctness, float preci
         +sion, edge cases, and contract violations. Checked retry_after 
         +math, burst refill clamping, division-by-zero paths, state pack
         +ing round-trips, and negative-value edge cases. No code bugs fo
         +und — implementation is correct for its design.                
      10 +**Test status:** 57 passing, 0 failing, 0 skipped              
      11 +**For next agent:** Refactorer could DRY the `do_check`/`do_ach
         +eck` pair (trivial — they differ only by sync/async calls). Or 
         +Hardener could add internal assertions on invariants (e.g., `re
         +maining >= 0`, `retry_after >= 0`).                            
      12 +**For human:** Two spec-level observations:                    
      13 +1. **Race condition**: `check()` does non-atomic read→compute→w
         +rite. Concurrent calls for the same key can bypass the limit. T
         +he `Store` protocol has no CAS/lock primitive to fix this — con
         +sider whether this matters for your use case, or whether a `loc
         +k(key)` method should be added to the Store protocol.          
      14 +2. **Fixed-window boundary doubling**: A caller can get 2× thro
         +ughput by timing calls across window boundaries. This is a know
         +n trade-off vs sliding window. The interface deliberately says 
         +"algorithm is an implementation detail," so this is valid — jus
         +t be aware of it.                                              

● Now delete the plan file.

● Bash(rm
      /home/bruno/blackboxing/kata/rate-limiter/ex1-python/.blackbox/plan.md)
  ⎿  Done

● Done. Here's the summary:

  ---
  Reviewer pass complete

  Role: Reviewer | Module: ex1-python rate-limiter

  Result: Implementation is clean — no code bugs found. The _impl.py algorithm
  (fixed window + token bucket) is correct:
  - No float precision issues (burst clamped properly)
  - No division-by-zero paths (config validation prevents)
  - No negative retry_after edge cases
  - State packing round-trips correctly

  Two spec-level observations logged for you:

  1. Race condition — check() does non-atomic read→compute→write. Concurrent
  same-key calls can bypass the limit. The Store protocol would need a lock(key)
   or CAS primitive to fix this.
  2. Fixed-window boundary doubling — Callers can get ~2× throughput by timing
  calls across window boundaries. Known trade-off of fixed vs sliding window.

  For next agent run: Refactorer (DRY sync/async duplication) or Hardener
  (internal assertions) are the natural next steps.

✻ Worked for 2m 48s

❯ is the limit bypassing the main issue or is there risks for crash ? lets use  
sliding window instead please.                                                  

● Good question. The race condition is about accuracy, not crashes — no crash
  risk. The code handles all edge cases safely (no division by zero, no negative
   values, no overflow). The worst case is allowing a few extra calls under high
   concurrency.

  The fixed-window boundary doubling is the more practical concern — it's a
  correctness issue where a caller can get 2× throughput by timing calls at
  window edges. Switching to sliding window fixes that.

  Let me launch the agent to rewrite the algorithm.

● Skill(blackboxing-agent)
  ⎿  Successfully loaded skill

● Alright, the human wants me to switch from fixed-window to sliding window
  algorithm. Let me orient and then execute.

  Step 1: Orient

  I have context from the previous run. Let me read the current log and run
  tests to confirm state.

● Read 2 files (ctrl+o to expand)

● Let me also read the test files to understand exactly what the tests expect,
  so the sliding window rewrite passes them all.

● Explore(Read all test files)
  ⎿  Done (12 tool uses · 57.3k tokens · 22s)
  (ctrl+o to expand)

● Good, I have full context now. Let me run the current tests to confirm
  baseline, then rewrite.

  Step 2: Challenge Gate

  No spec issues. The interface says "The algorithm used internally is an
  implementation detail" — switching to sliding window is a pure internal
  change. All 57 tests are algorithm-agnostic. Proceeding.

  Step 3: Role — Refactorer

  All tests pass, the human requested an algorithm change. This is a rewrite of
  internals without changing behavior — Refactorer role.

● Write(.blackbox/plan.md)
  ⎿  Wrote 15 lines to .blackbox/plan.md
       1 # Plan — Refactorer — 2026-03-08
       2 
       3 ## Assessment
       4 Human requested switch from fixed-window to sliding window to el
         iminate boundary-doubling. Current impl is 120 lines, hybrid fix
         ed-window + token bucket. All 57 tests pass and are algorithm-ag
         nostic.
       5 
       6 ## Goal
       7 Rewrite `_impl.py` to use sliding window log + token bucket for 
         burst, passing all 57 tests.
       8 
       9 ## Steps
      10 - [ ] Rewrite _compute to use sliding window log (store timestam
         ps of calls within window)
     … +5 lines (ctrl+o to expand)

● Bash(source .venv/bin/activate && python -m pytest tests/ -q 2>&1)
  ⎿  .........................................................
        [100%]
     57 passed in 0.79s

● 57 passing. Now let me rewrite _impl.py with a sliding window log algorithm.

  Step 4: Execute

  The key design decisions for the rewrite:
  - Sliding window log: Store individual call timestamps, prune expired ones on
  each check
  - Token bucket for burst: Keep continuous refill, same as before
  - State format: Variable-length — encode burst state + list of timestamps
  - TTL: Set to window_seconds so the store auto-expires stale entries

● Write(rate_limiter/_impl.py)
  ⎿  Added 48 lines, removed 33 lines
      1  """Rate Limiter — implementation (black box).
      2  
      3 -Hybrid algorithm:                                               
      4 -- Fixed window counter for sustained rate (resets when window ex
        -pires)                                                          
      5 -- Token bucket for burst limiting (refills continuously)        
      3 +Sliding window log + token bucket:                              
      4 +- Sliding window: stores timestamps of each allowed call, prunes
        + expired ones                                                   
      5 +- Token bucket: burst tokens refill continuously, cap rapid-fire
        + calls                                                          
      6  """
      7  
      8  from __future__ import annotations
     ...
      16      Store,
      17  )
      18  
      19 -# State: (window_start, call_count, burst_tokens, last_burst_ti
         -me)                                                            
      20 -_STATE_FMT = "!dddd"                                           
      19 +# State layout: [burst_tokens: double, last_burst_time: double,
         + N timestamps: double...]                                      
      20 +_HEADER_FMT = "!dd"                                            
      21 +_HEADER_SIZE = struct.calcsize(_HEADER_FMT)                    
      22 +_TS_SIZE = struct.calcsize("!d")                               
      23  
      24  
      23 -def _pack(window_start: float, count: float, burst: float, burs
         -t_time: float) -> bytes:                                       
      24 -    return struct.pack(_STATE_FMT, window_start, count, burst, 
         -burst_time)                                                    
      25 +def _pack(burst: float, burst_time: float, timestamps: list[flo
         +at]) -> bytes:                                                 
      26 +    header = struct.pack(_HEADER_FMT, burst, burst_time)       
      27 +    body = struct.pack(f"!{len(timestamps)}d", *timestamps) if 
         +timestamps else b""                                            
      28 +    return header + body                                       
      29  
      30  
      27 -def _unpack(raw: bytes) -> tuple[float, float, float, float]:  
      28 -    return struct.unpack(_STATE_FMT, raw)                      
      31 +def _unpack(raw: bytes) -> tuple[float, float, list[float]]:   
      32 +    burst, burst_time = struct.unpack(_HEADER_FMT, raw[:_HEADER
         +_SIZE])                                                        
      33 +    n = (len(raw) - _HEADER_SIZE) // _TS_SIZE                  
      34 +    timestamps = list(struct.unpack(f"!{n}d", raw[_HEADER_SIZE:
         +])) if n else []                                               
      35 +    return burst, burst_time, timestamps                       
      36  
      37  
      38  def validate_config(config: RateLimiterConfig) -> None:
     ...
       54  ) -> tuple[bool, int, float, bytes]:
       55      """Core logic. Returns (allowed, remaining, retry_after, n
           ew_state)."""
       56      if raw is None:
       50 -        window_start = now                                    
       51 -        count = 0.0                                           
       57          burst = float(config.burst_max)
       58          burst_time = now
       59 +        timestamps: list[float] = []                          
       60      else:
       55 -        window_start, count, burst, burst_time = _unpack(raw) 
       61 +        burst, burst_time, timestamps = _unpack(raw)          
       62  
       57 -    # Reset window if expired                                 
       58 -    if now >= window_start + config.window_seconds:           
       59 -        window_start = now                                    
       60 -        count = 0.0                                           
       63 +    # Prune timestamps outside the current window             
       64 +    window_start = now - config.window_seconds                
       65 +    timestamps = [t for t in timestamps if t > window_start]  
       66  
       67      # Refill burst tokens
       68      elapsed = now - burst_time
       69      if elapsed > 0:
       70          burst_rate = config.burst_max / config.window_seconds
       66 -        burst = min(config.burst_max, burst + elapsed * burst_
          -rate)                                                         
       71 +        burst = min(float(config.burst_max), burst + elapsed *
          + burst_rate)                                                  
       72      burst_time = now
       73  
       69 -    sustained_remaining = config.sustained_rate - int(count)  
       74 +    count = len(timestamps)                                   
       75 +    sustained_remaining = config.sustained_rate - count       
       76      burst_available = burst >= 1.0
       77  
       78      if sustained_remaining >= 1 and burst_available:
       73 -        count += 1.0                                          
       79 +        timestamps.append(now)                                
       80          burst -= 1.0
       75 -        new_sustained = config.sustained_rate - int(count)    
       81 +        new_sustained = sustained_remaining - 1               
       82          remaining = min(int(burst), new_sustained)
       77 -        state = _pack(window_start, count, burst, burst_time) 
       83 +        state = _pack(burst, burst_time, timestamps)          
       84          return True, remaining, 0.0, state
       85  
       80 -    # Rejected                                                
       81 -    burst_wait = (                                            
       82 -        (1.0 - burst) / (config.burst_max / config.window_seco
          -nds)                                                          
       83 -        if burst < 1.0                                        
       84 -        else 0.0                                              
       85 -    )                                                         
       86 -    sustained_wait = (                                        
       87 -        (window_start + config.window_seconds - now)          
       88 -        if sustained_remaining < 1                            
       89 -        else 0.0                                              
       90 -    )                                                         
       86 +    # Rejected — compute retry_after                          
       87 +    if sustained_remaining < 1:                               
       88 +        # Earliest timestamp will expire first, opening a slot
       89 +        oldest = min(timestamps)                              
       90 +        sustained_wait = oldest + config.window_seconds - now 
       91 +    else:                                                     
       92 +        sustained_wait = 0.0                                  
       93 +                                                              
       94 +    if burst < 1.0:                                           
       95 +        burst_rate = config.burst_max / config.window_seconds 
       96 +        burst_wait = (1.0 - burst) / burst_rate               
       97 +    else:                                                     
       98 +        burst_wait = 0.0                                      
       99 +                                                              
      100      retry_after = min(max(burst_wait, sustained_wait), config.
           window_seconds)
       92 -    state = _pack(window_start, count, burst, burst_time)     
      101 +    state = _pack(burst, burst_time, timestamps)              
      102      return False, 0, retry_after, state
      103  
      104  
      105 +def _do(key: str, config: RateLimiterConfig, store: Store, now
          +: float) -> CheckResult:                                      
      106 +    """Shared logic for sync and async paths."""              
      107 +    raw = None  # placeholder — caller passes raw via closures
      108 +    raise AssertionError("not called directly")               
      109 +                                                              
      110 +                                                              
      111  def do_check(
      112      key: str,
      113      config: RateLimiterConfig,

● Now let me clean up the dead _do function I left in there and run tests.

● Update(rate_limiter/_impl.py)
  ⎿  Removed 5 lines
      102      return False, 0, retry_after, state
      103  
      104  
      105 -def _do(key: str, config: RateLimiterConfig, store: Store, now
          -: float) -> CheckResult:                                      
      106 -    """Shared logic for sync and async paths."""              
      107 -    raw = None  # placeholder — caller passes raw via closures
      108 -    raise AssertionError("not called directly")               
      105  
      110 -                                                              
      106  def do_check(
      107      key: str,
      108      config: RateLimiterConfig,

● Bash(source .venv/bin/activate && python -m pytest tests/ -v --tb=short 2>&1)
  ⎿  ============================= test session starts ====================
     ==========
     platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0 -- /home/b
     … +82 lines (ctrl+o to expand)

● 57/57 passing on first try. Clean rewrite.

  Step 5: Handoff

● Update(.blackbox/log.md)
  ⎿  Added 6 lines, removed 1 line
      11  **For next agent:** Refactorer could DRY the `do_check`/`do_ach
          eck` pair (trivial — they differ only by sync/async calls). Or 
          Hardener could add internal assertions on invariants (e.g., `re
          maining >= 0`, `retry_after >= 0`).
      12  **For human:** Two spec-level observations:
      13  1. **Race condition**: `check()` does non-atomic read→compute→w
          rite. Concurrent calls for the same key can bypass the limit. T
          he `Store` protocol has no CAS/lock primitive to fix this — con
          sider whether this matters for your use case, or whether a `loc
          k(key)` method should be added to the Store protocol.
      14 -2. **Fixed-window boundary doubling**: A caller can get 2× thro
         -ughput by timing calls across window boundaries. This is a know
         -n trade-off vs sliding window. The interface deliberately says 
         -"algorithm is an implementation detail," so this is valid — jus
         -t be aware of it.                                              
      14 +2. ~~**Fixed-window boundary doubling**~~ — resolved by Refacto
         +rer (see below).                                               
      15 +                                                               
      16 +## 2026-03-08 — Refactorer                                     
      17 +**What I did:** Rewrote `_impl.py` from fixed-window counter to
         + sliding window log + token bucket. State now stores individual
         + call timestamps (variable-length) instead of a single counter.
         + Eliminates the boundary-doubling issue where callers could get
         + 2× throughput by timing calls across window edges. Also remove
         +d dead `_do` stub.                                             
      18 +**Test status:** 57 passing, 0 failing, 0 skipped              
      19 +**For next agent:** Hardener could add internal assertions and 
         +stress-test the sliding window with large sustained_rate values
         + (state grows linearly with allowed calls — potential memory co
         +ncern for very high rates). Race condition from Reviewer's note
         +s remains unaddressed (spec-level issue).                      

● Bash(rm
      /home/bruno/blackboxing/kata/rate-limiter/ex1-python/.blackbox/plan.md)
  ⎿  Done

● Refactorer pass complete

  Algorithm switched: Fixed window → Sliding window log + token bucket for
  burst.

  What changed in _impl.py:
  - State now stores individual call timestamps instead of a single counter
  - On each check, expired timestamps are pruned (t > now - window_seconds)
  - Sustained rate is enforced by counting timestamps in the window
  - Burst token bucket is unchanged (continuous refill)
  - retry_after now uses the oldest timestamp to compute when the next slot
  opens

  Result: 57/57 tests passing. The boundary-doubling issue is eliminated — a
  caller can no longer game window edges to get 2× throughput.

  Trade-off noted for next agent: State size grows linearly with sustained_rate
  (one timestamp per allowed call). For very high rates (e.g., 100k/window),
  this could be a memory concern. A Hardener pass could assess this.

✻ Baked for 2m 10s

❯ ok commit                                                                     

● Bash(cd /home/bruno/blackboxing && git log --oneline -5)
  ⎿  b83f6d9 Add rate-limiter implementation: 57/57 tests passing
     8e6ba7a Add spec phase conversation export
     cdb663f Add .gitignore and remove accidentally committed __pycache__
     … +3 lines (ctrl+o to expand)

● Bash(git add kata/rate-limiter/ex1-python/.blackbox/log.md
      kata/rate-limiter/ex1-python/rate_limiter/_impl.py && git commit -m "$(cat
       <<'EOF'
      Switch rate-limiter fro…)
  ⎿  [main 64ad42f] Switch rate-limiter from fixed-window to sliding window
      algorithm
      8 files changed, 404 insertions(+), 33 deletions(-)
     … +8 lines (ctrl+o to expand)

● Bash(git status)
  ⎿  On branch main
     Your branch is ahead of 'origin/main' by 2 commits.
       (use "git push" to publish your local commits)
     … +4 lines (ctrl+o to expand)

● Committed as 64ad42f. Note: git also picked up some skill files that were
  moved from skills/ to .claude/skills/ — looks like a prior restructuring that
  wasn't committed. There's also a staged README.md change left over — that's
  not from this session, so I left it alone.