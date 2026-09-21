# Share activity products for fixed columns

Round 76 reuses a column's already computed minimum-activity contribution when
its maximum and minimum exact bounds are equal. The existing unbounded, unit,
and zero shortcuts still run first. Otherwise, a fixed column now avoids the
second multiplication or negative-unit negation. Unequal bounds retain the
previous computation.

The comparison uses exact cached bounds, so two stored BigFloat endpoints that
only round to the same value at ambient precision remain distinct. Cache
updates and activity arithmetic replace values; the shared rational product
is never mutated. Candidates, row-bound handling, worklists, and postsolve
retain their previous behavior.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 75 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

The three targets contain 128 identical rows `[c, c]`, with coefficients two,
minus two, or minus one. Both columns are fixed at two, and both row bounds
are `4c`. All rows are redundant and are removed. The unit-coefficient control
uses the same fixed-column model with coefficient one, exercising the existing
product shortcut. The unequal-bound control uses coefficient two, column bounds
`[1, 10]`, and row bounds `[4, 40]`; all rows are also redundant. All objectives
are ones.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Fixed, coefficient 2 | 479,696 | 382,720 | 20.22% | 13,558 → 10,998 |
| Fixed, coefficient -2 | 481,248 | 384,704 | 20.06% | 13,558 → 10,998 |
| Fixed, coefficient -1 | 334,704 | 311,232 | 7.01% | 9,974 → 9,206 |
| Unit-coefficient control | 289,152 | 288,560 | — | 8,438 → 8,438 |
| Unequal-bound control | 527,264 | 526,464 | — | 15,094 → 15,094 |

The nonunit targets remove 2,560 allocations each; the negative-unit target
removes 768. Both controls retain their allocation counts. Small byte differences
on unchanged paths reflect cross-process exact-arithmetic variation; no benefit
is claimed for those cases.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 97,144 → 96,920 | 2,617 → 2,617 | 801,728 → 799,488 |
| adlittle | 680,312 → 679,128 | 19,142 → 19,142 | 3,463,216 → 3,461,536 |
| kb2 | 524,712 → 523,640 | 14,699 → 14,699 | 10,898,440 → 10,896,344 |
| sc50a | 244,824 → 244,328 | 6,663 → 6,663 | 3,039,400 → 3,038,248 |
| flugpl | 139,776 → 138,000 | 3,685 → 3,655 | 1,288,672 → 1,285,392 |

Flugpl removes 30 allocations in the direct propagation pass. The other four
fixtures keep the same allocation counts at this level.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 937,408 → 935,520 | 914,768 → 914,544 | 0 |
| adlittle | 4,251,728 → 4,250,640 | 4,528,256 → 4,527,872 | 0 |
| kb2 | 11,351,528 → 11,349,144 | 11,364,776 → 11,362,760 | 0 |
| sc50a | 3,386,056 → 3,384,360 | 3,338,776 → 3,336,936 | 0 |
| flugpl | 1,398,648 → 1,395,144 | 1,443,560 → 1,439,912 | 60 |

Flugpl removes 60 allocations in full presolve and in each whole solve. The
other four fixtures retain their counts, so their lower byte totals alone do
not establish an improvement. All paths without presolve also keep identical
allocation counts, with byte differences from -352 to +64.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-fixed-products-allocations-before.toml`](propagation-fixed-products-allocations-before.toml)
and [`propagation-fixed-products-allocations-after.toml`](propagation-fixed-products-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-fixed-products-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function propagation_fixed_products_probe(kind; count=128)
    coefficient = kind == :negative ? -2.0 : kind == :negative_unit ? -1.0 : kind == :unit ? 1.0 : 2.0
    low, high = kind == :unequal ? (1.0, 10.0) : (2.0, 2.0)
    return LinearProblem(sparse(fill(coefficient, count, 2)), ones(2);
        row_lower=fill(min(2low*coefficient, 2high*coefficient), count),
        row_upper=fill(max(2low*coefficient, 2high*coefficient), count),
        column_lower=fill(low, 2), column_upper=fill(high, 2))
end
for kind in (:positive, :negative, :negative_unit, :unit, :unequal)
    problem = propagation_fixed_products_probe(kind)
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

All three target allocation guards failed on the original implementation:
13,603 exceeded 12,000, 13,566 exceeded 12,000, and 9,982 exceeded 9,500.
The other 340 assertions passed, including both controls. All 343 new assertions
now pass as part of 3,628 targeted propagation and presolve assertions.
Whole-pass budgets use allocation counts to avoid unstable exact-arithmetic
byte totals. Existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; positive,
negative, and fractional coefficients; positive and negative fixed values;
unit and unequal-bound controls; propagation to other columns; changed flags;
postsolve; source bounds and coefficients; and full/incremental propagation
using newly fixed bounds from an earlier row. A mixed-precision regression
checks that endpoints stored at 192/256 bits remain distinct even when they
round equal at ambient 32/64 bits: their row must remain active instead of
being incorrectly removed as redundant.

Independent review found no issues and separately passed all 343 new assertions.
Its 9,252 additional saved-baseline assertions passed, covering mixed precision,
nearly equal bounds, signed/fractional coefficients, fixed zero/negative values,
unbounded endpoints, contradictions, incremental fixing, input immutability,
postsolve, and basis restoration. Both review runs exited successfully.

The full mandatory suite passed all 24,329 assertions in 4m57.8s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
