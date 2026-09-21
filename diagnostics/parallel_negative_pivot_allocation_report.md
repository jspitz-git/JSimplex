# Negate exact coefficients for negative unit parallel pivots

Round 67 replaces rational division by minus one in `_parallel_signature` with
negation of the already converted exact coefficient. The negative-unit condition
is computed once per signature. The existing equal-coefficient shortcut still
takes precedence, unit pivots retain their conversion-only path, and other
nonunit pivots retain ordinary division. Conversion must precede negation so
stored BigFloat values do not round to ambient precision. Signatures, grouping,
representative selection, interval comparisons, contradictions, and postsolve
remain unchanged. No exact values or input coefficients are mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 66 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The probes contain 128 identical rows and three free columns with zero objective.
Rows are `[s, 2s, -s]`, with bounds between zero and `6s`. The target has `s = -1`;
controls use `s = 1`, `s = 2`, and `s = -2`. A fourth control uses row
`[-1, -1, -1]`, whose signature already skips all division. Only the first row
is retained in every case.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Negative unit pivot | 520,064 | 447,824 | 13.89% | 15,291 → 13,499 |
| Unit pivot | 356,832 | 358,480 | — | 10,683 → 10,683 |
| Positive nonunit pivot | 521,056 | 522,480 | — | 15,291 → 15,291 |
| Negative nonunit pivot | 520,992 | 522,416 | — | 15,291 → 15,291 |
| Equal coefficients | 323,168 | 324,832 | — | 9,275 → 9,275 |

The target removes 1,792 allocations. All four controls retain their counts;
their small byte increases reflect cross-process exact-arithmetic allocation
variation.

| Model | Parallel pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 8,064 → 8,064 | 125 → 125 | 826,192 → 825,728 |
| adlittle | 75,568 → 76,240 | 1,638 → 1,638 | 3,617,560 → 3,615,992 |
| kb2 | 182,000 → 182,448 | 4,690 → 4,690 | 11,150,688 → 11,148,800 |
| sc50a | 25,992 → 25,992 | 478 → 478 | 3,059,552 → 3,059,344 |
| flugpl | 5,808 → 5,808 | 89 → 89 | 1,338,720 → 1,338,128 |

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 962,880 → 961,504 | 941,936 → 940,352 | 0 |
| adlittle | 4,406,888 → 4,404,696 | 4,683,656 → 4,681,032 | 0 |
| kb2 | 11,604,096 → 11,602,432 | 11,619,600 → 11,616,288 | 0 |
| sc50a | 3,405,088 → 3,405,280 | 3,357,856 → 3,358,016 | 0 |
| flugpl | 1,448,584 → 1,447,768 | 1,493,288 → 1,492,536 | 0 |

All five fixtures retain identical allocation counts in the direct parallel
pass, full presolve, and whole solves. The measurements establish a benefit for
the targeted negative-unit case, not for these fixtures. Unchanged paths without
presolve vary from -464 to +48 bytes with identical allocation counts. Lower
byte totals alone do not establish an improvement when counts remain unchanged.

All ten model snapshots (five fixtures × parallel/full presolve) matched exactly:
CSC arrays, objective and constant, sense, bounds, domains, names, and original
column count. All 20 whole-solve combinations remained `OPTIMAL`, with identical
status, objective, complete primal vector, and iteration count (`isequal`).

Machine-readable results:
[`parallel-negative-pivot-allocations-before.toml`](parallel-negative-pivot-allocations-before.toml)
and [`parallel-negative-pivot-allocations-after.toml`](parallel-negative-pivot-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_parallel_rows --output=parallel-negative-pivot-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:negative, :unit, :positive, :nonunit, :equal)
    count = 128
    pivot = kind == :unit ? 1.0 : kind == :positive ? 2.0 : kind == :nonunit ? -2.0 : -1.0
    row = kind == :equal ? fill(pivot, 1, 3) : [pivot 2pivot -pivot]
    problem = LinearProblem(sparse(repeat(row, count, 1)), zeros(3);
        row_lower=fill(min(0.0, 6pivot), count), row_upper=fill(max(0.0, 6pivot), count),
        column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_parallel_rows(problem); samples=3))
end
```

## Regression coverage

The target allocation guard failed against the original implementation:
15,336 allocations exceeded the 14,100 limit. The other 109 assertions,
including all four controls, passed. All 110 new assertions now pass as part
of 1,052 targeted parallel-row and presolve assertions. Allocation-count budgets
avoid unstable exact-arithmetic byte totals.

Tests cover Float32, Float64, BigFloat, and Rational{BigInt}, signed and fractional
trailing coefficients, vector and tuple inputs, arbitrary column indices,
single-term rows, equal/opposite/zero coefficients, representative replacement,
interval orientation, contradictions, postsolve, and input preservation.
The BigFloat regression retains 256-bit coefficients with a 2^-100 fractional
part under 64-bit working precision, ensuring conversion precedes negation.

Independent review found no issues and separately passed all 110 new assertions.
Thirty-two saved-baseline cases passed 832 additional assertions across four
numeric types; four mixed-precision BigFloat cases passed another 28 assertions.
Checks cover exact signatures, hash/dictionary equivalence, shared exact-one
values, unchanged inputs, representative replacement, contradictions, complete
results, and postsolve. A stored 384-bit coefficient was tested under 32–256-bit
working precision to distinguish exact conversion before negation from rounding
the BigFloat first. The nonzero-pivot contract was checked at `_row_entries`
and the reducer's empty-row guard.

The full mandatory suite passed all 22,365 assertions in 5m02.0s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
