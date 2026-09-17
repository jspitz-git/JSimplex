# LP Presolve Reductions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reversible equality aggregation, implied-bound reasoning, and dual fixings to JSimplex LP presolve.

**Architecture:** Each rule consumes a `LinearProblem{T}` and returns a `PresolveResult` or `PresolveFailure`. Batch independent removals per pass so large MPS models require one sparse matrix rebuild per pass. Postsolve steps restore both primal values and a candidate original-model basis; `cleanup_original` remains the final solve.

**Tech Stack:** Julia 1.13, `SparseArrays`, `Rational{BigInt}` for exact proof arithmetic, existing `JSimplex` tests.

**Spec:** `docs/superpowers/specs/2026-09-17-lp-presolve-reductions-design.md`

## Global Constraints

- Keep work in the `feature/presolve` worktree.
- Accept a transformed finite value only when `_represent_exact(T, value)` succeeds.
- Limit estimated fill-in for non-singleton substitutions to 10 NNZ per pivot.
- Preserve primal and basis restoration and original-model cleanup.

---

### Task 1: Batch singleton equality aggregation

**Files:** Create `src/presolve_aggregation.jl`; modify `src/JSimplex.jl` and `src/presolve.jl`; test `test/presolve_tests.jl`.

**Interfaces:** `aggregate_singleton_equalities(problem::LinearProblem{T})::PresolveResult{T}` and `SingletonEqualityStep <: AbstractPostsolveStep` with `postsolve_primal` and `restore_basis`.

- [ ] Write a failing test for `x + y = 5`, `0 ≤ x ≤ 3`, with nonzero cost on `x`: the reduced LP has one fewer column, the row becomes `2 ≤ y ≤ 5`, and the objective and original primal agree after `solve`.
- [ ] Run `julia --project=dev -e 'using Test,JSimplex,SparseArrays; include("test/presolve_tests.jl")'` with the worktree dev manifest and verify the new test fails for the missing transformation.
- [ ] Implement row-bound projection using exact rational arithmetic: `s = b - a*x`; accept only representable projected bounds and objective updates. Select at most one singleton pivot per equality row and rebuild `A[:, kept_columns]` once.
- [ ] Restore eliminated values using `x = (b-s)/a`. Map a basic reduced row slack to basic `x`; otherwise map its active row side to the corresponding original column bound. Verify basis index uniqueness.
- [ ] Run focused tests, the small LP regression suite, and commit the rule.

### Task 2: Implied bounds and bounded-fill equality substitution

**Files:** Modify `src/presolve_aggregation.jl` and `src/presolve.jl`; test `test/presolve_tests.jl`.

**Interfaces:** `aggregate_implied_free_equalities(problem::LinearProblem{T})::PresolveResult{T}` with `AggregationStep <: AbstractPostsolveStep`.

- [ ] Write a failing test with a three-term equality whose pivot has redundant finite bounds and appears in another row. Assert that one row and one column disappear, the updated coefficient and objective are exact, and `solve` restores the original optimum.
- [ ] Write a rejection test where another variable is unbounded, so the pivot's finite bound is not implied, and a test where substitution exceeds 10 estimated new NNZ.
- [ ] Run focused tests and verify the reduction test fails before implementation.
- [ ] Compute the exact activity range of the other equality terms and certify each finite pivot bound. Estimate fill-in from pivot row and column supports. Choose mutually independent pivots, apply their sparse row/objective updates in a batch, and skip candidates whose resulting stored values cannot be represented exactly.
- [ ] Restore eliminated pivots from saved equality coefficients in reverse order and mark them basic in the removed rows. Run focused and solver tests; commit.

### Task 3: Objective-aware dual fixings

**Files:** Create `src/presolve_dual.jl`; modify `src/JSimplex.jl` and `src/presolve.jl`; test `test/presolve_tests.jl`.

**Interfaces:** `reduce_dual_fixings(problem::LinearProblem{T})::PresolveResult{T}`.

- [ ] Write a failing test where a positive-cost minimization variable with a finite lower bound occurs only in upper rows with positive coefficients, and another test proving a ranged row blocks the fixing.
- [ ] Run focused tests and verify the first case is unchanged before implementation.
- [ ] Test the objective sign and every incident row side exactly; choose a finite improving bound, then reuse `_presolve_basic` style fixed-column elimination and `PresolveMap` restoration in a single batch.
- [ ] Test maximization, negative coefficients, zero cost, infinite chosen bounds, and original LP optimum after cleanup; commit.

### Task 4: Benchmark, integration, and documentation

**Files:** Modify `README.md`; test `test/presolve_tests.jl` only where a new behavior needs protection.

- [ ] Run the full test suite with `JULIA_DEPOT_PATH=/tmp/jsimplex-depot:/home/jspitz/.julia` and `JULIA_LOAD_PATH=<worktree>/dev:<worktree>:@stdlib`.
- [ ] Run the same read-plus-presolve probe on `runtime.mps` and `medium.mps`, recording rows, columns, NNZ, elapsed seconds, and max RSS. Compare with the previous 34,885/41,561/235,920 and 466,095/333,791/1,204,628 results.
- [ ] Run bounded end-to-end solves on small and medium fixtures to exercise postsolve and cleanup. Confirm model status, primal feasibility, and objective against a no-presolve reference.
- [ ] Document new rules, exact-representation skips, and fill-in limits in `README.md`; review `git diff --check`, commit, and report any gap to HiGHS without attributing interacting rule counts independently.
