# Avoid objective-ratio division for unit aggregation pivots

Round 90 changes two objective-ratio expressions in singleton and sparse
equality aggregation. After exact conversion, a pivot of one reuses the exact
price and a pivot of minus one negates it. Zero prices retain their previous
shortcut; all other pivots retain exact division.

Both pivot comparisons and the negation operate on exact rational values.
Stored BigFloat values therefore cannot be rounded to a unit pivot or rounded
during price negation by a lower ambient precision. Objective updates,
representability checks, candidate selection, staging, row projections, and
restoration remain unchanged. Reused rational values are not mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 89 allocation rounds. All 41 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each target probe has 128 equalities `c*x[i] + y = 5`. The `x[i]` columns have
bounds `[1,3]`, unit cost, and coefficient `c=1` or `c=-1`. The shared `y`
column is free and has cost two; the objective constant starts at seven.
Singleton aggregation can remove each `x[i]` directly. Sparse probes append
`sum(x) + 2*y <= 1000`, giving every pivot column degree two. Positive pivots
produce final cost -126 and constant 647; negative pivots produce cost 130
and constant -633.

The nonunit control uses singleton aggregation with `c=2` and pivot cost one.
The zero-price control uses singleton aggregation with `c=1` and pivot cost
zero. Both controls retain their previous ratio calculation paths.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Singleton, coefficient 1 | 1,034,400 | 991,136 | 4.18% | 27,005 → 25,853 |
| Singleton, coefficient -1 | 1,050,152 | 1,013,784 | 3.46% | 27,520 → 26,624 |
| Sparse, coefficient 1 | 1,704,128 | 1,661,632 | 2.49% | 45,905 → 44,753 |
| Sparse, coefficient -1 | 1,720,560 | 1,684,688 | 2.08% | 46,423 → 45,527 |
| Nonunit-pivot control | 1,078,336 | 1,078,400 | — | 28,029 → 28,029 |
| Zero-price control | 763,544 | 762,872 | — | 19,328 → 19,328 |

Positive-pivot targets remove 1,152 allocations (nine per eliminated column);
negative-pivot targets remove 896 (seven per column). Both controls retain their
allocation counts; byte differences on unchanged paths alone establish no benefit.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 44,352 → 44,496 | 852 → 843 | 247,432 → 245,648 | 5,681 → 5,665 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 180,688 → 178,736 | 2,915 → 2,888 |
| kb2 | 112,808 → 112,512 | 2,085 → 2,060 | 172,272 → 171,440 | 3,087 → 3,087 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 352,304 → 350,688 | 7,891 → 7,882 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 220,320 → 215,368 | 5,852 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 754,128 → 751,664 | 889,264 → 886,512 | 867,456 → 865,168 | 18 |
| adlittle | 3,359,504 → 3,356,256 | 4,150,704 → 4,145,568 | 4,427,088 → 4,421,744 | 45 |
| kb2 | 10,691,536 → 10,688,136 | 11,146,848 → 11,142,760 | 11,159,488 → 11,155,944 | 25 |
| sc50a | 2,928,416 → 2,925,728 | 3,274,448 → 3,271,568 | 3,227,088 → 3,223,776 | 9 |
| flugpl | 1,215,656 → 1,204,768 | 1,324,656 → 1,313,704 | 1,369,312 → 1,357,992 | 240 |

Full presolve and both whole solves remove 18 allocations for afiro, 45 for
adlittle, 25 for kb2, nine for sc50a, and 240 for flugpl.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-unit-objective-ratio-allocations-before.toml`](aggregation-unit-objective-ratio-allocations-before.toml)
and [`aggregation-unit-objective-ratio-allocations-after.toml`](aggregation-unit-objective-ratio-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-unit-objective-ratio-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-unit-objective-ratio-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_unit_objective_ratio_probe(kind; count=128)
    sparse_pass = kind in (:sparse_positive, :sparse_negative)
    coefficient = kind in (:singleton_negative, :sparse_negative) ? -1.0 : kind == :nonunit ? 2.0 : 1.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    row_lower = Union{Nothing,Float64}[5.0 for _ in 1:count]
    row_upper = fill(5.0,count)
    if sparse_pass
        A = vcat(A,sparse(reshape(vcat(ones(count),2.0),1,count+1)))
        push!(row_lower,nothing); push!(row_upper,1000.0)
    end
    problem = LinearProblem(A,vcat(fill(kind == :zero ? 0.0 : 1.0,count),2.0);
        objective_constant=7.0,
        row_lower,row_upper,
        column_lower=vcat(fill(1.0,count),nothing),
        column_upper=vcat(fill(3.0,count),nothing))
    pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
    return problem,pass
end
for kind in (:singleton_positive, :singleton_negative, :sparse_positive,
             :sparse_negative, :nonunit, :zero)
    problem, pass = aggregation_unit_objective_ratio_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused test file passed 692 assertions and failed the
four target allocation guards. Singleton counts 27,050 and 27,528 exceeded
26,500 and 27,000; sparse counts 45,913 and 46,431 exceeded 45,400 and 45,900.
Both controls passed. All 696 new assertions now pass as part of 7,955 targeted
aggregation and presolve assertions. Existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; both passes;
pivots ±1 and prices -3/0/3; exact costs/constants, primal restoration, and
unchanged source values. Sequential eliminations with both unit pivot signs
verify that prior committed objective updates are retained.

Stored 256-bit BigFloat prices ±2^-200 under ambient precision 32/64 exercise
accepted nonzero ratios and exact objective updates. Additional rejection
cases use prices or pivots of ±(1 ± 2^-200). Both passes must retain their
unrepresentable exact constant and reject the only eligible pivot, preserving
source prices and coefficients. These cases guard against negation before
exact conversion and approximate comparisons to unit pivots.

An independent read-only review found no issues. All 696 focused assertions
passed again, along with 1,248 additional baseline comparisons across 80 models
and 320 basis restorations. The review covered signed unit/nonunit pivots,
sequential updates, tiny signed BigFloat prices, near-unit rejection under
lowered precision, complete result/primal/objective/basis equivalence, and
unchanged source and restoration inputs.

The complete `test/runtests.jl` suite passed 33,351/33,351 assertions in
5m12.3s (exit code zero), including all existing allocation guards.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
