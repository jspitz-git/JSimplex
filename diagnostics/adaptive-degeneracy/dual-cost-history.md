# Dual feasibility history across numerical cost repairs

Baseline: `92bee39`, including method-specific progress and ordered adaptive
pricing/perturbation trials. Functional change: `3cbf373`. Only adaptive history
changes in this experiment;
core numerical price repairs, pivot arithmetic, tolerances and precision stay
unchanged.

## Evidence and hypothesis

The prior 900-second medium dual report shows several different monitor
identities after the auxiliary handoff at iteration 35,395. At iterations
37,000, 38,000 and 39,000 their observation counts are only 4, 44 and 16.
Thus the final local progress classification does not belong to one continuous
phase history. Its previous low primal infeasibility has repeatedly been lost.

The full stagnation context hashes working costs as well as bounds, scaling and
algorithm. Numerical dual pivots can repair nonbasic costs in `update_duals!`,
or adjust an entering cost when Harris accepts a price within dual tolerance.
Either invalidates that context. A cost-only change starts a fresh monitor even
though its primal feasibility metric is still comparable. Frequent repairs
therefore keep reopening an initially productive window.

A small regression exercises the actual `update_duals!` repair at a fixed,
primal-infeasible point. Before the fix, 16 of its 36 assertions fail: history
never reaches a full window, stagnation is hidden and no bounded pricing trial
starts. Cost changes at a fixed point must not themselves count as improvement.

## Bounded change

The workspace stores a second context excluding costs. When only costs change
in dual simplex, preserve the monitor, observation count, window cadence, primal
anchors and primal normalization. Recompute cost normalization and rebase all
objective and dual-price anchors at the current point. No objective or price
comparison crosses different working cost vectors.

Bounds, scaling, algorithm, dimensions and tolerance changes still recreate the
monitor. Explicit phase resets discard it; explicit adaptive perturbation and
restoration still reset its history. Primal cost changes retain their prior
full-reset behavior. Disabled adaptive stagnation does no extra work. The
pricing-trial budget and the gate preventing simultaneous adaptive shifts are
unchanged.

This is not a new stagnation threshold, a convergence certificate, or a reason
to increase perturbation levels. It restores comparable history to the existing
adaptive controller. `stagnation_cost_rebase` makes the operation observable in
opt-in diagnostics.

## Regression checks

The first focused semantic run passes 3,799 assertions. The final run with normal
compilation passes 472 assertions including explicit perturbation reset, recovery above the
prior feasibility record, and precision-state coverage. These overlapping totals
are targeted evidence, not a whole-project suite.

The rebase event fires before the current observation: its primal endpoint and
observation count describe the preceding observation. Objective/dual anchors
already describe the new working cost vector. Do not interpret these event
fields as a completed window at the current iteration.

## Medium dual, 900-second isolated run

The input, numerical policy flags, Float64/PFI/native/80 configuration and retry
restriction match the previous coordinated run. The production digest is
`c72ebe2862aa66194cd238ab35d93a19dc56ae59e2f80948c9e9d3a447ff48bc`.
Objective and infeasibility observations match the baseline at each available
1,000-iteration checkpoint through iteration 35,000.

The first cost rebase occurs at iteration 35,082 in the auxiliary workspace.
The auxiliary handoff then occurs at 35,378, versus 35,395 previously; both
workspace pricing states reset correctly. There are 144 cost rebases in total:
one in the auxiliary monitor and 143 in a single original-workspace monitor.
The latter retains 3,253 observations through termination instead of repeatedly
restarting its feasibility history. The event validator confirms retained
normalization and nonincreasing best primal violation, allowing explicit resets.

| Observation | Previous coordinated run | Retained cost-repair history |
| --- | ---: | ---: |
| Status | TIME_LIMIT | TIME_LIMIT |
| Iterations | 39,163 | 38,631 |
| Refactorizations | 490 | 483 |
| Final working objective | -7.370366633641006e13 | -7.370356838040953e13 |
| Final primal infeasibility | 5.3816579571150465e9 | 1.757514526667896e10 |
| Final reported dual infeasibility | 0 | 0 |
| Automatic perturbations | 0 | 0 |

These are uncertified workspace observations from single time-limited runs,
not speed comparisons or certified original solutions. The worse final primal
infeasibility rules out claiming an overall medium improvement.

A new original-workspace pricing trial starts at 37,810 after two stalled
windows and returns at 38,066, exactly at its 256-observation cap. Its last two
windows satisfy the existing productive-return criterion, so its transition
reason is progress. The feasibility gain remains negative relative to the saved
record; objective gain alone authorizes that return. All 65 trials close, 64 in
the auxiliary workspace and one in the original workspace. There is no numerical
error, retry or precision boost, but still no optimum.

At the final window the monitor correctly reports negative feasibility gain
(about `-18739` in its normalized units), while a positive objective gain
(`4.96e-8`) exceeds the existing `5.68e-14` monitor threshold. Preserving history
therefore removes one masking mechanism but does not resolve the separate
question of how much progress should justify an adaptive productive state.
Changing that heuristic threshold would be another intervention, not a
numerical-tolerance repair; this experiment does not tune it.

## Primal rejection probe

`primal_rejection_work.jl` instruments the existing final candidate-rejection
point. It groups failures by their actual message, whether the candidate search
has already refreshed the basis, and active bound-perturbation level. A refreshed
search flag does not mean the individual rejection caused a refactorization.
The script also records the ten iterations with most rejections and asserts that
its total equals the solver diagnostic counter.

The hook does not alter arithmetic, candidate order, exclusions or retry limits.
It excludes diagnostic-free compilation warmup. The first fresh-search price
mismatch at each perturbation level also saves a local mathematical snapshot
and the observed FTRAN direction. These binaries are not committed.
The run produces no such price-mismatch samples, so no binary snapshot or
higher-precision price reference is generated. Like the prior isolated runs,
it retains `defer_weak=false`; the independent weak-pivot preference is not being
tested. Instrumentation overhead prevents treating iteration counts as speed
measurements.

The 300-second runtime primal run ends at `TIME_LIMIT` in Phase I after 7,724
iterations and 1,793 refactorizations. Its final uncertified auxiliary objective
is `600968.7127027455`, with zero reported primal infeasibility and dual
infeasibility about `8.24e12`. Every common preexisting 1,000-iteration checkpoint
through 7,000 matches the preceding coordinated run exactly in objective,
infeasibilities and pricing. Different stopping iteration/objective is not
attributed to a primal algorithm improvement.

The recorded 164,560 final candidate rejections split as follows:

| Final rejection reason | Before bound shift | After first bound shift | Total |
| --- | ---: | ---: | ---: |
| Pivot below absolute zero tolerance | 48 | 118,629 | 118,677 |
| Pivot transpose-row validation fails | 9,591 | 4,675 | 14,266 |
| Ratio test inconclusive | 70 | 31,547 | 31,617 |
| Direction price disagrees | 0 | 0 | 0 |
| All reasons | 9,709 | 154,851 | 164,560 |

Small pivots account for 72.1% of final rejections; inconclusive ratios account
for 19.2%, and pivot-row validation for 8.7%. All final small-pivot and pivot-row
rejections occur in a search that has already refreshed the basis. At most 297
candidates are rejected before one iteration completes. The only bound shift
occurs at 6,656, as in the previous coordinated run. Counts before and after it
span different trajectories and durations; this is not a controlled proof that
the shift caused the subsequent rejection workload.

The price-direction guard is not the dominant final-rejection source in this
capture. Initial disagreements resolved by a retry are outside this final-event
counter. Similarly, the pivot-row category includes multiple internal checks;
it does not identify which solve or validation condition failed. The ratio
category can include an unsafe bound snap or a nonfinite ratio, so it must not
be interpreted as one established numerical cause.

The next primal probe should capture the selected tiny pivot and its competing
ratio-test rows, especially after the bound shift. It should establish why
perturbation leaves so many unusable candidates before changing any selection
heuristic. The core numerical guards must remain in force. On dual medium, the
remaining policy question is a meaningful rate of progress, now measured over
retained history rather than repeatedly restarted windows.

## Reproduction

Run sequentially using the existing owned-process memory guard: 8 GiB virtual
memory cap, at least 6 GiB available RAM, at most 1 GiB swap, one Julia and one
BLAS thread. Preserve local `precompile_workload=false`.

```sh
julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/cost_history_semantics.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/cost_history_compiled.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl medium dual both 900 /tmp/medium-dual-cost-history
julia --project=. diagnostics/adaptive-degeneracy/reproduce/primal_rejection_work.jl runtime primal both 300 /tmp/runtime-primal-rejections
```

The real-model runner verifies the input digest, disables the original-LP retry,
and enables only stagnation, pricing, primal/dual perturbation and Phase-I
policy flags. The independent weak-pivot preference remains disabled. Auxiliary
dual perturbation restrictions continue to apply. Its final workspace values
are uncertified observations, not returned feasible solutions.
