# Adaptive Precision and Final Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Add working-precision escalation, correction LPs, and an evidence-based choice of default strategy.

**Architecture:** A typed driver transfers bases between precision levels. Higher-precision factorization, more accurate residual evaluation, and correction LPs are separate mechanisms. Results retain the original problem's scalar type.

**Tech Stack:** Julia 1.13, Test, SparseArrays, existing JSimplex backends, and MOI.

**Spec:** [Specification](../specs/2026-09-22-simplex-modernization-design.md). Also read the [main plan](2026-09-22-simplex-modernization.md) for validation and commits and the [test corpus plan](2026-09-22-simplex-test-corpus.md) for external data and stress exclusions.

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

- F22: stored BigFloat precision, unbounded Bound values, and input immutability.
- F23: Float64 factorization errors, a shared deadline, and post-conversion certification.
- F24: incorrect correction formulations for ranged rows and false certificates.
- F25: holdout separation, timeouts, performance versus robustness, and stress exclusions.

---

### F22: Transfer the Basis and Working Model Across Precisions

**Files:** Create: src/simplex_precision.jl, test/simplex_precision_tests.jl. Modify: src/simplex_driver.jl, src/simplex_recovery.jl, src/options.jl, src/JSimplex.jl.
**Interfaces:** transfer_precision(ws, ::Type{S}, bits::Int, budget, policy) creates a new typed workspace. copy_working_values(::Type{S}, values; bits) preserves input values when increasing precision. The proposed BoostedRunResult{T} retains the original T and validated internal information rather than returning a public Solution{BigFloat}.

- [x] Test a stored value that cannot be represented in a 64-bit ambient context:

~~~julia
v = setprecision(BigFloat, 512) do
    [BigFloat(1) + BigFloat(2)^(-200)]
end
converted = setprecision(BigFloat, 64) do
    JSimplex.copy_working_values(BigFloat, v; bits=512)
end
@test converted == v
@test precision(only(converted)) >= 512
~~~

- [x] Transfer matrix coefficients, costs/constant, finite Bound values, basis/states, and the F12 journal. Dimensions and model hashes must match. Rebuild the factorization, values, and pricing; do not wrap a Float64 LU in a BigFloat object.
- [x] The new bits value must not reduce the highest stored input precision. Float32→Float64 transfers values exactly; Float64→BigFloat represents the stored binary model, not unknown original decimal data. Do not automatically convert the rational branch.
- [x] Perform conversions inside a local setprecision block and typed function barrier. Do not change F/M/R workspace types through incompatible field assignment or by introducing Any into the hot loop.
- [x] Test Bound(nothing), MAX objectives/constants, active perturbations, scaling/postsolve mappings, invalid bases, deadlines, and preserved cumulative counters. Run the full suite, BigFloat integrity tests, and options/MOI checks.
- [x] Commit: feat: transfer simplex state across working precisions.

### F23: Increase Factorization and Simplex Decision Precision

**Files:** Modify: src/simplex_precision.jl, src/simplex_driver.jl, src/simplex_recovery.jl, src/factorization.jl, src/markowitz_factorization.jl, src/solver.jl. Extend: test/simplex_precision_tests.jl.
**Interfaces:** next_working_precision(::Type{T}, current_bits, policy)::Union{Nothing,Int}; solve_with_precision_recovery(ws, budget, policy, stop)::DualRunResult{T_original}. Float32 first escalates to Float64, then BigFloat at 128/256/512 bits. Never reduce stored BigFloat input precision; return nothing when no higher level is allowed.

- [x] Test level selection and the precision ceiling:

~~~julia
policy = JSimplex.NumericalPolicy(Float64; max_precision_bits=512,
                                 precision_boosting=true)
@test JSimplex.next_working_precision(Float64, 53, policy) == 128
@test JSimplex.next_working_precision(BigFloat, 256, policy) == 512
@test isnothing(JSimplex.next_working_precision(BigFloat, 512, policy))
~~~

- [x] Activate after exhausting cheaper F05–F07 recovery or demonstrating that the current precision cannot provide a reliable solve. Start from the last valid basis. Higher precision applies to the actual factorization, reduced costs, ratio test, and updates, not only residual evaluation.
- [x] Initially use the existing dense/Markowitz backend for BigFloat, without silently converting back to Float64. Before a large dense fallback, check its memory estimate and use an available sparse backend or return explicit numerical failure instead of allocating without bounds. Include conversion/factorization costs in measurements.
- [x] Test an ill-conditioned basis replay where Float64 refinement stagnates but a higher-precision factor succeeds. Independently verify a small binary LP with Rational{BigInt}. Add a case that exceeds the allowed precision ceiling and a timeout during escalation.
- [x] Restore original costs/bounds before returning; convert x and necessary dual information to the original T and certify the original model again. Do not return OPTIMAL if the result represented in T misses the requested tolerances. Statistics include all steps at all precisions.
- [x] Run the full suite, numerical/MOI integrity checks, ill_conditioned cases, and holdout; compare Float64-only with boosting. Commit: feat: boost simplex working precision on numerical failure.

### F24: Iterative Refinement of the Entire LP

**Files:** Create: src/lp_refinement.jl, test/lp_refinement_tests.jl. Modify: src/simplex_driver.jl, src/simplex_precision.jl, src/solver.jl, src/JSimplex.jl.
**Interfaces:** CorrectionMap maps original working structural/activity variables into the correction LP. build_correction_problem(ws, residuals, primal_scale, dual_scale) returns the problem and map. refine_lp!(ws, budget, policy, stop)::DualRunResult{T}. Consumes F22/F23 and a verified basis.

- [x] Pin the formulation on an equality LP: the original constraint is x=1, current x=0.75, and primal_scale=4. Correction z must satisfy z=1 and reconstruct x+z/4=1. Add a ranged row and nonzero y; the test must expose omission of row activities from the correction objective.
- [x] Use the standard working form with row activities. Subtracting Aᵀy from the objective of a general inequality LP without this lifting is incorrect:

~~~text
v := [structural x; row activities]
M := [A, -I]; original working costs := [c; 0]
primal residual := -M*v
dual residual := costs - Mᵀ*y
choose finite positive power-of-two scales s_p, s_d
correction LP:
    minimize (s_d * dual residual)ᵀ z
    M*z = s_p * primal residual
    s_p*(lower-v) <= z <= s_p*(upper-v)
recover v_new := v + z/s_p
recover y_new := y + correction_equality_dual/s_d
~~~

- [x] Evaluate residuals and add corrections at sufficient precision. Unbounded limits remain unbounded; scaling must not underflow/overflow. Both scales are powers of two and adapt to measured residual reduction.
- [x] Warm-start through CorrectionMap. Additional activity/slack variables introduced by the correction solver must not survive as original columns. Validate reconstructed or completed bases through F06/F21. Mapping uncertainty must not produce an unverified checkpoint.
- [x] Accept a correction only when it improves relevant primal/dual/KKT errors without uncontrolled degradation elsewhere. Limit rounds to max_lp_refinements; on stagnation invoke F23 with the remaining budget. INFEASIBLE/UNBOUNDED on a correction LP alone does not establish that status for the original LP.
- [x] Test ranged/fixed/free bounds, nonzero row multipliers, objective constant/sense, an exactly solvable rational oracle, unrepresentable corrections, and deadlines. Distinguish linear-solve corrections, precision escalation, and LP rounds in diagnostics.
- [x] Run the full suite and ill_conditioned benchmarks with three ablations: linear refinement only, refinement plus boosting, and refinement plus boosting plus LP refinement. Commit: feat: refine LP solutions through scaled correction problems.

### F25: Integration Validation and Default Strategy

**Files:** Modify: src/options.jl, src/moi/optimizer.jl, src/moi/attributes.jl, README.md, test/options_tests.jl, test/benchmark_regression_tests.jl, test/moi/optimizer_tests.jl. Create: diagnostics/simplex-modernization/final_report.md and machine-readable benchmark results. Isolate and revalidate heuristic changes; do not hide them inside documentation work.

**Interfaces:** Preserve all public options and finish documented defaults. Auto pricing does not become implicit merely because simplex_strategy is adaptive; decide and test any pricing-default change separately within this task.

- [x] Review F01–F24 coverage against the main plan. Each feature has tests, a report, and a commit. Check MOI option reset/copy and README examples.
- [x] Run the full production suite and development JET/JuMP/GLPK checks. Runtime tests must not import the old checkout. Do not blindly update snapshots or raise allocation limits.
- [x] Run quick, degenerate, ill_conditioned, phase_one, sparse_large, and the frozen holdout using /home/jspitz/NetLib, /home/jspitz/MIPLib, and /home/jspitz/mps. Decompress .mps.gz safely and compare explicit LP relaxations. Run eligible runtime/medium/greenbea cases to completion or preset F01 limits; report unfinished solves explicitly.
- [x] Verify exclusion of big.mps, largo.mps, and AnyMod.mps/AnyMOD.mps from all complete solves, including explicit --file selection and aliases. Run only their opt-in bounded stress probes and report parsing, resource limits, and component outcomes separately from solved-LP coverage and speed scores.
- [x] Compare the parent, d93cfd3, legacy, and adaptive. Record statuses, original KKT/primal/dual errors, total/phase times, iterations, refactorization reasons, repair counts, precision, and memory. Do not tune on the holdout and then call that same run independent validation.
- [x] Apply the rollout rule:

~~~text
if any false certificate or new unexplained loss of solvability:
    keep affected feature opt-in; fix and revalidate
elseif timing crosses project regression thresholds:
    explain class-specific tradeoff; keep regressing policy opt-in
else:
    select verified defaults and document supported scope
~~~

- [x] Only after selecting a default, update its concrete test, such as SolverOptions().simplex_strategy == :adaptive, and the MOI equivalent. Add this expectation only if evidence supports the change. If legacy remains the default, use the truthful commit message docs: record adaptive simplex validation and retained defaults.
- [x] Rerun relevant options/MOI tests and the full suite after changing defaults, then check the diff. For a successful rollout, commit: feat: enable verified adaptive simplex defaults. The branch remains separate; merging/pushing is outside this task.

F25 outcome: retain legacy/steepest-edge defaults; no production/default change.
The unchanged F24 production gate is reused after source, dependency and all
production-test identity checks; the complete changed development and numerical
GLPK gates ran afresh. See the [final integration report](../../../diagnostics/simplex-modernization/final_report.md)
for adverse outcomes, supplemental timing limitations and bounded stress results.
