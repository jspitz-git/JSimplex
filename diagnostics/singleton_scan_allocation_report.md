# Singleton-row detection allocation audit

Round 22 replaces complete row-entry lists in `reduce_singleton_rows` with a
compact scan. This pass only needs to identify rows with exactly one nonzero;
storing every coefficient in every row was unnecessary.

The new `_singleton_row_positions` helper records one `(column, CSC position)`
pair per row. A column marker of zero means empty; minus one means multiple
nonzeros. Further nonzeros preserve the multiple-entry marker. Explicit zeros
are skipped, and the scan visits active CSC storage only. For a singleton, the
reduction reads the stored coefficient directly from the source matrix.

Exact arithmetic, candidate acceptance, bound sources, failure diagnostics,
result construction, and basis restoration retain their previous behavior.
Other presolve passes continue using `_row_entries` where full lists are needed.

## Method

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native
basis factorization with PFI updates. Each case was warmed twice and sampled
three times, with input setup outside measurement and garbage collection before
each sample. Tables show minimum allocated bytes. All 32 measurements per run
recorded zero compilation time. The baseline includes the preceding 21 rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timing
overlapped validation, so no runtime-speedup claim is made. These are allocated
bytes per call, not peak or retained memory.

## Measurements

| Synthetic 128 × 128 CSC input | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Dense, no singleton rows | 283,712 | 12,232 | 95.69% | 406 → 21 |
| Identity matrix, all singleton rows | 493,424 | 481,816 | 2.35% | 13,107 → 12,852 |

Both probes have unit objectives. The dense case has unbounded row bounds; the
identity case has row bounds `[1, 2]` and exercises actual bound tightening and
row removal. Existing exact-arithmetic work dominates the latter case.

| Model | Singleton pass before | Singleton pass after | Reduction | Full presolve before | Full presolve after | Reduction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| afiro | 19,872 | 16,800 | 15.46% | 1,182,184 | 1,174,648 | 0.64% |
| adlittle | 53,016 | 43,192 | 18.53% | 4,892,664 | 4,874,296 | 0.38% |
| kb2 | 11,840 | 4,480 | 62.16% | 13,189,024 | 13,166,096 | 0.17% |
| sc50a | 10,480 | 5,200 | 50.38% | 4,318,752 | 4,304,176 | 0.34% |
| flugpl | 13,800 | 11,864 | 14.03% | 1,510,000 | 1,505,040 | 0.33% |

Whole solves with presolve enabled allocated 0.15–0.64% fewer bytes. The unchanged
paths with presolve disabled varied by -208 to +288 bytes with identical
allocation counts. Those small differences are not attributed to this change;
the isolated singleton pass provides the clearest evidence.

All ten model snapshots (five fixtures × singleton/full presolve) matched
exactly: CSC arrays, objective and constant, objective sense, bounds, domains,
names, and original column count. All 20 whole-solve combinations (five fixtures,
primal/dual, presolve on/off) remained `OPTIMAL`; status, objective, complete
primal vector, and iteration count matched baseline snapshots exactly with
`isequal`.

Machine-readable measurements are in
[`singleton-scan-allocations-before.toml`](singleton-scan-allocations-before.toml)
and [`singleton-scan-allocations-after.toml`](singleton-scan-allocations-after.toml).

## Reproduction

The existing audit covers the singleton pass, full presolve, and whole solves:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_singleton_rows --output=singleton-scan-audit.toml
```

For the synthetic probes, run from the repository root with the same Julia flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays

dense = LinearProblem(sparse(ones(128, 128)), ones(128))
singletons = LinearProblem(sparse(1:128, 1:128, ones(128), 128, 128), ones(128);
    row_lower=ones(128), row_upper=fill(2.0, 128))
for problem in (dense, singletons)
    println(measure_allocations(_ -> JSimplex.reduce_singleton_rows(problem); samples=3))
end
```

## Regression coverage

The allocation budget failed before the change at 283,712 bytes against a
30,000-byte limit and now passes at 12,232 bytes.

The 98 new checks cover empty, singleton, and multiple-entry rows, a third
nonzero after a row is already marked multiple, explicit and signed zeros,
inactive CSC storage, independent scan results, positive and negative
coefficients, bound sources, postsolve and basis restoration, unchanged inputs,
inexact-candidate rejection, infeasibility metadata, and empty dimensions.
Numeric coverage includes Float32, Float64, BigFloat, and Rational{BigInt}.

Independent review found no issue. Its 210 differential cases across six numeric
types, including 38 failures, matched baseline models, CSC storage, source maps,
and restored bases. Separate Int32 and Int64 sparse-index checks also passed.

The complete mandatory suite passed **16,318/16,318** tests, including the 98 new
checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
