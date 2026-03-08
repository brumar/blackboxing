# Blackboxing

AI agents produce code faster than it can be reviewed. The usual answer is to review anyway. This repo tries something different: explore whether modules can be designed so that review adds little. Not with new ideas — software engineering has thought about modularity and contracts for decades. The question is which lessons matter most when AI writes the code.

This is an exploration, not a recommendation. The goal is to open the discussion.

The approach we're trying: humans own interfaces and tests, AI agents own implementation. Humans are "forbidden" to look at the implementation.

My two questions are:

- What quality attributes should modules exhibit in this new era of ai-assisted programming?
- How to structure the discipline of writing code around this new target? Both for Human and for AI agents

This repository is a modest attempt to answer those questions.

## Modularity First

Good software is modular software. Ousterhout's *A Philosophy of Software Design* argues for **deep modules**: a simple interface hiding complex behavior. The value of a module is the complexity it absorbs — the gap between what it does and what its caller needs to know.

Deep modules have narrow interfaces, explicit dependencies (everything injected, nothing hidden), and no leaking internals. These are old ideas. They're good ideas regardless of who writes the code.


## What Changes with AI

If AI agents write the implementation, the properties we want from modules arguably shift:

- **Testability** matters more — tests are how the human verifies work they don't read. Stubs, fakes, purity, no integration harness.
- **Replaceability** becomes practical — an agent that can rewrite a module from scratch in minutes makes the spec the valuable artifact, not the code.
- **Composability** is essential — swapping implementations must have zero ripple effects, because it will happen often.

The hypothesis is that a module with these properties narrows the gap between "what the tests verify" and "what code review would catch."

## How It's Organized

**Humans** co-design interfaces with the AI, write or co-write tests as specification, and don't read implementation code.

**AI agents** challenge the interface during design, implement to satisfy all tests, maintain internal quality, debug across boundaries, and adapt or rewrite when requirements change.

| Artifact | Owner | Human reads it? |
|---|---|---|
| Public API / types | Human + AI | Yes |
| Test suite | Human + AI | Yes |
| Module docs | Human + AI | Yes |
| Implementation code | AI | **No** |


## Workflow Suggestion

```
1. BRAINSTORM   Human + AI define the problem and module boundaries
2. INTERFACE    Co-design the public API
3. DOCUMENT     Write developer-facing docs — usage, examples, error semantics
4. CONTRACT     Write tests as specification
5. IMPLEMENT    AI implements (human doesn't look). Tests must pass
6. CHALLENGE    AI can suggest spec updates/improvements
7. IMPROVE      Agents improve code quality and internal documentation for few rounds.
8. EVOLVE       Requirements change → update spec → AI adapts or rewrites
```

Writing docs before tests is deliberate. My bet is that explaining how to use the module — instantiation, common patterns, error handling — forces you to experience the API as a consumer. Awkward docs mean an awkward interface. Fix the design here, before locking it in with tests.

If it feels like a mixture of TDD, SDD, Documentation Driven Design and vibe coding, that's warranted.

## Kata

The `kata/` folder contains attempts at following the blackboxing discipline on small problems. They serve as examples of what the workflow looks like in practice — not as a prescribed structure.

### Rate Limiter (Python)

A sliding-window rate limiter with burst support. Built using the two skills below over several sessions. The `conversations/` folder contains exported Claude Code sessions showing the human-AI collaboration from spec through implementation.

- **Problem**: [`kata/rate-limiter/PROBLEM.md`](kata/rate-limiter/PROBLEM.md)
- **Example of "solution"**: [`kata/rate-limiter/ex1-python/`](kata/rate-limiter/ex1-python/) — 76/76 tests passing. [Conversation files](kata/rate-limiter/ex1-python/conversations/) are maybe the most interesting documents.

## Skills

The repo includes two [Claude Code skills](https://docs.anthropic.com/en/docs/claude-code/skills) (in `.claude/skills/`) that attempt to encode the workflow above — `blackboxing-spec` for the spec phase and `blackboxing-agent` for autonomous implementation. They're early and rough. The methodology and the quality attributes that make it viable (testability, replaceability, composability) matter more than the tooling. The skills follow from the ideas, not the other way around.

## Blackboxing vs Spec-Driven Development

Spec-Driven Development (SDD) is the mainstream term for "write a specification, let AI generate code." Blackboxing shares the premise but makes different choices: specs are executable (tests, not documents), the goal is to eliminate code review (not just assist it), and the architecture is opinionated (deep modules, dependency injection, purity).

Full comparison: [SDD-COMPARISON.md](SDD-COMPARISON.md)
