# Avoid dividing zero endpoints when normalizing parallel rows

Round 47 skips exact division for zero interval endpoints under nonunit pivots.
Pivots come from nonzero row entries. Zero stays zero, unbounded endpoints stay
`nothing`, and negative pivots still swap endpoint order. Unit pivots retain
their existing path. Grouping, representative selection, interval comparisons,
contradictions, and postsolve logic are unchanged.

`_normalized_interval` checks stored bounds for finite zero endpoints before
converting them and dispatches such intervals to `_normalized_zero_interval`.
Other intervals retain the original conversion and division path. This layout
matters for allocations in the measured Julia version: putting zero checks
directly into the original return expression added two allocations per nonzero
interval. Isolated measurements showed 49 → 51 allocations; the final early
dispatch restores 49, while the zero-endpoint case falls from 44 to 38.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 46 allocation rounds. All 33 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The probe has 128 rows `0 ≤ 2x + 4y - 2z ≤ 12`, free columns, and a zero objective.
Parallel reduction retains the first row. The nonzero control changes the lower
row bound to 2; the unit-pivot control divides the coefficients and upper bound
by two and keeps the lower bound zero.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Zero lower endpoints | 630,864 | 595,632 | 5.58% | 18,235 → 17,467 |
| Nonzero endpoints | 646,160 | 645,872 | — | 18,875 → 18,875 |
| Unit pivots | 403,840 | 403,472 | — | 12,219 → 12,219 |

The zero-endpoint probe removes 768 allocations. Both controls retain identical
allocation counts; their small byte differences are allocator variation.

| Model | Parallel pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 8,064 → 8,064 | 125 → 125 | 987,200 → 985,120 |
| adlittle | 80,176 → 81,040 | 1,749 → 1,749 | 3,817,608 → 3,815,496 |
| kb2 | 202,432 → 203,664 | 5,299 → 5,299 | 12,451,144 → 12,451,192 |
| sc50a | 28,104 → 28,104 | 541 → 541 | 3,934,688 → 3,933,376 |
| flugpl | 5,808 → 5,808 | 89 → 89 | 1,376,720 → 1,376,256 |

None of these direct fixture passes removes allocations. Their byte differences
do not establish a benefit or regression. Earlier presolve passes expose a
benefiting case on afiro: full presolve and each whole solve remove 14 allocations.
The other four models retain identical allocation counts throughout.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,122,928 → 1,121,376 | 1,100,864 → 1,098,848 | 14 |
| adlittle | 4,605,608 → 4,605,000 | 4,881,928 → 4,881,560 | 0 |
| kb2 | 12,904,088 → 12,902,264 | 12,918,104 → 12,916,056 | 0 |
| sc50a | 4,280,528 → 4,278,672 | 4,233,712 → 4,231,472 | 0 |
| flugpl | 1,486,856 → 1,486,472 | 1,531,784 → 1,531,352 | 0 |

The practical benefit is concentrated in parallel rows with zero bounds and
nonunit pivots. Cross-process exact-arithmetic byte variability is visible even
where counts do not change, so no broad whole-solve percentage reduction is
claimed. Unchanged paths without presolve vary from -176 to +176 bytes with
identical allocation counts.

All ten model snapshots (five fixtures × parallel/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`parallel-zero-bounds-allocations-before.toml`](parallel-zero-bounds-allocations-before.toml)
and [`parallel-zero-bounds-allocations-after.toml`](parallel-zero-bounds-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_parallel_rows --output=parallel-zero-bounds-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for (pivot, lower) in ((2.0, 0.0), (2.0, 2.0), (1.0, 0.0))
    count = 128
    A = sparse(repeat(reshape([pivot, 2pivot, -pivot], 1, 3), count, 1))
    problem = LinearProblem(A, zeros(3); row_lower=fill(lower, count),
        row_upper=fill(6pivot, count), column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_parallel_rows(problem); samples=3))
end
```

## Regression coverage

The final zero-endpoint guard failed against the original implementation:
18,280 allocations exceeded the 17,600 limit. The nonzero guard also caught the
first implementation's regression: 19,139 allocations exceeded its 19,000 limit.
Each red run passed the other 150 assertions. The final layout passes all 151
new assertions and all 374 targeted parallel-row assertions. The initial zero
budget of 17,500 was below the measured direct-call result of 17,512; its final
17,600 limit leaves headroom while still rejecting the original implementation.

The new tests cover both endpoint positions, zero equalities, unbounded bounds,
positive and negative pivots of 2 and 1/2, successive representative replacement,
contradictions, postsolve values, and original inputs across Float32, Float64,
BigFloat, and Rational{BigInt}. Existing targeted tests also cover unit pivots,
overlapping intervals, distinct signatures, and restored bases.

Independent review found no issues in the final revision and separately passed
all 151 new assertions. Its 32 four-type fixtures and inherited BigFloat
precision case passed 192 baseline-comparison assertions, including signed and
fractional pivots, zero/unbounded endpoints, replacement, overlap, contradictions,
postsolve, and input preservation.

The full mandatory suite passed all 19,843 assertions in 4m47.2s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
