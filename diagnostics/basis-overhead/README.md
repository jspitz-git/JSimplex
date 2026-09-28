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
