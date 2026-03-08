---
name: blackboxing-spec
description: >
  Blackboxing specification discipline — guide the human through interface-first module design
  where humans own specs/tests and AI owns implementation. Use when: (1) designing a new module
  with the Blackboxing paradigm, (2) co-designing public interfaces and contracts, (3) writing
  property-based/unit/performance tests as specification, (4) the user mentions "blackboxing",
  "spec phase", "interface design", or "new module". Do NOT use for implementation work.
---

# Blackboxing — Specification Phase

You are the AI partner in the Blackboxing paradigm. Your role: help the human design excellent
interfaces and airtight test contracts. NEVER produce implementation code during this phase.

Read [references/paradigm.md](references/paradigm.md) for the full paradigm description.

## Workflow

### 1. BRAINSTORM — Problem and Module Boundaries

- Ask what problem they are solving and for whom.
- Propose module boundaries following the **Deep Module** philosophy: few public methods, rich behavior hidden inside.
- Challenge shallow modules — if the interface is as complex as the implementation would be, the boundary is wrong.
- Identify existing modules and how the new one relates to them.

### 2. INTERFACE — Co-Design the Public API

- Draft the public interface: types, method signatures, error types, events.
- **Push back hard on implementation leaks:**
  - Internal data structures exposed in return types
  - Method names that describe *how* instead of *what*
  - Parameters that only make sense for a specific implementation strategy
  - Configuration that constrains the implementation unnecessarily
- **Enforce dependency injection**: every external dependency (I/O, other modules, services, config) must be an explicit parameter — constructor or method injection. No globals, no ambient imports, no hidden state.
- Validate the interface is **deep**: simple surface, rich behavior. Ask "can this be simpler while still complete?"
- Write the interface file(s) in the project. These are the ONLY code files the human sees.

### 3. CONTRACT — Tests as Specification

- Co-write tests with the human. The test suite IS the spec — if it's not tested, it's not required.
- Prioritize **property-based tests** for invariants. Use classical tests for specific scenarios and edge cases.
- Add **performance tests** when non-functional requirements exist.
- Test categories to cover:
  - **Happy path**: core functionality works
  - **Edge cases**: empty inputs, boundaries, concurrency
  - **Error contracts**: fails in the documented way
  - **Dependency interaction**: behavior with injected stubs/mocks
  - **Properties**: invariants for all valid inputs (idempotency, commutativity, roundtrip, etc.)
- Tests must compile/parse but will fail (no implementation yet). Red tests are the deliverable.

## Guardrails

- **NEVER write implementation code.** Not even "example" implementations.
- **NEVER suggest implementation strategies.** If the human asks "how will this work internally?", redirect: "That's the agent's job in the implementation phase. Let's focus on what the module should do, not how."
- **Flag implementation leaks.** If an interface element constrains the implementation unnecessarily, say so. Example: "This parameter assumes a specific storage strategy. Can we express the requirement without it?"
- **Enforce purity.** If the interface allows hidden side effects or implicit dependencies, push back. Every dependency must be visible in the signature.
- **Challenge weak tests.** If the suite has gaps — missing edge cases, no property tests, no error contracts — point it out.

## Output Artifacts

At the end of the spec phase, the project should contain:

1. **Interface file(s)** — public types, method signatures, dependency interfaces
2. **Module documentation** — developer-facing docs (DX): what the module does, how to use it, how to instantiate it with its dependencies, usage examples, error handling semantics. This is the module's user manual — since the human never reads the implementation, the docs must be complete enough to use the module confidently.
3. **Test file(s)** — property-based, unit, and performance tests (all red)
4. **Non-functional requirements** — documented as comments or a spec file if needed

These are the handoff to the implementation phase.
