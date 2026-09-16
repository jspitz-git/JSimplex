# Advanced LP Presolve Implementation Plan

> **For agentic workers:** Implement inline in the existing `feature/presolve` worktree. Use test-driven development for each task.

**Goal:** Add safe singleton, proportional, dependent-row, and free-doubleton reductions with reversible postsolve.

**Architecture:** Keep `presolve_problem` as orchestrator. Each rule takes a `LinearProblem{T}` and returns an updated problem plus a typed postsolve step, or `PresolveFailure`. Compose steps in chronological order and unwind them in reverse for primal and basis restoration.

**Tech Stack:** Julia 1.13, SparseArrays, Rational{BigInt}, Test.

**Spec:** `docs/superpowers/specs/2026-09-17-advanced-presolve-design.md`

## Global Constraints

- Preserve the public `Solution{T}` contract, input immutability, and original-model cleanup.
- Never remove a row from approximate rank evidence alone.
- Accept transformed floating data only when exactly representable.
- Bound general rational elimination work and leave undecided reductions unapplied.

---

### Task 1: Compose reversible steps

**Files:** Modify `src/presolve.jl`; extend `test/presolve_tests.jl`.

**Interfaces:** `restore_basis(::PresolveResult, ::Basis)` applies each step in reverse; `postsolve_primal` already uses this order.

- [x] Test sequential reductions and primal/basis restoration.
- [x] Generalize the restoration stack and add a pass composer.
- [x] Run focused tests.

### Task 2: Singleton rows and exact bound tightening

**Files:** Create `src/presolve_rows.jl`; modify `src/JSimplex.jl`, `src/presolve.jl`; extend `test/presolve_tests.jl`.

**Interfaces:** `reduce_singleton_rows(::LinearProblem{T})` returns a reduced problem and a basis-restorable row step or `PresolveFailure`.

- [x] Test signed coefficients, two-sided bounds, conflicts, and active-bound basis restoration.
- [x] Implement exact bound conversion and row removal.
- [x] Run focused tests.

### Task 3: Proportional and linearly dependent rows

**Files:** Create `src/presolve_dependencies.jl`; modify `src/presolve.jl`; extend `test/presolve_tests.jl`.

**Interfaces:** `reduce_parallel_rows(::LinearProblem{T})` and `reduce_dependent_rows(::LinearProblem{T})` return a reduced problem and row-removal step or `PresolveFailure`.

- [x] Test dominated and inconsistent parallel rows, redundant and necessary dependent rows, and inconsistency.
- [x] Implement exact normalized signatures, interval proofs, and bounded sparse rational elimination.
- [x] Run focused tests.

### Task 4: Free doubleton substitution

**Files:** Create `src/presolve_substitution.jl`; modify `src/presolve.jl`; extend `test/presolve_tests.jl`.

**Interfaces:** `substitute_free_doubleton(::LinearProblem{T})` returns a reduced problem and substitution step or unchanged problem.

- [x] Test objective and row updates, rejection of inexact candidates, and primal/basis reconstruction.
- [x] Implement exact candidate checks and reversible substitution.
- [x] Run focused tests.

### Task 5: Integrate, document, and verify

**Files:** Modify `src/presolve.jl`, `README.md`, and `src/solver.jl`; extend `test/presolve_tests.jl`.

- [x] Test composed passes and both public simplex algorithms.
- [x] Wire the pass order and finite repetition limit, and document limits.
- [x] Run the full suite and inspect the final diff.
