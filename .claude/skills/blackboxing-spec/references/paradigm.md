# Blackboxing: A Human-AI Coding Paradigm

## Core Principle

**Humans own the interface. Agents own the implementation.**

The human never reads or modifies implementation code. The implementation is a black box —
tested, maintained, and debugged entirely by AI agents.

## Why

1. **Interfaces are the expensive decision.** A good interface makes implementations replaceable.
2. **Rewrites are cheap now.** Reimplementing from a spec costs minutes, not weeks.
3. **Humans are bad at implementation discipline.** Agents are more consistent and willing to start over.
4. **TDD already proved the direction.** Blackboxing is TDD taken to its logical conclusion.

## What the Human Does

- Co-designs interfaces with AI (AI pushes back on implementation leaks)
- Defines module boundaries (Deep Module philosophy)
- Writes/co-writes tests: property-based, unit, integration, performance
- Defines non-functional requirements
- **Never reads implementation code**

## What the AI Does

- Challenges the interface during co-design
- Implements the module to satisfy all tests
- Maintains internal quality (for other agents, not humans)
- Debugs failures across module boundaries
- Adapts or reimplements when requirements evolve

## Artifacts

| Artifact | Owner | Visible to Human |
|---|---|---|
| Module interface (public API, types) | Human + AI | Yes |
| Test suite (property, unit, perf) | Human + AI | Yes |
| Module documentation (DX) | Human + AI | Yes |
| Non-functional requirements | Human | Yes |
| Implementation code | AI | **No** |

## Design Principles

### Deep Modules (Ousterhout)
Simple interfaces, complex implementations. The human manages a small expressive surface;
the agent manages the deep internals.

### Tests as Specification
Every expectation must be encoded as a test or type constraint. No "checking by reading the code."

### Pure Modules and Dependency Injection
Every module declares dependencies explicitly through its interface. All external dependencies
are injected via constructor or method parameters. No globals, no ambient imports, no hidden state.
This ensures testability, composability, no hidden coupling, and true black-box behavior.

### No Peeking
The human never reads implementation. This forces formal expression of every requirement and
complete trust in the test suite.
