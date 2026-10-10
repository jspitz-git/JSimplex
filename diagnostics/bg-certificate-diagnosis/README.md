# BG runtime numerical-terminal diagnosis

Base revision: `fce68dad8f2044684939db561806785da195ac8f`.
Repair commit: `d978393`.
The preceding basis-kernel comparison reached OPTIMAL in both original and
optimized BG runs, but both recorded one `certification_failed` event and
restarted on the original LP. That event alone does **not** prove rejection of
an optimality certificate: `_internal_solution` emits it for every
`NUMERICAL_ERROR` terminal status.

The diagnostic retains Float64, dual legacy steepest-edge, BG/native, interval
320, default presolve/scaling, no partial pricing, relaxed integrality,
`time_limit=Inf` and one million iterations. Runtime input SHA-256 is
`d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`.

`reproduce/capture.jl` wraps only cold optimizer/terminal boundaries, preserving
the original method bodies. It records the actual terminal message and saves
workspace arrays plus the BG update representation. The native base matrix is
stored explicitly instead of relying on serialized UMFPACK pointers. It stops
deliberately at the first numerical terminal before an original-LP restart;
this is a diagnostic stop, not a completed solve. Snapshots are diagnostic
states, not a promise of bitwise restart of native factorization internals.

Run sequentially through `../basis-kernel-savings/reproduce/run.py` with the
existing 8 GiB VM, 6 GiB available-RAM and 1 GiB swap guard, one Julia/BLAS
thread, a fresh output directory and an external 900 s watchdog. Local
preferences keep precompile workload disabled. No production source change or
precision escalation is part of the initial capture.

## Located failure

The capture records three cold boundaries on the reduced/scaled workspace
(28,453 rows, 31,615 structural columns):

| Boundary | Local iterations | Result |
| --- | ---: | --- |
| Auxiliary dual solve | 259 | OPTIMAL |
| Main dual optimization | 50,718 | OPTIMAL, reported primal/dual infeasibility zero |
| Driver verification | 50,718 | NUMERICAL_ERROR: bounded feasibility recovery exhausted |

The last failure occurs before original-cost cleanup, optimality certification,
or postsolve. `certification_failed` was a misleading diagnostic event name,
not the actual terminal reason. No production event rename is included here.

Fresh native LU does not eliminate it. The compensated BTRAN residual for the
working costs initially has relative error `3.4219307227306743e-13` (14 failing
equations). The first Float64 correction reduces this to
`7.803841006103988e-14`; only basis equation 27,613 remains outside the unchanged
`5.684341886080802e-14` threshold. Its absolute residual is
`-3.615562597665526e-31` against componentwise scale `4.63305517736396e-18`.
Small absolute error alone is not an acceptance criterion. Repeating the outer
verification does not accumulate the first correction: rejected paired updates
are private, and the next recomputation starts from LU again. Homogeneous cleanup
would erase real tiny working costs, and the existing coupled local
reconstruction does not certify a replacement. The saved row probe exposes
cancellation in the first update: one coordinate combines about `-2.519e-15`
with `+2.518e-15`, leaving about `-9.511e-19`. The remaining equation links
several such coordinates, so an independently verified global correction is
useful even after local reconstruction fails. A second native correction
reduces the maximum relative residual to `1.0538682679765426e-16`, with every
equation passing. The saved primal point independently passes the original
objective certificate of that reduced/scaled workspace already; certification
itself is not the failing step. This probe does not certify the postsolved full LP.

## Bounded repair

Only `_native_cleanup_solve!(...; local_reconstruction=true)` gains a second
correction, after existing local reconstruction fails. Both production callers
belong to driver basis recomputation. The extra solve requires a strictly
improving first relative residual and `max_refinements >= 2`; at most two correction solves
per direction are attempted. Ordinary price/direction checks keep their single-correction
path. Float32/Float64 arithmetic, tolerances, original-model certification,
basis selection, and precision policy are unchanged.

The candidate stays private until all equations pass and cancellation is
checked. The caller also validates both primal/dual values and the newly
computed prices before workspace publication. A latched callback prevents a
one-shot cancellation in local reconstruction from starting the fallback.

## Initial verification

A small fixture uses a real factorization of a slightly perturbed matrix to
model an inaccurate inverse action. The exact solution is independently known.
The first correction cannot meet tolerance or the local reconstruction cutoff;
the second can. The test failed on the original implementation and passed after
the change: 298 checks across Float32/Float64, all five basis managers, both
solve orientations, bounded rejection, and every observed cancellation boundary.

On the captured BG state, the complete original-objective driver now returns
OPTIMAL with **no additional simplex iterations and the same basis**. It
restores original costs, passes primal feasibility and optimality certification
for the saved reduced/scaled workspace, and records no feasibility-recovery event. The 16.41 s cold replay
includes 16.29 s compilation and is not a steady-state timing measurement.

## Work and memory review

No new scans, solves, or matrix copies enter ordinary simplex iterations.
The exceptional fallback adds two compensated basis scans, one native basis
solve, two finite-vector scans, and one in-place vector update. Sparse scan
work is O(nnz(B)+m); dense scan work is O(m²); solve cost depends on the basis
manager and its update chain. Existing scratch, correction, and candidate
buffers are reused. Cancellation adds only constant-sized state. Independent
review found no avoidable work or retained-memory increase. The transpose test
fixture is diagonal; the captured real nonsymmetric BTRAN provides additional
orientation coverage.

## Focused timing and regressions

The complete paired primal/dual recomputation was measured in nine warmed
samples per arm on the same saved state, with factor restoration and input
reset outside the timed call. Baseline deliberately installs the original
helper in-process; sources remain pinned. All measured samples have zero
compilation time.

| Recovery arm | Outcome | Median | Range | Allocated bytes | Allocation count |
| --- | --- | ---: | ---: | ---: | ---: |
| Original | rejected | 16.564 ms | 15.870–17.328 ms | 11,982,704 | 136 |
| Repaired | accepted | 17.950 ms | 17.247–18.577 ms | 12,463,368 | 140 |

This is the cost of obtaining a verified result, not a faster kernel. The
accepted path also executes the existing price-vector allocation/publication
that rejection skipped (60,068 prices); the 480,664-byte difference must not be
attributed entirely to the extra basis solve. No additional workspace buffer
is retained by the repair.

Compiled targeted tests passed 2,248 checks. The broader semantic regressions
passed 15,705 with `--compile=min`; these overlap the targeted checks and are
not independent sample counts. All 100 unique external combinations (five
models × five managers × primal/dual × native/Markowitz) passed original primal
feasibility and reference-objective checks, with 305 assertions. Their iteration
counts match the preceding basis-kernel validation; this is not a claim of
identical pivot histories. The guarded external job took 758.3 s including
process setup and compilation (previous job: 761.3 s).

The normal-compilation full project command, `test/runtests.jl`, was interrupted
by its 600 s watchdog during LLVM compilation at `dual_entry_phase_tests.jl:15`.
The guard returned 75, peak RSS was 1,810,532 KiB, and pinned sources were
unchanged. This is an **incomplete suite**, not a passing full-suite claim or a
solver NUMERICAL_ERROR. The complete stack and resource log are retained.

The isolated `dual_entry_phase_tests.jl` then passed all 182 checks with
`--compile=min` (126 + 38 + 18), including Float32, Float64, BigFloat and exact
rational entry paths. This establishes its semantics, not normal-compilation
completion of the whole suite.

## Complete runtime result

The full solve reached OPTIMAL with original primal feasibility and objective
`51,425,691.76210469`, matching the reference. Two successful certification
events, zero `certification_failed` events, and zero precision boosts were
recorded. One internal feasibility-recovery event remains legitimate; the
previous numerical terminal and original-LP restart are eliminated. This run
includes postsolve and original-model cleanup, unlike the saved-state replay.

| Metric | Previous optimized BG run | Repaired BG run |
| --- | ---: | ---: |
| Iterations | 128,742 | 51,931 |
| Refactorizations | 462 | 166 |
| Timed solve | 1,387.023 s | 470.810 s |
| Compilation inside timed solve | 0.0661 s | 0.0660 s |
| GC inside timed solve | 54.167 s | 8.455 s |
| Allocated bytes | 59,074,397,536 | 16,708,815,952 |
| Allocation count | 471,964,210 | 102,984,752 |

The guarded process took 554.372 s including loading, warm-up and input/setup,
with peak RSS 2.503 GiB and no swaps. All pinned inputs/sources stayed unchanged.
The earlier unoptimized BG run contained a profiling intervention and is not
used as the timing comparator here.

These are single full solves with **different trajectories**: avoiding the
restart removes substantial numerical work. They do not establish a faster
basis-solve kernel or a repeatable timing ratio. The small focused recovery
measurement above isolates the additional correction cost.

`results/summary.json`, the per-job TOML/log files, and `results/provenance.json`
retain complete outcomes, resource limits, hashes, and incomplete attempts.
`reproduce/audit.py` verifies all 100 external combinations, references and
original feasibility, the complete runtime result, the snapshot boundaries,
and source immutability. The audit does not relabel the full-suite timeout as a
success.

## Reproduction and evidence boundaries

`reproduce/capture.jl` must run against the base revision named above to reproduce
the original failure. Use the guarded runner with `--project=<base-checkout>`
and this capture script's absolute path. `reproduce/replay.jl` runs the current
driver on the locally saved `capture1/3-internal.bin`. Neither snapshot restoration
nor the deliberately interrupted capture is counted as a complete solve.
`reproduce/stages.jl` separates one correction, homogeneous cleanup, local
reconstruction, and a diagnostic second correction; `cost.jl` measures the
complete paired recomputation. `validate.py` runs the verification jobs
sequentially, and `audit.py` exports compact results and provenance.

All original attempts remain in `.superpowers/bg-certificate-diagnosis`.
`stages1` failed because of diagnostic Julia include-guard syntax; `replay1`
failed because a diagnostics object was assigned to a context parameterized by
`Nothing`. Their corrected replacements are `stages2` and `replay2`; neither
initial error is a solver numerical failure. Early probe helpers were read
without individual helper digests in preflight; subsequent replay/cost runs pin
the included restore helper explicitly. The capture, production sources,
environment, input, guard, and directly invoked scripts have per-run digests.



Independent code and final evidence reviews found no blocking correctness,
cancellation, publication, work/memory, or reporting issues. The reviewed
production and test files match the full-run digests.
