# Incremental Primal and Refactorization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce the cost of primal steps and manage refactorization jointly for both algorithms.

**Architecture:** Separate value/cost updates from full recomputation. Drift checks, refactorization, and certification trigger full recomputations.

**Tech Stack:** Julia 1.13, Test, SparseArrays, the existing JSimplex backends, and MOI.

**Spec:** [specification](../specs/2026-09-22-simplex-modernization-design.md). Also read the [main plan](2026-09-22-simplex-modernization.md), especially the verification commands and commit protocol.

## Global Constraints

- Julia 1.13; preserve support for Float32, Float64, BigFloat, and rational types.
- Production dependencies remain LinearAlgebra, Logging, MathOptInterface, OrderedCollections, and SparseArrays; this plan adds no dependencies.
- Work in .worktrees/simplex-modernization on branch feature/simplex-modernization, starting from commit d93cfd3.
- Each verified feature gets its own commit, including tests, documentation, and a validation report.
- Preserve Solution{T}, existing statuses, explicit LP relaxation, and validation against the original model.
- Share the time limit and completed-step budget across phases, repairs, retries, algorithm switches, and precision increases.
- Do not weaken user tolerances or certification to make a benchmark pass.
- Exact rational arithmetic uses neither floating-point perturbations nor automatic conversion to floating-point arithmetic.
- Working perturbations must not modify the input model and must be removed before certification.
- Algorithm changes need not preserve bitwise intermediate results or the pivot path.
- Write all material intended for the remote repository in English, including documentation, code comments, reports, and commit messages.
- Use /home/jspitz/NetLib, /home/jspitz/MIPLib, and /home/jspitz/mps as the external test collections; solve MIPLib cases only as explicit LP relaxations.
- Exclude big.mps, largo.mps, and AnyMod.mps (stored locally as AnyMOD.mps) from complete simplex solves; use them only for explicitly bounded stress tests.

## Review Focus

- F08: upper bounds, free variables, and a flip without a basis change.
- F09: cost signs, cancellation, scratch aliasing, and long update chains.
- F10: extreme costs, absent measurements, and conservative fallback for stale factors.

---

### F08: Incremental Primal Bound Flip

**Files:** Create: src/primal_updates.jl, test/primal_update_tests.jl. Modify: src/primal_simplex.jl, src/simplex.jl, src/JSimplex.jl.
**Interfaces:** `apply_primal_flip!(ws, entering::Int, signed_change, tableau_column)::Nothing`. Consumes a validated direction from F04/F05 and produces updated `x_B` and `x_N` without changing the factor or costs.

- [x] The case `A=[1]`, `x∈[0,1]`, row upper bound `2`, and cost `-1` is a bound flip. The result has `x=1`, the same basis/factorization, and one completed step. Targeted test of the direct update:

~~~julia
p = LinearProblem(JSimplex.sparse([1.0;;]), [-1.0];
                  row_upper=[2.0], column_upper=[1.0])
w = JSimplex.initialize_workspace(p, SolverOptions(verbose=false))
before = copy(w.basis.basic_indices)
JSimplex.apply_primal_flip!(w, 1, 1.0, [-1.0])
@test w.primal ≈ [1.0, 1.0]
@test w.basis.basic_indices == before
@test w.basis.states[1] == JSimplex.AT_UPPER
~~~

- [x] Implement `x_B -= signed_change*d`, `x_entering += signed_change`, and set the state to the opposite bound. `signed_change` is the actual change in `x`, not an unsigned ratio-test step. Working cost/`c_B`/basis remain unchanged, so reduced costs are not recomputed.
- [x] Check the prediction before application; return control to F07 if the result is infinite. Enable the incremental path only with a reliable direction. A periodic audit compares values with an independent recomputation.
- [x] Test the opposite direction `AT_UPPER→AT_LOWER`, a fixed variable, zero, and a deadline before completion. The direct helper does not increment `iterations`; the driver increments it exactly once per completed step.
- [x] Run primal/recovery tests and the full suite; measure a flip without a hidden full recomputation and a complete boxed LP. Commit: `feat: update primal bound flips incrementally`.

Validation: [F08 report](../../../diagnostics/simplex-modernization/F08.md).
The boxed case saves 244 FTRANs and 244 BTRANs and runs 41.9% faster than the
F08 ablation; quick corpus timings do not establish a global speedup.

### F09: Incremental Primal Pivot and Sharing of Pricing Computations

**Files:** Modify: src/primal_updates.jl, src/primal_simplex.jl, src/simplex.jl, src/simplex_numerics.jl, test/primal_update_tests.jl.
**Interfaces:** `apply_primal_pivot!(ws, entering, leaving_row, signed_change, column, row; leaving_state, stop_requested=nothing)::Nothing`. New helper `update_reduced_costs!(costs, row, entering, leaving, pivot)::Nothing`; `row` is the unoriented row of `B⁻¹[A,-I]`. Prepare it before changing the factor. The result includes states and basis indices; the driver counts the completed step.

- [x] Test reduced costs against an explicit reference; `leaving=3`, `entering=1`:

~~~julia
r = [-2.0, 3.0, 0.0]
JSimplex.update_reduced_costs!(r, [-1.0, 2.0, 1.0], 1, 3, -1.0)
@test r == [0.0, -1.0, -2.0]
~~~

- [x] Implement the update in the old basis:

~~~text
alpha := reduced_cost[entering] / tableau_row[entering]
x_B := x_B - signed_change * tableau_column
x_entering := old_x_entering + signed_change
reduced_cost := reduced_cost - alpha * tableau_row
set entering reduced cost to zero; set leaving to its bound
apply validated factor update; exchange basis states/indices
~~~

- [x] The leaving variable's tableau column is the old unit basis column; other basic reduced costs remain zero. Share row/direction/pivot and the auxiliary row for steepest edge only when their meaning and lifetime match; do not overwrite live scratch storage. Remove the unconditional recomputation at the end of a primal iteration only in the adaptive branch.
- [x] Perform a full recomputation on refactorization, detected drift, a phase/cost/bound change, and before certification. Initially audit at least every 20 pivots; F10 adapts the interval. Use F07 if primal feasibility is lost.
- [x] On small exact LPs, test `A*x`, basic costs, state bounds, and an independent solve after every pivot; test long Float32/64 chains, alternating flip/pivot operations, steepest/devex/dantzig, and all updates/backends. Also verify Phase I and perturbed cleanup.
- [x] Run targeted tests and the full suite, plus a whole-solve primal benchmark against the parent and baseline; separately count saved solves. Commit: `feat: update primal pivots incrementally`.

Validation: [F09 report](../../../diagnostics/simplex-modernization/F09.md).
Incremental pivots reduce basis-solve counts; quick and difficult-model
measurements do not establish a global speedup. Adaptive remains opt-in.

### F10: Shared Numerical and Economic Refactorization

**Files:** Create: src/refactorization_policy.jl, test/refactorization_policy_tests.jl. Modify: src/simplex.jl, src/dual_simplex.jl, src/primal_simplex.jl, src/factorization.jl, src/triangular_factorization.jl, src/markowitz_factorization.jl.
**Interfaces:** `RefactorizationState` owns the update count, most recent quality, EMA costs of fresh/update solves, fresh LU cost, growth scale, and stored-element count. `refactor_reason(state, policy)::Symbol` returns `:none`, `:residual`, `:pivot_growth`, `:fill`, `:cost`, or `:limit`. `record_basis_cost!(state, operation::Symbol, seconds)::Nothing`. Tests do not read the wall clock; they supply synthetic costs.

- [ ] Test that a safety reason takes precedence over economic savings. Construct the state with named fields `nupdates=4`, `residual_bad=true`, `fresh_seconds=100.0`, `update_seconds=0.0`; expect `:residual`. Add a clean state with no samples that follows the user's initial interval.
- [ ] Implement reason selection with the following priority:

~~~text
if solve/pivot unreliable: refactor for numerical quality
elseif growth/fill exceeds guarded budget: refactor
elseif number of updates reaches hard ceiling: refactor
elseif estimated future update overhead > amortized fresh factorization cost:
    refactor for cost
else:
    retain factors
~~~

- [ ] Initialize from the existing `refactorization_interval`; preserve the fixed rational mode and legacy dual behavior. Require several high-quality cycles before adaptive growth, and reduce the interval after repeated failures. Do not evaluate economics from a single microsecond-scale solve duration.
- [ ] Sample fresh LU and solve costs at a bounded frequency; include the cost of checks, row/column solves, BFRT RHS work, and pricing. Use the update count when data is insufficient. Preserve a deterministic mode without timing adaptation for replay. F19 provides support and more accurate fill data.
- [ ] Tests inject short/expensive update chains, zero/NaN measurements, stagnation, repeated residual failures, and recovery. A small inexpensive LP must not extend the interval without bound.
- [ ] Run both simplex suites, basis tests, and the full suite; separately measure refactor time/counts for PFI and triangular updates on runtime and quick. Commit: `feat: schedule basis refactorization by quality and cost`.
