# Owned working bounds in primal zero-step row preservation

Baseline: `aa73565`. This investigation follows the small-pivot rejection counts
in [the preceding experiment](dual-cost-history.md). **Neither experimental patch
is retained in production.** Both pass focused regressions but expose subsequent
real-model numerical failures. Production sources and registered tests are restored
exactly to the baseline. The patches, candidate tests, captures and negative
results are preserved for further investigation. No merge or push was performed.

The experiments alter two numerical consistency checks in the native primal
kernel. They do not change adaptive scheduling, tolerances, precision, or the
dual progress heuristic.

The subsequent [coupled-point investigation](coupled-point-recovery.md) captures
the iteration-8,464 candidates and records another rejected recovery experiment.

## Captured cause

A 300-second baseline runtime primal run captures four ratio-test decisions
without changing their arithmetic or selection. It ends at TIME_LIMIT in Phase I,
with 7,721 iterations and 1,790 refactorizations. The final auxiliary objective is
600981.4776227123. These are uncertified working-LP observations.

At iteration 6,695, after the first owned bound perturbation at 6,656, the
Harris band contains row 16,106 with pivot -15.211407129663568. Its row-activity
variable 50,292 is at 1.2999999999999998e-6, the working upper bound is 1.2e-6,
and the primal tolerance is 1e-7. A zero step is allowed by the working bounds.
The original upper bound is zero.

The working-point certificate already respects an owned active bound journal.
However, `_can_preserve_primal_row_value` still checks the original row bound.
It therefore refuses to preserve this tolerated row value. Exact snapping would
require a negative step and fails the snap-feasibility check. The ratio test
instead selects fixed row 1,445 with pivot -3.988916534395134e-16, which the
absolute pivot safeguard subsequently rejects.

Pure native ratio replay reproduces all four baseline selections exactly.
None of the four first passes exits early on a nonfinite ratio or excessive
bound violation. This audit matters because reconstructed Harris-band membership
alone does not prove that the production kernel reached the band, or that a
candidate passed snap and whole-point feasibility.

## First candidate: owned working-row bounds

The first candidate makes row-value preservation use the supplied working bound when the bound journal
is active and its workspace ownership is valid, matching the working-point
certificate. The hardware-precision, primal-algorithm, row-only and numerical
policy guards stay intact. The same primal tolerance applies. Absent or inactive
journals retain the original-bound check. Restoration disables the exception
before original-model cleanup. Structural variables remain excluded.

On the captured iteration 6,695, replay now selects row 16,106 with the strong
pivot and a zero step. The other three captured selections are unchanged:
iteration 5,745 before perturbation, the inconclusive ratio at 6,753, and the
tiny pivot at 7,000. At 7,000 the only stronger member of the Harris band is a
structural variable, deliberately outside this correction's scope. Pure replay
tests selection only; it does not factorize or apply the captured pivot.

## Regression evidence

A small real-pivot regression exercises both bound directions, Float32/Float64
and all four basis managers. Before the correction, 32 assertions fail and 16
subsequent nonbasic-value assertions error because the pivot never happened.
Afterward, all 181 assertions pass, including refactorization/recomputation,
restoration, excessive violation, structural exclusion and foreign ownership.
The fixture certifies only its perturbed working LP; it intentionally has no
original feasible solution and does not claim an original optimum.

The first combined semantic run had 19 failures caused by its include order:
the Phase-I interaction harness installs a process-local weak-pivot override,
then later policy tests expected the unmodified method. The final runner places
that harness last. No production change was made for this harness issue.

The row-scope-only semantic runner passes 6,498 assertions with `--compile=min`;
the separate normal-compilation runner passes 510 assertions including allocation
checks. This is necessary but insufficient evidence: the real model uncovers the
second issue below.

## Residual correction at a representable bound endpoint

The row-scope-only runtime experiment fails at iteration 6,799 after 44 seconds:
`primal point could not be certified`, 948 refactorizations. Final candidate
rejections after the perturbation have disappeared on this short trajectory,
but that does not count as an overall improvement. The failing point has two
basic variables with bound violation 1.000000000000001e-7 against tolerance 1e-7.
The real-model failure prevents accepting the row-scope change alone.

The pre-pivot snapshot reproduces the same failing point and basis exactly.
Moving the two reconstructed basic values inward by one representable neighbor
still fails the working-model certificate: row 23,590 exceeds its lower-bound
tolerance by 1.6643e-21 in exact stored-coefficient arithmetic. The predicted
point also fails this row. Its stored activity is within tolerance, showing why
stored bounds and equation consistency alone cannot replace model certification.

The existing compensated-residual correction repairs that row, but basic variable
2,297 remains one representable step outside its tolerated lower bound. Moving
that corrected value from -1.8e-6 to -1.7999999999999997e-6 passes the complete
point, working-model and row certificate. The additional exact arithmetic
diagnoses the failing rows; solver state and correction stay Float64. The existing certificate, including its exact fallback
for inconclusive row intervals, is unchanged.

The second experimental candidate runs only when the existing residual-correction
candidate fails certification. Each violating BASIC Float32/Float64 value can
move to its immediate inward neighbor once. Both bounds must then pass the same
tolerance, at least one value must change, and the complete point certificate
must pass. It never rounds a nonbasic value or expands a tolerance. Partial
trials, failed certificates, cancellation and exceptions roll back through the
existing correction transaction. Scratch publication and the new opt-in
`primal_bound_roundoff_corrected` event occur only after acceptance.

The new regression initially fails 48 of 96 assertions. Its expanded version
passes 172, covering both directions and precisions, all four managers, two-ULP
rejection, equation amplification, nonbasic violations and rollback. The actual
captured pivot now completes at iteration 6,799 with a certified working point.
This is pivot-level evidence, not a convergence result.

The combined experimental source passes 6,670 focused semantic assertions with `--compile=min`
and 682 checks with normal compilation, including allocations. These overlapping
counts are not a full project-suite pass. Independent read-only review found no
actionable issue in the implementation, rollback tests or diagnostic scope.

## Longer continuation rejects promotion

All three runs requested a 300-second solver budget. The candidate runs terminate
early on their own numerical errors; the guard does not stop them.

| Variant | Status | Iterations | Refactorizations | Seconds | Final auxiliary objective |
| --- | --- | ---: | ---: | ---: | ---: |
| Baseline ratio capture | TIME_LIMIT | 7,721 | 1,790 | 300.00 | 600981.4776 |
| Working-row scope only | NUMERICAL_ERROR | 6,799 | 948 | 44.00 | 602966.6010 |
| Working-row scope plus rounded correction | NUMERICAL_ERROR | 8,464 | 1,791 | 173.67 | 601153.5014 |

The combined run accepts four completely certified inward-rounding corrections,
including the captured iteration 6,799. It nevertheless terminates at 8,464 with
`primal point could not be certified`. Its 95,153 candidate rejections comprise
26,528 small pivots, 9,601 transpose-row failures and 59,024 inconclusive ratios.
This is a different trajectory and duration; these counts are not a speed or
convergence comparison with the 164,560 baseline rejections reported previously.

The final state has three basic values barely beyond bound tolerance. Exact
inspection additionally finds the true activity of row 26,319 outside its
working lower-bound tolerance. Small stored-bound errors alone therefore cannot
justify accepting this point. The second failure's pre-pivot/corrected candidates
have not been captured, so its exact recovery failure is not yet localized.

Neither candidate is promoted. The production digest after restoration is again
`c72ebe2862aa66194cd238ab35d93a19dc56ae59e2f80948c9e9d3a447ff48bc`.
No medium run is added after runtime has already rejected the candidate. All
runs remain within the guarded single-process setup; maximum recorded RSS for
the combined runtime run is about 1.91 GiB. No original-LP retry or precision
boost occurs. Phase I convergence is still unresolved.

The next targeted step is to capture the iteration-8,464 point candidates and
identify which constraints block simultaneous bound and equation certification.
This should precede accepting the working-bound change or adding another
anti-degeneracy intervention. Independent coordinate adjustments have not yet
proved adequate for this coupled feasibility problem.

## Reproduction and interpretation

Use the established owned-process memory guard and Julia wrapper, one process
at a time, from this worktree. The experiments retain Float64/PFI/native/80,
steepest-edge and relaxed integrality. Only phase-one handling, stagnation,
adaptive pricing and the two perturbation policies are enabled. Other adaptive
mechanisms are disabled; the independent weak-pivot preference remains explicitly
isolated with `defer_weak=false`. Original-LP retry is disabled for diagnosis.

The ratio capture runs on the unmodified baseline. Candidate test runners and
the combined model run require `working-row-rounded.patch`, applied to a separate
baseline checkout using `git apply --unidiff-zero`. This full patch includes the
row-scope change; do not apply it on top of `working-row-only.patch`.
The historical `aa73565` checkout lacks these new diagnostic files: copy this
finalized diagnostics directory into that checkout before using the relative
commands below. Keep its production source at the recorded baseline.

```sh
# Baseline capture:
julia --project=. diagnostics/adaptive-degeneracy/reproduce/capture_runtime_ratios.jl runtime primal both 300 /tmp/runtime-ratios
# After applying the combined experimental patch:
julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/row_value_semantics.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/row_value_compiled.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/primal_rejection_work.jl runtime primal both 300 /tmp/runtime-row-value
```

The capture run used the baseline source digest
`c72ebe2862aa66194cd238ab35d93a19dc56ae59e2f80948c9e9d3a447ff48bc`.
Its raw report retains the original `eligible_rows` and `eligible_above_zero`
field names. They count only reconstructed band membership. The current capture
script names them `reconstructed_band_*` and records first-pass exit metadata.
It also stores policy and rejected rows in new snapshots. The four older captures
use the explicitly isolated policy and an empty rejected-row list in replay.

Binary mathematical snapshots and the as-run capture script are preserved locally
under `.superpowers/adaptive-degeneracy/runtime-ratios/`, with `sha256.json`.
They are not exact continuation checkpoints and are not committed. Replay creates
an empty workspace and invokes only read-only ratio/snap kernels; it never uses
that workspace's empty factorization to solve the captured basis. Raw records,
replay comparisons and test logs are in `results/row-value/`.

For the intermediate failure, apply `reproduce/working-row-only.patch` with
`git apply --unidiff-zero` to an isolated checkout of `aa73565`, then run `capture_runtime_point.jl` with
`runtime primal both 300 PREFIX`. `probe_runtime_roundoff.jl PREFIX` reproduces
the failed pivot and compares its three point candidates; it expects that
intermediate source. With the combined patch present, run `verify_runtime_point.jl` with
`PREFIX-before.bin` to check successful application of the captured pivot.
Local snapshots and full logs are in `.superpowers/adaptive-degeneracy/runtime-point/`.
Committed failure-log excerpts omit repeated stack traces; the point summary
omits per-variable dumps. Raw TOML reports remain complete.

`reproduce/validate_working_rows.py` checks the restored baseline, the four replay
results, both negative model outcomes, rejection totals and correction count.
It applies each candidate patch to a temporary source-only copy and requires an
exact match with the corresponding recorded production digest. The intervention
validators additionally confirm that all nine pricing trials close within budget
and no perturbation overlaps a temporary pricing trial in any of the three runs.
