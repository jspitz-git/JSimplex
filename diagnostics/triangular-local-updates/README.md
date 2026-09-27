# Stable row identities for Bartels–Golub updates

Based on `e1b1567`, following the PrecompileTools work. BG rotations used to
rewrite every stored row index within a moved interval. Stable row identities
remove those writes and use the existing row incidence to visit only columns
containing the moved row. Numerical policy, adaptive behavior, precision and
refactorization thresholds are unchanged.

## Implementation

Each BG factor owns a shared permutation between stable identities and logical
row positions. Packed columns retain stable identities; an index view exposes
logical positions to existing lookup, sparse graph construction and diagnostics.
Entries remain sorted by logical row. A rotation moves the stored occurrence of
its first row within each affected column, then updates the shared permutation.
Adjacent swaps reorder stored entries only in columns containing both rows.

Dense solves gather a physical work vector, traverse coefficients in the existing
logical arithmetic order, and scatter the result. This avoids a permutation
lookup per coefficient. Prepared spikes remain logical vectors. Copy and reset
own their mappings, including empty factors and changed dimensions.

FT and SS retain their original plain index vectors, replacement algorithms and
dense solve kernels. PFI is unchanged. The packed-column type has a concrete
index-storage parameter so the shared helpers specialize on each representation.

## Paired recorded-exchange measurements

Each sample replays 320 recorded exchanges from the same starting basis. A full
unchanged baseline module is loaded alongside the current module. Execution
order alternates within each exchange and across three repeats. Each exchange
times two forward solves, replacement and one transpose solve; the first
exchange is excluded for compilation warm-up. Validation is outside the timers.

The table gives median cumulative BG replacement times and the reduction in the
median sum of all four operations. An 80-exchange checkpoint times 79 exchanges;
a 320-exchange checkpoint times 319. These are kernel measurements, not full
simplex timings.

| History start | Exchanges | Replacement before → after (s) | Replacement reduction | All operations reduction |
|---|---:|---:|---:|---:|
| runtime 24017 | 80 | 0.1501 → 0.0687 | 54.2% | 25.5% |
| runtime 30017 | 80 | 0.1085 → 0.0745 | 31.3% | 11.1% |
| runtime 40097 | 80 | 0.1908 → 0.1102 | 42.2% | 18.9% |
| medium 2000 | 80 | 1.0308 → 0.3749 | 63.6% | 38.6% |
| runtime 24017 | 320 | 0.7926 → 0.5668 | 28.5% | 11.0% |
| runtime 30017 | 320 | 0.9017 → 0.6004 | 33.4% | 13.3% |
| runtime 40097 | 320 | 1.6401 → 1.0735 | 34.5% | 15.5% |
| medium 2000 | 320 | 4.4162 → 1.9038 | 56.9% | 36.7% |

Raw results include every repeat, checkpoints at 20/80/160/320 exchanges, and
FT/SS/PFI controls. Timing variability is material even for unchanged
FT/SS controls at medium's 320 checkpoint differ by -10% and +20% in total time, respectively.
Individual repeats vary substantially even within the same implementation.
The directional BG improvement repeats across all histories and prototypes;
the precise percentages should not be generalized to other machines. At short
20-exchange windows, the vector mapping overhead can offset the saved updates.
No parity with PFI is claimed.

## Correctness checks

- 34,301 unique assertions cover permutations, ownership, resized resets,
  prepared spikes, factorization sequences, sparse traversal, lookup and
  hypersparse edge/overflow paths. The new permutation checks include Float32,
  Float64, BigFloat and rational arithmetic.
- All four histories, all four managers and three repeats have exactly equal
  forward/transpose outputs against the baseline at every exchange. First
  repeats additionally compare logical packed coefficients, permutations and
  update history for the three triangular managers. Scaled residuals are checked at each checkpoint below 1e-10.
- The external corpus completed 72 solves and 225 assertions: both algorithms,
  all four managers, nine hash-checked models across NetLib/MIPLib/mps. Every
  solution is optimal, matches the independent objective, and passes the original
  primal-feasibility certificate. Iteration counts and objective values exactly
  match the prior precompile-workloads corpus results.
- The complete runtime pair passed exact objective/iteration/refactorization
  and diagnostic-count comparisons; both original primal certificates passed.

This is focused verification; it is not a claim that the entire package test
suite has been rerun.

## Complete runtime.mps pair

One fixed-order pair ran the unchanged baseline first and the BG optimization
second in the same process. Both were warmed with afiro. Timings exclude model
parsing, include diagnostics and the complete cleanup, and are not a repeated
estimate. Options: legacy dual, steepest edge, native factorization, BG,
configured interval 80, iteration limit 1,000,000 and time limit 1,500 seconds.

| Measurement | Baseline | Stable BG identities |
|---|---:|---:|
| Solver time | 527.909 s | 448.871 s |
| Iterations | 55855 | 55855 |
| Refactorizations | 410 | 410 |
| Status | OPTIMAL | OPTIMAL |
| Original primal certificate | passed | passed |

Total time decreased by **14.97%** in this pair. The objective is exactly
identical (51425691.76210459), as are every diagnostic event count, the iteration
count and the refactorization count. Cleanup began at iteration 54690 in both
runs: approximately 511.7 s / 436.1 s into the baseline/current solve. From
that callback to return, cleanup and final checks took approximately 16.2 s /
12.8 s. Full results and progress records are stored alongside the replay data.
This validates a complete solve; it does not establish cross-machine speedup
or performance parity with PFI. A complete medium solve was not run here.

## Rejected experiments

A shared packed-interval rotation passed 6,801 new and 19,895 existing assertions
but did not establish a consistent speedup. It was removed.

Stable row identities for FT/SS, followed by persistent incidence lists that
rebuild only the changed elimination row, passed correctness checks and improved
medium replacement times by about 22%/31%. However, runtime's late history became
about 73%/58% slower in replacement. Those changes were removed; only BG uses
the new representation. Local patches and measurements retain the rejected
experiments. A separate FT/SS optimization needs evidence on both model shapes.

## Reproduction

Julia 1.13.0, Linux aarch64, one Julia/BLAS/image/precompile thread, one numerical
job at a time, 24 GiB virtual-memory ceiling. Broad PrecompileTools workloads
were disabled only in this worktree for repeated source edits. Editor processes
were not signaled; independent compiler activity was observed during the work.
No allocation investigation was performed.

From the repository root, with the project dependencies instantiated:

```sh
python3 diagnostics/triangular-local-updates/reproduce/prepare-baseline.py /tmp/jsimplex-baseline-src
export JSIMPLEX_BASELINE_SOURCE=/tmp/jsimplex-baseline-src
export JULIA_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 JULIA_IMAGE_THREADS=1 JULIA_NUM_PRECOMPILE_TASKS=1
ulimit -v 25165824
julia --startup-file=no --project=. diagnostics/triangular-local-updates/reproduce/compare-stable.jl /tmp/paired-results HISTORY...
julia --startup-file=no --project=. diagnostics/triangular-local-updates/reproduce/compare-runtime.jl /home/jspitz/mps/runtime.mps /tmp/runtime-results
```

Serialized histories remain local. Runtime histories were produced by
`diagnostics/triangular-update-kernels/reproduce/capture-late.jl` and the prior
runtime-cliff recorder; their source iterations and input SHA-256 hashes are
included in the result files. The medium history starts at iteration 2000 in the
earlier basis-cleanup experiment. Keep the recorded exchanges fixed when
comparing implementations; regenerating a history is a different measurement.

The external corpus uses the existing
`diagnostics/simplex-basis-cleanup-performance/reproduce/quick-corpus.jl` driver
and a hash-checked manifest prepared by `prepare-corpus.py` in that directory.
Set `JSIMPLEX_CORPUS_MANIFEST` and `JSIMPLEX_CORPUS_OUTPUT` before running it.
It covers nine models from NetLib, MIPLib and mps, both simplex algorithms and
all four managers. Excluded large models are never solved or factorized.
