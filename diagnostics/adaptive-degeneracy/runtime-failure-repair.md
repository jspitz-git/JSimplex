# Diagnosing failures in the full runtime reader/method matrix

Base: `e1af30b` (`b8955ac` production source). The input, isolated adaptive
profile and all four original outcomes are recorded in `runtime-reader-full.md`.
This investigation preserves native arithmetic in solver repairs and keeps
heuristic activation separate from numerical correctness.

## Dual feasibility loss with an active perturbation journal

Both detached final dual workspaces have a fresh factorization, `perturbed=true`
and an active cost journal. The sole failing nonbasic variable is at its lower
bound. Independent 256-bit diagnostic prices confirm the sign/tolerance failure:

| Reader | Variable | Stored price | Diagnostic price | Working cost |
| --- | ---: | ---: | ---: | ---: |
| Native | 12652 | -1.0000024985856726e-7 | -1.0000012079226497e-7 | 2.0000000142108546e-6 |
| JuMP | 23461 | -1.000000000000001e-7 | -1.000000000000001e-7 | 1.2999999999999998e-6 |

The tolerance is 1e-7. Thus recomputing prices more accurately cannot alone
recover dual feasibility. `_shift_marginal_dual_prices!` already handles small
working-cost drift in native arithmetic, but excludes *every* active journal.
This conflicts with the perturbation journal's explicit owned-buffer contract:
later pivots and repairs are supposed to update the same active working costs.

The repair admits only an active cost journal owned by this workspace whose
active buffer is exactly the workspace cost vector. It retains the existing
per-repair bound and representability margin and also enforces the journal's
512-tolerance total displacement cap. Original saved costs, perturbation levels
and the user's feasibility tolerance are unchanged. Bound-only, foreign or
detached active journals remain ineligible. Original-cost cleanup continues to
exclude new working-cost shifts.

Independent small regressions use the real perturbation API before introducing
a marginal working-price loss. The pre-fix run has 36 passes and 8 failures;
Float32 cannot repair the price, while Float64 enters higher-precision recovery.
After the repair, the existing and new price tests pass 249 checks, including
exact restoration, fresh recomputation, both bound orientations, cancellation,
unsafe displacement and ownership rejection.

## JuMP phase-I export reconstruction

The captured local-reconstruction candidate has seven failing relative residual
checks. Its tiny coupled coordinates are around 1e-26, with nonzero right-hand
sides down to 1e-44. The existing homogeneous-component proposal changes 18
coordinates but cannot preserve those nonzero equations; the final certificate
correctly rejects it. The failure is not permission to erase small input data or
relax residual tests.

A diagnostic connected block contains 29 small coordinates and 27 internal
rows. Including all 100 incident rows in an ordinary least-squares solve imports
larger boundary residuals and corrupts the tiny interior equations. Restricting
the proposal to internal equations avoids that contamination; boundary equations
remain mandatory in the full-system certificate. Native column-pivoted QR,
three compensated native corrections, and the existing local reconstruction
then pass that full certificate. These probes are diagnostic only; production
integration and regression coverage are recorded below when completed.

## Dual repair verification

Production SHA-256 after the journal repair:
`5fb3401023e5efc388d15583995565a04f6993062e998df0b625d17e8dd2cbd8`.
The fresh native dual solve now reaches verified `OPTIMAL` at **62,200 iterations**,
**787 refactorizations**, and **262.848422856 seconds**, with objective
**51425691.762104526**. Both original/reader primal checks and objective agreement
pass; no original-LP retry occurs. Complete observational records are retained
in `results/runtime-failure-repair/native-dual.toml`. Its console stream was not
retained in full; the TOML contains all observer records.

The separate adaptive interaction suite passes **3,289 checks** with
`--compile=min`, covering pricing, stalling, both perturbations and handoff
atomicity. Independent read-only review found no actionable defect in the price
repair. No full-project pass is claimed; broader validation follows the second
repair. All Julia runs are serial and use the established memory guard.

The fresh JuMP dual solve also reaches verified `OPTIMAL`: **61,775 iterations**,
**786 refactorizations**, **255.769808547 seconds**, objective
**51425691.76210435**. Neither full dual run attempts an original-LP retry.

## Coupled reconstruction implementation and targeted verification

After the existing local sweeps and homogeneous proposal fail, reconstruction
can propose a small block solve in Float32/Float64. It follows only rows whose
active coordinates are below the existing correction-derived cutoff and limits
the proposal to **64 columns and 128 internal rows**. These are computational
bounds, not model-specific accuracy thresholds. Rows connecting to larger
coordinates are excluded from the solve but retained in the final certificate.

The block uses row-normalized column-pivoted QR and at most `max_refinements`
compensated corrections, all in the original scalar type. One final scalar
reconstruction call disables recursive block recovery. Both pre- and post-local
changes must fit the original cutoff. The unchanged full-system residual check,
phase-export primal/bound checks and original-model certificate still decide
acceptance. No precision increase, tolerance widening, pricing switch or new
adaptive trigger is introduced. Stop requests are latched across proposals,
including a one-shot cancellation after tentative homogeneous clearing.

The new two-equation example fails before repair in both Float32 and Float64
(20 passes, 2 failures). The final focused set passes **483 checks**, including
row/column permutations, row/column scaling, inconsistent/oversized blocks,
late cancellation, exceptions, original transfer tests and cleanup regressions.
Existing negative tests specific to homogeneous-only recovery now explicitly
use `coupled=false`; their rejection assertions are retained.

Two new test-fixture expectations needed correction without production changes:
the initial inconsistent system differed by less than its relative residual
allowance; its inconsistency was raised to the scale of its terms. A later
absolute-residual bound omitted the matrix row scale; it now derives that bound
from the coefficient norm, while retaining the explicit known-solution checks.
Both intermediate logs are preserved. Independent read-only review found no
remaining actionable issue after the one-shot cancellation concern was fixed.

The unmodified detached-export replay passes **19 checks** on the real JuMP
failure state at iteration 86,607. Before recovery the primal and dual basis
solves fail their residual checks; afterward both pass. Original primal
feasibility and all rollback/cancellation checks pass. Maximum primal change is
**4.656612873077393e-10**; no saved nonbasic coordinate changes. This is an export
replay, not an outer-driver continuation or a convergence claim.

The fresh whole-MPS JuMP primal verification reaches the same export boundary
at iteration **86,607**, successfully starts phase II, and matches all **84**
shared phase-I objective samples exactly. Its subsequent original-model cleanup
is still running at this checkpoint; this commit establishes the repaired export,
not the final solve outcome. Later validation below records the completed run.

## Later original-model cleanup failure

The completed JuMP/primal run with the first two repairs reached phase II and
then the original-model cleanup, but returned `NUMERICAL_ERROR` at **165,969
iterations**, after **1270.607121923 seconds**. The reason was `bounded pivot
validation and basis recovery attempts exhausted`. This supersedes the running
checkpoint above; repairing the original export did not finish this solve.
The full trace and report are `results/runtime-failure-repair/jump-primal.*`.

A detached observed cleanup workspace reproduces the rejection after a fresh
native factorization. It is not an outer-driver checkpoint. At leaving row
23,224 / entering column 18,805, the uncorrected FTRAN and BTRAN pivots differ
by about 3.58e-12, exceeding their existing strict 1.11e-13 agreement allowance.
A native compensated-residual correction brings FTRAN to the independently
computed 256-bit reference, -7.420996551845639e-6. Rounding the BTRAN correction
into the large row entries first loses the information required to recover
this small coefficient. Compensating the dot product of that already-rounded
row alone is insufficient. Pricing the row and its correction separately with
compensated FMA products recovers the reference coefficient in Float64.
A second independent pivot (row 12,418 / column 17,609) shows the same mechanism.
The higher-precision calculations occur only in the diagnostic probe.

The bounded recovery therefore retains the two terms while pricing. It runs
only in an existing transactional retry with fresh factors, after the original
strict pivot comparison failed. It corrects FTRAN in native arithmetic, keeps
the strict comparison, and repeats the ratio test. Both the selected entering
variable and pending bound flips must remain identical. Rejection restores the
scratch row and flips; acceptance invalidates the affected solve caches and
rechecks steepest-edge weights. Existing factor provenance checks prevent an
old prepared update from being reused for a changed direction.

The independent two-row regression failed before the repair (4 passes,
12 failures). The expanded focused set passes **361 checks**, covering all four
basis managers, factor solves after the update, singular duplicate columns,
bounded exhaustion, changed flips, cancellation and callback exceptions. A
short replay of the actual observed workspace advances from iteration 165,969
to 165,970 instead of exhausting recovery. These checks establish the repaired
pivot mechanism, not whole-problem convergence. The completed validations below
record the subsequent result. Independent read-only review found no actionable
implementation defect; its requested atomicity tests were added.

The separate `runtime_cleanup_replay.jl` attempt to re-enter the complete dual
driver from the same detached observation returns `bounded feasibility recovery
exhausted` before advancing. This observation can be a speculative candidate and
lacks an outer-driver checkpoint; the result does not establish continuation of
the original solve. Fresh whole-MPS verification is required. The first replay
script attempt had a diagnostic context type mismatch before any solver call;
its corrected construction and both logs are retained. Likewise, an initial
fresh-run launcher attempt stopped at the source-hash assertion before solving:
Python path-component sorting differed from Julia string sorting. The launcher
now uses the identical string order. Neither diagnostic correction changes the
solver source.

## Fresh whole-MPS verification of all three repairs

Production SHA-256:
`647b74f10277b7b01d6f9589b16d519c7c037a0ed0a784c9d165ae5e38a88ccc`.
The fresh JuMP/primal run reaches verified `OPTIMAL` at **174,385 iterations**,
**2,189 refactorizations**, and **1426.008775741 seconds**, with objective
**51425691.76210436**. Reader and original-model primal checks and reference
objective agreement all pass. The coupled phase reconstruction is attempted
and certified once; there is no outer original-LP retry. Pivot rejections are
20, compared with 455 in the preceding failed full run; the trajectories differ,
so this is not a paired kernel timing comparison. The fresh log first differs
from the preceding run's sampled objective around iteration 129,000.
`final-jump-primal.log` and `.toml` preserve the complete observation record.

The final-source native dual run returns verified `OPTIMAL` at **61,387 iterations**, **775 refactorizations**, and **273.347902658 seconds** (objective **51425691.762099**). JuMP dual returns verified `OPTIMAL` at **59,617 iterations**, **758 refactorizations**, and **263.339850860 seconds** (objective **51425691.76210435**). Both retain the original feasibility and reference-objective checks and make no outer original-LP retry. These are fresh whole-MPS solves under the same isolated adaptive profile.

Independent verification in a new process evaluates the stored Float64 model and returned points as exact `Rational{BigInt}` values. All four points satisfy the original absolute primal tolerance of `1e-7`. The native-primal point is the already successful baseline run, **not a fourth fresh solve of the final source**; the other three are the fresh repaired runs.

| Reader | Requested method | Maximum exact row violation (shown as Float64) | Maximum exact column violation (shown as Float64) |
|---|---|---:|---:|
| native | dual | 6.67058823343e-08 | 9.19732619977e-08 |
| jump | dual | 8.79120688694e-09 | 2.12478101502e-12 |
| jump | primal | 1.09835564826e-10 | 0 |
| native | primal | 9.10184136472e-09 | 3.32376833688e-12 |

`exact-verification.toml` retains the exact rational violations and objectives. Higher precision here is independent diagnosis only. The solver repairs retain the original scalar type, original tolerances and final certificates.

## Regression validation

The focused reconstruction/tableau tests pass **124 checks with normal
compilation**, including Float32/Float64 arithmetic and all four basis managers.
The wider semantic runner passes **16,279 checks with `--compile=min`** in
195.3 seconds. It includes phase transfers, native recovery, pivot consistency,
pricing/perturbation interactions, rollback and cancellation, presolve and
terminal certificates. The eight split-pricing checks added after the original
361-check focused run are included in both final runners.

This is not a full-project pass. The previously established full-suite failures
and compiler timeout remain documented in
[simplex-infeasibility-tolerance.md](simplex-infeasibility-tolerance.md#main-suite-pre-existing-legacy-test-failures).
The unchanged failing primal fixture tests and known LLVM timeout were not
repeated here; validation targets the modified paths and the broader semantic
suite instead. `runtime_failure_validate.py` retains an explicit `full-suite`
option for reproduction but it is not part of the completed checks above.

Fresh solves are reproduced serially with:

```sh
python3 diagnostics/adaptive-degeneracy/reproduce/runtime_failure_full.py jump-primal native-dual jump-dual
```

The runner refuses to overwrite existing output prefixes, enforces an unchanged
source digest and stops on a non-passing solve. The completed final validation
uses:

```sh
python3 diagnostics/adaptive-degeneracy/reproduce/runtime_failure_validate.py exact-verification compiled semantics models
```

Both launchers use the existing memory guard and a single Julia/BLAS thread.
Local snapshots remain under `.superpowers/adaptive-degeneracy/runtime-failure-repair/`;
no old worktree or depot was removed, and local manifests/preferences are not
part of the commits.

The external suite passes **104/104 cases on 33 distinct models**: 76 dual and
28 primal solves, 48 native reads, 42 JuMP reads and 14 explicit permutations.
Every case reaches the reference optimum and passes both reader and original
primal checks. Inputs, reference values and isolated numerical-policy settings
match the prior suite. All iteration counts, refactorizations, objectives,
phase records, pivot observations and zero-step counts are unchanged. Of all
compared fields, only `pilotnov/native/dual/pfi` differs: correction attempts
increase from 251 to 259, without changing its accepted trajectory statistics.
103 cases match every compared field, including event counts. The coupled
fallback is attempted once and accepts no block in this external corpus; the
runtime export and portable small-system tests provide its positive coverage.
The result is a non-regression check, not a claim of robustness on every LP.

`models-comparison.json` records the full comparison. Diagnostic instrumentation
hashes differ because the phase probe now recognizes the new bounded block
fallback; they are recorded explicitly rather than assumed identical.
`validation-processes.json` records the guarded commands and successful exits.
`artifacts.json` records source, reproduction and local snapshot hashes.
