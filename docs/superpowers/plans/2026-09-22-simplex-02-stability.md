# Simplex Pivot Stability and Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stabilize pivoting and recover the computation without unbounded repetition.

**Architecture:** BFRT proposes a transactional step, solves share refinement, and the driver owns the common budget. Recovery also changes the basis when a fresh LU alone is insufficient.

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

- F03: fixed/free/boxed variables, overflow, and exhausted candidates.
- F04–F06: a rejected pivot or callback must not change the live basis or budget.
- F07: simultaneous primal and dual infeasibility, restoration of original costs, postsolve, and deadline handling.

---

### F03: Stable Harris BFRT

**Files:** Create: src/dual_ratio.jl, test/dual_ratio_tests.jl. Modify: src/dual_simplex.jl, src/simplex.jl, src/JSimplex.jl, test/runtests.jl.
**Interfaces:** `DualPivotProposal{T}` contains `entering::Int`, `flips::Vector{Int}`, `dual_step::T`, and `outcome::Symbol` (`:pivot`, `:exhausted`, `:uncertain`). `propose_dual_step!(ws, row, orientation, violation, policy)` returns a proposal without changing costs, states, or the basis. `flips` is a borrowed buffer valid until the next proposal; F04 must not invalidate it with a nested call.

- [x] Test nearly identical breakpoints with substantially different pivots:

~~~julia
p = LinearProblem(JSimplex.sparse([1e-6 1.0]), [1e-6, 1.0 + 5e-8];
                  column_upper=[1e6, 2.0])
w = JSimplex.initialize_workspace(p, SolverOptions(verbose=false))
q = JSimplex.propose_dual_step!(w, [1e-6, 1.0, 0.0], 1.0, 0.5,
                               JSimplex.NumericalPolicy(Float64; stable_ratio=true))
@test q.entering == 2
@test isempty(q.flips)
~~~

- [x] Partition candidates into breakpoint tolerance intervals. Preserve the restrictions for non-boxed variables. Within an interval, try the strongest safe pivots; for each pivot, rederive the flips required for dual feasibility at that pivot's step. Do not automatically apply all earlier flips when the cost deviation is still within tolerance.
- [x] Validate the reduced costs of affected nonbasic variables and the remaining primal displacement after flips. Sort stably by breakpoint and index. The rational branch uses no floating-point relaxation and performs exact comparisons.
- [x] Test zero width, free variables, upper-bound-only variables, width overflow, a negative step within tolerance, and candidate exhaustion. Threshold rejection returns `:uncertain`, not proof of `INFEASIBLE`. Compare small rational cases with enumeration of feasible pivots and flips.
- [x] Run dual/benchmark tests, the full suite, F01 quick, and replay of the late failure. Commit: `feat: stabilize dual bound flipping ratio test`.

### F04: Pivot Selection Validation and Retry

**Files:** Modify: src/simplex_numerics.jl, src/dual_ratio.jl, src/dual_simplex.jl, src/primal_simplex.jl, src/simplex.jl. Create: test/pivot_retry_tests.jl.
**Interfaces:** `_pivot_agrees(row_pivot, column_pivot, error_bound)::Bool`; `validate_pivot!(ws, proposal, policy)::Symbol` returns `:accept`, `:reject_candidate`, or `:refresh`. The bounded rejection list belongs to a specific basis generation.

- [x] Test both disagreement and a small pivot with a sufficiently accurate estimate:

~~~julia
@test !JSimplex._pivot_agrees(1.0, 1.0001, 1e-10)
@test JSimplex._pivot_agrees(1e-9, 1e-9 + 1e-16, 1e-15)
@test !JSimplex._pivot_agrees(NaN, 1.0, 1e-10)
~~~

- [x] Combine the error estimate from solve residuals, dot-product accumulation, and, when uncertain, refinement. Require the correct sign and a pivot separated from the error; an absolute cutoff is not the sole gate. Test a low residual but disagreeing pivot for an ill-conditioned basis.
- [x] Dual tries at most `max_pivot_candidates` entering variables, then another violated row from a bounded set. Primal tries alternative leaving rows within the Harris limit, then another entering variable if needed. After rejection, recompute the proposal, including flips and orientation. Exhaustion enters recovery rather than returning a false status.
- [x] Stage changes in candidate buffers. Application after validation must not invoke a callback midway through mutation. If a factor update fails, restore the previous consistent state. A timeout before application or a logger exception must not count an unperformed step.
- [x] Test deliberately stale factors for all updates/backends, both algorithms, and callback exceptions; run the full suite and replay. Commit: `feat: retry numerically unsafe simplex pivots`.

### F05: Shared Refinement of Basis Solves

**Files:** Create: src/simplex_recovery.jl, test/simplex_refinement_tests.jl. Modify: src/dual_simplex.jl, src/primal_simplex.jl, src/simplex_numerics.jl, src/JSimplex.jl.
**Interfaces:** `refine_basis_solve!(destination, ws, rhs, policy, stop; transposed=false)::SolveQuality{T}`. The RHS must survive scratch operations. Migrate the current cost/row/direction repairs to shared refinement without losing their additional validation.

- [x] Reproduction: `B=[1 1; 1 1+2^-30]`, `rhs=B*[1,-1]`, `destination=[1.001,-1]`. Build a workspace with both structural columns in the basis and refactor. Call the new API; require `reliable` and an independent BigFloat residual within the declared bound. Repeat for `Bᵀ` and a deliberately stale factor.
- [x] Implement a bounded loop; here, solve means the existing forward/transpose solve of the current factorization:

~~~text
repeat at most policy.max_refinements:
    r := rhs - B * destination       # the transposed branch uses Bᵀ
    quality := solve_quality(...)
    if reliable: return quality
    correction := solve(r)
    if correction nonfinite or residual stagnates: return unreliable
    destination := destination + correction
~~~

- [x] Accumulate Float32 residuals through Float64, Float64 residuals through local BigFloat when needed, and BigFloat residuals at the actually stored precision. Expensive duplicate 256/512-bit verification does not belong in every ordinary step. Exact rationals do not use floating-point stagnation criteria.
- [x] Check the deadline for every refinement, conversion overflow, and a correction that makes no change after rounding. A rejected candidate must not corrupt active costs. The aggregate BFRT flip RHS is subject to the same check.
- [x] Add tests for destination/RHS aliasing, failed refinement, and callback exceptions; run targeted tests and the full suite, and collect a refinement-count census on quick. Commit: `feat: share iterative refinement across simplex methods`.

### F06: Basis Checkpoint and Repair

**Files:** Modify: src/simplex_recovery.jl, src/simplex.jl, src/dual_simplex.jl, src/primal_simplex.jl. Create: test/basis_recovery_tests.jl.
**Interfaces:** `BasisCheckpoint{T}` owns `basis::Basis`, costs, lower bounds, upper bounds, and a working-model identifier, without time or consumed iterations. `checkpoint_basis(ws)::BasisCheckpoint{T}`; `restore_checkpoint!(ws, checkpoint, stop)::Bool`; `repair_basis!(ws, policy, stop)::Bool`.

- [ ] Test independent ownership and preservation of consumed iterations:

~~~julia
p = LinearProblem(JSimplex.sparse([1.0;;]), [1.0]; row_lower=[1.0])
w = JSimplex.initialize_workspace(p, SolverOptions(verbose=false))
c = JSimplex.checkpoint_basis(w)
w.costs[1] = 7.0
@test c.costs[1] == 1.0
w.iterations = 9
@test JSimplex.restore_checkpoint!(w, c, () -> false)
@test w.iterations == 9
@test w.costs[1] == 1.0
~~~

- [ ] Keep at most two copies of the most recently verified bases; invalidate them when the model or phase changes. Restore rejects a different model/dimension, reconstructs the factor and values/costs/weights, and does not share mutable LU scratch. It counts the new factorization.
- [ ] Repair tries bounded exchanges in a private trial basis, replacing suspect slots with independent nonbasic slack or structural columns. Success requires nonsingularity and a high-quality solve; F07 subsequently restores feasibility. On failure, restore the checkpoint and record a bounded rejection of the pivot pair that triggered the failure.
- [ ] Test a singular trial basis, no suitable column, a deadline during factorization, and a callback exception. The original checkpoint must survive. Working perturbations are restored together with the basis.
- [ ] Run targeted tests, the full suite, and a replay where fresh LU is insufficient. Commit: `feat: recover simplex from verified basis checkpoints`.

### F07: Feasibility Recovery and Shared Driver

**Files:** Create: src/simplex_driver.jl, test/simplex_driver_tests.jl. Modify: src/JSimplex.jl, src/solver.jl, src/dual_simplex.jl, src/primal_simplex.jl, src/simplex_recovery.jl.
**Interfaces:** `SimplexRunBudget` owns the start/deadline, limit, and cumulative completed steps/refactors. `feasibility_mode(primal_ok::Bool, dual_ok::Bool)::Symbol`. `run_from_basis!(ws, budget, policy, stop)::DualRunResult{T}`. Move shared termination/result types before both algorithms.

- [ ] Pin the decision table with a test:

~~~julia
@test JSimplex.feasibility_mode(true, true) == :certify
@test JSimplex.feasibility_mode(true, false) == :primal
@test JSimplex.feasibility_mode(false, true) == :dual
@test JSimplex.feasibility_mode(false, false) == :phase_one
~~~

- [ ] After a verified recomputation, the driver uses the table. Simultaneous primal and dual infeasibility requires an auxiliary phase rather than directly starting a method whose invariant is violated. When restoring original costs, use the same path to run primal cleanup. Use the current Phase I implementations for now; F21 modernizes them.
- [ ] An explicit `algorithm` selects the initial method; handoff is enabled only by adaptive strategies. Allow at most two recovery rounds without progress; the same basis/states/phase must not switch primal↔dual indefinitely.
- [ ] Test infeasibility during cleanup, an algorithm change after basis repair, `iteration_limit=0`, a deadline in the auxiliary phase, and user exceptions. Rollback does not decrease completed steps; rejection does not increase them. The output passes original-model certification and postsolve.
- [ ] Run driver/retry/primal/dual/MOI tests and the full suite; run quick and difficult replays. Commit: `feat: add bounded simplex feasibility recovery`.
