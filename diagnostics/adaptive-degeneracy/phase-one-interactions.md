# Phase-I perturbations and adaptive pricing

Base: `9bf9cef` on `codex/adaptive-degeneracy`; working-bound correction: `1fe8a5c`.
This investigation does not
include the separate scan-performance experiments and does not enable the
internal Phase-I path in the public adaptive preset.

## Question and configuration

The default primal Phase I disables bound perturbations. The existing internal
`phase_one=true` artificial-variable path allows them and restores the working
problem before certification. We compare four policies using that same path:
monitoring only (`none`), bound/cost perturbations (`perturb`), bounded temporary
pricing (`pricing`), and both (`both`). Only the relevant algorithm's
perturbation mechanism can act. All other policy switches are explicitly false.

All runs use Float64, PFI, native refactorization every 80 updates, initial
steepest-edge pricing, relaxed integrality, and 1,000,000 iterations. The shared
`pricing_isolation.jl` override disables the separate primal weak-pivot
preference in every arm; it retains all native numerical checks. The option
label is adaptive, but the explicitly supplied and asserted `NumericalPolicy`
determines the actual switches. These instrumented experiments do not measure
the public adaptive preset.

Julia 1.13.0 aarch64 runs with one Julia thread and one BLAS thread. Only one
numerical process runs at a time, with the existing 8 GiB virtual-memory limit,
6 GiB available-memory floor, and 1 GiB swap ceiling. The guard signals only its
owned process group. AFIRO warms common paths. Matrix variants run sequentially
in one process with fresh solve state; timings still include rare-path
compilation and diagnostics. `process_peak_rss` is the maximum for the whole
process, not an independently reset measurement for each variant. Earlier
reports called this same quantity `peak_rss`.

## Runtime: a concrete compatibility defect

The initial four-arm matrix used a 300-second solve budget per variant:

| Policy | Status | Iterations | Refactorizations | Last completed recorded working objective |
| --- | --- | ---: | ---: | ---: |
| none | TIME_LIMIT | 12,386 | 5,492 | 605,524.514609 at iteration 12,352 |
| perturb | TIME_LIMIT | 5,478 | 1,879 | 600,725.273419 at iteration 5,000 |
| pricing | TIME_LIMIT | 11,550 | 5,274 | 602,968.895258 at iteration 11,520 |
| both | TIME_LIMIT after original-LP retry | 6,637 total | 1,293 | See below; different working problems |

None completed phase I. Objectives belong to the artificial-variable working
LP, with bounds perturbed where applicable. They are not certified original
objectives and are not sufficient to rank convergence. A final observed mutable
workspace may be left partway through reconstruction at a time limit; the table
therefore uses completed event records instead of termination-time arrays.

The combined run applied a bound shift and started a temporary Dantzig trial
at iteration 576. The trial returned to steepest edge at iteration 704. The
first attempt reached a working objective of 603,743.826424 at iteration 4,000,
then failed at 4,010 with `primal point could not be certified`. The outer solver
retried the original LP, whose auxiliary objective and dimensions differ, and
spent the rest of the shared budget there. The final TIME_LIMIT hid the earlier
NUMERICAL_ERROR. It must not be described as an error-free run.

A separate first-failure reproduction suppresses only that outer retry. It
reproduced NUMERICAL_ERROR at iteration 4,010 and 979 refactorizations in 190.69
seconds. The reported maximum working-bound violation was
`1.000000000000001e-7`, just above the configured `1e-7` tolerance. Native point
recovery was incorrectly checking a candidate against the unperturbed model
bounds while an owned bound perturbation was still active. A mathematically
valid point of the current working LP could consequently be rejected.

The small production correction shares the existing strict row/column
feasibility implementation between original and working-bound checks. Native
point recovery uses working bounds only when an active bound journal owned by
that workspace exists. Otherwise it retains original-model checking. Row
consistency, tolerances, interval arithmetic, and the existing Float32/Float64
exact row-certification fallback are unchanged. This adds no precision
escalation or new heuristic. Original-result certification still uses original
bounds; a working-only feasible point cannot become an optimal original result.

The combined first-failure run after the correction follows the same recorded
trajectory through iteration 4,000, continues past the previous failure,
and reaches TIME_LIMIT at 4,734 iterations and 1,334
refactorizations (300.0009 seconds). It records one `primal_point_preserved` and
18 native correction attempts/completions. It remains in phase I. This verifies
removal of the captured compatibility defect, **not resolution of stagnation**.

The original matrix/source digest is
`ab4555ffebf4a641216bc3676e2bf0ade9a5f8d1479e3761ab3654dd2d6cc3c1`;
the corrected source digest is
`9d0a013c0011c142a9bb51015e20fe3f6ae600d1e1b5338393e03a1990bfd862`.
The common weak-pivot isolation method digest is
`5108e2d40266d6c849b0261881186e67b74096539c14c4cfe76d53c5ec91d811`.

The perturbation runs still spend substantial work rejecting candidates:
319,499 rejections for perturbations alone, and 315,113 in the corrected combined
run, compared with 135,569 for monitoring alone and 124,395 for pricing alone.
Different trajectories and the corrected combined source prevent a speed
ranking, but the counts show that removing the captured numerical failure did
not remove the costly selection problem. The combined run records only one
stalled event and one bound-perturbation level; it does not exhaust all three
available levels. Pricing/stagnation observations advance with completed
iterations, not every rejected candidate. A small number of successful pivots
can therefore hide substantial candidate-search work from that progress signal.

## Intervention lifecycle

The recorded pricing trials retain their observation budget when a perturbation
resets the stagnation monitor. Completed trials take at most 256 observations;
expiry occurs at exactly 256. The combined runtime run returns after 128
observations. Simultaneous actions are observable, but do not themselves prove
that the actions conflict or that either caused later progress. In particular,
a productive return after a bound shift is not an isolated measurement of the
benefit of Dantzig pricing.

Small deterministic interaction cases exercise paths that stalled large models
never reach: all four policies, primal artificial-variable removal and original
bound cleanup, dual cost restoration, exact arithmetic without perturbations,
and cancellation both during perturbation and restoration. They verify original
feasibility and objective at optimal returns, no active journal or temporary
pricing in phase II, and no adoption of a partially processed auxiliary phase.
The combined diagnostic interaction suite passes 126 assertions.

## Medium primal: the perturbation levels do activate

The 300-second four-arm experiment covers the initial plateau and first adaptive
interventions, not medium's known late dual phase transition. Monitoring alone
finishes 9,212 iterations and 116 refactorizations. Its recorded auxiliary
objective is 162,060,000 at iterations 1,000 through 5,000, 160,016,000 at
6,000 through 8,000, and 157,242,950 at 9,000. The initial flat objective is
accompanied by declining dual infeasibility; the monitor calls those windows
productive. A later objective decrease also happens without any intervention.

Perturbations alone finish 6,463 iterations and 81 refactorizations. They activate
at 5,440, 5,632, and 5,824, exhausting all three levels. At iteration 6,000 the
working objective is 160,015,999.995325, only about 0.004675 below the unperturbed
plateau. The run records 843 point preservations, two native corrections, and
424 rejected candidates; monitoring alone records none of those events in its
longer completed iteration prefix. This is evidence of additional numerical
recovery work after the shifts, not a pure timing comparison. The shared
iteration-6,000 checkpoint shows no substantial auxiliary-objective advance.

Pricing alone finishes 9,015 iterations and 113 refactorizations. At iteration
9,000 its working objective is also 157,242,950. Ten Dantzig trials start;
nine expire at 256 observations and one is interrupted by the solve limit.
There are no productive returns in this prefix. This does not demonstrate a
convergence benefit over the monitoring-only trajectory.

The combined arm activates both interventions at iteration 5,440. At 5,443 the
first attempt terminates and the outer solver restarts the original problem.
It ultimately reports TIME_LIMIT with 7,919 total iterations and 100
refactorizations. Its final auxiliary objective belongs to the larger original
problem and must not be ranked against the other arms. The Dantzig trial in the
failed private workspace is interrupted, not successfully completed or carried
into the original retry. The retry starts with steepest-edge pricing and a
fresh history. This is a second captured failure of the proposed combined path,
not evidence that the working-bound correction resolves every numerical issue.

| Policy | Final status | Iterations | Refactorizations | Phase-I outcome |
| --- | --- | ---: | ---: | --- |
| none | TIME_LIMIT | 9,212 | 116 | No completion |
| perturb | TIME_LIMIT | 6,463 | 81 | Three perturbation levels, no completion |
| pricing | TIME_LIMIT | 9,015 | 113 | Nine expired trials, no completion |
| both | TIME_LIMIT after original-LP retry | 7,919 total | 100 | First attempt fails at 5,443 |

A separate first-failure reproduction, with the outer original-LP retry
explicitly disabled, confirms NUMERICAL_ERROR (`primal point could not be
certified`) at 5,443 iterations and 69 refactorizations in 186.016 seconds.
The failed reconstructed point has one working-bound violation: basic row
activity 534,344 (working row 295,287) is `1.0000007932831068e-7`, with an
upper bound of zero and primal tolerance `1e-7`. The last declared primal step
is negative zero. A zero step does not prevent a basis exchange, leaving-bound
snap or reconstruction from changing the represented point.

An independent exact sum of that row's three stored coefficient/value products
has activity approximately `1.0000004749454088e-7`: it exceeds the working
tolerance by about `4.74945e-14`. The original/working-bound correction is not
the missing check here. This is a genuinely inadmissible point under the
existing absolute tolerance, not merely an overestimated interval or stored
row activity. The sampled largest equation residuals are only about `2e-13`;
small equation residuals do not establish bound feasibility. Rejecting this
point is correct. The snapshot contains the reconstruction after rejected
prediction/correction trials were rolled back, so it does not identify why
those individual candidates failed. A pre-pivot capture with the chosen indices,
direction and rejected candidates is the next diagnostic step. No tolerance
change or additional heuristic is justified by this evidence alone.

All four use the corrected source digest above. These bounded observations do
not justify enabling the combined Phase-I path as a default anti-degeneracy fix.

## Regression evidence

The initial owned-working-bound regression had 24 passing and 40 failing
assertions before the correction. The final regression file has 97 assertions
covering all four basis managers, Float32/Float64, working-only points rejected
as original results, inactive/cost-only/wrong-owner journals, restoration, and
both directions of perturbed row bounds with cancellation-sensitive activity.
The focused semantic runner passes 2,392 assertions with `--compile=min`.
The separate normal-compilation runner passes 98 assertions, including the
existing AFIRO allocation limit. These overlap with the 126 interaction assertions; counts are not distinct-suite
totals or a full project-suite pass.

The first broad validation attempt incorrectly included an allocation limit
under `--compile=min` and omitted a logger helper. The corrected runner loads
the helper and reserves the allocation assertion for normal compilation.
A broader normal-compilation attempt then reached the 300-second wall guard;
it is not counted as a passing run. The guard stopped only its own process.
Independent read-only review found no blocking issue in the source correction
or final regression cases.

## Scope of the conclusion

The owned-working-bound mismatch is a numerical-core compatibility fix, not a
new adaptive fallback. The four-arm experiments test the existing perturbation
mechanism in an already existing internal Phase-I path. Neither that path nor
stronger perturbations are enabled by default here. The evidence does not yet
justify treating their combination with pricing as a solution to degeneracy.

In particular, the remaining questions concern the progress signal and useful
selection work: the monitor can recognize decreasing dual infeasibility during
a primal objective plateau, and it does not advance for every rejected
candidate. Perturbation-induced progress is also not evidence that a concurrent
pricing trial helped. These are reasons to evaluate shared intervention
scheduling and progress criteria before increasing perturbation levels or
adding numerical rejection rules. No such scheduling change is made here.

Large-model dual behavior after its late auxiliary handoff is not retested by
this primal Phase-I experiment. The small dual interaction cases verify cost
restoration and pricing cleanup, not medium dual convergence. The earlier
900-second pricing-only dual result remains documented separately in README.

## Reproduction and evidence

Run commands from this worktree through the established guarded wrapper. The
wrapper's wall-time allowance must exceed the sum of solve limits plus model
reading and compilation. Do not run these commands concurrently.

```sh
julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/working_point_semantics.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/working_point_compiled.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_matrix.jl runtime primal 300 /tmp/runtime-phase-one
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_matrix.jl medium primal 300 /tmp/medium-phase-one
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl runtime primal both 300 /tmp/runtime-first-failure
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl medium primal both 300 /tmp/medium-first-failure
julia --project=. diagnostics/adaptive-degeneracy/reproduce/inspect_phase_failure.jl /tmp/medium-first-failure.bin
python3 diagnostics/adaptive-degeneracy/reproduce/validate_phase_one_reports.py
```

`phase_one_models.jl` can also run a single variant; its arguments are model,
algorithm, variant, seconds, output TOML. It verifies each input's SHA-256.
`phase_one_first_failure.jl` labels its disabled original-LP retry and additional
method hashes. The earlier recorded first-failure reports predate those metadata
fields; their filenames and the discussion above identify the instrumentation.
The original runtime binary contains a portable problem, basis and arrays, not
the factor-update chain, journal or pricing lifecycle. The later medium capture
also saves the journal and pricing state, but still omits factors and other
workspace caches. Neither is an exact continuation checkpoint. They remain
local under the ignored `.superpowers/adaptive-degeneracy/` directory as
`runtime-combined-failure.bin` and `medium-combined-first-failure.bin`.
`inspect_phase_failure.jl` performs no new optimization or basis factorization;
it compares working bounds and independently sums selected rows exactly.

The structured results and selected reproduction/test logs are in
[results/phase-one](results/phase-one/). Complete local logs, including the
superseded test-runner attempts, remain in
`.superpowers/adaptive-degeneracy/phase-one-logs/`.
