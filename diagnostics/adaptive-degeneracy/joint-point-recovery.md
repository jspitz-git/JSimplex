# Bounded joint primal point recovery

This investigation starts from `7da710f` and follows the rejected
[prediction/correction midpoint](coupled-point-recovery.md). The question is
whether a bounded native feasibility method can repair coupled errors with
nonbasic values fixed, instead of trying additional predetermined points.

## Feasibility contract

The numerical recovery operates on the current working point, without changing
basis indices, variable states, costs, tolerances, factorization, pricing or
perturbation journals. It is reached only after the existing prediction,
prediction/reconstruction midpoint and single residual correction have failed.
The old experimental inward rounding and prediction/correction midpoint are
not included. The previously diagnosed working-row bound-scope correction is
included separately; it enables strong zero-step pivots under owned shifts.

For structural values `x` and row activities `r`, acceptance requires all of:

- Stored structural and activity bounds within the original primal tolerance.
- Actual `A*x` within the current model's row bounds at that same tolerance.
- `A*x-r` within that tolerance on every row.

The model bounds come from the owned active perturbation when present, otherwise
from the original problem. Stored working bounds still apply in both cases.
A nonbasic value remains bitwise unchanged. A basic row activity can be eliminated:
there must exist an admissible stored activity within one tolerance of `A*x`.
This gives an additional interval for `A*x`, intersected with the model interval.
The model tolerance is never doubled; two tolerances occur only when composing
the activity-bound and equation constraints. The final activity is clamped into
its own admissible interval and the entire original certificate is rerun.

## Bounded native method

The diagnostic prototype builds a sparse row view and projects structural basic
values along the coefficients of violated rows. It normalizes coefficients before
forming the squared norm and evaluates activities with compensated native
products and sums. The first prototype reserved one quarter of the primal tolerance,
limited by the width of each admissible interval. The controlled failure below
shows why this reserve is too large; the revised candidate uses native roundoff
room instead. Neither changes the acceptance tolerance.

The candidate allows at most eight sweeps and limits each basic coordinate's
movement to `8*max(tolerance, eps(T)*max(1,abs(original_value)))`. The production
candidate also applies this locality limit to basic activities; the initial
prototype limited structural values only. Float32/Float64, round-to-nearest and
gradual underflow are required. No new factorization, FTRAN, precision boost or
exact-arithmetic update is performed. The unchanged final certificate retains
its existing exact fallback for inconclusive row enclosures.

Interior targets, rounding and the finite budget can make recovery fail even
when a feasible point exists. Failure is not an infeasibility proof. Every failed,
nonfinite, cancelled or exceptional trial rolls back the full original primal
vector. The row-solution cache is published only after the full certificate and
a final cancellation check. `primal_projection_attempt` and
`primal_point_projected` distinguish attempts and accepted recoveries.

This is numerical point recovery. It does not monitor stagnation, switch pricing,
change perturbations or schedule adaptive interventions.

## Captured-point evidence

The prototype repairs all three saved mathematical failures (iterations 6,799,
8,464 and 8,589) in one sweep each. It projects 15, 44 and 44 rows, respectively.
Maximum changes are about 2.49e-8, 1.27e-7 and 1.27e-7, with all nonbasic values
unchanged. These checks use the stored problem, basis and point without solving
with the reconstructed workspace's factorization.

The initial quarter-margin candidate also passes all 15 mathematical-point checks and all
14 one-pivot checks for the two runtime snapshots. The latter preserve the
captured ordered basis and states, certify the new complete point and publish
the corresponding basic solution. These snapshots are not outer-driver restart
checkpoints, and none of these results establishes convergence.

The older medium pre-pivot binary snapshot raises `EOFError` during deserialization
with the current code and is not counted as a successful replay. A subsequent
change added a field to `WorkspaceStagnation`; serialization layout compatibility
is a possible explanation, not a proven diagnosis of the file. The original
snapshot is preserved with its hash. Fresh-model testing is needed for medium.

## Regression evidence

A two-row regression uses an admissible intersection that contains neither the
reconstruction, prediction nor their midpoint. Before adding joint recovery,
72 assertions pass and 24 fail. All initial 96 pass afterward, in Float32 and
Float64 with all four basis managers. Independent rational checks evaluate the
actual row and equation bounds, rather than only the stored activity.

Expanded tests cover impossible intersections, invalid fixed nonbasic values,
rows without a movable structural value, locality-budget exhaustion, conflicting
unowned bounds, nonfinite input, owned-bound restoration and ownership errors.
Cancellation and exceptions are checked both after a full trial and in the middle
of a 300-row sweep. The 210 checks pass. A further eight checks cover arithmetic
overflow from finite inputs after the first basic coordinate has changed.

The focused semantic runner passes 6,708 assertions with `--compile=min`, including
phase transitions and adaptive intervention ordering. That run preceded the eight
additional overflow assertions. Counts from different runners overlap and do not
constitute a full project-suite pass.

## Diagnosing the first joint-recovery failure

The first fresh runtime run accepts six joint recoveries but fails its seventh
at iteration 9,391: NUMERICAL_ERROR, 1,805 refactorizations and 158.9749 seconds
from a requested 300-second budget. There are 96,765 candidate rejections. The
final auxiliary objective 600127.7998 is an uncertified working-LP observation.
The guard does not interrupt this run.

A method-level trace of the saved mathematical point shows that all eight sweeps
execute; no fixed nonbasic violation or empty preprocessing interval causes the
rejection. Stored bounds become feasible, but actual model/equation checks fail.
The original reconstructed point violates four basic stored bounds and already
passes the model rows and equations. After the first sweep, row 3,678 fails;
after sweeps two and eight, rows 2,357 and 5,911 fail. At sweep eight their exact
equation errors are approximately 1.1002e-7 and -2.0737e-7 against tolerance 1e-7.
The listed basic movements stay well below the 8e-7 locality limit.

A controlled diagnostic changes only the interior reserve, retaining the same
eight-sweep budget, locality limits and full certificate. Quarter-tolerance
reserve fails; zero reserve and a machine-roundoff reserve both pass. The
successful maximum displacement is only about 1.33e-8. This localizes a defect
in the trial targets rather than justifying a larger iteration or movement budget.

A new two-column regression makes the issue explicit: two fixed nonbasic
activities restrict the same structural variables to a thin but nonempty
intersection. A quarter-tolerance reserve pushes the two projection targets
outside that intersection. It fails four of twelve assertions before the
correction and passes all twelve afterward, in Float32 and Float64.

The revised reserve is
`min(8*eps(T)*max(tolerance,abs(clamp(value,lo,hi))), tolerance/4, (hi-lo)/4)`.
Its scale follows the value and tolerance, with no unit-magnitude floor; that
also avoids an unnecessarily large reserve for small Float32 values. The
controlled diagnostic's roundoff variant used a unit-magnitude floor. The
revised scaled formula is verified separately on all four captured mathematical
failures and both runtime pivots (20 and 14 checks). All 230 focused regression
checks pass, including overflow and the thin intersection. Nonzero reserve and
finite iteration limits can still miss an even thinner feasible region; this is
not a complete feasibility decision procedure.


## Revised candidate and clipping diagnostic

The native-margin candidate also fails on a fresh runtime run: NUMERICAL_ERROR,
iteration 9,612, 1,985 refactorizations and 178.0579 seconds from the requested
300-second budget. Seven of eight joint recoveries are accepted; 83,384 pivot
candidates are rejected. The final auxiliary objective 599982.8907 is an
uncertified working-LP observation, not an achieved bound or a convergence result.

At the saved failure, basic structural variable 21,505 starts at approximately
-2.73125e-7 with lower bound zero. Projection clamps it to -1e-7. Each row's
unconstrained correction still includes that coordinate, so clipping discards
part of the calculated correction. The three remaining violations contract
across sweeps but do not reach the certificate. After sweep eight, exact excesses
on rows 3,608, 3,678 and 8,015 are about 2.38e-11, 1.74e-13 and 1.12e-12.
This is different from the earlier quarter-tolerance target conflict.

A controlled diagnostic redistributes the lost correction among coordinates
that can still move in the required direction. It retains the eight outer
sweeps, locality bounds, interior margin and certificate, but adds up to
`nnz(row)+1` inner passes per corrected row. It therefore does more work than
the measured production candidate. This variation still fails: only row 3,608
remains outside the tolerance, by approximately 8.62e-22, identically after
sweeps one, two and eight. The complete certificate correctly rejects it.
The recorded `maximum_change=0` for a rejected trial describes the restored
point after rollback; it does not mean the trial made no changes.

Neither increasing the allowed tolerance nor accepting this almost-feasible
point is part of the proposal. A future feasibility method needs to handle
active coordinate bounds and representable update sizes together. The evidence
supports investigating those two aspects; redistribution alone has not passed
the certificate and has not been run as a production solver candidate.


## Fresh medium run

The revised candidate reaches TIME_LIMIT in phase I after 2,875 iterations,
36 refactorizations and 300.1739 seconds. No joint projection attempt occurs.
The run therefore checks the ordinary path and intervention ordering, but does
not exercise the new recovery or reach the old failure near iteration 5,443.
It is not evidence that medium is repaired or converges. It also does not replace
a successful replay of the incompatible binary snapshot.

## Final regression checks

The final native-margin candidate passes 6,728 assertions in the focused semantic
runner with `--compile=min` (1m52s). This includes all 230 joint-recovery assertions.
A separate normal-compilation runner passes 740 assertions, including allocation
checks (1m46.1s). These counts overlap with the earlier runs and are not a full
project-suite pass. A full-suite run is not claimed for this rejected candidate.

Event validators also pass for both runtime runs and the medium run. Perturbations
do not overlap temporary pricing trials; closed trials stay within their budget.
Medium ends with one pricing trial still open at the time limit, not an observed
trial-budget violation. No collision between those adaptive interventions is
shown by these runs.

## Disposition and reproduction

Both full solver candidates are rejected. The final repository retains diagnostic
patches, tests, scripts and evidence; production source files are restored to
`7da710f`. No new numerical recovery is enabled and no adaptive option is changed.
The patches are complete alternatives relative to that baseline, not incremental
patches to stack on the old working-row experiments.

Use the existing single-process Julia guard (8 GiB virtual memory, 6 GiB minimum
available RAM, 1 GiB maximum swap), one Julia thread and one BLAS thread. Preserve
`LocalPreferences.toml` with `precompile_workload=false`. Binary snapshots remain
local in `.superpowers/adaptive-degeneracy/`; they are not portable driver restart
checkpoints. No excluded large model is solved or factorized.

To reproduce the revised candidate on a clean baseline production tree:

```sh
git apply --unidiff-zero diagnostics/adaptive-degeneracy/reproduce/joint-native.patch
julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/joint_point_semantics.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/joint_point_compiled.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/joint_point_replay.jl /tmp/joint-native-replay.toml
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl runtime primal both 300 /tmp/runtime-joint-native
julia --project=. diagnostics/adaptive-degeneracy/reproduce/inspect_joint_failure.jl /tmp/runtime-joint-native.bin /tmp/joint-native-failure
julia --project=. diagnostics/adaptive-degeneracy/reproduce/inspect_joint_constraints.jl /tmp/runtime-joint-native.bin /tmp/joint-native-failure
julia --project=. diagnostics/adaptive-degeneracy/reproduce/probe_joint_clipping.jl /tmp/runtime-joint-native.bin /tmp/joint-clipping.toml
julia --project=. diagnostics/adaptive-degeneracy/reproduce/inspect_joint_failure.jl /tmp/runtime-joint-native.bin /tmp/joint-redistributed-failure /tmp/joint-clipping.toml-redistributed.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/inspect_joint_constraints.jl /tmp/runtime-joint-native.bin /tmp/joint-redistributed-failure
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl medium primal both 300 /tmp/medium-joint-native
git apply --reverse --unidiff-zero diagnostics/adaptive-degeneracy/reproduce/joint-native.patch
```

These are the Julia payloads; wrap each separately in the guard and wait for it
to exit before starting the next. The real-model guard wall limit is 540 seconds,
including compilation, while the solver limit is 300 seconds. The scripts disable
the original-LP retry to expose the first failure and isolate adaptive pricing
plus perturbations from the other adaptive interventions.

The earlier `joint-quarter.patch` reproduces the 9,391 failure and is required
by `probe_joint_margin.jl`; its source-pattern assertion deliberately prevents
running that probe against a different method. The current focused test file
includes the thin-intersection regression that intentionally fails against that
earlier source. Intermediate passing-test counts refer to the test versions
at those checkpoints, not to all later assertions.

After restoring production, run `reproduce/validate_joint_point.py`. It rebuilds
both source patches in temporary copies, checks their measured digests, verifies
the numerical evidence and validates local artifact hashes when those files are
present. Text results are in [results/joint-point](results/joint-point/). Full logs,
point snapshots, generated diagnostic variants and red-test output are kept in
`.superpowers/adaptive-degeneracy/joint-point/`, with a committed hash manifest.

## Follow-up

The [representable-point investigation](representable-point-recovery.md) replaces
these rejected candidates with a bounded native recovery that handles clipped
coordinates, representable updates and the locality anchor. Its runtime result
and remaining convergence limitations are documented separately.
