# Avoid unit-pivot division in sparse row substitution

Round 91 changes the row-substitution multiplier in sparse equality aggregation.
The stored coefficient from the other row is still converted to an exact
rational first. Pivot one reuses it; pivot minus one negates it exactly;
all other pivots retain exact division.

Unit comparisons and negation operate on exact rational values, so ambient
BigFloat precision cannot change the coefficient or misclassify a near-unit
pivot. Objective ratios, row shifts, matrix updates, representability checks,
candidate selection, staging, and restoration retain their previous paths.
Reusing a rational value does not mutate its source.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 90 allocation rounds. All 41 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each target probe has 128 equalities `c*x[i] + y = 5`, with pivot `c=1` or
`c=-1`, zero-cost `x[i]` bounded by `[1,3]`, and a free shared `y` with cost
two. An extra row `d*sum(x) + 2*y <= 1000`, with `d=2` or `d=-2`, gives each
pivot column degree two. The objective constant starts and ends at seven.
After all eliminations, the last row has coefficient `2 - 128*d/c` and upper
bound `1000 - 640*d/c`. The four targets cover every pivot/coefficient sign
combination and repeated updates of the shared row.

The nonunit control uses the same sparse probe with `c=2,d=2`. The singleton
control uses `c=1` and omits the extra row, exercising a pass unaffected by
this change.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Pivot 1, other coefficient 2 | 1,429,000 | 1,387,320 | 2.92% | 38,222 → 37,070 |
| Pivot 1, other coefficient -2 | 1,431,504 | 1,388,912 | 2.98% | 38,231 → 37,079 |
| Pivot -1, other coefficient 2 | 1,446,336 | 1,410,688 | 2.46% | 38,743 → 37,847 |
| Pivot -1, other coefficient -2 | 1,446,136 | 1,410,120 | 2.49% | 38,734 → 37,838 |
| Nonunit-pivot control | 1,475,080 | 1,475,688 | — | 39,380 → 39,380 |
| Singleton-pass control | 761,112 | 762,264 | — | 19,328 → 19,328 |

Positive-pivot targets remove 1,152 allocations (nine per substitution);
negative-pivot targets remove 896 (seven per substitution). Both controls retain
their allocation counts; byte differences alone establish no benefit on unchanged
paths.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 44,192 → 44,784 | 843 → 843 | 245,728 → 242,352 | 5,665 → 5,587 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 177,984 → 177,680 | 2,888 → 2,861 |
| kb2 | 112,160 → 112,544 | 2,060 → 2,060 | 170,608 → 169,344 | 3,087 → 3,028 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 350,608 → 341,520 | 7,882 → 7,651 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 215,720 → 216,168 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 751,456 → 749,808 | 887,504 → 885,808 | 865,648 → 863,392 | 55 |
| adlittle | 3,356,032 → 3,356,192 | 4,146,752 → 4,145,200 | 4,423,504 → 4,422,480 | 27 |
| kb2 | 10,685,960 → 10,684,776 | 11,139,320 → 11,137,800 | 11,153,480 → 11,151,080 | 64 |
| sc50a | 2,926,656 → 2,914,344 | 3,271,568 → 3,260,232 | 3,224,368 → 3,212,488 | 336 |
| flugpl | 1,205,136 → 1,206,000 | 1,315,128 → 1,315,192 | 1,359,560 → 1,359,752 | 0 |

Full presolve and both whole solves remove 55 allocations for afiro, 27 for
adlittle, 64 for kb2, and 336 for sc50a. Flugpl retains its count. Singleton
aggregation retains its allocation count on all five fixtures.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-unit-multiplier-allocations-before.toml`](aggregation-unit-multiplier-allocations-before.toml)
and [`aggregation-unit-multiplier-allocations-after.toml`](aggregation-unit-multiplier-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-unit-multiplier-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-unit-multiplier-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_unit_multiplier_probe(kind; count=128)
    coefficient = kind in (:negative_positive,:negative_negative) ? -1.0 : kind == :nonunit ? 2.0 : 1.0
    other_coefficient = kind in (:positive_negative,:negative_negative) ? -2.0 : 2.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    row_lower = Union{Nothing,Float64}[5.0 for _ in 1:count]
    row_upper = fill(5.0,count)
    if kind != :singleton
        A = vcat(A,sparse(reshape(vcat(fill(other_coefficient,count),2.0),1,count+1)))
        push!(row_lower,nothing); push!(row_upper,1000.0)
    end
    problem = LinearProblem(A,vcat(zeros(count),2.0);objective_constant=7.0,
        row_lower,row_upper,column_lower=vcat(fill(1.0,count),nothing),
        column_upper=vcat(fill(3.0,count),nothing))
    pass = kind == :singleton ? JSimplex.aggregate_singleton_equalities : JSimplex.aggregate_sparse_equalities
    return problem,pass
end
for kind in (:positive_positive, :positive_negative, :negative_positive,
             :negative_negative, :nonunit, :singleton)
    problem, pass = aggregation_unit_multiplier_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 938 assertions and failed the
four target allocation guards. The positive-pivot probes allocated 38,267
and 38,239 objects, exceeding 37,600; negative-pivot probes allocated 38,751
and 38,742, exceeding 38,100. Both controls passed. All 942 new
assertions now pass as part of 8,897 targeted aggregation and presolve
assertions. Existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; both unit
pivot signs; signed and explicitly stored zero off-pivot coefficients; lower,
upper, two-sided, and unbounded other rows. Tests verify exact matrix entries,
shifted bounds, objective preservation, primal restoration, and unchanged
source matrices/bounds. Probes exercise projected pivot bounds and repeated
updates of the shared row.

Stored 256-bit BigFloat coefficients ±2^-200 under ambient precision 32/64
exercise accepted tiny multipliers and exact matrix/bound updates. Rejection
cases use pivots or off-pivot coefficients of ±(1 ± 2^-200). Finite other-row
bounds expose unrepresentable shifts; unbounded rows expose unrepresentable
matrix coefficients. The only eligible pivot must be rejected in each case,
retaining the original matrix and bounds. These cases guard against rounding
before exact conversion and approximate unit-pivot comparisons.

An independent read-only review found no issues. It reran all 942 focused
assertions and passed 2,768 additional baseline comparisons across 168 models
and 672 basis restorations. Coverage included projected pivot bounds, sequential
matrix updates, staged rejection followed by acceptance, exact near-unit
rejection, and unchanged source/primal/basis inputs.

The complete `test/runtests.jl` suite passed 34,293/34,293 assertions in
5m13.3s (exit code zero), including all existing allocation guards.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
