# Reuse unit-weight endpoints in dependent-row intervals

Round 51 avoids multiplying an exact source endpoint by one in
`_implied_interval`. The existing finite-zero and unbounded guards remain in
front of the arithmetic. Other coefficients retain their multiplication,
including negative one. Coefficient signs still select the same source bounds;
accumulation, interval comparisons, contradictions, and postsolve are unchanged.
No exact values are mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 50 allocation rounds. All 32 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The target has 128 identical rows `1 ≤ x + 2y - z ≤ 6`, free columns, and a zero
objective. The control scales all but the first row, including bounds, by two.
Both reductions retain the first row; the control uses nonunit proof weights.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Unit weight | 795,440 | 709,568 | 10.80% | 20,675 → 18,389 |
| Nonunit weight | 969,840 | 970,096 | — | 25,247 → 25,247 |

The target removes 2,286 allocations. The control retains its allocation count;
its small byte difference does not establish a regression.

| Model | Dependency pass before → after | Allocation count, unchanged | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 255,872 → 256,560 | 5,804 | 973,760 → 973,184 |
| adlittle | 808,952 → 809,656 | 19,175 | 3,814,824 → 3,814,824 |
| kb2 | 4,125,304 → 4,124,248 | 96,869 | 12,211,816 → 12,215,176 |
| sc50a | 1,965,376 → 1,965,296 | 48,044 | 3,888,000 → 3,887,520 |
| flugpl | 217,776 → 219,840 | 4,731 | 1,377,040 → 1,378,032 |

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,109,776 → 1,110,160 | 1,088,544 → 1,088,032 | 0 |
| adlittle | 4,603,544 → 4,603,960 | 4,880,856 → 4,881,048 | 0 |
| kb2 | 12,666,616 → 12,665,800 | 12,681,048 → 12,679,736 | 0 |
| sc50a | 4,233,824 → 4,233,424 | 4,186,592 → 4,185,904 | 0 |
| flugpl | 1,486,840 → 1,487,384 | 1,531,416 → 1,532,008 | 0 |

All five fixtures retain identical allocation counts at every stage. Their
small byte differences reflect cross-process exact-arithmetic allocation
variation; this round establishes no fixture-wide benefit. Unchanged paths
without presolve vary from -368 to +16 bytes with identical allocation counts.
The measured benefit applies to the targeted unit-weight, nonzero-endpoint case.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-unit-products-allocations-before.toml`](dependent-unit-products-allocations-before.toml)
and [`dependent-unit-products-allocations-after.toml`](dependent-unit-products-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-unit-products-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:unit, :nonunit)
    count = 128
    multipliers = kind == :unit ? ones(count) : [1.0; fill(2.0, count - 1)]
    problem = LinearProblem(sparse(multipliers * [1.0 2.0 -1.0]), zeros(3);
        row_lower=multipliers, row_upper=6multipliers, column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_dependent_rows(problem); samples=3))
end
```

## Regression coverage

The allocation guard failed against the original implementation: 20,720
allocations exceeded the 19,000 limit, while the other 125 assertions passed.
All 126 new assertions now pass, as do all 471 targeted dependency and presolve
assertions together. Direct instrumentation includes 45 allocations beyond the
warmed benchmark. Allocation-count budgets avoid unstable exact-arithmetic
byte totals.

The tests cover positive and negative unit/nonunit weights, sums of mixed-sign
source bounds, zero and unbounded endpoints, ignored current rows and zero
weights, dependent-row removal, contradictions, postsolve values, and input
preservation across Float32, Float64, BigFloat, and Rational{BigInt}.

Independent review found no issues and separately passed all 126 new assertions.
Thirty-two comparisons with the original implementation passed 92 additional
assertions across all four numeric types, including fractional weights, mixed
stored BigFloat precisions under 64-bit working precision, full reduction,
contradictions, postsolve, and input preservation.

The full mandatory suite passed all 20,237 assertions in 4m53.7s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
