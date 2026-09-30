# Native point recovery after a degenerate bound snap

This investigation continues the `medium.mps` combined Phase-I experiment in
[phase-one-interactions.md](phase-one-interactions.md). Its baseline is `2cf7d17`.
The core correction is committed as `4e6777a`.
The input, PFI/native/80 configuration and isolated perturbation/pricing policy
are unchanged. Other adaptive mechanisms, including the separate weak-pivot
preference, remain disabled by the existing diagnostic harness.

## Captured failure and independent probe

The instrumented baseline stops at the same first failure: iteration 5443,
69 refactorizations, `NUMERICAL_ERROR: primal point could not be certified`.
A synchronous numerical-workspace snapshot before that pivot includes the
factor/update chain, current bounds, pricing state and scratch buffers.
Replaying one production pivot reproduces the entire failed primal vector and
basis exactly. It is not an outer-driver continuation: the observer is removed
and the progress context's reporting objective is rebuilt for the auxiliary LP.

The leaving structural variable (232704) is `-9e-7`, its working lower bound is
`-8e-7`, and the raw ratio step is `-1e-7`. Harris clips that step to zero. The
existing pre-snap feasibility check accepts the direction, but snapping the
leaving nonbasic value still changes the stored point. The entering variable is
row activity 534344 (row 295287), with direction -1 and pivot -1.

Before the pivot, the point passes the working-model and equation certificates.
After it:

- The predicted point remains model-feasible but fails row consistency.
- Reconstruction fails feasibility. One native correction is row-consistent,
  but the independently summed watched row activity is
  `1.0000004749454088e-7` against upper bound zero and tolerance `1e-7`.
- Native convex combinations of the predicted and reconstructed basic values
  with reconstruction weights 0.25, 0.5 and 0.75 pass both certificates. All
  nonbasic values remain fixed. Both endpoints fail.

The exact row sum is a diagnostic reference, not a higher-precision solve. This
is a conflict between small point errors after a tolerated negative-step snap,
not evidence of a singular pivot or a reason to change the pricing rule.

## Bounded core change

If reconstruction and the predicted point both fail, recovery now tries one
midpoint in the problem's Float32/Float64 type. It accepts the point only after
checking finiteness, every variable's working bounds, model feasibility and
consistency with stored row activities at the existing tolerance. The existing
certificate may refine ambiguous row sums exactly; neither solver values nor
solve precision are promoted by this change.

The basis, factorization, costs, bounds and nonbasic values are unchanged.
Rejected or cancelled trials restore the reconstructed values. A successful
trial synchronizes `row_solution` with the accepted point and invalidates its
support cache. The existing `primal_point_preserved` count includes the new
case; `primal_point_balanced` identifies the subset accepted by the midpoint.
If it fails, the existing single native correction is still available.

This is a numerical recovery at an already failed point, without a stagnation
trigger, new pricing choice, tolerance relaxation or perturbation escalation.
It does not claim that interpolation solves degeneracy. The reconstruction
fast path and valid prediction path still avoid the midpoint trial.

## Reproduction

Run one Julia process at a time with the established memory guard, one Julia
thread and one BLAS thread. Allow compilation/model reading in addition to each
300-second solve limit. Binary snapshots remain local and ignored under
`.superpowers/adaptive-degeneracy/medium-pivot/`; do not commit them.

On the baseline `2cf7d17`, use the capture and probe scripts from this revision:

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/capture_medium_pivot.jl medium primal both 300 /tmp/medium-pivot
julia --project=. diagnostics/adaptive-degeneracy/reproduce/replay_medium_pivot.jl /tmp/medium-pivot
```

On the fixed revision, using that same snapshot prefix:

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/verify_medium_pivot.jl /tmp/medium-pivot
julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/balanced_point_semantics.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/balanced_point_compiled.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl medium primal both 300 /tmp/medium-balanced
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl runtime primal both 300 /tmp/runtime-balanced
```

The first-failure harness disables the original-LP retry, so a later restart
cannot hide a failure. Reports contain input and production-source hashes,
policy switches, method hashes and lifecycle events. A final mutable workspace
is explicitly an uncertified observation, not a returned solution. The raw
capture records also distinguish stored activities from independently computed
row activities.

## Regression evidence

The small deterministic point-recovery regression failed 56 of 88 assertions
before the source change; all 128 initial assertions passed afterward. After
adding the accepted-midpoint diagnostic event, its final 144 assertions pass.
The failure/rollback cases include cancellation after certification, a throwing
caller, nonfinite values and an uncertifiable midpoint. The fixture checks the
actual bounds and equations independently rather than requiring a specific
interpolation formula.

The final semantic runner passes **2,536 checks** with `--compile=min` (144 new
checks and 2,392 existing point, perturbation, strategy, phase, precision,
regression and solver checks). The compiled runner passes **242 checks** (the
same 144 and 98 working-bound/allocation checks). Counts overlap; this is not a
full project-suite pass. The first real-pivot verification checks acceptance,
iteration 5443, unchanged basis/nonbasic values, point certification and cache
consistency. The packaged verifier was also rerun successfully against the
preserved local snapshot. Independent read-only review found no actionable issue.

While adding the diagnostic counter, the first extended test run caught its
missing event registration; registration was added and both final runners
passed. An initial throwaway replay script also needed its SHA import fixed.
Neither attempt is counted as passing evidence.

## Full medium run after the change

The isolated combined primal run reaches **6,778 iterations and 85
refactorizations in 300.044 seconds**, ending at `TIME_LIMIT` in Phase I with
no numerical failure. Original-LP retry is disabled. It accepts two midpoint
recoveries among 1,032 preserved points; there are 30 rejected pivots and three
bound-perturbation levels. No precision boost is recorded.

Four Dantzig trials return to steepest edge through the existing productive
window rule, with no open trial at termination. The first return occurs at
iteration 5568, after passing the former failure at 5443. The last recorded
auxiliary objective remains approximately `1.60016e8`; no feasible original
solution or Phase-I convergence is established.

This also exposes a limitation of the current adaptive progress signal. At
iteration 5568 it declares progress despite a slightly worsening auxiliary
objective, because dual infeasibility decreases. The first three pricing trials
start at the same iterations as perturbations (5440, 5760 and 6080). Consequently,
these returns verify lifecycle operation, not an independently measured benefit
of Dantzig. Shared intervention scheduling and phase-appropriate progress
criteria remain separate adaptive work; the numerical repair does not change
those policies.

## Runtime regression and remaining scope

With the same production-source hash and isolated policy, `runtime.mps` reaches
**4,539 iterations and 1,287 refactorizations in 300.001 seconds**, also ending
at `TIME_LIMIT` in Phase I without a numerical error or original-LP restart.
No midpoint is accepted (zero `primal_point_balanced` events). One predicted
point is preserved, and the existing numerical machinery records 18 corrections.
There are 304,345 rejected candidates, 310,144 pricing calls and 1,259
pivot-triggered refactorizations. Its one temporary Dantzig trial returns to
steepest edge. The final mutable observation has auxiliary objective about
`603523.38`; it is not a certified returned original solution.

This run checks compatibility, not a speed improvement. Iteration counts from
separate time-limited runs are not controlled timing measurements. Neither
large model completes Phase I in these checks, and medium dual behavior is not
retested here. The next adaptive investigation still needs to distinguish
useful phase progress from changes in dual infeasibility and to separate the
measured effects of perturbation and temporary pricing.

Logs, source hashes and reports are in [results/balanced-point](results/balanced-point/).
The pricing lifecycle validator passes on both fixed reports: four closed
trials on medium, one on runtime, and no open trial at termination. No other
adaptive policy switch is enabled and no precision boost is recorded. All
Julia runs were sequential under the existing owned-process memory guard.
