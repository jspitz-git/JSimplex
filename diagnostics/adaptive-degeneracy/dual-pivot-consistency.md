# Native dual pivot consistency before publication

Base: `0392fb2` on `codex/adaptive-degeneracy`.
This fixes the dual core failure exposed by the separate no-presolve
[pilotnov controls](expanded-dual-validation.md#separate-pilotnov-control-without-presolve-a-new-core-failure).
The presolve tolerance discrepancy is a separate issue and is not changed.

## Cause and bounded correction

The ordinary dual path could accept a FTRAN direction whose pivot contradicted
the BTRAN coefficient used by the ratio test, even in sign. Small backward
residuals do not exclude that disagreement in an ill-conditioned basis. Exact
rational diagnosis of the saved pilotnov matrices showed a nonsingular basis
before the accepted pivot and a singular basis afterwards.

Before publishing flips or the pivot, the ordinary floating-point path now
requires the two estimates to have the same sign and agree relatively, using
`sqrt(eps(T)) * max(abs(forward_pivot), abs(row_pivot))`. The existing
`_pivot_agrees` predicate also requires both estimates to be finite, nonzero and
separated from that agreement bound. This follows the native primal consistency
criterion; it does not increase a solver tolerance or globally raise the pivot
cutoff.

Only a failed comparison enters the existing bounded transactional retry.
Within a staged candidate, failure throws the existing refresh rejection rather
than recursively starting another retry. The current point and basis remain
unpublished while the retry refactorizes and tries candidates under the existing
budgets. Consistent steps retain the direct path. Exact arithmetic and the
existing optional checked-pivot path retain their own validation.

The correction introduces no pricing switch, perturbation, adaptive-policy
change or precision escalation. All solver arithmetic stays in the problem's
scalar type. The sole production change is 15 lines in `src/dual_simplex.jl`.

## Independent regression

A four-row matrix generated independently of pilotnov has a fifth column exactly
equal to its first basic column. The selected second-row pivot is therefore
exactly zero. Native forward/transpose roundoff previously admitted this
exchange and installed an exactly singular basis. Before the fix, the initial
fixture gave four passing and eight failing assertions; afterwards all twelve
passed. Exact rational LU is used only in the tests to verify nonsingularity,
not by the solver.

The expanded portable test covers all four basis managers and both legacy and
isolated adaptive settings. Additional cases check bounded exhaustion,
cancellation at rejection and after refresh, propagation of ordinary and
numerical observer exceptions, unchanged published state and no completion
events after cancellation. Accurate small pivots retain their values and avoid
refactorization/rejection in Float32, Float64, BigFloat and exact rationals.

The first expanded callback tests incorrectly expected the original exception
type directly. Existing diagnostics intentionally wrap observer exceptions in
`DiagnosticObserverFailure`; the expectations were corrected to that established
contract, including the wrapped exception type. No production change was made
for those test-expectation failures.

## Targeted verification and corrected test expectations

- Normal compilation: **851/851** focused native-dual checks, including all
  **216** new pivot-consistency assertions; testset time 3m51.6s.
- `--compile=min`: **14,592/14,592** expanded semantic checks, testset time
  2m19.4s. These include scalar types, both algorithms, phase transitions,
  postsolve, feasibility recovery, adaptive-policy isolation and callbacks.

The first expanded semantic run exposed two previously untested, obsolete
expectations that original-cost cleanup must clear `dual_devex_fallback`.
The identical test on the exact base `0392fb2` also gives 14 passes and these
same two failures. Original-cost cleanup now uses a primal step, where the dual
weight-reliability flag does not control pricing. Clearing the flag would lose
reliability history without repairing the dual weights. The test now observes
that the actual primal completion step uses the explicitly requested
steepest-edge pricing; solution, objective, iteration and cost-restoration
assertions remain unchanged. No production flag-reset behavior was added.

That first run also accidentally supplied the older artificial-exchange mod010
snapshot (324 iterations, one artificial), whereas the regression specifies
272 iterations and two artificials. Only its three fixture/count expectations
failed; recovery and all certificates passed. The final run uses the documented
`.superpowers/adaptive-degeneracy/native-prices/direction-price-removal-boundary`
prefix and passes all eight captured-state assertions. Both initial and final
logs are retained, so neither failure is hidden as a passing run.

An independent read-only review found no blocking issue in the production guard,
staging/retry behavior or the corrected cleanup-pricing test.

## Full pilotnov controls

Both original no-presolve failures now reach independently verified optima:

| Reader | Before | After | Refactorizations after | Rejected candidates |
| --- | --- | --- | ---: | ---: |
| Native | NUMERICAL_ERROR / 164 | OPTIMAL / 1806 | 28 | 8 |
| JuMP | NUMERICAL_ERROR / 142 | OPTIMAL / 2524 | 34 | 3 |

Both objectives are `-4497.276188218871`, matching the independent HiGHS reference.
Both reader-model and original unscaled primal certificates pass. All other
policy settings, input/reference hashes and process instrumentation match the
baseline controls. No original-LP retry occurs. This verifies successful
continuation and completion, not merely rejection of the captured false pivot.

## Paired dual corpus

All **76** existing dual configurations retain their previous outcome and exact
trajectory fields: status, iterations, refactorizations, phase sequence and
objective. Diagnostic-event and repair-coverage counts also match exactly.
There are **74 verified optima** and the two unchanged presolve rejections of
pilotnov, with no numerical errors, time limits, harness exceptions or
original-LP retry attempts. See the [paired dual table](results/dual-pivot-consistency/dual-comparison.md).

The 76 configurations combine the prior 28-case dual corpus and the disjoint
48-case expansion. They cover 33 underlying models, both readers, selected
permutations and all four basis managers on the previously selected cases.
The two no-presolve pilotnov controls above are separate from these 76 jobs.

## Paired primal corpus

All **28/28** existing primal configurations reach verified original optima.
Status, iterations, refactorizations, phase sequence, objective, diagnostic
counts and repair coverage match the prior stocfor2-point baseline exactly.
These jobs include both readers, explicit mod010 permutations and the selected
four-manager cases. They exercise phase transfers and original-model cleanup,
including paths that may enter the dual kernel. There are no original-LP retry
attempts. See the [paired primal table](results/dual-pivot-consistency/primal-comparison.md).

## Reproduction and verification scope

Use one numerical process, one Julia/BLAS thread, `precompile_workload=false`,
and the established memory guard (8 GiB virtual, at least 6 GiB available RAM,
at most 1 GiB swap). The real-model runs use normal compilation, Float64,
steepest-edge, native refactorization every 80 updates, 90 seconds per model and
1,000,000 iterations. Only the existing isolated stagnation, adaptive pricing,
primal/dual perturbation and Phase I switches are enabled. Weak-pivot preference
and original-LP retry remain disabled diagnostically.

- `test/dual_pivot_consistency_tests.jl`: independent portable regression.
- `reproduce/dual_pivot_focused.jl`: adjacent native dual guards under normal compilation.
- `reproduce/dual_original_costs_regression.jl`: extracts and runs the original-cost
  test from the loaded package tree, for identical baseline comparison.
- `reproduce/dual_pivot_semantics.jl MOD010_BOUNDARY_PREFIX OUTPUT_TOML`:
  expanded semantic chain under `--compile=min`.
- `reproduce/broad_without_presolve.jl INPUTS REFERENCES JOBS OUTPUT_PREFIX`:
  the two pilotnov controls, using the jobs from `results/dual-expanded`.
- `reproduce/broad_corpus.jl INPUTS REFERENCES JOBS OUTPUT_PREFIX`:
  retained `dual-jobs.toml` and `primal-jobs.toml` under `results/dual-pivot-consistency`.
- `reproduce/compare_dual_corpus.py BASE CANDIDATE OUTPUT --additional-base EXTRA`:
  combines disjoint baseline reports only after checking identical source,
  instrumentation and policy. It checks all paired results and certificates.
  Use `--algorithm primal` with the stocfor2-point baseline to compare the
  28 primal jobs; the default is dual.

A separate normal-compilation run of `test/runtests.jl` was stopped by the
300-second wall-time guard (exit 75), while LLVM was compiling the testset at
`test/simplex_strategy_separation_tests.jl:57`. The log contains no assertion
failure before termination, but no completed whole-suite summary either. This
is **not a full-project pass**. The focused normal-compilation run and the
expanded semantic run above completed successfully; no memory guard fired.

Runtime and medium are not rerun for this bounded core change, and their
convergence is not claimed. The usual presolve-enabled pilotnov rejection is
not fixed by bypassing presolve in a diagnostic control.
