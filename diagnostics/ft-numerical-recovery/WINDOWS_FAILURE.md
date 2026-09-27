# Captured Windows failure and small-pivot price propagation

## Provenance and reproduction

The second capture in `/home/jspitz/logs/ft-session-01*` contains the original
failure, including `certification_failed.45617.bin`. All diagnostic snapshots are
kept local. `results/windows-session/inputs.toml` records received file sizes and
SHA-256 hashes; text log line endings are normalized to LF in the archive.

- Run ID: `58777316640800-18336`.
- Julia 1.13.0, native Windows x86_64, one Julia thread and eight BLAS threads.
- Package tree hash `de4c04976887978ac4e77b67a4eb9792d251bfec` exactly equals
  `git rev-parse e1b1567^{tree}`. The package installation has no git checkout,
  so its reported source revision is `unavailable` and git tracking revision is
  `master`; the tree hash establishes the source match.
- Same runtime.mps SHA-256 and legacy dual / steepest-edge / FT / native /
  configured interval 80 as reported. No AFIRO warm-up.
- At iteration 45,617 the reduced solve reports objective
  47,609,229.38986641, primal infeasibility 1.3224132815448925e14 and dual
  infeasibility 3.2702076479000897, then restarts the original LP after
  `dual feasibility lost`. These values exactly match the original excerpt. All 14 shared logged
  iterations match in objective and both infeasibility fields.
- The final report says ITERATION_LIMIT at 46,000 because the subsequent
  original-LP retry reaches the diagnostic cap. It does not mean the reduced
  solve avoided failure. Solve time is 424.150 seconds; outer time includes
  compilation and is not a performance comparison.

This closes the earlier reproduction gap. It does not establish a BLAS race or
prove eight threads alone cause the failure: the first capture also differed in
startup and warm-up. Thread counts can affect the floating numerical trajectory.

## Saved-basis inspection

The first problematic-looking small pivot after the refactorization at 45,537
is a real nonzero pivot. After it, the
fresh-basis inspection reports primal infeasibility about 5.65e11, compared with
5.42e4 before the exchange. Large primal infeasibility alone does not prove an
incorrect exchange in dual simplex.

The independently refined post-pivot prices remain dual feasible in every saved
sample through iteration 45,552. The final saved basis has two violations in a
256-bit recomputation (about 0.249879 and 0.0195123), not merely the larger error
in its fresh Float64 price calculation. The final basis has already been
refactorized, with no updates left. These facts do not identify every intermediate
exchange responsible for the eventual failure; the small-pivot capture limit was
exhausted at 45,552.

A specific propagation defect is visible at iteration 45,538:

| Quantity | Value |
|---|---:|
| Independently refined pivot | 1.2175185313102243e-7 |
| Independently refined entering price | 2.25893104810974e-10 |
| Stored outgoing price | -0.001861913092358453 |
| Independently recomputed outgoing price | -0.001855356604452506 |
| Outgoing price discrepancy | about 6.6e-6 |

The incoming price error is only about 8e-13, below the dual tolerance of 1e-7,
but division by the near-cutoff pivot amplifies it. Later saved discrepancies
grow (for example, about 0.00497 for the outgoing price at iteration 45,552).
Factor solves for these sampled pivots generally agree closely with refined
calculations; this evidence does not support blaming an indexing error in FT.

Use `reproduce/inspect-capture.jl` to inspect provenance and fresh solves, and
`reproduce/inspect-price-sequence.jl report.toml snapshot.bin ...` for post-pivot
price checks. The archived results are in `results/windows-session/inspection.log`
and `sequence.log`. They recompute from saved matrices on Linux, not the original
Windows native solve. The first script's stored pre-pivot vectors must not be
interpreted as residuals of the post-pivot terminal basis.

Two local continuation probes, with rebuilt native factors and with explicit
saved Windows L/U factors, immediately changed the refactorization path and did
not reproduce the failure. Replacing the saved prices with refined prices gave
the same outcome in those probes. They are not evidence that the price correction
alone resolves the Windows run; their logs are retained to make this limitation
explicit. The captured states are algebraic inspection snapshots, not complete
restart checkpoints.

## Narrow correction

`_stabilize_small_dual_pivot!` already computes and cross-checks the entering
price at 256 and 512 bits for a near-cutoff pivot. On an accepted forward step
it previously discarded that value, so the following update divided the stale
stored price by the small pivot. The correction publishes the already certified
price when both the stored and certified steps are forward. It preserves the
backward-step path and its working-cost representability checks.

There are no additional higher-precision solves, new tolerances, forced
refactorizations, changes to the adaptive strategy or basis-manager kernels.
This removes a demonstrated source of price drift. A matching complete Windows
run is still required before calling the originally reported failure fixed.

## Validation

The original regression has 40 passing and 8 failing checks on the baseline:
the outgoing price is wrong for all four basis managers and both bound directions.
With the correction, all 48 checks pass under normal compilation. A competing-
column case with a preceding bound flip extends the focused coverage to 104
checks. The selected dual regression suite passes 2,055 assertions across 76
testsets using `--compile=min`; this checks correctness, not solve speed. A
normal-compilation regression invocation was interrupted after several minutes;
it is not counted as a completed run. The completed log is
`results/dual-regression.log`. The price correction and the added bound-flip case
also received an independent read-only review with no blocking findings.

The complete local runtime.mps run (normal compilation, legacy FT/native/80,
steepest-edge, one Julia/BLAS thread, 24 GiB virtual-memory ceiling) reaches
OPTIMAL in **405.908 seconds**, with **62,939 iterations**, **790 refactorizations**
and objective **51,425,691.76210457**. The original primal certificate passes.
Status, objective, iteration count, refactorizations and every diagnostic event
count exactly match the earlier successful local baseline. This is a regression
check; the different wall time is not claimed as a patch speedup. The report is
`results/runtime-patched.toml`. Its `source_revision` records the pre-commit HEAD;
`results/validated-source.toml` records the actual patched source SHA-256.

The targeted check on the real Windows 45,538 snapshot also passes all seven
assertions (`reproduce/check-small-pivot-snapshot.jl`, output in
`results/windows-session/snapshot-correction.log`). The inferred incoming-price
error amplification drops from 6.55800e-6 to about 8.69e-20. Including the saved
tableau-coefficient error, the predicted outgoing-price discrepancy falls from
**6.55649e-6 to 1.51457e-9**, below the 1e-7 dual tolerance, without a cost change.
The 256- and 512-bit reference prices agree within 1e-30. This validates the
isolated correction on real saved data, not the subsequent Windows trajectory.


Twenty additional LP solves reached OPTIMAL with matching objectives and passing
original-primal certificates: NetLib AFIRO, ADLITTLE and SC50A, and the LP
relaxations of MIPLib PK1 and FLUGPL, each with PFI, BG, FT and SS. This adds 55
assertions. The two MIPLib `.mps.gz` inputs were decompressed into a task-local
directory; originals were unchanged. Source and decompressed hashes are in
`results/small-model-inputs.toml`.

The initial invocation completed AFIRO/ADLITTLE under normal compilation, then
stopped before solving BLEND because the existing reader rejected its NAME line
with explanatory text. That incomplete invocation and its parser error are
retained in `results/small-models-initial.log`. SC50A replaced BLEND; the remaining
12 solves completed under `--compile=min`, recorded in
`results/small-models-remaining.log`. These small-model times are not speed
comparisons. The initial invocation also verified provenance of all 13 Windows
snapshots against the report.

The BLEND reader limitation was subsequently corrected and the model solved with
all four basis managers; see [reader validation](results/blend-reader-validation.md).

After installation of the corrected version, the remaining acceptance check is
the original Windows run in its usual environment (one Julia thread, eight BLAS
threads). Use a fresh output prefix if capturing it again. No complete corrected
Windows run has been observed yet.
