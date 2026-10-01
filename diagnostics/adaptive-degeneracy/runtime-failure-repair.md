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
