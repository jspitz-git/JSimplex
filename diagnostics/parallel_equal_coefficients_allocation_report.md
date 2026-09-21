# Reuse one for repeated coefficients in parallel signatures

Round 66 extends `_parallel_signature`'s leading-one shortcut to every stored
coefficient equal to the nonzero pivot. The unit-pivot path reuses the already
converted pivot; the nonunit path creates one exact one and reuses it for each
matching coefficient. Other coefficients retain exact conversion and division.
This removes redundant conversions as well as divisions. Equality compares the
stored values directly, preserving differences below ambient BigFloat precision.
The signature order, grouping, representative selection, bound comparisons,
contradictions, and postsolve remain unchanged. Exact values are never mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 65 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The probes contain 128 identical rows and three free columns with zero objective.
Targets have row `[s, s, s]` for `s = 2`, `s = -2`, and `s = 1`; controls have
row `[s, 2s, -s]` for `s = 2` and `s = 1`. Bounds are the interval between zero
and `6s`. Only the first row is retained.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Repeated positive pivot | 504,560 | 323,168 | 35.95% | 14,651 → 9,275 |
| Repeated negative pivot | 505,536 | 324,352 | 35.84% | 14,651 → 9,275 |
| Repeated unit pivot | 341,472 | 247,184 | 27.61% | 10,043 → 6,971 |
| Unequal coefficients, nonunit pivot | 522,592 | 522,432 | — | 15,291 → 15,291 |
| Unequal coefficients, unit pivot | 358,336 | 358,224 | — | 10,683 → 10,683 |

Each nonunit target removes 5,376 allocations; the unit target removes 3,072.
Both controls retain their counts; their small byte differences reflect
cross-process exact-arithmetic allocation variation.

| Model | Parallel pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 8,064 → 8,064 | 125 → 125 | 830,064 → 826,656 |
| adlittle | 78,224 → 75,984 | 1,686 → 1,638 | 3,625,272 → 3,617,192 |
| kb2 | 189,424 → 182,688 | 4,906 → 4,690 | 11,164,080 → 11,150,544 |
| sc50a | 25,992 → 25,992 | 478 → 478 | 3,061,616 → 3,059,824 |
| flugpl | 5,808 → 5,808 | 89 → 89 | 1,339,728 → 1,338,192 |

Adlittle and kb2 remove 48 and 216 allocations from the direct parallel pass,
with 2.86% and 3.56% lower byte totals. The other three direct passes are
unchanged. Earlier presolve stages expose a benefiting case on afiro.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 965,440 → 962,384 | 945,264 → 941,840 | 99 |
| adlittle | 4,415,480 → 4,406,360 | 4,691,544 → 4,683,304 | 192 |
| kb2 | 11,617,232 → 11,604,208 | 11,631,920 → 11,617,424 | 432 |
| sc50a | 3,408,000 → 3,405,584 | 3,360,640 → 3,358,304 | 0 |
| flugpl | 1,448,728 → 1,448,696 | 1,493,480 → 1,493,160 | 0 |

Full presolve removes the same number of allocations as each whole solve.
Three fixtures benefit at that level; sc50a and flugpl retain identical counts.
Unchanged paths without presolve vary from -240 to +32 bytes with identical
allocation counts. Counts provide the clearer evidence for small fixture
differences; lower byte totals alone do not establish a benefit when counts
remain unchanged.

All ten model snapshots (five fixtures × parallel/full presolve) matched exactly:
CSC arrays, objective and constant, sense, bounds, domains, names, and original
column count. All 20 whole-solve combinations remained `OPTIMAL`, with identical
status, objective, complete primal vector, and iteration count (`isequal`).

Machine-readable results:
[`parallel-equal-coefficients-allocations-before.toml`](parallel-equal-coefficients-allocations-before.toml)
and [`parallel-equal-coefficients-allocations-after.toml`](parallel-equal-coefficients-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_parallel_rows --output=parallel-equal-coefficients-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:positive, :negative, :unit, :unequal, :unit_unequal)
    count = 128
    pivot = kind in (:unit, :unit_unequal) ? 1.0 : kind == :negative ? -2.0 : 2.0
    row = kind in (:unequal, :unit_unequal) ? [pivot 2pivot -pivot] : fill(pivot, 1, 3)
    problem = LinearProblem(sparse(repeat(row, count, 1)), zeros(3);
        row_lower=fill(min(0.0, 6pivot), count), row_upper=fill(max(0.0, 6pivot), count),
        column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_parallel_rows(problem); samples=3))
end
```

## Regression coverage

All three target allocation guards failed against the original implementation:
14,696 and 14,659 exceeded the 11,500 limit, and 10,051 exceeded 8,500. The other
123 assertions, including both controls, passed. All 126 new assertions now pass
as part of 942 targeted parallel-row and presolve assertions. Allocation-count
budgets avoid unstable exact-arithmetic byte totals.

Tests cover Float32, Float64, BigFloat, and Rational{BigInt}, unit, positive,
negative, and fractional pivots, vector and tuple inputs, arbitrary column
indices, single-term rows, repeated, opposite, unequal and zero coefficients,
representative replacement, contradictions, postsolve, and input preservation.
The BigFloat regression uses stored 192/256/320-bit values under 64-bit working
precision, with an unequal coefficient differing by only 2^-120.

Independent review found no issues and separately passed all 126 new assertions.
Thirty-two saved-baseline cases passed 896 additional assertions, including 64
reducer runs; twelve mixed-precision BigFloat cases passed another 72 assertions.
Checks cover exact signatures and their hashes, input forms and ordering,
representative selection, disjointness, postsolve, input preservation, and
read-only downstream use of shared exact-one values.

The full mandatory suite passed all 22,255 assertions in 4m57.1s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
