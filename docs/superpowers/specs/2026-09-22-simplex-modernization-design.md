# Staged Modernization of Primal and Dual Simplex

Date: 2026-09-22. Baseline commit: d93cfd3.

## Objective and success criteria

Improve the numerical robustness and speed of both simplex algorithms through
algorithm changes. Cover stable pivoting, numerical recovery, incremental
primal updates, degeneracy, pricing, hypersparse computations, better initial
bases and phase I, adaptive precision, and iterative refinement of the LP.
Development takes place in a dedicated worktree, with a commit after each
verified feature. This specification and its plans describe proposed work;
they do not claim that features or speedups have already been delivered.

Evaluate correctness and certification first, then solved-instance coverage,
whole-solve time, and memory. Iteration counts and kernel costs explain the
results. Changes to the pivot path, iteration count, or bitwise solution are
acceptable. Degenerate optima need not produce the same primal vector.

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

## Current implementation and ordering rationale

dual_simplex.jl has a Harris branch and BFRT, but BFRT selects the first
breakpoint with sufficient movement capacity. Dual simplex has residual checks,
local Float64/BigFloat repairs, adaptive refactorization, and fixed triggers
after 256/1024 zero steps. Primal simplex has a Harris test but recomputes all
values and reduced costs after every step, with limited numerical recovery.
Factorizations use dense work arrays. Triangular updates maintain
B = B₀ R⁻¹ U Q⁻¹ over a base LU; Forrest–Tomlin is already implemented.

Establish reproducible measurements and shared numerical quality checks first.
Then remove redundant recomputation and introduce approximate pricing.
Hypersparse solves build on stable solve/factorization interfaces. Phase I
and higher precision reuse the resulting basis transfer and budget management.

## Architecture and ownership

Keep LinearProblem, Basis, SimplexWorkspace, and the existing backends.
Add focused modules incrementally. New internal types must be concrete and
parametric. Do not introduce Any, mutable global policy, or an unbounded
history into the pivot loop.

| Module | Responsibility | Feature |
| --- | --- | --- |
| simplex_diagnostics.jl | Counters and bounded event history | F01 |
| simplex_numerics.jl | Policy, residuals, solve and pivot quality | F02 |
| dual_ratio.jl | Propose a BFRT step without mutating the solver | F03 |
| simplex_recovery.jl | Corrections, checkpoints, restoration, basis repair | F05–F06 |
| simplex_driver.jl | Algorithm handoff, phases, shared budget | F07 |
| primal_updates.jl | Incremental values and reduced costs | F08–F09 |
| refactorization_policy.jl | Numerical and cost-based refactorization | F10 |
| simplex_stalling.jl, simplex_perturbation.jl | Stagnation and reversible working changes | F11–F13 |
| simplex_pricing.jl | Weights, adaptation, candidate pools | F14–F15 |
| indexed_vector.jl, sparse_pricing.jl | Sparse work vectors and row access to A | F16 |
| hypersparse_factorization.jl | Reachability through LU and updates | F17–F19 |
| simplex_start.jl, simplex_phase_one.jl | Crash bases and phase I | F20–F21 |
| simplex_precision.jl, lp_refinement.jl | State transfer, precision boosting, correction LPs | F22–F24 |

Include new files in type-definition order in JSimplex.jl. DualTermination
and DualRunResult also serve primal simplex; F07 moves their definitions
before both algorithms without renaming them. A method signature cannot
reference a type before that type is defined during include.

Pivot proposals are transactional: validate the candidate, flips, directions,
and reduced costs before changing the basis, states, costs, bounds, or counters.
Proposal scratch must not overwrite data retained by callers. Checkpoints own
copies of the basis and working perturbations. Restoration rebuilds the
factorization and never restores already consumed iterations or time.

## Numerical contracts

For Bz=b and Bᵀz=b, measure componentwise backward error
max_i |r_i| / (|B||z| + |b|)_i. A zero denominator contributes zero only
when its residual is zero; otherwise it indicates unbounded error. Also retain
absolute residuals and finiteness information. Overflow in a scale computation
must not cause an inaccurate result to pass.

Small backward error alone does not guarantee an accurate pivot in an
ill-conditioned system. Separately compare FTRAN and BTRAN pivots and their
distance from the error estimate. Feasibility tolerance, solve tolerance, and
pivot safety are distinct. Internal policy depends on type, scaling, and
factor quality without changing the user's requested tolerances.

BFRT must check dual feasibility after the entire step and the primal change
from the combined flip RHS. Trying more candidates may change the pivot path,
but must not bypass a valid step restriction or turn rejected pivots into an
infeasibility proof. Preserve the aggregate primal tolerance used by the
current primal Harris test; changing it is outside this project's incidental
scope.

Recovery proceeds from cheap recomputation/correction through refactorization
to basis repair or restoration, then algorithm handoff, increased precision,
or failure. Every stage has bounded attempts and checks the deadline.
Exceptions from user callbacks or loggers must not become numerical failures.

## Development policy and public interfaces

F02 adds simplex_strategy=:legacy|:adaptive, initially defaulting to :legacy.
The adaptive profile enables only implemented modules. Internal
NumericalPolicy{T} provides named stage switches for ablations, passed
explicitly to the internal driver. These switches are neither global nor all
public. Record the policy and source revision in benchmark results.

F14 adds explicit pricing=:auto. Existing explicit pricing modes retain their
meaning and documented safety fallbacks. F25 makes any final default changes
based on validation results.

Update SolverOptions conversions, _remaining_options, MOI construction,
reset/get/set, and documentation in the same commit as each public option.
Existing basis update/refactorization choices remain usable. Unsupported
sparse paths fall back to correct dense paths. Precision escalation has a
policy limit and preserves Solution{T}, with fresh validation after conversion.

## Test collections and oversized instances

The external collections are /home/jspitz/NetLib, /home/jspitz/MIPLib, and
/home/jspitz/mps. The [test corpus plan](../plans/2026-09-22-simplex-test-corpus.md)
defines discovery, compression handling, selection, stress limits, and the
exact locally observed names. Keep small repository fixtures for offline
regressions, but use the user's collections for algorithm evaluation.

F01 introduces quick, degenerate, ill_conditioned, phase_one, sparse_large,
holdout, and a separate opt-in stress suite. MIPLib contains .mps.gz files:
decompress with bounded streaming and solve the explicit LP relaxation.
Integer optimum metadata must never be used as the expected LP objective.

big.mps, largo.mps, and AnyMod.mps, locally named AnyMOD.mps, are excluded
from complete simplex solves regardless of suite aliases, compression, or
filename capitalization. They can exercise parsing, bounded memory behavior,
sparse data access, and bounded component probes on tractable extracted
subproblems. They must not trigger an unrestricted basis factorization or
solve, and do not contribute to solved-LP coverage or speed scores.

Use /home/jspitz/mps/runtime.mps, /home/jspitz/mps/medium.mps, and suitable
NetLib/MIPLib instances for bounded end-to-end tests. External data remain
read-only and are not committed. Record paths and SHA-256 hashes. Missing
data, limits, and failed solves must remain visible in reports. Capture late
failure replays and also run complete eligible solves with fixed limits.

## Validation and default selection

Each feature requires targeted regressions, the full production suite,
relevant MOI/development checks, local diff review, and a validation report.
Run timing benchmarks without concurrent tests, after warmup, with matched
BLAS settings and budgets. Use seven paired repetitions for small cases and
three for larger eligible cases. Compare both the immediate parent and
d93cfd3. Stress tests use their own limits and reporting categories.

A commit does not require speeding up every LP. A verified feature may remain
opt-in if it helps its target class and has correct fallbacks. Default rollout
requires no false certified status, no new loss of solvability in the solve
suite, and no unexplained median slowdown above 10% on jointly solved
instances or above 2× on an individual case. These are project decision
thresholds, not speedup promises. Repeat noisy measurements. Report robustness
and timeouts separately from the timing of jointly solved cases.

## Scope boundaries

All previously proposed directions are included, including crash bases and
phase I. A new interior-point solver, GPU support, parallel suboptimization,
a MIP solver, new presolve reductions, and wholesale scaling changes are
outside this plan.

## References

- [Huangfu and Hall: Parallelizing the dual revised simplex method](https://link.springer.com/article/10.1007/s12532-017-0130-5): BFRT, pricing, sparse solves, and updates.
- [Eifler, Nicolas-Thouvenin, and Gleixner: Combining Precision Boosting with LP Iterative Refinement](https://arxiv.org/abs/2311.08037): precision boosting versus LP refinement.
- diagnostics/dual_stability_report.md: local evidence and its limitations.
- diagnostics/runtime_audit_report.md: existing benchmark methodology.

Continue with the [implementation overview](../plans/2026-09-22-simplex-modernization.md).
