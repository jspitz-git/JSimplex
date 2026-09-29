# Phase-I stagnation: bound snapping and candidate geometry

The results and decisions below describe the recorded historical revision. See
[the native pivot-probe follow-up](NATIVE-PIVOT-PROBE.md) for the later core fix,
its certified runtime runs, and the remaining bound-snap obstruction.
The [point-recovery follow-up](POINT-RECOVERY.md) addresses a subsequently found
error path when both reconstruction and predicted-point preservation fail.

Base: `b29e10efc1bf1f0c02412a69edd13b80b4e9f9c1`.
This investigation uses the saved PFI endpoint from the direction-price work.
This initial investigation made no production solver change. The experimental intervention below
is diagnostic and is not a proposed convergence fix.

## Controlled starting point

Input: `/home/jspitz/mps/runtime.mps`, SHA-256
`d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`.
The local snapshot is
`.worktrees/primal-direction-prices/.superpowers/primal-prices/early-guard-runtime-pfi.toml.1.time_limit.bin`
(relative to the primary checkout), SHA-256
`bb56b32796358582a9a98cabec500209acc8dde2c662fe8c24b6f93d84c9eeb1`.
It contains iteration 7,533, auxiliary objective 605519.5025248753,
28,453 rows, 34,186 explicit columns, and 2,460 basic artificial variables.

These are reference continuations: they refresh the native basis factor, preserve
a certified feasible saved point when reconstruction is infeasible, and rebuild
DSE weights. They do not restore the original pricing cache or factor updates.

## Evidence at the original endpoint

After fresh native factorization and fresh DSE weights, selected column 21,276
has cached price -7.892537433443076e10 and direction-implied price
-7.892537433443082e10. They pass the existing price consistency check.
Its direction infinity norm is 6.692106690107453e9.

The most restrictive Harris row is 13,598 (structural variable 15,754):

- Value: -9.866022685226112e-8, just inside the allowed 1e-7 violation.
- Direction component: 2.2969070259643742e8.
- Relaxed step limit: 5.832944618976723e-18.
- Exact snapping to the lower bound would require a negative step and is rejected
  by the existing feasibility check: it would induce a 1.3978785452653356e-6
  violation at variable 27,417, exceeding the 1e-7 tolerance.

Row 3,930 is similarly blocked. The ratio test instead chooses a zero step at
row 17,022, with pivot 38.911895713434504 (relative pivot about 5.81e-9).
The same blocking rows recur among the 32 highest freshly computed DSE scores.
One compensated native residual correction changes the direction by only
2.89e-4 in infinity norm and leaves the zero-step choice unchanged.
This supports a local bound-snap/degeneracy obstruction. Neither rebuilding
weights nor applying this native correction removes the measured zero-step
choice; these probes do not establish independent forward accuracy.

An unchanged-code 32-step continuation makes 6,244 candidate rejections and
33 refactorizations (including its initial refresh). The objective changes by
only about 4e-9; the final phase-model primal point is independently certified.
This is a targeted reproduction, not a new full runtime solve.

A separate inspection of the saved Suhl–Suhl endpoint finds the same limiting
structural variables 15,754 and 23,386. Selected column 21,414 has a direction
norm 158713.90; snapping the first limiter induces a 3.3237e-7 violation at
variable 55,155. Its raw ratio proposal instead uses a zero step and a
1.9234e-13 pivot. This is a ratio proposal, not an accepted pivot. The endpoint
passes phase-primal, stored-row and all-bound checks before and after refresh.
This is evidence that the local obstruction is shared by these two snapshots;
it is not a convergence result for SS or either other manager.

## Diagnostic intervention

The existing legacy path retains a tolerated out-of-bound nonbasic row activity
instead of snapping it exactly to its bound. The `preserve_structural` mode in
`reproduce/continuation.jl` temporarily extends that rule to nonfixed explicit
phase-model columns (including artificial columns) within their original bound
tolerance. It leaves the existing row behavior, model bounds, tolerances, costs,
and arithmetic type unchanged.
The override exists only inside the diagnostic Julia process. Its implementation
is shared with the inspector in `reproduce/intervention.jl`.

An earlier exploratory variant also disabled retention for fixed row activities;
that confounded trial is not used as the controlled comparison. It left the
original plateau but stalled again near 605504.70. The controlled experiment
preserves the existing fixed-row behavior.

## Controlled continuation results

The revised runner follows production's finite/basic-feasibility checks before
every iteration. Endpoint checks additionally cover every variable bound,
phase-model primal feasibility, and equality between matrix activities and the
stored row-activity variables used by the ratio test.

| Mode | Completed steps | Refactorizations | Rejections | Auxiliary objective |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 32 | 33 | 6,244 | 605519.5025248714 |
| Preserve explicit nonfixed values | 1,200 | 73 | 1,757 | 605142.6843376105 |

Both endpoints pass all those checks. The experimental endpoint has maximum
individual bound violation 9.974437078468954e-8 and 2,430 basic artificials.
The run is stopped at a completed-step boundary, before an interruption can
leave a partially recomputed point. Timing is not a controlled performance test.

A preceding 300-second continuation of the same intervention reaches 2,144
steps, 1,017 refactorizations, 131,182 rejections and objective 605141.4672630595.
It again stagnates. Its final explicit phase primal point is certified, but that
earlier runner omitted the production pre-iteration checks and the separate
stored-row consistency check, so this long run is supporting exploratory
evidence rather than the primary controlled comparison.

Inspecting the certified 1,200-step endpoint with the same intervention and
fresh factor/weights moves its point by at most 1.40e-12 and retains all
certificates. It selects column 46,118 with direction norm 88.13735, price
-761.846829, and a positive ratio step 2.05490844675115e-6. This establishes a
positive ratio-test candidate after that refresh, not why the preceding trajectory
was spending so much work on retries; subsequent pivot acceptance checks were
not run on that isolated proposal. A live trace of the controlled trajectory's
last 150 accepted pivots finds 120 exactly zero steps and a maximum stored/actual
DSE weight ratio of 1.00012013. It reproduces the same final objective and counts.
These observations concern accepted pivots only; they do not rule out bad scores
or prices among rejected or unselected alternatives. The original bound-snap
obstruction is therefore an actionable local mechanism, not a complete explanation or remedy
for every later plateau.

## Verification and current decision

- 1,498 focused assertions passed with `--compile=min` on unchanged production
  source. This is not a full project-suite run.
- Normal compilation was stopped after over four CPU minutes; its termination
  stack is in LLVM SimplifyCFG while compiling
  `test/legacy_primal_point_tests.jl:85`. No test failure was established by that
  interruption. No allocation claim is inferred from interpreted tests.
- Independent read-only review identified missing trajectory/certificate checks
  and experiment-mode mismatch in the initial instrumentation. The corrected
  controls and matching-mode inspections were rerun. Residual probes now guard
  unavailable/nonfinite quality results.
- No production change is being proposed from this investigation. The process-only
  intervention changes nonbasic-value semantics and has not completed phase I.
  It would need dedicated regressions and full original-LP validation before
  adoption, including artificial-variable and final-certificate behavior.

The initial next diagnostic target was the rejection surge after roughly 1,140 steps of
the controlled intervention, including rejected candidates and retained pricing
state. The current accepted-pivot trace and freshly rebuilt inspector cannot
attribute that surge to stale weights or a specific rejection cause.

The follow-up [rejection-surge investigation](REJECTION-SURGE.md) identifies
a finite-residual gate as the local cause and records why removing it globally
was rejected after a fresh runtime regression. That investigation left production source unchanged.
The subsequent [equation-loss investigation](EQUATION-LOSS.md) locates the first
inconsistent reconstructed point and documents a narrow preservation fix.

## Reproduction and limits

Use Julia 1.13.0 on aarch64, one Julia and BLAS thread, the existing 8 GiB virtual
memory limit, and the owned-process guard requiring at least 6 GiB available RAM
and at most 1 GiB swap use. Keep `precompile_workload = false` locally. Run only
one numerical Julia process at a time. Local manifests, preferences and binary
snapshots are not source fixtures.

From this worktree, invoke these scripts through that guarded Julia wrapper:

```sh
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/inspect-candidates.jl SNAPSHOT baseline
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/continuation.jl SNAPSHOT baseline 120 32 OUTPUT.toml
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/continuation.jl SNAPSHOT preserve_structural 300 1200 OUTPUT.toml
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/trace-pricing.jl SNAPSHOT preserve_structural 1200 180
```

The primary TOML reports record both production and diagnostic source hashes.
The preliminary 300-second report is explicitly labeled exploratory; its original
runner is retained locally at `.superpowers/phase1/continuation-v1.jl` and lacks
the later instrumentation guards. Its endpoint snapshot is retained locally as
`.superpowers/phase1/pfi-preserve.toml.bin`.

Each continuation saves a local endpoint as `OUTPUT.toml.bin`. When inspecting an
experimental endpoint, pass `preserve_structural` as the inspector's second
argument. Both tools log before/after restoration certificates and point changes;
they refuse an uncertified restored point. A compensated correction is reported
only when the native residual probe returns a finite result. Matching prices and
a small correction do not independently certify forward accuracy of an
ill-conditioned basis. Time-limit endpoints can be interrupted
inside recomputation, so their final feasibility certificate must be inspected.
Neither an improving auxiliary objective nor a time limit without an error
establishes feasibility of the original LP or convergence.
