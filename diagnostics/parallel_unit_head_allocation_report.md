# Reuse the converted pivot in unit parallel signatures

Round 49 reuses the already converted first coefficient when a parallel-row
signature has a unit pivot. Previously `_parallel_signature` converted that
stored coefficient once to inspect the pivot and again while building the
signature. The first iteration now retains the pivot; all remaining entries
keep their original exact conversions. The nonunit path is unchanged.

The shortcut follows iteration position rather than column number. Signatures,
grouping, interval comparisons, representative selection, contradictions, and
postsolve behavior remain unchanged. No exact values are mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 48 allocation rounds. All 33 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

Each probe has 128 identical rows proportional to `0 ≤ x + 2y - z ≤ 6`, free
columns, and a zero objective. The target uses pivot 1; the controls use pivots
2 and -2 with corresponding scaled row bounds. Parallel reduction retains the
first row in every case.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Pivot 1 | 403,392 | 356,096 | 11.72% | 12,219 → 10,683 |
| Pivot 2 | 522,320 | 521,664 | — | 15,291 → 15,291 |
| Pivot -2 | 522,400 | 521,520 | — | 15,291 → 15,291 |

The unit probe removes 1,536 allocations. Both controls retain identical
allocation counts; their small byte differences are allocator variation.

| Model | Parallel pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 8,064 → 8,064 | 125 → 125 | 985,520 → 983,664 |
| adlittle | 79,384 → 78,160 | 1,698 → 1,686 | 3,813,800 → 3,809,384 |
| kb2 | 191,144 → 189,280 | 4,942 → 4,906 | 12,427,640 → 12,422,440 |
| sc50a | 26,352 → 25,992 | 490 → 478 | 3,926,256 → 3,924,272 |
| flugpl | 5,808 → 5,808 | 89 → 89 | 1,374,800 → 1,374,016 |

Three direct fixture passes remove 12–36 allocations and record 0.98–1.54%
fewer bytes. Afiro and flugpl have unchanged direct-pass measurements.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,121,920 → 1,119,360 | 1,099,712 → 1,098,400 | 24 |
| adlittle | 4,602,136 → 4,598,936 | 4,878,920 → 4,875,208 | 48 |
| kb2 | 12,877,896 → 12,876,264 | 12,891,880 → 12,890,760 | 72 |
| sc50a | 4,272,928 → 4,270,896 | 4,225,952 → 4,223,456 | 72 |
| flugpl | 1,484,552 → 1,484,312 | 1,529,080 → 1,528,696 | 0 |

Full presolve removes the same number of allocations as each whole solve.
Earlier passes expose a benefiting case on afiro. Flugpl retains identical
counts throughout; its small byte differences do not establish a benefit.
Fixture gains are small relative to cross-process exact-arithmetic byte
variation, so allocation counts provide the clearer evidence. Unchanged paths
without presolve vary from -384 to +112 bytes with identical allocation counts.

All ten model snapshots (five fixtures × parallel/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`parallel-unit-head-allocations-before.toml`](parallel-unit-head-allocations-before.toml)
and [`parallel-unit-head-allocations-after.toml`](parallel-unit-head-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_parallel_rows --output=parallel-unit-head-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for pivot in (1.0, 2.0, -2.0)
    count = 128
    A = sparse(repeat(reshape([pivot, 2pivot, -pivot], 1, 3), count, 1))
    problem = LinearProblem(A, zeros(3); row_lower=fill(min(0.0, 6pivot), count),
        row_upper=fill(max(0.0, 6pivot), count), column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_parallel_rows(problem); samples=3))
end
```

## Regression coverage

The allocation guard failed against the original implementation: 12,264
allocations exceeded the 11,500 limit, while the other 53 assertions passed.
All 54 new assertions now pass, as do all 530 targeted parallel-row assertions
together. Direct instrumentation includes 45 allocations beyond the warmed
benchmark. Allocation-count budgets avoid unstable exact-arithmetic byte totals.

The new tests cover negative, zero, and fractional trailing coefficients,
noncontiguous column indices, one-term signatures, vector and tuple inputs,
mixed-sign representative replacement, contradictions, postsolve values, and
input preservation across Float32, Float64, BigFloat, and Rational{BigInt}.
Stored 256-bit trailing BigFloat coefficients retain exact ratios under 64-bit
working precision. Existing targeted tests also cover nonunit pivots, unbounded
and zero row endpoints, overlapping intervals, and restored bases.

Independent review found no issues and separately passed all 54 new assertions.
Thirty-two comparisons with the original implementation passed 476 assertions
across all four numeric types, including input forms, grouping, contradictions,
postsolve, and preservation. Six additional assertions checked inherited
BigFloat precision. Its separate warmed probe also removed 1,536 allocations.

The full mandatory suite passed all 19,999 assertions in 4m44.3s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
