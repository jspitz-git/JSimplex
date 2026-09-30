# Isolated adaptive anti-degeneracy investigation

Base: `621380f35f1b5ea6e9352067b6fc39d578723595` (master).
The unrelated scan-performance experiments remain on
`codex/simplex-scan-performance`; none are included here.

## Respect the pricing policy during stagnation monitoring

The legacy zero-step Dantzig trigger has already been removed from the numerical
core. A separate adaptive trigger in `_observe_workspace_stagnation!` still
selected Dantzig when the dual monitor reported stagnation, even with
`adaptive_pricing=false`. Thus enabling only the monitor could change pricing,
confounding isolated anti-degeneracy experiments.

The trigger now also requires `adaptive_pricing`. With it disabled, monitoring
continues to advance and report stalled windows, but does not set the dual
Dantzig fallback. The existing positive case with adaptive pricing enabled is
unchanged. Numerical recovery of invalid edge weights remains independent;
this change does not reset an already active pricing fallback with stale weights.

The new regression observed three expected failures before the fix: effective
pricing became Dantzig, the fallback flag was set, and a fallback event was
emitted. Its three monitoring assertions already passed. All six assertions
pass after the added policy guard.

`reproduce/focused.jl` passes **2,764 checks** with Julia 1.13.0 aarch64,
`--compile=min`, one Julia thread and one BLAS thread. It covers numerical/strategy
separation, legacy dual policy, stagnation, both perturbation mechanisms and
adaptive pricing, including existing positive and disabled cases. The run uses
the existing owned-process memory guard and finishes within its 240-second
budget (testset time 68.4 seconds). See `results/policy-isolation.log`.

Reproduce from this checkout through the established wrapper:

```sh
python3 /home/jspitz/JSimplex.jl/.worktrees/primal-direction-prices/.superpowers/primal-prices/guard.py --seconds 240 \
  /home/jspitz/JSimplex.jl/.worktrees/primal-direction-prices/.superpowers/primal-prices/julia.sh \
  --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/focused.jl
```

Independent read-only review found no blocking issue. This is targeted semantic
verification, not a full-suite pass or a real-model convergence result. No
medium/runtime solve or anti-degeneracy intervention has been performed in this
change. Isolated experiments still need explicit policy settings for the other
adaptive mechanisms; `simplex_strategy=:adaptive` alone enables several defaults.
Phase-I perturbation eligibility and original-model cleanup are unchanged.

## Temporary adaptive pricing lifecycle

This change builds on `af7c68a`. The policy-isolation result above describes
that earlier commit; the direct switch inside the stagnation monitor is now
replaced by the shared pricing controller.

Automatic and explicit weighted pricing in both algorithms now use the same
bounded trial. A completed stalled window can select Dantzig only when both
`adaptive_stalling` and `adaptive_pricing` are enabled. The controller saves the
previous weighted rule. Two consecutive completed productive windows restore
that rule. An unsuccessful trial expires after four windows of observations;
either return starts a two-window cooldown. With the default window of 64,
the trial budget is 256 observations and the cooldown is 128. Duplicate monitor
reads do not count as progress, and replacing a monitor does not renew the
trial budget. Disabling adaptation ends an owned trial before another selection.

Candidate selection and weight maintenance are separate. Temporary Dantzig
pivots retain the previous rule's existing weight updates and validation in
the problem's scalar type. Refactorization preserves steepest-edge geometry;
checkpoint recovery rebuilds the appropriate maintained framework. Returning
to weighted pricing therefore does not treat stale weights or a vector of ones
as current steepest-edge weights. Maintaining weights costs more than the old
unweighted Dantzig path; this is a lifecycle correction, not a speed claim.
Explicitly requested Dantzig stays unweighted and fixed.

Phase changes end the trial and clear progress history. Dual auxiliary handoff
transfers weights, reference membership, cache validity and pricing state
together; the live monitor resets only after the candidate is accepted.
Primal artificial-column construction/removal transfers only the safe rule to
new weights with the new indexing. Numerical rejection of steepest-edge weights
ends a trial and establishes a fresh Devex reference independently of adaptive
pricing. That numerical fallback survives phase changes. A change of algorithm
alone does not introduce a Devex heuristic.

Diagnostics distinguish the selected rule (`pricing_dantzig`,
`pricing_steepest_edge`, `pricing_devex`) from the reason for returning
(`pricing_progress_return`, `pricing_trial_expired`, `pricing_phase_reset`).
Events from discarded candidates are not published as completed transitions.

### Regression evidence

The first lifecycle regressions failed 14 of 42 assertions before source
changes. A real dual pivot then independently exposed a stale weight of `1`
where the current inverse-row norm squared was `0.25`. Additional review
regressions reproduced disabled-policy selection (12 failures), an unwanted
algorithm-change Devex (one), lost numerical Devex during artificial removal
(one), and lost numerical Devex at phase entry (two).

After the fixes:

- The focused semantic runner passes **3,209 checks** with `--compile=min`.
- The expanded lifecycle suite passes **441 checks** with normal compilation,
  including real primal/dual pivots, independent steepest-edge norms, comparison
  with fixed Devex on all four basis managers, phase transitions, cancellation,
  monitor replacement, and disabled policies.
- The additional phase, recovery, atomic-pivot and partial-pricing runner passes
  **1,818 checks** with `--compile=min`.

These suites overlap; their counts are not a count of distinct tests. This is
not a full project-suite pass. The first additional-runner attempt had a
test-helper include-order error; the corrected runner passed. Independent
read-only review found the phase/policy integration omissions described above;
all were reproduced and fixed before the model experiments.

### Isolated model experiment

`reproduce/models.jl` verifies each input SHA-256 and runs Float64 PFI, native
refactorization, interval 80, steepest-edge, relaxed integrality and a shared
1,000,000-iteration budget. Only the stagnation monitor and adaptive pricing
policy are enabled. All other numerical-policy switches are explicitly checked
as false; the common native numerical safeguards remain active.

The production `adaptive_pricing` flag also controls a separate primal
weak-pivot preference. For these experiments only, the runner loads the exact
current `_legacy_primal_iteration!` body with its preference initializer replaced
by `defer_weak = false`. A small independent pivot regression verifies the
override before solving a model. The numerical checks and bounded rejection
and retry code are unchanged. The report records both the production source
digest and the isolated method digest. This is an explicitly instrumented
diagnostic configuration, not a benchmark of the public adaptive preset.

The runs use Julia 1.13.0 aarch64, one Julia thread and one BLAS thread. The
existing guard caps the owned process at 8 GiB virtual memory and stops its
process group below 6 GiB available RAM or above 1 GiB swap use. An afiro solve
warms common paths; rare-path compilation and diagnostic recording still affect
timings. Each process runs one model. A time limit never certifies convergence.

Reproduce from this worktree through the existing guarded wrapper:

```sh
julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/focused.jl
julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/regressions.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/models.jl runtime primal 300 runtime-primal.toml
julia --project=. diagnostics/adaptive-degeneracy/reproduce/models.jl medium primal 900 medium-primal.toml
julia --project=. diagnostics/adaptive-degeneracy/reproduce/models.jl medium dual 900 medium-dual.toml
```

The focused runner additionally includes the final 80 lifecycle assertions
that were added for the normal-compilation run; its earlier recorded count
predates those additions. The lifecycle suite itself can be run with `using Test,
JSimplex; include("test/adaptive_pricing_lifecycle_tests.jl")`.

### Runtime primal result

The isolated 300-second runtime primal run ends with `TIME_LIMIT` after 11,551
iterations and 5,275 refactorizations. It stays in phase I. There are 21 Dantzig
trials: eight productive returns, 12 expired trials and one still active when
the solve limit stops the run. Completed trials consume 128 or 256 observations,
within the configured maximum. The last trace point (iteration 11,328, 180.36
seconds) has working objective 602,968.8953; it is not a final original-model
objective or feasibility certificate. The initial productive episodes change
the trajectory, but later trials still stagnate. This does not solve runtime.
See [the structured result](results/runtime-primal-lifecycle.toml).

### Medium dual result

The isolated 900-second medium dual run ends with `TIME_LIMIT` after 38,724
iterations and 484 refactorizations. It completes the auxiliary phase. All 64
Dantzig trials return after productive windows; none expire. At iteration
35,395 (824.91 seconds), the accepted original-bound handoff records steepest
edge, `temporary=false` and zero pricing observations. No trial is carried into
phase II. Its later recorded points stay on steepest edge.

The early flat objective accompanies decreasing primal infeasibility and does
not trigger Dantzig. Later in phase I, repeated stalled weighted intervals
alternate with productive Dantzig trials and returns. At the phase boundary the
working objective and primal infeasibility still jump to approximately
-7.37362e13 and 1.28412e9, respectively; dual infeasibility is zero. The last
recorded phase-II point at iteration 38,000 has objective -7.37037e13 and primal
infeasibility 5.12854e9. These working metrics do not certify an original-model
solution, and the run does not reach optimality. See
[the structured result](results/medium-dual-lifecycle.toml).

### Medium primal result

The isolated 900-second medium primal run ends with `TIME_LIMIT` after 26,893
iterations and 337 refactorizations, still in phase I. Its 35 Dantzig trials
include two productive returns and 33 expirations. Completed trial lengths are
128, 192 or 256 observations. The last recorded working objective is 148,923,900
at iteration 26,000 (872.65 seconds), down from the initial 346,750,000. Long
plateaus remain between occasional improvements. Original-model optimality is
not established. See [the structured result](results/medium-primal-lifecycle.toml).

| Model | Algorithm | Limit (s) | Iterations | Refactorizations | Productive returns | Expired trials | Status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| runtime | primal | 300 | 11,551 | 5,275 | 8 | 12 | TIME_LIMIT |
| medium | dual | 900 | 38,724 | 484 | 64 | 0 | TIME_LIMIT |
| medium | primal | 900 | 26,893 | 337 | 2 | 33 | TIME_LIMIT |

All three reports have production digest
`ab4555ffebf4a641216bc3676e2bf0ade9a5f8d1479e3761ab3654dd2d6cc3c1`.
A post-run check of every recorded entry and return confirms at most 256
observations per completed trial, exactly 256 for expiry, restoration of the
saved rule, and at least 128 observations before a subsequent trial. Phase
resets start with zero observations and no active trial. The final runtime
trial is interrupted by the overall solve limit rather than completed.

These measurements establish the intended lifecycle over the recorded runs.
They do not show that switching pricing resolves degeneracy: no tested model
run reaches optimality. In particular, phase-II medium dual is observed only
from approximately 825 to 900 seconds; longer-term behavior remains untested.

## Phase-I perturbations with bounded adaptive pricing

The next investigation compares monitoring, perturbations, pricing and their
combination with the same internal `phase_one=true` construction. It reproduces
and fixes a native point-recovery check against the wrong bounds while an owned
perturbation is active. See [the interaction report](phase-one-interactions.md)
for the isolated model measurements, regression evidence and remaining limits.
The captured runtime failure is removed; convergence is not established. The
combined medium primal run still fails at iteration 5,443, with independently
confirmed working-bound infeasibility. The report retains this negative result
and does not recommend enabling the combined path by default.

## Degenerate bound-snap point recovery

[The pre-pivot capture and certified midpoint recovery](balanced-point-recovery.md)
localize the combined medium Phase-I failure at iteration 5443. The report
distinguishes the numerical repair from evidence about degeneracy and convergence.

## Method-specific progress and intervention ordering

[The ordered-intervention report](intervention-order.md) separates the progress
metric change from scheduling, records both primal measurements, and checks
that adaptive shifts do not occur inside a temporary pricing trial.

## Dual feasibility history across cost repairs

[The cost-history report](dual-cost-history.md) identifies repeated monitor
replacement during numerical dual cost repairs, preserves comparable feasibility
history, and distinguishes that repair from the remaining convergence problem.

## Working row values after primal bound perturbation

[The ratio capture and working-row experiments](working-row-values.md) identify
an original/working-bound mismatch that discards a strong zero-step pivot. The
report separates exact ratio replay and passing pivot regressions from subsequent
real-model failures. Both candidate patches are retained only as diagnostic
artifacts; production sources remain unchanged.

## Complementary errors in primal point recovery

[The coupled-point investigation](coupled-point-recovery.md) captures the next
experimental failure and identifies different model rows blocking prediction
and residual correction. A single joint midpoint repairs that pivot but fails
125 iterations later in a fresh runtime run. The new candidate is also retained
only as a diagnostic artifact; none of the working-row experiments is promoted.
