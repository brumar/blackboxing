# Blackboxing Repo

## How to Work Here

This repo follows the **Blackboxing paradigm**: humans own specs/tests, AI owns implementation.
See `BLACKBOXING.md` for the full manifesto.

## Modules

| Module | Path | Status |
|---|---|---|
| Rate Limiter (Python) | `kata/rate-limiter/ex1-python/` | Stable — 76/76 tests passing |

## Build & Test

### rate-limiter/ex1-python
```bash
cd kata/rate-limiter/ex1-python
.venv/bin/python -m pytest tests/ -v
```

## Conventions

- **Interface files** (`interface.py`) and **test files** belong to the human — agents never modify them.
- **Implementation files** (`_impl.py`, `defaults.py`) belong to agents.
- **`.blackbox/log.md`** is the agent handoff log — append-only, trim at 100 lines.
- Module docs live in `rate_limiter/DOCS.md` (human-owned).
- Use `FakeClock` + `MemoryStore` for deterministic tests — no sleeps.

## Known Open Items

- **Race condition**: `check()` does non-atomic read-compute-write. Needs Store protocol change (CAS/lock) to fix.
- **Memory growth**: Sliding window stores one timestamp per allowed call. Fine for typical rates, watch for very high `sustained_rate`.
