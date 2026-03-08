# Blackboxing: A Human-AI Coding Paradigm

## Core Principle

**Humans own the interface. Agents own the implementation.**

The human never reads or modifies implementation code. The implementation is a black box — tested, maintained, and debugged entirely by AI agents. Human effort is concentrated where it matters most: defining *what* a module does, not *how*.

## Why

1. **Interfaces are the expensive decision.** A bad interface forces bad implementations and costly rewrites. A good interface makes implementations replaceable. In a world where AI can reimplement a module in minutes, the interface is the only artifact worth sustained human thought.

2. **Rewrites are cheap now.** When regenerating an implementation costs minutes instead of weeks, the economics of software change. Throwing away code and reimplementing from a spec becomes a routine operation, not a crisis.

3. **Humans are bad at implementation discipline.** We cut corners, accumulate tech debt, mix concerns. An agent given a clear spec and strong constraints can be more consistent, more thorough, and more willing to start over when needed.

4. **TDD already proved the direction.** Test-Driven Development showed that thinking interface-first produces better software. Blackboxing takes TDD to its logical conclusion: write the tests, write the types, and *never look at the green code*.

## The Paradigm

### What the Human Does

- **Co-designs interfaces** with the AI through dialogue. The AI pushes back if the human leaks implementation details into the interface.
- **Defines module boundaries** following the Deep Module philosophy (simple public interface, complex hidden implementation).
- **Writes or co-writes tests**: property-based tests, classical unit tests, integration tests, and performance benchmarks. These tests *are* the specification.
- **Defines non-functional requirements**: latency budgets, memory constraints, concurrency guarantees, error semantics.
- **Never reads implementation code.** This is the discipline. If a requirement isn't captured in a test or a type, it doesn't exist.

### What the AI Does

- **Challenges the interface** during co-design. Pushes back on leaky abstractions, suggests simpler contracts, identifies missing edge cases.
- **Implements the module** to satisfy all tests and constraints.
- **Maintains internal quality**: clean architecture, readability (for other agents), maintainability — even though no human will see it.
- **Debugs failures** across module boundaries. When something breaks, the AI investigates, proposes whether the bug is in the spec (test/interface) or the implementation, and fixes accordingly.
- **Adapts or reimplements** when requirements evolve. May modify the existing implementation or rewrite from scratch — the human doesn't care which, as long as the tests pass.

### The Artifacts

| Artifact | Owner | Visible to Human |
|---|---|---|
| Module interface (public API, types) | Human + AI | Yes |
| Test suite (property, unit, perf) | Human + AI | Yes |
| Module documentation (DX) | Human + AI | Yes |
| Non-functional requirements | Human | Yes |
| Implementation code | AI | **No** |
| Internal documentation / architecture | AI | No |

### The Workflow

```
1. BRAINSTORM   Human + AI define the problem and module boundaries
2. INTERFACE    Human + AI co-design the public API
                AI pushes back on implementation leaks
3. CONTRACT     Human + AI write tests (the specification)
                Property-based, classical, performance
4. IMPLEMENT    AI implements (human does not look)
5. VERIFY       Tests run. Green = done. Red = AI debugs or
                human refines the spec.
6. EVOLVE       Requirements change? Update the spec/tests.
                AI adapts or rewrites. Repeat from step 2 or 3.
```

## Design Principles

### Deep Modules (Ousterhout)

Modules should have **simple interfaces** and **complex implementations**. The interface should hide as much complexity as possible. This is the ideal shape for Blackboxing: the human manages a small, expressive surface; the agent manages the deep internals.

### Tests as Specification

If the human cannot see the implementation, every expectation must be encoded as a test or a type constraint. This forces extraordinary rigor in test design — which is a feature, not a bug. Vague requirements that would normally be "checked by reading the code" must be made explicit.

### Pure Modules and Dependency Injection

Every blackboxed module must be **pure** — it declares its dependencies explicitly through its interface, never reaching for them internally. All external dependencies (other modules, services, I/O, configuration) are **injected** through the constructor or method parameters.

This is non-negotiable because:
- **Testability**: Pure modules with injected dependencies are trivially testable. The human can write tests against the interface using stubs, mocks, or alternative implementations without knowing anything about the internals.
- **Composability**: Modules become pluggable building blocks. Swapping an implementation (or letting the AI rewrite one) has zero ripple effects as long as the interface contract holds.
- **No hidden coupling**: If a module secretly depends on a database, a file system, or a global, the "no peeking" rule breaks down — the human can't reason about the module's behavior from its interface alone. Dependency injection makes all coupling visible at the interface level.
- **Enforces the black box**: A pure module's behavior is fully determined by its interface inputs and injected dependencies. No hidden state, no ambient authority, no surprises.

### No Peeking

The "no peeking" rule is the most radical — and most important — constraint. It forces the human to:
- Express every requirement formally
- Trust the test suite completely
- Treat the module as a true black box

This feels uncomfortable at first. So did TDD.

## Tooling

Two Claude Code skills have been created to support this paradigm (alpha release):

- **`blackboxing-spec`** — guides the spec phase: brainstorming, interface co-design, test writing
- **`blackboxing-agent`** — autonomous agent that picks a role, improves module internals, challenges broken specs, and maintains `CLAUDE.md`

See `.claude/skills/` for the skill definitions.

## Why Modularity Matters in the Agentic Era

Strong modularity isn't just good design — it's a practical necessity for AI agents. Agents operate within a limited context window. A deep module with a small interface and a comprehensive test suite fits comfortably in that window. An agent can hold the entire module in its head, reason about it fully, and implement or refactor with confidence. Monoliths and tangled dependencies exceed what any agent can reliably work with. The smaller and more self-contained the unit of work, the better agents perform.

## The Bet

AI agents will continue to improve at implementation. The gap between "what the human specifies" and "what the agent delivers" will shrink. Investing human effort in specification — interfaces, tests, requirements — is the highest-leverage activity in this future. Blackboxing is a bet that this future is already here.
