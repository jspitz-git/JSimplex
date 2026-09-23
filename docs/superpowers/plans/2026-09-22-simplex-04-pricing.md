# Simplex Degeneracy and Pricing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce stagnation and the number or cost of pricing passes.

**Architecture:** A bounded window measures stagnation, perturbations own a reversible journal, and pricing respects both numerical quality and completion of a full pass.

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

- F11: near-zero steps, a large objective constant, and genuine slow progress.
- F12–F13: fixed/free bounds, unrepresentable perturbations, and restoration of the original LP.
- F14–F15: invalid weights, a missed best candidate, and false optimality.

---

### F11: Stagnation Detection

**Files:** Create: src/simplex_stalling.jl, test/simplex_stalling_tests.jl. Modify: src/simplex.jl, src/dual_simplex.jl, src/primal_simplex.jl, src/JSimplex.jl.
**Interfaces:** `StagnationMonitor{T}(window::Int)`; `observe_progress!(monitor; objective, primal_violation, dual_violation, primal_step, dual_step)::Symbol` returns `:progress`, `:watch`, or `:stalled`. Normalization uses working-LP scales and F02 tolerances, not a huge additive objective constant.

- [x] Test that nonzero steps alone are insufficient to rule out stagnation:

~~~julia
m = JSimplex.StagnationMonitor{Float64}(64)
state = :progress
for _ in 1:128
    state = JSimplex.observe_progress!(m; objective=1.0,
        primal_violation=1.0, dual_violation=0.0,
        primal_step=1e-30, dual_step=1e-30)
end
@test state == :stalled
~~~

- [x] Maintain a window of the minimum/start/end objective and infeasibilities, relative improvement, and the count of insignificant steps. A phase, cost, or scale change resets the window; restoring the same basis must not repeatedly postpone detection forever.
- [x] Add a monotonically improving sequence, oscillation, zero steps with improving primal violation, and an `objective_constant` shift of `1e20`. Test types and bounded memory; the exact branch uses exact zero comparisons.
- [x] Connect only diagnostics and the trigger for the existing fallback; add two-window hysteresis. F12–F14 consume the events without duplicating counters. Run the full suite and pk1 plus holdout degeneracy cases. Commit: `feat: detect scaled simplex stagnation`.

### F12: Adaptive Dual Cost Perturbation

**Files:** Create: src/simplex_perturbation.jl, test/simplex_perturbation_tests.jl. Modify: src/dual_simplex.jl, src/simplex.jl, src/simplex_driver.jl, src/JSimplex.jl.
**Interfaces:** `PerturbationJournal{T}` owns the original and active working costs/bounds, not a reference into the input model. `perturb_dual_costs!(ws, monitor, journal, policy)::Int`; `restore_perturbations!(ws, journal)::Nothing`. F13 extends the same journal to bounds.

- [ ] Test that restore returns the bit-identical original working costs and does not affect the model; do not use subtraction of the previous perturbation as the inverse:

~~~text
snapshot := copy(ws.problem.objective), copy(ws.costs)
perturb_dual_costs!(...)
assert number_of_shifts > 0 for stalled near-zero reduced costs
assert model objective equals snapshot bitwise
restore_perturbations!(...)
assert ws.costs equals snapshot bitwise
~~~

- [ ] In response to F11, apply a deterministic index-based shift of nonbasic costs toward the interior of the dual-feasible side. Derive the amplitude from the dual tolerance and local scale; cap it and check representability and resulting feasibility. Handle fixed and free variables explicitly; a free variable has no one-sided cone and must not receive an uncontrolled shift.
- [ ] After another stagnating window, increase the perturbation through only a bounded number of levels, with a cooldown after recovery. Do not propagate shifts into the original auxiliary dual phase without a new analysis of the mapping.
- [ ] Test upper/lower/free states, a very large cost, a subnormal value, and `Rational{BigInt}`, for which nothing is shifted. Restoring original costs proceeds through F07 for cleanup and original-model certification.
- [ ] Run the full suite, pk1, and independent degenerate cases, with an ablation comparison without and with perturbation. Commit: `feat: adapt dual cost perturbations to stagnation`.

### F13: Reversible Primal Bound Perturbation

**Files:** Modify: src/simplex_perturbation.jl, src/primal_simplex.jl, src/simplex_driver.jl, src/simplex.jl. Extend: test/simplex_perturbation_tests.jl.
**Interfaces:** `perturb_primal_bounds!(ws, monitor, journal, policy)::Int`; `restore_perturbations!` from F12 also restores bounds. The input `LinearProblem` and presolve metadata remain untouched.

- [ ] For a stalled basic variable at its lower bound, verify a small decrease in the working lower bound; at its upper bound, verify a small increase. After restore, both values and boundedness flags must match. Test a fixed variable, which the first version does not shift at all.
- [ ] Use a directional expansion that preserves current primal feasibility. The amplitude respects the local scale and primal tolerance, does not change the bound type, and must not introduce `lower>upper`. Skip free and fixed variables; preserve index-based determinism.
- [ ] After reaching a candidate optimum, remove perturbations and hand the original state to F07:

~~~text
restore original working bounds and costs from journal
recompute original primal/dual feasibility
run_from_basis! with same remaining budget
certify only the original problem
~~~

- [ ] Test a problem that is optimal at shifted bounds but still infeasible at the original bounds, a deadline during cleanup, postsolve, and the exact branch. Add a cycling/degenerate primal example and validate the complete resulting LP, not only the step count.
- [ ] Run the full suite and a degeneracy benchmark for both methods, with perturbation removal included in the timing. Commit: `feat: recover degenerate primal paths with bound perturbations`.

### F14: Automatic Pricing and Weight Recovery

**Files:** Create: src/simplex_pricing.jl, test/adaptive_pricing_tests.jl. Modify: src/options.jl, src/simplex.jl, src/primal_simplex.jl, src/dual_simplex.jl, src/moi/optimizer.jl, src/moi/attributes.jl, README.
**Interfaces:** `pricing=:auto` is a new public value. `PricingState` owns `active::Symbol`, weight quality, cooldown, and cost/progress statistics; `next_pricing!(state, monitor, policy)::Symbol`. `validate_edge_weight(stored, recomputed, policy)::Bool` accounts for the representation of primal weights (square roots in the current floating-point primal implementation).

- [ ] Test the public round trip and type conversion:

~~~julia
o = SolverOptions(pricing=:auto, simplex_strategy=:adaptive)
@test SolverOptions(Float32, o).pricing == :auto
@test SolverOptions(Float32, o).simplex_strategy == :adaptive
~~~

- [ ] Auto starts with steepest edge; unreliable weights switch to a fresh Devex reference framework. Under stagnation it may temporarily use Dantzig; switch back only after the cooldown and a recomputation or valid weight reset. Explicit pricing must not switch solely because of elapsed time; preserve documented safety fallbacks.
- [ ] For the selected candidate, compare the stored weight with an independent solve; do not create an additional solve for every candidate on every iteration. Reuse already computed FTRAN/BTRAN results from F09. Nonpositive/NaN weights trigger recovery rather than numerically meaningless division.
- [ ] Test artificially corrupted primal and dual weights, correct weights under stagnation, reset after refactorization and phase transition, and exact arithmetic. Verify that the hybrid path reaches the same certified objective as an independent reference.
- [ ] Run options/MOI tests, pricing tests, the full suite, and an ablation comparing pricing cost with iteration count. Commit: `feat: adapt simplex pricing using reliable edge weights`.

### F15: Partial Pricing and Candidate Pools

**Files:** Modify: src/simplex_pricing.jl, src/primal_simplex.jl, src/dual_simplex.jl, src/simplex.jl. Create: test/partial_pricing_tests.jl.
**Interfaces:** `CandidatePool` owns indices, the current basis/cost generation, and the cyclic scan position. `select_pricing_candidate!(ws, pool, policy; force_full=false)::Int`. Zero is allowed as a terminal signal only after a complete current scan.

- [ ] Create 129 columns, with no improving candidate in the first block of 64 and column 129 as the only improving column. Initial pool exhaustion must not terminate as `OPTIMAL`; a forced scan must find 129. After changing its cost, invalidate the cache and verify a new scan.
- [ ] Primal uses block passes and recomputes candidate scores; dual maintains a list of violated basic rows that is updated after primal values change. Candidates are a selection heuristic; costs and feasibility must not become stale.
- [ ] Implement the termination rule:

~~~text
candidate := best valid candidate in pool
if candidate absent or pool stale:
    scan remaining blocks; refresh pool
if no candidate after full current scan:
    recompute and certify via driver
else:
    validate current candidate before pivot
~~~

- [ ] Test a new best column outside the pool, removal of a basic/fixed variable, a cost change after perturbation, a basis change after restore, and deterministic tie breaks. A full scan is mandatory before returning `INFEASIBLE` and after pricing uncertainty.
- [ ] Run the full suite and ablations on wide and small LPs; record saved passes, not only the cost of a single selection. Commit: `feat: add partial simplex pricing with full-scan certification`.
