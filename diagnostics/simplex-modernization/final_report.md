# Simplex modernization: integration validation

Status: the F25 integration snapshot at `620f778` completed its correctness
gates, corpus matrix, supplemental experiments and bounded stress validation.
A subsequent whole-branch review identified two correctness gaps. Both are
fixed, with fresh full-suite and external verification recorded in the
[final review report](final_review.md).
All corpus timings below describe the pre-review production fingerprint, not
the subsequently corrected code.
The default decision is to retain `simplex_strategy=:legacy` and
`pricing=:steepest_edge`. Observed losses of solvability rule out an adaptive
default rollout. Production defaults are unchanged.

## Scope and provenance

F01–F24 each have a separate implementation commit, regression tests and a
[feature coverage record](F25-feature-coverage.json). The
[implementation plan](../../docs/superpowers/plans/2026-09-22-simplex-modernization.md)
tracks all stages and their dependencies. The [decision record](decisions.md)
preserves implementation deviations and their stated tradeoffs. F24 parent is `dca3555`; the original
comparison revision is `d93cfd3`.

At `620f778`, F25 changes the benchmark harness, development tests and documentation. Its
production fingerprint is unchanged from F24:
`cc14d2e38ae5a9fa8cdddb40665f60f3fac30adb9280481b073060085814b824`.
The baseline fingerprint is
`937ca7d7223940c4ff69a62a458369ff1f31a3a0e0724a0659583f5a1320d3c4`.
Fingerprints include sorted relative paths and bytes of Project.toml and every
src/**/*.jl file. Archived sources carry explicit revision markers and use the
same dependency manifest. Every measured worker checks the loaded source path.

The parent and final legacy configurations have identical production sources,
dependencies, options and inputs under the common corrected worker. Their timing
evidence is shared and labelled as such; they are not independent repetitions.

## Harness corrections

A renamed hardlink to a registered stress-only input previously escaped the
filename and symlink checks. Selection and worker validation now compare file
identity against excluded corpus paths before parsing, including a replay's
original path. The regression failed twice before the fix and passes all four
checks. Ordinary medium/runtime inputs remain eligible.

Every configuration now executes two complete fresh warmups, including the old
source and diagnostics-off runs. Instrumented warmups execute the observer body;
each solve owns fresh phase dictionaries, counters, precision history, final
workspace and replay/trace state. Warmup replay artifacts use disposable paths.
The regression changed from 8/10 to 28/28 passing checks. Recorded warmup outcomes
are distinct from measured samples. This corrects the limitation disclosed in
F21–F24; their historical measurements have not been rewritten.

The cached-multiplier regression now uses a nonunit row scaling divisor to force
actual high-precision unscaling under a lower ambient BigFloat context.

Scaled-witness validation now reconstructs the working matrix by dividing each
stored coefficient by its row and column factors, and divides costs by column
factors while preserving objective sense. The old multiplication check could
hide available original-unit dual diagnostics. Direct division avoids overflowing
reciprocal factors when the quotient itself is representable. A mapped-start
regression failed 4/20 checks before the fix and passed 32/32 afterward, covering
both algorithms, MIN/MAX, objective constants and original KKT errors. Expanded
legacy Phase I workspaces still require a separate mapping and remain unavailable
in this diagnostic. All final measurements use the corrected common worker.

## Correctness verification

The complete F24 native production suite passed 253,612/253,612 checks in
122m55.5s. F25 reuses that gate only after checking byte identity of production
sources and all 320 production test files. Production defaults and dependencies
are unchanged. A new production or production-test change invalidates this reuse.
The changed development suite passed 1,208/1,208 checks across 69 testsets,
including 249 JET checks. The separate numerical GLPK command passed all six
cases. Both ran afresh and exited successfully. The [verification record](F25-verification.json)
contains the gate counts and log fingerprints.

The MOI adapter remains one-shot: `optimize!(optimizer, source)` translates the
current model supplied by JuMP's cache and returns `copied=false`. It does not
implement an incremental `copy_to` interface. Existing tests cover repeated
models, original-unit results, scalar option conversion and option persistence
through `empty!`.

## Measurement design

All six solve-suite views use the frozen registry and the requested NetLib,
MIPLib and mps roots. The 26 unique eligible cases are counted once per numerical
configuration; shared quick/degenerate/phase_one membership does not duplicate
aggregate samples. Every MIP case is an explicit LP relaxation. No heuristic is
tuned using the holdout results.

Primary timing compares original baseline, current legacy/parent and current
adaptive profiles with the common corrected worker. All use explicit
steepest-edge pricing, PFI/native factors, automatic scaling, presolve, a 100,000
iteration limit and no numerical-policy overrides. Diagnostics and kernel timing
are disabled. Solver options and the current profile's policy are prepared before
the timed solve; these are warmed solver timings, not public first-call latency.

The adaptive profile enables its usual numerical safeguards and clock-driven
refactorization policy. It does not implicitly enable `sparse_pricing`,
`hypersparse`, `crash`, `phase_one`, `precision_boosting` or `lp_refinement`;
these optional policies remain false in this public-profile comparison. Their
separate feature reports provide the relevant opt-in validation. This matrix
does not establish compatibility or performance for every combination of
experimental policies.

Cases outside sparse_large/runtime receive seven measured repetitions after two
complete warmups; sparse_large and runtime receive three. Runtime, medium and
greenbea each receive 360 seconds per solve; other cases retain the 60-second
preset used in the earlier sparse_large comparisons. Both warmups use the same
per-solve limit as the recorded samples. The requested
24 GiB address-space cap (`RLIMIT_AS`) is clipped to host/cgroup limits. Parsing, compilation and
warmups are visible separately from warmed solve time.
Reported peak RSS is the worker process high-water mark, including loading,
parsing and warmups; it is not an isolated per-solve allocation measurement.

Separate single-sample diagnosed observations for current legacy and adaptive
record phase times, iterations, repairs, refactorization reasons, working
precision, memory and available original-model dual errors. They follow two
complete warmups and the same numerical settings and deadlines. These observations
are excluded from speed scores; baseline diagnostics that do not exist are marked
unavailable. A presolved witness without a verified original mapping is also
unavailable, not a zero residual.

An available witness does not necessarily pass every strict diagnostic. The
complementarity metric uses the sign of every nonzero reconstructed price;
if that sign requires a missing bound, it reports infinity even when the
dual-sign error is below solver tolerance. This occurs in the final small-case
observations as well as earlier feature reports. Raw infinities are retained;
primal feasibility and reference-objective agreement are reported separately
from finite independent KKT certification.

Timing ratios require both configurations to be measured during the same boot
epoch, with every sample optimal, passing original primal feasibility checks and
matching an accepted GLPK or analytic optimum. Cases without an accepted optimum,
timeouts, numerical failures, incomplete workers and stress probes remain
separate outcomes. The rollout thresholds are no unexplained median slowdown
above 10% across jointly solved cases or above 2x for an individual case, with
no false certificate or unexplained new loss of solvability.

The supplemental timing-repeat rule was fixed after the first 70 primary
configurations, which already included blend and share2b holdout records. It is
a post hoc noise check: repeat both members of every eligible comparison with
a within-profile range greater than 20% of its median, regardless of which
profile was faster, using unchanged options and reversed profile order. Keep
the primary matrix intact and report these repeats separately. They do not
constitute a new independent holdout evaluation or alter the primary score.

## Reproduction and artifacts

The raw [primary records](F25-results.json), [reference results](F25-references.json),
and [timing repeats](F25-timing-repeats.json) preserve input hashes, source and
worker fingerprints, options, warmups, statuses and resource limits. The runs
used Julia 1.13.0 on Linux aarch64 with one BLAS thread. Each configuration ran
sequentially in a separate worker. A Julia language server was present; timings
are observations of this host, not measurements on a dedicated idle machine.

For example, run one public profile with the current checkout as follows:

```bash
julia --startup-file=no --project=dev dev/simplex_benchmarks.jl \
  --source=. --suite=quick --simplex-strategy=legacy \
  --pricing=steepest_edge --basis-update=pfi --scaling=auto --presolve=on \
  --iteration-limit=100000 --samples=7 --time-limit=60 \
  --memory-limit-mib=24576 --diagnostics=off --kernel-timing=off \
  --output=/tmp/simplex-quick-legacy.toml
```

The registered roots default to the three requested local collections. Use
`--simplex-strategy=adaptive` for the public adaptive profile. For individual
cases, `--file` selects the input; retain the case-specific repetition count
and deadline recorded in the raw results. Separate diagnostic observations use
`--diagnostics=on --kernel-timing=on --samples=1`. Do not combine their times with
public-profile timing ratios. The runner always records two complete warmups.

## Results and default decision

The [primary summary](F25-summary.json) covers all 130 configurations and 958
measured samples. There were 125 completed workers and five input errors, all
from the same blend reader failure; no worker stopped for resource exhaustion.
The primary matrix's maximum recorded process RSS was 10,831,097,856 bytes.

| Public profile | Optimal | Iteration limit | Numerical error | Time limit | Fully optimal case/algorithm pairs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original baseline | 218 | 21 | 15 | 32 | 34/50 |
| Current legacy / identical parent | 218 | 21 | 15 | 32 | 34/50 |
| Current adaptive | 199 | 13 | 3 | 71 | 29/50 |

Each public profile has 286 measured samples. These sample counts use different
repetition counts for different suites and are not counts of independent models.
The 50 case/algorithm pairs come from 25 parsed inputs and two methods; a fully
optimal pair requires every repetition to finish optimally. Blend contributes
no solve samples. Separate diagnosed observations contribute 100 further samples.

The audit found no discrepancy between an optimal result's original primal
checks and its accepted independent reference objective. Of 60 available
original-model dual witnesses, 27 had finite strict diagnostics; the remaining
33 retained their infinite metric values. This is not a claim of finite
independent KKT certification for every optimum. All 100 diagnosed observations
used 53-bit working precision under the frozen public profiles.

Among eligible, jointly solved pairs, the primary median of per-pair timing
ratios is 1.061 for current legacy versus baseline (34 pairs) and 1.612 for
adaptive versus legacy (28 pairs). The corresponding primal/dual medians are
1.074/1.036 and 2.187/1.393. These are warmed timing ratios, not pooled run times.
The supplemental noise criterion selects 28/34 and 26/28 comparisons respectively;
the separate repeat results below retain substantial variation. These primary
ratios alone do not establish stable timing regressions. Solvability losses
already prevent default rollout.

The [reference record](F25-references.json) covers all 26 eligible inputs:
21 accepted GLPK optima, the exact analytic optimum of the generated
scaled-diagonal case, three unavailable optima and one reader failure. Reused
F23 references require matching compressed/source and decompressed hashes.
The scaled-diagonal oracle remains 3; the previously rejected raw GLPK value
of 2 is not treated as a valid reference.

GLPK reached its 360-second limit on medium and test without proving optimality
(`GLP_ETMLIM`, code 9). The aaa reference failed with `GLP_EFAIL` (code 5),
which is not a timeout. The local blend input still fails native MPS parsing
before reference construction. These limitations are retained explicitly;
an unavailable reference is not evidence of infeasibility or solver success.

Completed degeneracy comparisons show a mixed result. On degen2, original and
current legacy primal each hit the iteration limit in all seven samples;
adaptive primal solved all seven in approximately 19 seconds. For dual on the
same input, both legacy profiles solved seven of seven, while adaptive produced
four optima, two numerical failures and one timeout. A separate successful
diagnosed observation does not replace those unsuccessful public samples.

On degen3, both legacy dual profiles solved seven of seven; adaptive dual reached
the 60-second limit in all seven. On greenbea, both legacy dual profiles solved
all three samples, while adaptive reached the 360-second limit in all three.
Adaptive primal also timed out in all three greenbea samples, whereas both
legacy primal profiles returned numerical failures. These failed comparisons
are excluded from solve-speed ratios.

The separate greenbea primal diagnostic spent 359.84 of 360.01 seconds in
Phase I, with 245.66 seconds in the inclusive pricing timer. Its dual diagnostic
spent 359.83 seconds in the auxiliary problem, with 174.89 seconds in the
refactorization timer and 846 checkpoint restorations. Kernel timers may overlap;
these are observations of instrumented runs, rather than an additive profile of
the public timing runs. They identify different costs for the two algorithms.

On 10teams, both legacy dual profiles solved all seven samples, while adaptive
dual exhausted the 100,000-iteration limit in all seven. Legacy primal exhausted
that limit in seven samples per profile; adaptive primal had six iteration
limits and one timeout. The separate adaptive diagnostic had a primal timeout
and a dual iteration limit. This adds another observed loss of solvability
under the matched budgets and prevents an adaptive default rollout.

In the diagnosed 10teams dual run, adaptive performed 15,915 cost-triggered
refactorizations and stored 16,153 checkpoints before reaching the iteration
limit. Legacy solved in 1,707 iterations with 84 limit-triggered refactorizations.
These counters identify substantial additional work; they do not establish that
clock-driven refactorization alone caused the different pivot trajectory.

The runtime public comparison contains no optimum. Baseline and current legacy
each returned three primal numerical failures at iteration 767 and three dual
timeouts at 360 seconds. Adaptive returned three timeouts for each algorithm
at the same limit. All warmups received that solver budget too. These unfinished
outcomes do not establish a solve-speed improvement, and are excluded from
timing ratios.

The runtime adaptive diagnostic spent 358.43 seconds of its primal solve in
Phase I and 356.45 seconds of its dual solve in the main dual phase, completing
659 and 704 iterations respectively. Refactorization timers accounted for only
1.31 and 0.54 seconds in those runs. In contrast, legacy dual spent 358.43 seconds
in its auxiliary phase, including 153.33 seconds in refactorization. The existing
kernel timers do not explain most of the adaptive wall time; a more detailed
profile is needed before attributing that cost to a particular safeguard.

The medium public comparison completed all 18 measured solves, each with a
360-second timeout and no memory failure. Worker peak RSS was 6,167,638,016 bytes
for baseline, 7,185,108,992 bytes for current legacy and 5,279,031,296 bytes for
adaptive. Each worker's recorded address-space ceiling was 25,141,342,208 bytes;
RSS and address space are different resource measurements. Medium therefore did
not encounter the configured memory limit in these runs. Its unfinished solves
and unavailable independent optimum remain outside speed scores.

Both medium diagnostic profiles also timed out for both algorithms. Adaptive
primal spent 349.50 seconds in Phase I and completed 165 iterations, with only
1.42 seconds in its refactorization timer. Adaptive dual spent 348.44 seconds in
the auxiliary phase and completed 6,031 iterations. Its largest recorded kernels
were FTRAN (11.32 seconds), pricing (9.86 seconds) and refactorization (6.71 seconds).
As on runtime, these timers leave substantial adaptive wall time unattributed;
they do not justify assigning the slowdown to one mechanism without profiling.

On fast0507, baseline and current legacy solved all three samples for each
algorithm and matched the accepted reference optimum. Adaptive primal returned
one numerical failure and two timeouts; adaptive dual returned three timeouts.
The common limit was 60 seconds. This is a loss of solvability under the matched
budgets, not an eligible adaptive/legacy speed comparison.

The test holdout's 42 public samples all reached the 60-second preset, with no
memory failures. Each profile ran seven repetitions per algorithm under the
frozen suite-based repetition rule. This case has no accepted independent
optimum, and these unfinished results contribute no solve-speed ratios.

### Separate refactor-timing experiment

The [degen2 experiment](F25-degen2-timing-ablation.json) changes only
`refactor_timing=false` for adaptive dual, retaining the same input, source,
worker, limits and remaining policy. All seven public repetitions returned
`NUMERICAL_ERROR` at iteration 670, with a median elapsed time of 12.32 seconds.
The separate diagnosed repetition returned the same failure at iteration 670
and recorded zero cost-triggered refactorizations. Each configuration used two
complete warmups. The reported failure was exhausted bounded feasibility recovery.

Disabling clock-driven refactorization therefore did not restore solvability in
this experiment. The primary timing-on observation remains four optima, two
numerical failures and one timeout. These data do not establish the root cause,
and the experiment is neither a replacement for primary failures nor a change
to production policy.


### Supplemental timing repeats

The [repeat summary](F25-repeat-summary.json) covers all 82 selected workers and
574 measured samples: 573 optima and one timeout. All optimal samples passed
original-primal and independent-reference checks. Adaptive primal on air03
returned six optima and one 60-second timeout, so that repeated comparison is
ineligible for a speed ratio. Its seven primary optima remain unchanged.

| Comparison | Eligible repeat pairs | Primary median on those same pairs | Repeat median | Pairs still above the noise criterion |
| --- | ---: | ---: | ---: | ---: |
| Current legacy / baseline | 28 | 1.061 | 1.171 | 26 |
| Adaptive / current legacy | 25 | 1.792 | 1.593 | 25 |

These are medians of per-case/algorithm median ratios. They describe the selected
noisy subset, not the full corpus, and do not replace the primary score. Even
after repeating, 51 of 53 eligible comparisons exceed the 20% range/median
criterion. The legacy repeat median exceeds the project's 10% threshold;
therefore this experiment does not demonstrate absence of a legacy performance
regression. It also does not isolate a stable regression magnitude from the observed
variation. A controlled timing investigation remains necessary before claiming
a general performance improvement or cost-free legacy compatibility.

Nine adaptive repeat comparisons exceed 2x, including adlittle primal/dual
(21.98x/17.95x), stein9inf primal (12.40x), flugpl primal (4.04x), pk1 primal
(3.03x), air03 dual (2.79x), kb2 primal/dual (2.48x/2.06x) and sc50a dual (2.23x).
The repeated slowdown and observed solvability losses support retaining
experimental policies as opt-in. These repeats were selected post hoc under the
symmetric documented rule and are not independent holdout validation.

## Bounded oversized-input probes

The [stress records](F25-stress.json) contain nine separate probes with a 4 GiB
address-space ceiling and a 256 MiB read cap. Inspection and component probes
had 60-second worker limits; reader probes had 300 seconds. None ran simplex on
an oversized model or factored its full basis. These outcomes do not enter
solved-instance coverage or speed scores.

| Input | Inspection | Reader | Components |
| --- | --- | --- | --- |
| big.mps | First 256 MiB inspected | Stopped before parsing by read cap | Stopped before parsing by read cap |
| largo.mps | All 142,643,690 bytes inspected | Parsed successfully | Bounded extracted components verified |
| AnyMOD.mps | First 256 MiB inspected | Stopped before parsing by read cap | Stopped before parsing by read cap |

The largo reader produced 1,021,024 rows, 856,110 columns and 3,891,132 stored
entries in 10.59 seconds of parse time. Its leading 256x256 block has no stored
entries, so the leading-block pricing result alone offers little coverage.
The separate occupied-block extraction scanned 2,641 entries and selected a
64x64 block with 108 stored entries. It constructs a normalized diagonally
dominant component basis, not an original-model basis. Factor solves, sparse and
dense paths, cancellation, update chains, checkpoints and refactor resets passed
233 recorded reference checks, one cancellation check and eight checks each for
checkpoints and refactor resets. Update/pipeline probes use at most 32x32 bases.
The resource stops for big and AnyMOD demonstrate enforced bounds; they do not
claim successful full parsing or component execution for those inputs.

## Follow-up work supported by these results

The implementation provides individually tested opt-in mechanisms; it has not
established a general speed or robustness improvement for the combined adaptive
profile. Before promoting it, investigate the degen2 recovery failure and the
lost dual solvability on degen3, greenbea and 10teams, along with fast0507.
Profile the unattributed adaptive work on runtime and medium and isolate policy
interactions with separate ablations. Validate any resulting policy changes on
new frozen evidence; the current holdout must not be relabelled independent after
tuning against it. A controlled timing study must also resolve the observed
legacy slowdown before claiming performance compatibility with the original
baseline. Existing legacy and steepest-edge defaults therefore remain in place.
