# Local row reconstruction at the runtime phase boundary

This follows [the native residual diagnosis](phase-transfer-residuals.md).
The approved experiment tests whether direct reconstruction of the offending
local equations can preserve tiny nonzero right-hand sides and pass the existing
full-system checks. It is an experimental diagnostic candidate, not a production
solver change.

## Candidate and controlled setup

The source baseline is `d14c8b7`, production SHA-256
`d338c92dd9e92c5064c4621291796bf3808341aa7d56668ff931d34452dcc6d4`.
The same runtime snapshot at iteration 102,446 is used, SHA-256
`70797028c15c9c33f98259dbe17bd2001996ba9c2ff35d35a85de008a7fff7c7`.
Input provenance and the isolated adaptive policy are unchanged from the
[original boundary capture](phase-transfer-capture.md). Its long prefix is not
rerun. The replay has no outer-driver continuation or new adaptive intervention.

After reconstructing the workspace with its maintained nonbasic values, the
candidate performs the already tested single native primal correction. Instead
of broadly clearing tiny values, it then makes at most eight local sweeps:

1. Compute compensated residuals and componentwise scales for the whole basis
   system using the unchanged numerical policy.
2. In each offending equation, select the coordinate with the largest current
   absolute product. If all products are zero, use the largest coefficient.
3. Recompute that coordinate directly as `(rhs - sum(other terms)) / coefficient`,
   with FMA product residuals and compensated summation in Float64. Retain the
   actual right-hand side, including tiny nonzero values.
4. Apply only a finite update whose individual magnitude is at most
   `solve_tolerance * maximum(abs, native_correction)`.
5. Recheck the whole system between sweeps. Accept only after the unchanged
   solve-quality check passes; the sweep budget is not an acceptance condition.

The actual per-update cutoff is 4.6721294222177306e-21. It limits individual
updates, not their accumulated movement. Nonbasic coordinates, right-hand sides,
coefficients and tolerances remain unchanged. This is not a general guarantee
that the coordinate-selection rule converges.

The dual vector uses the existing `_native_cleanup_solve!` correction and
cleanup. Reduced costs are recomputed from it. The candidate must pass both
basis-solve quality checks, the full stored-point certificate and reduced
original-model primal feasibility before it can support an export result.

## Actual endpoint result

The local primal reconstruction takes **two sweeps**: 13 offending equations
before the first sweep and five before the second. It changes **18 distinct
basic-vector coordinates**, with maximum individual change
**1.1771283820094786e-30** after the ordinary correction. This figure does not
include the preceding ordinary correction, whose maximum was 8.219297001924415e-8.

For example, coordinate 16223 is recomputed from -1.1771283820094786e-30 to
-7.713801763061988e-74, balancing the other tiny term in homogeneous equation
4071. Equation 4933 keeps its nonzero right-hand side: its selected coordinate
changes from 9.115745035929407e-64 to 6.134681900140016e-64. Coordinate indices
refer to positions in the basic solution vector; equation indices refer to the
reduced workspace. They are not original MPS variable or row numbers.

| Check | Result |
| --- | --- |
| Primal componentwise relative residual | 3.639664073340952e-14; passes |
| Dual componentwise relative residual | 9.884630649085414e-17; passes |
| Unchanged solve tolerance | 5.684341886080802e-14 |
| Stored primal infeasibility | zero |
| Full stored-point certificate | passes |
| Reduced original-model primal feasibility | passes |
| Nonbasic values | bitwise unchanged during local recovery |

The primal and dual absolute residual maxima remain 2.4651904542252663e-10 and
1.2011557070673514e-7 respectively. Solve-quality acceptance is componentwise;
the dual absolute maximum alone must not be compared to the primal feasibility
tolerance. The cost dot product is 61,547,897.97008232, not an optimum claim.

## Complete export and rejection controls

A hashed process-local variant of `_remove_artificials!` supplies the mapped
point before the existing refactorization, then calls this experimental local
recovery. All original finite-state, basis-reliability, primal-feasibility and
original-model checks remain. Pricing inheritance, adoption and reset are also
unchanged.

The **complete export returns true**. Its primal vector is bitwise identical to
the independently reconstructed candidate, both residual checks and both primal
certificates pass, and effective pricing remains `steepest_edge`.

The same export with a zero local-sweep budget returns false, leaving the original
workspace's primal vector and basis indices unchanged. Consumed work is retained
by the normal wrapper. The incomplete candidate is not published.

A portable triangular system provides two additional controls. For
`B = [1 1; 0 1]`, `rhs = [0, 1e-66]` and initial point `[1e-30, 1e-66]`, the
method reconstructs `[-1e-66, 1e-66]` and passes the unchanged residual check.
Starting instead from `[0, 1e-66]`, the chosen coordinate alternates between the
two conflicting row repairs. The eight-sweep cap is reached and the quality
check still rejects. This counterexample explicitly limits the convergence claim
and demonstrates why the candidate must remain bounded and fully certified.

## Scope and production requirements

The experiment establishes successful export of this captured runtime endpoint.
It does **not** run the Phase-II driver, certify a postsolved original-input
solution, establish whole-solve convergence or cover all basis managers.
No production file is modified or reliability guard removed.

The diagnostic helper must not be copied directly into a general recovery API:

- It is specifically written for Float64. Production needs explicit supported
  type and numerical-policy guards.
- Sweep and row loops need the caller's cancellation/time-limit callback.
- An unavailable native residual currently asserts in the probe. Production
  must reject conservatively rather than treat ambiguity as acceptance.
- Completion writes to the private fresh workspace before its final certificate.
  Failure is safe here because export discards that workspace, but the helper
  alone does not provide transactional rollback for an arbitrary caller.
- Per-update and sweep limits are explicit; a general accumulated-movement
  guarantee is not established. The portable cycle remains a valid failure case.

The next bounded implementation should integrate guarded recovery into phase
export, preserve rejection and original-workspace ownership, add appropriate
portable regressions, and validate a fresh runtime solve through the real driver.
It should not change adaptive pricing or perturbation scheduling.

## Reproduction and retained evidence

Julia 1.13.0/aarch64 uses one Julia thread and one BLAS thread, with sequential
numerical processes. The existing guard imposes an 8-GiB virtual-memory limit,
a 6-GiB available-RAM floor, a 1-GiB swap ceiling and a 360-second outer wall
limit. All correction, row reconstruction and factor solves use Float64.

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/probe_phase_transfer_local_rows.jl .superpowers/adaptive-degeneracy/phase-transfer/runtime-transfer-capture /tmp/runtime-local-export
python3 diagnostics/adaptive-degeneracy/reproduce/validate_phase_transfer_local_rows.py
```

The final normal-compilation run passes **16 assertions** (testset time 5.9s).
These cover the actual point and complete export, retained nonbasic values,
bitwise agreement, safe zero-budget rejection and portable success/failure cases.
The evidence validator checks source/helper/snapshot hashes and all reported
outcomes. Earlier boundary and residual validators also pass on unchanged sources.
No new whole-project or external-matrix regression result is claimed.

Text evidence is in [results/phase-transfer-local-rows](results/phase-transfer-local-rows/).
Candidate/export snapshots, the injected method, log and exact as-run scripts
remain in `.superpowers/adaptive-degeneracy/phase-transfer-local-rows/`, with
hashes in the committed manifest. The original capture remains in its prior
location.
