# Complementary errors in native primal point recovery

This follows the [working-row experiments](working-row-values.md) from production
baseline `374178d` (unchanged numerical sources from `aa73565`). The scope is the
second experimental runtime failure at iteration 8,464, before accepting the
working-bound pivot change or adding another adaptive intervention.

**The new candidate is not retained in production.** It repairs the captured
pivot but fails the real model 125 iterations later. The complete patch and
negative result are preserved; production sources are restored to the baseline.
No merge or push was performed.

## One-pivot capture

The full `working-row-rounded.patch` reproduces `NUMERICAL_ERROR` at iteration
8,464, 1,791 refactorizations and auxiliary objective 601153.5014283091. The run
requests 300 seconds and stops on its own error after 175.106 seconds. It uses
Float64/PFI/native/80 with one Julia and one BLAS thread. Only Phase-I construction,
stagnation, pricing and primal/dual perturbation switches are enabled. The
existing diagnostic weak-pivot preference override remains disabled. Original-LP
retry is suppressed to preserve the first failure; no precision boost occurs.

The snapshot immediately before the pivot preserves the numerical workspace and
factorization but removes the observer. It supports a one-pivot replay, not an
exact restart of the outer adaptive driver. Replay reproduces the terminal
status, iteration, full primal vector, ordered basic indices and variable states.
The selected entering variable is 27,214, leaving row 2,729 (structural variable
32,271), step 0.11128243671532995 and pivot 4.8880389543255305.

Each captured candidate is checked against both stored bounds and the actual
working model. Native interval checks identify suspect rows; exact rational
arithmetic on the stored coefficients diagnoses the violations. Solver values
remain Float64, and the existing full certificate is not weakened.

| Candidate | Exact stored-bound failures | Actual model-row failures | Equation failures |
| --- | ---: | ---: | ---: |
| Before pivot | 0 | 0 | 0 |
| Reconstruction | 3 | 2 | 0 |
| Prediction | 0 | 1 | 0 |
| Existing midpoint of prediction and reconstruction | 0 | 1 | 0 |
| Residual correction | 3 | 1 | 0 |
| Inward-rounded correction | 0 | 1 | 0 |

Basic variables 2,297, 15,257 and row-activity variable 60,505 have stored bound
excess 1.0587911840678754e-22 beyond the 1e-7 tolerance before inward rounding.
The rounding helper completes successfully; independent replay produces the
exact captured rounded vector. The original capture script recorded the vector
without the helper's return value. Its preserved as-run copy and the inspector's
`ROUNDING_REPLAY completed=true same_point=true` record establish this distinction.
The current capture script also records the return value directly.

## Why the individual candidates fail

Row 23,590 fails under the prediction (exact bound excess 7.36244361778856e-22)
and the old midpoint (4.96381448883715e-21). Residual correction repairs this row.
Its stored activity is nonbasic, so changing that activity would change the
fixed nonbasic point rather than repair the equations.

Row 26,319 instead fails under residual correction and inward-rounded correction.
Its actual activity exceeds the lower-bound tolerance by 9.086564924864158e-23.
Only structural variable 9,126 among its contributors is basic, with value
1.5257939950526029e-6 and coefficient -1.179713648. The other contributing
variables are nonbasic zeroes. Rounding the separately stored basic activity
60,505 does not change actual `A*x` and therefore cannot repair this model row.
The prediction passes this row but fails row 23,590.

These are complementary constraint errors, not evidence of an impossible basis
point. A diagnostic one-ULP decrement of basic variable 9,126 in the rounded
point passes the complete certificate. This is an existence witness, not a
hardcoded coordinate-repair proposal.

## Joint native trial

The native midpoint of the prediction and the rounded correction passes the
complete certificate with all nonbasic values unchanged. In diagnostic blends,
prediction fractions 0 and 0.25 fail, 0.5 and 0.75 pass, and 1 fails. Applying the
existing residual correction to the prediction or the old midpoint fails; simply
repeating the same correction from either of those inputs is insufficient.

The new bounded candidate retains the old recovery order and adds exactly one
midpoint trial after a completed inward rounding fails full certification. It
copies the prediction before residual correction overwrites the aliased
`scratch.trial` rollback buffer. It changes only basic values, uses native
`a/2 + b/2`, adds no FTRAN, and requires the unchanged complete certificate.
Failure, cancellation and exceptions use the existing rollback. Acceptance emits
`primal_correction_balanced` in addition to the enclosing correction events,
so midpoint success is not attributed solely to one-ULP rounding.

The three-row regression represents the same complementary constraint errors and
uses the real `scratch.trial` alias. Before the new midpoint, 20 assertions pass
and 12 fail; with it, all initial 32 pass. Expanded tests cover all four managers,
actual model-row arithmetic, unchanged nonbasic values, unsuccessful midpoint,
cancellation and exceptions. The cancellation callback latches once triggered,
like a real time limit; an initial state-dependent callback incorrectly cleared
its request after rollback and was corrected in the test harness.

The final semantic runner passes 6,786 assertions with `--compile=min`; the
separate normal-compilation runner passes 798, including allocation checks.
These overlapping counts are not a full project-suite pass. The captured real
pivot passes seven checks: completion at the same iteration/basis/states,
unchanged nonbasic values, full certification and published basic solution.
An early replay script incorrectly queried diagnostics removed from the
snapshot; removing that unavailable event assertion leaves these numerical
checks intact. The unit regression checks the new event with diagnostics enabled.
Independent read-only review found no actionable issue in candidate ownership,
rollback or scope.

## Fresh model run rejects promotion

The candidate's fresh runtime run requests 300 seconds but terminates on its own
numerical error at iteration 8,589 after 174.4768 seconds. The memory/wall guard
does not stop it. Peak recorded RSS is about 2.01 GiB.

| Experimental source | Status | Iterations | Refactorizations | Seconds | Final auxiliary objective |
| --- | --- | ---: | ---: | ---: | ---: |
| Rounded correction, capture run | NUMERICAL_ERROR | 8,464 | 1,791 | 175.1065 | 601153.5014 |
| Added prediction/correction midpoint | NUMERICAL_ERROR | 8,589 | 1,793 | 174.4768 | 600673.5532 |

These are diagnostic timings, not a speed comparison. Both final objectives are
uncertified working-LP observations. The new midpoint is accepted exactly once.
Five rounded correction recoveries are accepted in total, compared with four in
the old capture. The count of rejected candidates remains 95,153. The additional
125 iterations do not establish reliable recovery or Phase-I convergence.

The final stored-bound infeasibility summary is approximately 3.0000000000000433e-7
across three variables; it sums violations and is not a maximum or a complete
model certificate. No pre-pivot candidates were captured at 8,589, so the exact
reason the recovery chain fails there is not established. Its failure must not be
attributed to the same pair of rows without further evidence.

The recorded adaptive lifecycle remains isolated and coordinated: nine pricing
trials close within their budget, seven return on measured progress and two
expire; no trial remains open. The single bound perturbation happens after a
pricing trial closes, never during it. This is scheduling evidence, not evidence
that pricing or perturbation resolves degeneracy.

The complete candidate source digest is
`7fa7e951556136200046d9102052931d31a9cf873d486dff3f115b936830891f`.
After restoring production, its digest is again
`c72ebe2862aa66194cd238ab35d93a19dc56ae59e2f80948c9e9d3a447ff48bc`.
No medium run is added after runtime has already rejected this candidate. None
of the three dependent experimental changes is promoted.

The evidence now argues against adding another fixed point trial as the next
production patch. A follow-up should examine a bounded joint feasibility
recovery with nonbasic values fixed, or prevent reconstructed points from landing
on incompatible tolerance edges. It needs a clearly stated acceptance/rollback
contract and validation on the captured failures before another full-model trial.
Which approach is sufficient remains open. Numerical recovery must stay separate
from adaptive scheduling and must not weaken the original-model certificate.

## Reproduction

Run only one numerical Julia process at a time, under the established owned-group
memory guard (8 GiB virtual limit, minimum 6 GiB available RAM, maximum 1 GiB
swap). Preserve `precompile_workload=false`. The following Julia commands are
payloads for that guard, not instructions to bypass it. Allow 540 seconds of
wall time for the 300-second model budget including compilation.

Use a separate checkout with production sources at `374178d` (or `aa73565`) and
copy these diagnostic files into it. The two full candidate patches below are
alternatives applied to the baseline; do not stack them.

1. Apply `reproduce/working-row-rounded.patch` with `git apply --unidiff-zero`.
   Capture and inspect the old failure:

   ```sh
   julia --project=. diagnostics/adaptive-degeneracy/reproduce/capture_coupled_point.jl runtime primal both 300 /tmp/runtime-coupled
   julia --project=. diagnostics/adaptive-degeneracy/reproduce/inspect_coupled_point.jl /tmp/runtime-coupled /tmp/runtime-coupled-inspection.toml
   julia --project=. diagnostics/adaptive-degeneracy/reproduce/probe_coupled_point.jl /tmp/runtime-coupled /tmp/runtime-coupled-probes.toml
   ```

2. Restore baseline production sources and apply `reproduce/working-row-coupled.patch`.
   Test the new candidate, replay the same pivot and measure a fresh driver run:

   ```sh
   julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/coupled_point_semantics.jl
   julia --project=. diagnostics/adaptive-degeneracy/reproduce/coupled_point_compiled.jl
   julia --project=. diagnostics/adaptive-degeneracy/reproduce/replay_coupled_candidate.jl /tmp/runtime-coupled
   julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl runtime primal both 300 /tmp/runtime-coupled-candidate
   ```

3. With baseline production restored, run `reproduce/validate_coupled_point.py`
   using Python. It checks source digests by rebuilding both candidate patches in
   temporary source copies, the complementary certificate failures, native trial
   outcomes, isolated policy and local artifact hashes when present.

Text records are in [results/coupled-point](results/coupled-point/). Binary snapshots,
full failure logs and as-run scripts remain local under
`.superpowers/adaptive-degeneracy/coupled-point/`; the committed manifest records
their hashes. The current capture adds helper-completion metadata relative to
its preserved as-run version. This does not change any numerical operation.
