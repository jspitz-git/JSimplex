# Basis overhead investigation

Base: `e95aabb`, combining master `0f3bbc5` with the previously verified
Bartels-Golub stable-index implementation `c7125f7`. Development uses a separate
worktree. Adaptive strategy and precision escalation policy are unchanged.

## Persistent Markowitz column maxima

Markowitz already stores stable row/column identities during sparse elimination.
There is no repeated triangular renumbering to remove here. Its maximum cache,
however, was discarded on every pivot search. Construction now invalidates only
the pivot column and the columns present in the pivot row. These are exactly the
columns changed by the Schur update and pivot-row removal. Merits based on current
row/column lengths are still evaluated afresh; threshold and magnitude tie rules
are unchanged. Standalone pivot searches retain their original cache behavior.

The paired construction probe checks exact equality of row/column permutations,
sparse L/U coefficients, diagonals, dense LU and dense permutations. It also
checks forward and transposed residuals. Each case alternates old/new order for
seven timed samples after warmup; compilation is excluded and explicitly checked.
Julia 1.13.0, Linux aarch64, one Julia and BLAS thread, 8 GiB virtual-memory
ceiling. Dimensions run in separate processes with a 180-second shell deadline.
The source hashes and raw samples are in `results/markowitz-pair-*.toml`.

| Pattern / dimension | Before (median ms) | After (median ms) | Time reduction |
| --- | ---: | ---: | ---: |
| band / 64 | 0.0508 | 0.0452 | 11.0% |
| fill / 64 | 0.1004 | 0.0835 | 16.8% |
| blocks / 64 | 0.1234 | 0.1134 | 8.1% |
| band / 256 | 0.4396 | 0.4092 | 6.9% |
| fill / 256 | 1.9309 | 1.8365 | 4.9% |
| blocks / 256 | 1.1464 | 0.9761 | 14.9% |
| band / 1024 | 5.6175 | 4.4898 | 20.1% |
| fill / 1024 | 24.1526 | 18.4482 | 23.6% |
| blocks / 1024 | 13.0500 | 9.5645 | 26.7% |

The 32-row Float32 band case increased from 9.3 to 9.8 microseconds; BigFloat and
Rational{BigInt} cases decreased by 9.6% and 4.5%. These short microbenchmarks do
not establish a universal speedup. In particular, they do not predict full
simplex speed or affect the user's `basis_refactorization=:native` configuration.

Validation: 396 paired-probe assertions, 418 focused correctness assertions
under `--compile=min`, and 126 cache/storage/allocation assertions under normal
compilation passed. The final cache regression group has 122 assertions,
including a new constructor-level case. A local negative-control copy with
invalidation removed fails both pivot-order checks in that case. No deliberate
fault is present in production source. Independent read-only review found no
correctness blockers. This is focused verification, not a full-suite claim.

Example after preparing a frozen baseline source directory and the Julia project:

```sh
JSIMPLEX_BASELINE_SOURCE=/path/to/baseline/src JSIMPLEX_PROBE_DIMENSION=256 \
  julia --startup-file=no --project=. diagnostics/basis-overhead/reproduce/markowitz-pair.jl /tmp/markowitz-256.toml
```

Use a fresh output path. `JSIMPLEX_PROBE_GENERIC=1` adds the three 32-row generic
cases. The script writes each completed case immediately. An earlier measurement
was interrupted by a host restart before saving results; it is not counted.

## Temporary FT/SS row spikes and empty elimination paths

After rotating the leaving row, FT and SS used to insert its entries into packed
upper columns, repeatedly search and modify them during elimination, then remove
them again. They now collect the row in existing dense scratch, perform the same
ordered elimination there, and write only touched surviving entries back once.
The unchanged triangular prefix is excluded from rotation and incidence scans.
Touched markers are initialized only for columns that can survive elimination.
Untouched explicit zeros are preserved; intermediate exact zeros are canonicalized
as in the old packed deletion/lookup path.

Two empty cases matter on large, initially sparse bases. FT starts scratch writes
and elimination at the first nonzero moved-row term, retaining the old arithmetic
path for zero or nonfinite diagonals. SS returns after packing the replacement
column when its last nonzero is already at the pivot position: there is no row
rotation or elimination to perform. Both paths append the normal update record,
preserve buffer recycling, and invalidate the same factor caches.

An earlier version wrote the full FT scratch suffix even for pure permutations.
It regressed on the captured 360,982-row `medium.mps` basis, motivating the empty
prefix optimization. A separate experiment transferred BG stable row identities
to FT/SS. It added solve overhead without a reliable overall benefit, so it was
discarded; FT/SS retain ordinary packed row indices. BG's previously verified
stable indices remain unchanged.

The paired replay uses frozen `e95aabb` source and actual recorded exchanges from
`runtime.mps` (near iterations 30,000 and 40,000) and `medium.mps` (iteration 2,000).
Each exchange alternates baseline/current order and measures two FTRANs, one
replacement and one BTRAN. The first exchange is excluded as warmup. Three
repetitions compare every solve result exactly; the first also compares packed
coefficients, permutations and update records exactly. Scaled forward/transposed
residuals are checked at 20, 80, 160 and 320 updates against the explicit basis.
These are fixed-history kernel measurements, not complete LP timings or evidence
of parity with PFI. Raw results retain source/input/history hashes.

| History / updates | Manager | Update before (ms) | Update after (ms) | Update reduction | Combined reduction |
| --- | --- | ---: | ---: | ---: | ---: |
| runtime / 30k / 80 | FT | 60.61 | 36.24 | 40.2% | 11.7% |
| runtime / 30k / 320 | FT | 427.70 | 278.57 | 34.9% | 8.1% |
| runtime / 30k / 80 | SS | 69.51 | 57.41 | 17.4% | 4.6% |
| runtime / 30k / 320 | SS | 477.16 | 422.87 | 11.4% | 3.4% |
| runtime / 40k / 80 | FT | 74.90 | 40.47 | 46.0% | 10.9% |
| runtime / 40k / 320 | FT | 505.11 | 355.02 | 29.7% | 7.0% |
| runtime / 40k / 80 | SS | 75.60 | 49.63 | 34.4% | 7.9% |
| runtime / 40k / 320 | SS | 567.49 | 413.51 | 27.1% | 6.9% |
| medium / 2k / 80 | FT | 608.89 | 380.65 | 37.5% | 21.2% |
| medium / 2k / 320 | FT | 2646.50 | 1789.01 | 32.4% | 18.3% |
| medium / 2k / 80 | SS | 480.57 | 414.61 | 13.7% | 6.5% |
| medium / 2k / 320 | SS | 2012.82 | 1911.56 | 5.0% | 3.5% |

These are medians of cumulative prefixes, excluding the first exchange (79 or
319 timed updates), without refactorization inside the replay. Timing varies
across runs; the seven-repeat FT medium check before the final SS-only change
also reduced update time by 33.5% and the combined time by 19.8%
(`results/triangular-medium-ft-check.toml`). The
final paired samples establish a local kernel benefit, not a universal speedup.

Final focused verification passed 32,468 assertions, including prepared-spike
provenance, explicit factor equations, exact rational arithmetic, BigFloat
precision, hypersparse update sequences, overflow, copies and resized resets.
New cases exercise delayed/empty FT spikes, invalid diagonals, and terminal SS
rotations with explicit signed zeros. Independent read-only review found no
remaining blockers. This is focused verification, not a full-suite claim.

The final external corpus passed 125 assertions: `afiro`, `adlittle`, `pk1`,
`flugpl` and `fast0507`, each with primal/dual, FT/SS and native/Markowitz
refactorization (40 solves). Every solve returned `OPTIMAL`, matched the existing
independent objective reference, and passed the original-problem primal check.
Input and production-source hashes are retained in `results/external-corpus.toml`.
This corpus checks correctness; its elapsed times are not paired speed benchmarks.

Results were captured before the final feature commit. The recorder's Git revision
therefore identifies the preceding commit; `results/triangular-source.json` and
the paired/corpus source hashes identify the tested production changes precisely.

An initial full-runtime diagnostic attempt stopped during LLVM compilation of
primal cleanup at iteration 61,746 under an 8 GiB virtual-memory
limit. It is not counted as a completed solve. The earlier successful diagnostic
baseline had recorded 7.86 GiB peak resident memory under a 24 GiB virtual limit,
so the smaller virtual limit was insufficient for that diagnostic workload.
`results/runtime-limited-attempt.txt` preserves the failure evidence. Production
source was unchanged for the isolated retry, which used a 12 GiB virtual limit.

The isolated full `runtime.mps` run completed with `OPTIMAL`, objective
`51425691.76210457`, 62,939 iterations and 790 refactorizations in 327.997 seconds.
The original-problem primal certificate passed. It used legacy dual FT, native
refactorization, steepest-edge pricing and interval 80, with one Julia/BLAS thread.
All recorded event counts match the earlier successful full diagnostic run;
cleanup begins at iteration 61,746. Peak resident memory was 6.83 GiB (no swap);
total process time including startup/warmup was 409.52 seconds.

The earlier full diagnostic result was 405.908 seconds with the same objective,
iteration count and refactorization count. These runs were not interleaved or
paired, so the elapsed difference is an observation, not a controlled whole-solver
speedup estimate. The fixed-history table above supplies the paired evidence.
No complete medium solve or complete runtime SS solve is claimed in this step.

Reproduction commands (prepare the project, source baseline and histories first):

```sh
julia --startup-file=no --compile=min --project=. diagnostics/basis-overhead/reproduce/verify-triangular.jl

JSIMPLEX_BASELINE_SOURCE=/path/to/baseline/src JSIMPLEX_BASELINE_REVISION=e95aabb \
  julia --startup-file=no --project=. diagnostics/basis-overhead/reproduce/triangular-pair.jl /tmp/replay-results /path/to/history.bin

julia --startup-file=no --project=. diagnostics/basis-overhead/reproduce/external-corpus.jl /path/to/prepared-inputs.toml /tmp/corpus-results.toml
```

Use fresh output paths and one numerical process at a time. `JSIMPLEX_PROBE_REPEATS`
changes the replay repeat count. The corpus manifest follows
`diagnostics/simplex-basis-cleanup-performance/reproduce/prepare-corpus.py`;
references and input hashes come from that existing independent corpus. History
capture scripts are described in `diagnostics/triangular-update-kernels/README.md`.
Large excluded models (`big.mps`, `largo.mps`, `AnyMod.mps`) are never solved here.
