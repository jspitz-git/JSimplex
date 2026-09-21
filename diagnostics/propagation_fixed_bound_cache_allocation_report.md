# Share exact bound conversion when initializing fixed-column caches

Round 77 seeds an empty upper-bound cache from the already converted lower
bound when both stored bounds are equal and the lower exact value is finite.
This avoids converting the same fixed value twice. A populated upper cache is
retained. Unbounded sides and unequal stored endpoints continue through the
existing upper-bound conversion helper.

`Bound` equality checks boundedness as well as the stored numeric value. Thus
an unbounded upper endpoint cannot be mistaken for a finite zero, and unequal
BigFloat bounds remain distinct even if they round equal at ambient precision.
The two exact caches can share their value safely because accepted updates
replace cache entries and arithmetic does not mutate the shared rational.
Candidate construction, worklists, postsolve, and source bounds retain their
previous behavior.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 76 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

The targets contain 128 independent singleton rows and 128 distinct columns.
Positive targets use coefficient two and columns fixed at two; negative targets
use coefficient minus two and columns fixed at minus two. The zero target uses
coefficient two and columns fixed at zero. Each row equals its fixed activity,
so all rows are removed. The unequal-bound control has coefficient two, column
bounds `[1, 10]`, and row bounds `[2, 20]`. The unbounded control has the same
coefficient and lower bounds, with no finite upper column or row bound. Both
controls also remove all rows. All objectives are ones.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Fixed positive value | 308,880 | 253,216 | 18.02% | 8,894 → 7,102 |
| Fixed negative value | 310,176 | 254,336 | 18.00% | 8,894 → 7,102 |
| Fixed zero | 232,192 | 185,600 | 20.07% | 6,462 → 5,054 |
| Unequal-bound control | 405,216 | 404,272 | — | 11,710 → 11,710 |
| Unbounded-upper control | 254,864 | 254,240 | — | 7,102 → 7,102 |

Each nonzero target removes 1,792 allocations; the zero target removes 1,408.
Both controls retain their allocation counts. Small byte differences on
unchanged paths reflect cross-process exact-arithmetic variation; no benefit
is claimed for those cases.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 98,328 → 97,832 | 2,617 → 2,617 | 802,864 → 801,264 |
| adlittle | 682,328 → 680,504 | 19,142 → 19,142 | 3,465,264 → 3,462,000 |
| kb2 | 526,456 → 525,368 | 14,699 → 14,699 | 10,899,336 → 10,896,648 |
| sc50a | 247,000 → 245,416 | 6,663 → 6,663 | 3,042,408 → 3,040,072 |
| flugpl | 140,208 → 139,072 | 3,655 → 3,655 | 1,288,256 → 1,285,520 |

The five direct propagation passes retain their allocation counts. Their lower
byte totals alone do not establish an improvement.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 938,272 → 936,896 | 916,032 → 915,952 | 0 |
| adlittle | 4,253,552 → 4,252,960 | 4,530,656 → 4,529,072 | 11 |
| kb2 | 11,352,312 → 11,348,648 | 11,366,408 → 11,362,392 | 0 |
| sc50a | 3,387,016 → 3,384,984 | 3,340,328 → 3,337,384 | 0 |
| flugpl | 1,398,936 → 1,395,832 | 1,443,480 → 1,440,456 | 28 |

Full presolve and each whole solve remove 11 allocations for adlittle and 28
for flugpl. The other three fixtures retain their counts, so no improvement is
claimed for them. All paths without presolve also keep identical allocation
counts, with byte differences from -432 to +16.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-fixed-bound-cache-allocations-before.toml`](propagation-fixed-bound-cache-allocations-before.toml)
and [`propagation-fixed-bound-cache-allocations-after.toml`](propagation-fixed-bound-cache-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-fixed-bound-cache-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function propagation_fixed_bound_cache_probe(kind; count=128)
    coefficient = kind == :negative ? -2.0 : 2.0
    low = kind == :negative ? -2.0 : kind == :zero ? 0.0 : kind in (:unequal, :unbounded) ? 1.0 : 2.0
    high = kind == :unequal ? 10.0 : kind == :unbounded ? nothing : low
    row_lower = isnothing(high) ? coefficient*low : min(coefficient*low, coefficient*high)
    row_upper = isnothing(high) ? nothing : max(coefficient*low, coefficient*high)
    return LinearProblem(sparse(1:count, 1:count, fill(coefficient, count), count, count), ones(count);
        row_lower=fill(row_lower, count), row_upper=fill(row_upper, count),
        column_lower=fill(low, count), column_upper=fill(high, count))
end
for kind in (:positive, :negative, :zero, :unequal, :unbounded)
    problem = propagation_fixed_bound_cache_probe(kind)
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

All three target allocation guards failed on the original implementation:
8,939 exceeded 8,000, 8,902 exceeded 8,000, and 6,470 exceeded 5,800.
The other 352 assertions passed, including both controls. All 355 new assertions
now pass as part of 3,983 targeted propagation and presolve assertions.
Whole-pass budgets use allocation counts to avoid unstable exact-arithmetic
byte totals. Existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; positive,
negative, and zero fixed values; initially free or one-sided bounds; a finite
zero versus an unbounded upper endpoint; full/incremental fixing and cache
updates; source bounds; changed flags; and postsolve. A mixed-precision
regression distinguishes equal and nearly equal stored bounds at 192/256 bits
under ambient precision 32/64: an unequal interval must remain active instead
of being incorrectly treated as fixed and removed as redundant.

Independent review found no issues and separately passed all 355 new assertions.
Its 5,088 additional assertions passed across 408 saved-baseline comparisons.
Coverage includes populated upper caches, positive/negative fixed bounds, signed
zero, unbounded endpoints, incremental fixing and contradiction, mixed-precision
near equality, input immutability, postsolve, and basis restoration.

The full mandatory suite passed all 24,684 assertions in 5m01.6s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
