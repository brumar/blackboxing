# Agent Roles

Each role represents an angle of improvement. One role per session. Do it well, hand off cleanly.

## Implementer

**Mission:** Make failing tests green.

- Focus on the simplest correct implementation first. Optimize later.
- If a test seems wrong or contradictory, do NOT modify it. Note the issue in the handoff log under "For human."
- Respect dependency injection — never import or instantiate dependencies that aren't injected through the interface.
- If the module has no implementation yet, scaffold the internal architecture before tackling individual tests. Create clean module structure with clear separation of concerns.

## Refactorer

**Mission:** Improve internal structure without changing behavior.

- All tests must stay green throughout. Run after every change.
- Targets: duplication, long functions (>30 lines), unclear naming, deep nesting, god files, tight internal coupling.
- Extract helpers, split files, rename for clarity, simplify control flow.
- Delete dead code and unused imports.
- Do NOT change the public interface or test behavior. If refactoring reveals a better interface, note it in the handoff log under "For human."

## Reviewer

**Mission:** Audit for correctness, security, and subtle bugs.

- Read the implementation with adversarial eyes. Look for:
  - Off-by-one errors, race conditions, resource leaks
  - Unhandled edge cases that tests don't cover (note these for the Hardener)
  - Security issues: injection, improper input handling, unsafe defaults
  - Incorrect error propagation or swallowed errors
  - Violations of the interface contract that happen to pass current tests
- For each finding, either fix it directly (if safe and tests stay green) or document it in the handoff log with recommended action and target role (Hardener, Implementer, or "For human").

## Hardener

**Mission:** Strengthen the module's resilience and performance.

- Add internal defensive measures: input validation at module boundaries, assertions on invariants, clear error messages.
- Profile performance if perf requirements exist. Identify hot paths and optimize.
- Look at error paths — are failures graceful? Do errors propagate correctly?
- If you discover untested edge cases, note them in the handoff log under "For human" — the human owns the test suite.
- Stress-test concurrency if the interface implies concurrent usage.

## Doc-gardener

**Mission:** Keep all markdown lean, accurate, and discoverable — including the repo's `CLAUDE.md`.

**Scope:** `.blackbox/log.md`, internal documentation files, and the repo-root `CLAUDE.md`.

### Internal docs (`.blackbox/`)
- Trim `log.md` to the last 10 entries if it's grown beyond 100 lines. Preserve only entries that still inform decisions.
- Remove stale information — anything that describes code that no longer exists.
- Delete resolved `challenge.md` files (check with the human first via handoff log).
- Verify every claim in docs against actual code. Delete or fix inaccuracies.

### Repo-root `CLAUDE.md`
- Create `CLAUDE.md` at the repo root if it doesn't exist. This is the "how to work here" file for all agents.
- Keep it updated with knowledge gained through agent experience:
  - **Build/test/lint commands** that actually work (verified by running them)
  - **Module inventory** — list of modules with their status (stable, in-progress, needs-spec-work)
  - **Conventions** — naming patterns, file structure, dependency patterns, language/framework versions
  - **Common pitfalls** — things that tripped up agents in previous sessions
- Do NOT duplicate spec content (interfaces, test descriptions) — reference module docs instead.
- Do NOT include implementation details — `CLAUDE.md` is visible to humans.

### General rules
- Flat structure: H2 + H3 max. No deeply nested sections.
- No section longer than 20 lines. Summarize or split.
- No duplication across files. If two files say the same thing, pick one source of truth and reference it.
- The goal: any agent should understand the module's state in <30 seconds of reading.
