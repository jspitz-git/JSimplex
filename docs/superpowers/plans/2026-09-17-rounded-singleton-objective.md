# Rounded Singleton Objective Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan inline in this session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate equality singleton columns blocked only by inexact floating objective updates.

**Architecture:** Add a narrowly scoped conversion helper in the singleton equality pass. Preserve exact rational accumulation, exactly transformed bounds and constant, and the existing postsolve map. Retry the original LP if cleanup cannot certify a restored basis.

**Tech Stack:** Julia 1.13, JSimplex internal presolve and simplex APIs, `Test`.

**Spec:** `docs/superpowers/specs/2026-09-17-rounded-singleton-objective-design.md`

## Global Constraints

- Round objective coefficients only in the singleton equality pass for `Float32` and `Float64`.
- Accept only finite relative error at most `8eps(T)` and reject nonzero underflow.
- Keep bounds, matrix values, and objective constants exactly representable.
- Validate final solutions on the original LP; do not solve `runtime.mps` or `medium.mps`.

---

### Task 1: Rounded singleton objective coefficient

**Files:** Modify `src/presolve_aggregation.jl`; test `test/presolve_tests.jl`.

**Interfaces:** `_singleton_objective_value(::Type{T}, ::ExactValue)` returns a
stored `T` or `nothing`; `aggregate_singleton_equalities` uses it only for
updated objective coefficients.

- [x] Add a test using equality `x + 0.1y = 1` with objective `0.3x + 0.01y`. Assert direct aggregation removes `x`, stores the rounded cost, restores a feasible primal and basis, and public solve returns the original optimum.
- [x] Run `julia --project=dev -e 'using Test, JSimplex, SparseArrays; include("test/presolve_tests.jl")'`; observe the new elimination assertion fail.
- [x] Implement `_singleton_objective_value` by first trying `_represent_exact`, then finite `Float32`/`Float64` conversion and exact-rational relative-error comparison. Use it at candidate validation and final storage; leave constant and bounds on `_represent_exact`.
- [x] Add and run tests that reject overflow and nonzero underflow and retain the exact rule for `BigFloat` and rational types.

### Task 2: Original-model recovery

**Files:** Modify `src/solver.jl`; test `test/solver_tests.jl` if a deterministic cleanup failure fixture can be constructed.

**Interfaces:** A numerical error returned by `cleanup_original` invokes
`_retry_original` using the already consumed iteration and time budget.

- [x] Add a test with a genuine singular restored basis that makes cleanup report `NUMERICAL_ERROR` and verify a retry solves the original LP.
- [x] After `cleanup_original`, call `_retry_original` for `NUMERICAL_ERROR`, then use the retry result as the final run. Keep TIME_LIMIT and ITERATION_LIMIT terminal.
- [x] Run the focused solver and presolve tests and inspect every failure.

### Task 3: Benchmark validation and completion

**Files:** Test `test/benchmark_regression_tests.jl`; update docs only if public behavior needs clarification.

**Interfaces:** Existing public `solve` API and logging remain unchanged.

- [x] Compare before/after presolved shapes and both simplex algorithms on checked-in NetLib `kb2`, `sc50a`, `adlittle` and MIPLib `stein9inf`, `flugpl`, `markshare_4_0`; also solve `afiro`, `beaconfd`, `scagr7`, and `bandm` in both algorithms.
- [x] Run `julia --project=dev test/runtests.jl` under a bounded timeout and inspect the suite summary.
- [x] Run `git diff --check`, review changed files, and commit the verified change in `feature/presolve`.
