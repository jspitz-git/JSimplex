# Pilotnov: equal dual breakpoints and unscaled feasibility

## Reproduction and cause

On baseline `eb20fdd70b7a04f3a0209b46f62dda3aec7e922c`, `pilotnov.mps`
fails after 696 iterations in phase II with bounded pivot/basis recovery
exhausted. Settings: Float64, native MPS reader, relaxed integrality, dual,
legacy, steepest edge, PFI/Markowitz, interval 80, no partial pricing,
default presolve/scaling, one million iterations and a 300-second solve limit.
The input SHA-256 is
`0885e278d768e76f1819416f7844eeebf39f7c4e965f5c376b75191253d21f8d`.
This reproduces the remaining failure documented in
`../numerical-guard-repair/README.md`; it is not a postsolve transition failure.

The previous audit verified accepted pivot values and selected complete
FTRAN/basic-state reconstructions. It did not independently audit ratio choices.
The present capture records 812 ratio proposals/retries through the failure,
without changing the decisions. At early growth events, the legacy bound-flipping
ratio test (BFRT) chooses the lowest column index among exactly equal breakpoints.
That ordering can select a vastly weaker pivot than another equally eligible,
unbounded candidate at the same zero dual step.

Independent 256-bit solves confirm both candidates have exactly zero reduced
price in the captured working problem:

| Iteration | Selected pivot magnitude | Alternative magnitude | Selected next maximum basic value | Alternative next maximum |
| --- | ---: | ---: | ---: | ---: |
| 49 | 5.889e-5 | 6922.08 | 9.187e10 | 11400 |
| 121 | 1.947e-5 | 4.048e6 | 2.504e17 | 4.367e8 |

These are reconstructions from the same pre-pivot state and leaving bound;
both recorded decisions have no bound flips. They are not comparisons between
different solve trajectories. The reference recomputes dual prices as well as
FTRAN, BTRAN, basic values, and each candidate's primal step. Maximum differences
between stored and reference reduced prices are about 1.6e-15 and 4.4e-16.
Higher precision is used only for this independent diagnosis.

## Narrow core repair

Order finite breakpoints by their numerical value, then descending absolute
pivot coefficient, then original column index. Both the heap and its long
sorted tail use the same comparator. Numerically equal signed zeros belong to
the same group. Unequal breakpoints retain their exact priority; there is no
new tolerance, relative-pivot threshold, refactorization trigger, or precision
promotion.

This is a stability tie-break within the existing legacy ratio test. It does
not enable the optional `stable_ratio` strategy, which additionally groups
nearby breakpoints using a Harris tolerance window and validates alternative
flip combinations. Pricing selection and other adaptive policies are unchanged.

The signed-zero detail is essential. A first prototype preferred stronger
pivots but retained `isless(-0.0,+0.0)` ordering. It escaped the 696-iteration
failure but ended at the one-million-iteration limit, with the dual objective
near the reference value and an infeasible primal point. This is **not** a solved
LP or a successful repair. Its source and all reports remain in the raw local
folder. A portable test then demonstrated that a weak unbounded upper-state
candidate at `-0.0` defeats a stronger lower-state candidate at `+0.0` unless
both zeros compare numerically equal.

With both aspects repaired, PFI/Markowitz finishes `OPTIMAL` in 2217 iterations,
objective `-4497.276188218871`, with original primal feasibility. The independent
stored reference is `-4497.2761882188715` in
`../refactor-safety/results/models.toml` (which used different adaptive settings
and is not a baseline trajectory comparison). The largest completed primal
magnitude is about 1.18e9; the repair does not claim to prevent every large
intermediate value.

## Scaling-only restoration gap

With the tie repair alone, nine of ten public manager/backend combinations solve
pilotnov. HH/Markowitz instead reaches a certified working optimum at iteration
1849, then fails original feasibility. This is not a regression from a successful
baseline: unchanged master HH/Markowitz fails at iteration 850 with bounded
pivot recovery exhausted and a maximum intermediate primal magnitude of 6.96e33.

The restoration snapshot has an empty postsolve stack (`reduced=false`). Four
original row residuals exceed the unchanged tolerance 1e-7; the largest ordinary
row-product violation is 6.37e-7. The original certificate independently rejects
the point. Existing cleanup was conditional on presolve reductions and therefore
never repaired this scaled-only result.

A one-row example reproduces the gap for both primal and dual methods in
Float32 and Float64: minimize x subject to 2^24*x >= 1, x >= 0, with presolve
disabled. Zero passes the scaled row tolerance but violates the original row by
one. Before the second repair, the regression has 16 passes and 12 failures.

Use the existing original-model cleanup when an unreduced restored point fails
original feasibility, carrying the same basis, native precision, and remaining
budgets. Already-feasible unreduced points reuse the original certificate;
there is no additional certificate pass on that normal path. Reduced-model
cleanup and the one-time original retry retain their existing behavior.
HH/Markowitz then finishes OPTIMAL at iteration 1849 with objective
-4497.276188218872 and original feasibility. Reconstruction needs no additional
simplex pivots.

Budget and no-cleanup controls accompany the portable regression. An intentionally
infeasible ill-scaled control is rejected with NUMERICAL_ERROR, not a proven
INFEASIBLE certificate; this change makes no claim to resolve that separate
classification problem. The initial overly strict INFEASIBLE assertion and its
failed run are preserved, as is an earlier matrix harness parse failure before
any solve. Neither is counted as successful validation.

## Full pilotnov comparison on the combined repair

All ten dual/legacy/steepest-edge combinations at interval 80 finish OPTIMAL,
match the reference objective, and pass original primal feasibility. Every case
was rerun on the final combined source.

| Manager | Native iterations | Markowitz iterations |
| --- | ---: | ---: |
| PFI | 1609 | 2217 |
| Huangfu–Hall | 1717 | 1849 |
| Forrest–Tomlin | 1641 | 1778 |
| Suhl–Suhl | 1617 | 2274 |
| Bartels–Golub | 2257 | 2005 |

The 300-second per-solve limit is a failure bound, not a convergence result.
Reports separate compilation time; this diagnostic run is not a controlled
performance benchmark. The earlier tie-only matrix and its HH failure remain
preserved locally, with the HH report also retained in `results/`.

## Tests and reproducibility

`test/dual_bfrt_tie_tests.jl` first fails four strong-tie assertions on the
baseline (six other checks pass). After adding strength ordering, the dedicated
signed-zero test fails three assertions. The final tests cover Float32,
Float64, BigFloat, fixed/arbitrary-width rationals, both orientations, exact
nonzero ties, unequal-step priority, ownership, index ties, and rejected
candidates. Existing queue tests are updated to the new numerical-zero contract;
the independent allocating oracle and long-flip tests check heap/sorted-tail
consistency. The old two-column trajectory test now verifies the changed bound
flip and unchanged objective/feasibility explicitly.

The preliminary targeted ratio, allocation, and hypersparse pipeline run passed
1540 checks. Its first harness omitted the separately registered queue tests,
which passed 28 separate checks and are included in the final harness. On the
combined source, the normal-compilation targeted run passes 1568 checks, the
unscaled-restoration controls pass 54, and the wider semantic selection passes
15689 with `--compile=min`. These are selected regressions, not a complete
project-suite or CI result. Counts from separate preliminary/final runs overlap.

Scripts in `reproduce/`:

- `capture.jl INPUT MANAGER BACKEND OUTDIR`: diagnostic-only interception before
  publishing ratio decisions, using the shared capture driver. Saves generated
  source beside the snapshot directory. No live factorization pointers are saved.
- `summarize.jl DIRECTORY OUTPUT`: records the actual decision and ordinary
  Harris alternative. A Harris alternative alone is not proof that BFRT may skip
  earlier flips; the independent reference here deliberately selects two
  no-flip, equal-zero cases.
- `reference.jl DIRECTORY OUTPUT`: independent 256-bit audit of captured decisions
  50 and 122 (iterations 49 and 121).
- `pilotnov.jl OUTPUT [MANAGER BACKEND]`: full solve with original feasibility,
  reference objective, events and maximum completed primal magnitude.
- `matrix.jl OUTDIR COMPLETED_PFI_MARKOWITZ`: all ten public manager/backend
  combinations; `-` runs every case fresh. A path can reuse a completed same-source
  PFI/Markowitz report for an exploratory run.
- `targeted.jl`: focused ratio, queue, allocation and pipeline regressions.
- `restore-capture.jl OUTPUT_PREFIX`: records the original-space handoff for HH.
- `restore-audit.jl SNAPSHOT OUTPUT`: lists row/column violations and records the
  independent original-feasibility decision.
- `audit.py RAW_FINAL_DIRECTORY`: checks all expected completed jobs, source
  digests, ten pilotnov combinations, 100 unique external combinations, original
  feasibility, references and full dual runtime; retains compact evidence.

Raw attempts are preserved under `.superpowers/pilotnov-ratio-audit/` in the
isolated checkout. Julia 1.13.0 aarch64 runs sequentially with one Julia/BLAS
thread, precompile workload disabled, and the preserved 8 GiB VM / 6 GiB available
RAM / 1 GiB swap guard. No excluded large input is solved or factored.

## Final validation

The final aggregate source digest is
`74441f569459eb92e729206bd21f6ac526c1607b6a85bd3ef5c929185de0183f`.
The completed-result audit passes for all six sequential jobs:

- 54 unscaled-cleanup checks and 15689 semantic checks with `--compile=min`;
- 1568 ratio, queue, allocation and pipeline checks under normal compilation;
- ten fresh full pilotnov solves, all reference-matched and originally feasible;
- 100 unique external combinations / 305 assertions: afiro, adlittle, pk1,
  flugpl and fast0507, both simplex algorithms, both backends and all five managers;
- full runtime dual/legacy/HH/native/160: OPTIMAL in 54061 iterations,
  objective 51425691.76210454, with original primal feasibility. The timed solve
  block is 189.745 seconds; this is not a controlled speed comparison.

`results/validation.json` records commands, source and log digests, process exit
codes, wall times and peak RSS. Final logs and compact reports are retained in
`results/`; raw final runs are in `.superpowers/pilotnov-ratio-audit/final-verified/`.
All six final jobs exit zero with unchanged source. No resource or compilation
failure occurred in that final sequence. This is selected regression validation,
not a full project-suite or hosted CI result.
