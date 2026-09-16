# Bound propagation implementation plan

**Goal:** Add exact multi-term row propagation and repeated presolve with
original-basis cleanup.

**Spec:** `docs/superpowers/specs/2026-09-17-bound-propagation-design.md`

**Status:** Implemented and verified with the full test suite.

1. Add focused failing tests for row-derived bounds, conflicts, redundant rows,
   inexact values, and a multi-round chain.
2. Implement a reversible propagation step and basis-state restoration.
3. Replace the one-shot pass sequence with a progress-driven round loop and a
   finite cap.
4. Update documentation and run focused, solver, MOI, and full tests.
