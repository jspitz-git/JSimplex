# Reuse the activity zero for finite zero row bounds

Round 78 skips exact-rational conversion of finite zero row bounds. Both lower
and upper endpoints reuse the existing activity zero. Separate `has_row_lower`
and `has_row_upper` flags retain their original meaning, so a finite zero is
still distinguished from an unbounded side. Nonzero endpoints keep the existing
conversion and equal-bound sharing paths.

The zero check inspects the stored numeric value and does not round BigFloat
inputs to ambient precision. Tiny nonzero values remain nonzero. Exact rational
arithmetic and cache updates replace values, so sharing this zero does not
mutate row bounds, activities, or previously accepted bounds. Candidate checks,
worklists, and postsolve retain their previous behavior.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 77 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each probe contains 128 independent singleton rows and initially free columns.
The lower-only and upper-only targets use coefficient two and one finite zero
row bound, producing a zero lower or upper column bound respectively. The
zero-equality target uses coefficient minus two and fixes all columns at zero.
The nonzero control uses coefficient two and row bounds `[2, 6]`, tightening
columns to `[1, 3]`. The unbounded control uses coefficient two and no finite
row bound; all rows are removed. All objectives are ones.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Zero lower row bound | 248,616 | 210,600 | 15.29% | 6,082 → 4,930 |
| Zero upper row bound | 249,704 | 211,960 | 15.12% | 6,082 → 4,930 |
| Zero equality | 334,160 | 296,816 | 11.18% | 7,877 → 6,725 |
| Nonzero-bound control | 502,192 | 502,144 | — | 12,997 → 12,997 |
| Unbounded-row control | 102,128 | 102,368 | — | 2,494 → 2,494 |

Each target removes 1,152 allocations. Both controls retain their allocation
counts. Small byte differences on unchanged paths reflect cross-process
exact-arithmetic variation; no benefit is claimed for those cases.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 97,608 → 91,368 | 2,617 → 2,437 | 801,008 → 793,424 |
| adlittle | 680,760 → 676,152 | 19,142 → 18,971 | 3,462,160 → 3,451,984 |
| kb2 | 525,672 → 513,592 | 14,699 → 14,312 | 10,895,160 → 10,870,632 |
| sc50a | 245,096 → 234,408 | 6,663 → 6,312 | 3,040,472 → 3,027,976 |
| flugpl | 139,120 → 136,048 | 3,655 → 3,556 | 1,284,848 → 1,279,216 |

All five direct propagation passes remove allocations; kb2 removes 387.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 936,368 → 929,280 | 915,008 → 908,016 | 225 |
| adlittle | 4,252,272 → 4,240,608 | 4,528,464 → 4,516,704 | 324 |
| kb2 | 11,350,600 → 11,325,896 | 11,363,240 → 11,339,080 | 765 |
| sc50a | 3,385,256 → 3,372,920 | 3,337,720 → 3,325,848 | 342 |
| flugpl | 1,394,728 → 1,389,960 | 1,439,064 → 1,434,408 | 180 |

Full presolve and each whole solve remove allocations on all five fixtures,
from 180 for flugpl to 765 for kb2. All paths without presolve keep identical
allocation counts, with byte differences from -80 to +112; no benefit is
claimed for these unchanged paths.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-zero-row-bounds-allocations-before.toml`](propagation-zero-row-bounds-allocations-before.toml)
and [`propagation-zero-row-bounds-allocations-after.toml`](propagation-zero-row-bounds-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-zero-row-bounds-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function propagation_zero_row_bounds_probe(kind; count=128)
    coefficient = kind == :equality ? -2.0 : 2.0
    low = kind in (:upper_only, :unbounded) ? nothing : kind == :nonzero ? 2.0 : 0.0
    high = kind in (:lower_only, :unbounded) ? nothing : kind == :nonzero ? 6.0 : 0.0
    return LinearProblem(sparse(1:count, 1:count, fill(coefficient, count), count, count), ones(count);
        row_lower=fill(low, count), row_upper=fill(high, count),
        column_lower=fill(nothing, count), column_upper=fill(nothing, count))
end
for kind in (:lower_only, :upper_only, :equality, :nonzero, :unbounded)
    problem = propagation_zero_row_bounds_probe(kind)
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

All three target allocation guards failed on the original implementation:
6,127 exceeded 5,500, 6,090 exceeded 5,500, and 7,885 exceeded 7,300.
The other 325 assertions passed, including both controls. All 328 new assertions
now pass as part of 4,311 targeted propagation and presolve assertions.
Whole-pass budgets use allocation counts to avoid unstable exact-arithmetic
byte totals. Existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; positive,
negative, and fractional coefficients; zero equalities and one-sided row bounds;
unbounded sides; signed-zero preservation in source bounds; full/incremental
propagation to later nonzero rows; changed flags; postsolve; and preservation
of source bounds. Stored 256-bit BigFloat endpoints at `±2^-200` remain nonzero
and produce the correct `±2^-201` column bounds under ambient precision 32/64.

Independent review found no issues and separately passed all 328 new assertions.
Its 8,476 additional saved-baseline assertions passed, covering signed zero,
unbounded flags, tiny and mixed-precision BigFloat bounds, unequal endpoints,
failures, redundancy, incremental propagation, input preservation, postsolve,
and basis restoration. The shared zero is initialized before use and remains
unmodified by downstream arithmetic.

The full mandatory suite passed all 25,012 assertions in 4m59.0s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
