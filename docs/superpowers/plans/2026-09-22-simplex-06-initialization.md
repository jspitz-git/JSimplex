# Simplex Initialization and Phase One Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Shorten the search for a feasible basis and safely transfer the basis between phases.

**Architecture:** Crash initialization has a verified slack fallback. The auxiliary phase consumes only the remaining budget and returns an explicitly mapped original basis without artificial columns.

**Tech Stack:** Julia 1.13, Test, SparseArrays, existing JSimplex backends, and MOI.

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

- F20: numerically poor crash bases, fixed/free states, zero rows, and zero columns.
- F21: zero-valued basic artificials, nearly dependent rows, and false infeasibility.
- F21: removal of the working phase, original objective/bounds, and postsolve mapping.

---

### F20: Guarded Crash Basis

**Files:** Create: src/simplex_start.jl, test/simplex_start_tests.jl. Modify: src/simplex.jl, src/simplex_driver.jl, src/primal_simplex.jl, src/dual_simplex.jl, src/JSimplex.jl.
**Interfaces:** crash_basis(problem, options, policy, stop)::Basis returns a valid structure; initialize_from_basis(problem, basis, options; progress, policy) creates a workspace and verifies the solve. The existing initialize_workspace remains available for slack starts and legacy mode.

- [x] A diagonal-problem test must produce a primal-feasible structural basis:

~~~julia
p = LinearProblem(JSimplex.sparse([2.0 0.0; 0.0 3.0]), [1.0, 1.0];
                  row_lower=[2.0, 3.0])
policy = JSimplex.NumericalPolicy(Float64; crash=true)
b = JSimplex.crash_basis(p, SolverOptions(verbose=false), policy, () -> false)
@test Set(b.basic_indices) == Set([1, 2])
~~~

- [x] Start from the slack basis and deterministically select singleton and inexpensive sparse structural columns. Evaluate estimated primal-violation reduction, relative-pivot magnitude, and fill growth. Every accepted exchange must have a numerically safe pivot; do not claim independence from row structure alone.
- [x] Build a fresh LU, then validate solve quality and state. If the crash basis is worse or low-quality, return the slack basis. If time expires during the crash driver, return TIME_LIMIT; do not start a new full solve.
- [x] Determine the state of a nonbasic column from its available bound and the objective; leave free columns FREE_NONBASIC. Phase I and the auxiliary dual start use measured feasibility, not a promise made by the crash initializer.
- [x] Test nearly dependent columns, fixed/free/upper-only variables, empty models, and a case where the crash basis increases fill and is correctly rejected. Verify input-model invariance.
- [x] Run the full suite and the phase_one benchmark; report crash cost, saved Phase I iterations, and total time separately. Commit: feat: construct guarded simplex crash bases.

### F21: Phase I Modernization and Artificial Removal

**Files:** Create: src/simplex_phase_one.jl, test/simplex_phase_one_tests.jl. Modify: src/primal_simplex.jl, src/dual_simplex.jl, src/simplex_start.jl, src/simplex_driver.jl, src/solver.jl, src/JSimplex.jl.
**Interfaces:** PhaseOneMap owns the mapping of original structural/slack and artificial columns. run_phase_one!(ws, budget, policy, stop)::DualRunResult{T}; remove_artificials!(phase_ws, map, original_ws, policy, stop)::Bool. Consumes the F07 budget, F09 updates, and F20 start.

- [ ] Test the original model A=[1 1], row lower=1, cost=[1,2]. Phase I finds a feasible basis; after artificial removal there are only n+m states and the optimal objective=1:

~~~julia
p = LinearProblem(JSimplex.sparse([1.0 1.0]), [1.0, 2.0]; row_lower=[1.0])
r = solve(p; options=SolverOptions(algorithm=:primal,
          simplex_strategy=:adaptive, presolve=false, verbose=false))
@test r.status == OPTIMAL
@test r.objective_value ≈ 1.0
~~~

- [ ] Refactor the current artificial construction to accept an existing verified basis and add auxiliary columns only for rows that are actually violated. If extending that basis cannot be done safely, use the current verified slack construction.
- [ ] Retain Phase I that minimizes the sum of artificials as the reference strategy. The first modernization uses incremental primal, shared recovery, weights, and perturbations, rather than a new unverified auxiliary objective. The auxiliary dual phase adopts the shared driver and the bound/cost mapping; its recession proof remains intact.
- [ ] When a basic artificial has zero value, perform a safe degenerate pivot to an original structural/slack column before removing the artificial. Do not merely overwrite the index. At a nonzero artificial optimum, verify a Farkas proof against the original LP; uncertainty means recovery/NUMERICAL_ERROR.

~~~text
phase-I optimum → verify auxiliary optimality
if artificial sum > tolerance:
    verify original infeasibility certificate
else:
    remove zero artificials using validated basis exchanges
    restore original costs/bounds; recompute and check basis
    continue from this basis with remaining budget
~~~

- [ ] Test redundant and nearly dependent equalities, a zero-valued basic artificial, a small reduced cost that matters for a large violation, an infeasible LP, upper-only and free variables, a deadline during removal, and postsolve. No artificial costs, weights, or RowAccess indexing may remain after mapping.
- [ ] Run phase/recession/certification/retry tests, both simplex methods, MOI, and the full suite. Measure Phase I and the complete solve separately with crash on/off. Commit: feat: reuse recovered bases in simplex phase one.
