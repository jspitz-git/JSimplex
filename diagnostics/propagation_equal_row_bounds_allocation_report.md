# Reuse exact conversion for equal propagation row bounds

Round 75 converts equal finite row bounds only once. Equality compares the
stored `Bound` values, whose comparison checks boundedness and numeric value;
it does not round BigFloat values to the ambient precision. The resulting
exact rational is shared without mutating its BigInt payloads.

Row endpoints now remain concrete `ExactValue` values, with separate
`has_row_lower` and `has_row_upper` flags. An unbounded side uses the already
initialized activity zero as a placeholder. All ten former nullable-row checks
use the matching boundedness flag: contradiction checks, row implication,
other-activity calculation, and candidate construction. The placeholder never
participates as a finite row bound. Unequal finite endpoints still convert
independently. Cache updates, worklists, and postsolve retain their behavior.

The flags are needed to avoid a compiler allocation regression. Simply sharing
nullable row endpoints added two temporary Rational{BigInt} wrappers per unequal
finite row, and one per upper-only row. Full allocation profiling confirmed
these wrappers; rearranging the nullable expression did not eliminate them.
Keeping endpoints concrete preserves the original control allocation counts.
Existing allocation budgets were not relaxed.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 74 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

The targets contain 128 identical rows `[c, c]`, with `c` equal to two, minus
two, or one. Both row bounds equal `10c`, and column bounds are `[0, 10]`.
Candidates equal the existing column bounds, so the model is retained unchanged.
The unequal-bound control has rows `[2, 2]`, row bounds `[8, 36]`, and column
bounds `[1, 10]`. The upper-only control uses the same model with no finite
lower row bound. Both controls also retain the model unchanged. All objectives
are ones.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Equality, coefficient 2 | 709,184 | 663,408 | 6.45% | 20,307 → 18,771 |
| Equality, coefficient -2 | 702,976 | 656,368 | 6.63% | 20,051 → 18,515 |
| Equality, coefficient 1 | 528,384 | 481,968 | 8.78% | 15,443 → 13,907 |
| Unequal-bound control | 1,110,832 | 1,110,688 | — | 30,937 → 30,937 |
| Upper-only control | 787,632 | 786,960 | — | 21,977 → 21,977 |

Each target removes 1,536 allocations. Both controls retain their allocation
counts; small byte differences reflect cross-process exact-arithmetic variation,
so no benefit is claimed for those cases.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 99,408 → 96,376 | 2,692 → 2,617 | 802,624 → 801,008 |
| adlittle | 686,080 → 680,360 | 19,298 → 19,142 | 3,472,320 → 3,461,696 |
| kb2 | 529,784 → 524,088 | 14,843 → 14,699 | 10,902,472 → 10,896,024 |
| sc50a | 251,128 → 244,472 | 6,843 → 6,663 | 3,042,472 → 3,040,104 |
| flugpl | 142,408 → 139,120 | 3,742 → 3,685 | 1,291,584 → 1,287,808 |

All five direct propagation passes benefit; sc50a removes 180 allocations.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 938,160 → 936,960 | 916,592 → 914,224 | 18 |
| adlittle | 4,262,656 → 4,251,744 | 4,539,360 → 4,528,384 | 246 |
| kb2 | 11,356,808 → 11,351,240 | 11,370,232 → 11,364,072 | 144 |
| sc50a | 3,388,392 → 3,385,080 | 3,341,000 → 3,337,688 | 36 |
| flugpl | 1,400,920 → 1,397,720 | 1,445,480 → 1,442,632 | 63 |

Full presolve and both whole solves remove allocations on all five fixtures.
Paths without presolve keep identical allocation counts, with byte differences
from -128 to +160. No improvement is claimed for these unchanged paths.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-equal-row-bounds-allocations-before.toml`](propagation-equal-row-bounds-allocations-before.toml)
and [`propagation-equal-row-bounds-allocations-after.toml`](propagation-equal-row-bounds-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-equal-row-bounds-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function propagation_equal_row_bounds_probe(kind; count=128)
    coefficient = kind == :negative ? -2.0 : kind == :unit ? 1.0 : 2.0
    if kind in (:unequal, :upper_only)
        return LinearProblem(sparse(fill(coefficient, count, 2)), ones(2);
            row_lower=fill(kind == :upper_only ? nothing : 4coefficient, count),
            row_upper=fill(18coefficient, count),
            column_lower=fill(1.0, 2), column_upper=fill(10.0, 2))
    end
    return LinearProblem(sparse(fill(coefficient, count, 2)), ones(2);
        row_lower=fill(10coefficient, count), row_upper=fill(10coefficient, count),
        column_lower=zeros(2), column_upper=fill(10.0, 2))
end
for kind in (:positive, :negative, :unit, :unequal, :upper_only)
    problem = propagation_equal_row_bounds_probe(kind)
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

All three target allocation guards failed on the original implementation:
20,352 exceeded 19,900, 20,059 exceeded 19,650, and 15,451 exceeded 15,000.
The other 328 initial assertions passed, including both controls. A further
24 assertions were added for distinguishing equal and nearly equal stored
BigFloat endpoints. All 355 new assertions now pass as part of 3,285 targeted
propagation and presolve assertions. Whole-pass budgets use allocation counts
to avoid unstable exact-arithmetic byte totals.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; positive,
negative, unit, and fractional coefficients; finite zero versus unbounded row
sides; signed zero; exact equality; unequal endpoints; preservation of stored
192/256-bit BigFloat values under lower ambient precision; incremental activation
of later rows; changed flags; source bounds; and postsolve. The near-equality
regression fixes a column at the upper endpoint: incorrectly merging distinct
row endpoints would report infeasibility instead of removing a satisfied row.

Independent review found no issues in the final implementation and separately
passed all 355 new assertions. Its 2,340 additional assertions passed against
the final bounded-flag variant: 188 paired propagation calls and 32 idle checks.
These cover differing stored BigFloat precisions, unequal values that round
equal, signed zero, unbounded sides, contradictions, caches, worklists, postsolve,
and basis restoration. The reviewed variant and final production function
match except explanatory comments and parentheses around fallback assertions.

The full mandatory suite passed all 23,986 assertions in 4m58.8s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
