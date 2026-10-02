# Primal point recovery with active bounds and representable updates

This investigation follows `0a75727` and the rejected
[joint projection candidates](joint-point-recovery.md). The approved question is
whether native point recovery can account for active coordinate bounds and
representable update sizes while preserving nonbasic values and the complete
feasibility certificate. No adaptive scheduling, pricing, perturbation policy,
precision boost or tolerance change is proposed.

## Evidence and method

The previous redistributed projection left row 3,608 outside its tolerance by
8.62e-22. The point was unchanged after subsequent sweeps. Individual structural
coordinates had magnitudes near 1e-5; their representable spacing was larger
than the residual update required at that row. A nearest-rounded update could
therefore reproduce the same infeasible point.

The controlled native probe compares the retained redistribution method with
one additional representable step in the direction of each coordinate update.
It certifies all five saved mathematical failures, with nonbasic values bitwise
unchanged. The comparison's source and each input snapshot are hashed. This is
point-only evidence: the reconstructed workspace's factorization is not used.

The integrated candidate retains the owned working-row scope correction and
joint interval construction from the previous experiment. Within each row it:

1. Fixes the correction direction toward the row target.
2. Forms the normalized squared norm using only basic coordinates that can
   still move in the required direction; zero normalized coefficients are skipped.
3. Adds the calculated correction, then takes `nextfloat` or `prevfloat` in its
   direction and clamps the result to the existing admissible coordinate interval.
4. Redistributes any part lost to clamping among the remaining movable coordinates.
   Each clipped pass saturates at least one previously movable coordinate, so
   `nnz(row)+1` bounds the inner loop. Reaching or crossing the target ends it.

The representable step is applied to every calculated update, not only updates
that round back to the original coordinate. It is a one-step reserve beyond the
nearest-rounded result, not an exact directed rounding of the mathematical sum.
A narrow feasible intersection can still be missed; the unchanged complete
certificate determines acceptance. Finite-input overflow and nonfinite projected
values abort and restore the full point.

The outer budget remains eight sweeps. Coordinate movement is still limited to
`8*max(tolerance, eps(T)*max(1,abs(anchor_value)))`, including basic row activities.
The inner passes increase work relative to the old single clipped projection.
Cancellation is checked between inner passes and during coordinate loops.
Basis metadata, nonbasic values, tolerances, costs and journals remain fixed.
Cache publication happens only after certification and the final stop check.

## Initial validation

A three-row fixture reduced from the failing row fails four of sixteen assertions
with the old redistribution method, all in Float64; the Float32 case already
passes. The new method passes all sixteen. The checks include independent rational
row residuals, structural bounds, unchanged nonbasic values, locality and the
published basic solution. Expanded cases mirror the bounds/directions and retain
an explicitly stored zero coefficient to check that its coordinate is untouched.

The initial focused run passes 246 assertions (230 existing plus the first sixteen
new ones). The integrated candidate, which also fixes the inner correction direction
and skips zero coefficients, separately passes 25 checks on all five mathematical
snapshots and 14 checks on both stored actual pivots. These results do not establish
convergence or a complete feasibility decision procedure.

## Fresh runtime result and the locality limit

The first complete run uses the integrated candidate with source digest
`89fbd0957df4f969f6056b6892a7990b5117c044520929b3db41f3a30e3f2848`.
It fails at iteration 14,186 after 272.4555 seconds: NUMERICAL_ERROR,
3,182 refactorizations and 98,997 rejected pivots. The last working auxiliary
objective 588956.4876 is an uncertified terminal observation. The requested
budget is 300 seconds; the memory guard does not terminate the run.

All 46 projections that reach the attempt counter are certified, but the last
recovery returns before that counter. This must not be described as complete
recovery success. The diagnostic trace rejects at interval construction, before
any projection sweep, and restores the original point.

Eighteen basic variables violate their stored bounds; no nonbasic variable does.
Eight basic coordinates have no overlap between their admissible bound interval
and the allowed locality interval. For example, x7930 needs a minimum correction
of 2.586e-6, while x28723 needs 1.516e-5 (about 19 times the radius and 152 times
the primal tolerance). Their allowed radius is 8e-7. The stored row equations
still pass. These observations prove that the current local box cannot contain
a point satisfying even the stored bounds; they do not prove the full fixed-basis
feasibility problem infeasible, or explain the larger reconstruction error.

No production radius increase follows from that observation. A targeted second
run captures the point before the failing pivot, the selected ratio, prediction,
reconstruction, midpoint and native residual correction for comparison.

## Captured pivot and the recovery anchor

The targeted run reproduces the same iteration, ordered basis and failed point.
The pivot enters x7288, leaves x2270, has zero step and pivot 1.686738184. The
pre-pivot maintained point passes the complete certificate. Instrumentation also
shows an already bound-infeasible reconstruction at iteration 14,185, before this
pivot; restoring its prediction succeeds. The large reconstructed bound errors
therefore precede this particular strong, zero-step pivot. This does not explain
the effects of the earlier numerical history or establish the origin of those errors.

After the pivot, prediction still satisfies every stored bound. It fails two row
checks: row 24,531 has an equation error 1.0000000000000005e-7, while row 28,453
has error 1.432215287280056e-7 and exceeds its model bound by 4.32215287280056e-8.
The reconstructed point differs from the maintained pre-pivot point by as much as
4.9007e-5. Its native residual correction does not remove the bound errors.

A controlled probe keeps the recovery algorithm, radius and eight-sweep budget
unchanged and supplies each captured point as its starting point. Reconstruction,
midpoint and native correction fail. Starting from prediction succeeds with a
maximum adjustment of 4.8296e-8 and unchanged nonbasic values. The resulting point
is still about 4.9007e-5 from reconstruction. This supports changing the locality
anchor, not inflating its radius. A prepared radius-inflation probe is not executed
or promoted; it is retained only among local working notes.

The revised candidate saves the prediction after the existing restoration fails,
before native residual correction overwrites the aliased trial buffer. Joint
recovery keeps reconstruction as its default anchor. Only when a basic stored-bound
interval has no overlap with reconstruction's locality interval does it select the
saved prediction. The prediction supplies basic values only; nonbasic values remain
those of the current workspace. All intervals and movement limits are then built
around the selected anchor. There is still one recovery with eight outer sweeps.
The radius has the same formula relative to that anchor; distance from reconstruction
is no longer bounded by its old radius when prediction is selected.

Workspace mutation starts inside the existing protected trial. Any failed,
cancelled or exceptional trial restores the original reconstruction, not the
prediction anchor, and leaves the previous row-solution cache intact. The unchanged
complete certificate and final stop check still precede publication.

A two-row regression has a remote bound-infeasible reconstruction, an aliased
prediction buffer and a nearby admissible prediction. Before the anchor change,
12 assertions pass and eight fail; afterward all twenty pass. Expanded tests cover
both floating types, opposite movement directions, explicit zero coefficients,
unreachable and invalid anchors, stop/throw after anchor mutation, and keeping the
reconstruction anchor when its local bound intervals are nonempty. All 378 focused
assertions pass. The revised integrated code also passes 25 mathematical-point
checks, the previous 14 pivot checks and eight checks of the newly captured pivot.


## Final bounded run and regression scope

The revised production source digest is
`1abe1ec7943e8736581d61b5f4b7a04ac5d1c5184148df0f7d7adad4be41d73c`.
A fresh 300-second runtime run reaches TIME_LIMIT at iteration 14,845, after
3,209 refactorizations and 99,204 rejected pivots. All 50 attempted projections
are certified. It passes the captured failure at 14,186 and continues for another
659 iterations without a numerical error. Phase I remains unfinished.

The last sampled completed pivot, at iteration 14,000, has auxiliary objective
589324.09259 and zero recorded primal infeasibility. The workspace observed at
termination has auxiliary objective 586361.32402 and primal infeasibility
3.17547e-5 over 17 coordinates; the report explicitly labels it
`uncertified_after_termination`. That interrupted workspace is not a certified
solution or an achieved feasible objective bound.

Only adaptive pricing and perturbations are enabled, with their shared stalling
monitor; all other adaptive functions and the original-LP retry are disabled.
There is one perturbation and nine closed pricing trials, including seven
productive returns. The intervention validators find no overlap. The change is
a numerical point recovery in the core; adaptive scheduling and intervention
policies are unchanged. No precision-boost event occurs. Arithmetic updates stay
in the task precision, while the existing complete certificate retains its exact
fallback for inconclusive row enclosures.

The wider semantic runner passes 6,876 assertions with `--compile=min`.
The normal-compilation runner passes 888 assertions, including allocation checks
and the registered project tests. These counts overlap the focused checks and
must not be added as independent coverage. This is not a full project-suite pass.
The two new project test files register the 378 joint-recovery assertions and
181 owned-working-row assertions for future suite runs.

The remaining primal degeneracy and eventual convergence are unresolved. This
run demonstrates progress past captured numerical barriers, not a general
anti-cycling result. There is no new medium continuation in this investigation;
the preceding 300-second medium run never entered joint recovery, and the older
full medium snapshot could not be deserialized in the current environment.

## Disposition and external regression

The established external matrix completes all 80 solves (245 assertions): afiro,
adlittle, pk1, flugpl and fast0507, both simplex methods, four basis managers and
native/Markowitz factorizations. Every solve reaches OPTIMAL, matches its reference
objective and passes the independent original-primal feasibility check. The wrapper
records the complete measured source digest before and after the matrix.

The bounded native recovery and owned working-row scope correction are accepted
on the development branch. No adaptive-policy change is included. The earlier
reconstruction-only anchor patch remains a rejected diagnostic checkpoint.

## Reproduction and provenance

Run Julia payloads sequentially through the existing memory guard, using one Julia
thread and one BLAS thread. Use a fresh output path for each external or model run.
The final candidate is integrated in production; no diagnostic patch is required.

```sh
julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/representable_point_semantics.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/representable_point_compiled.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/representable_point_replay.jl /tmp/representable-replay-new.toml
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl runtime primal both 300 /tmp/runtime-representable-new
julia --project=. diagnostics/adaptive-degeneracy/reproduce/representable_external.jl diagnostics/basis-selective-preparation/reproduce/external-inputs.toml /tmp/representable-external-new.toml
python3 diagnostics/adaptive-degeneracy/reproduce/validate_representable_point.py
```

Use guard wall budgets of 540 seconds for the runtime payload and 600 seconds for
the external matrix, including compilation. Replay needs the retained local binary
snapshots; the portable project fixtures do not. Full logs, snapshots and probe
sources are kept in `.superpowers/adaptive-degeneracy/representable-point/` and
hashed in the committed local artifact manifest. Text results are in
[results/representable-point](results/representable-point/).

`representable-reconstruction.patch` reproduces the first, rejected anchor choice
from commit `0a75727`; apply it only in a separate copy of that baseline. The capture
and initial failure inspectors refer to that measured source, not the final
prediction-anchor implementation. The provenance validator reconstructs the patch
in a temporary directory and checks both measured source digests. Earlier reports
and their baseline-specific validators describe rejected historical candidates.

## Longer-run follow-up

The [extended runtime diagnostic](extended-runtime.md) continues past this bounded
300-second result. It records further objective reduction and a new numerical
point-certification failure at iteration 19,222. The current recovery remains
bounded and incomplete; passing the earlier captured pivots did not eliminate
all later numerical barriers.
