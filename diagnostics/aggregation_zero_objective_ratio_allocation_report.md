# Reuse exact zero objective prices as elimination ratios

Round 89 changes ratio calculation in singleton and sparse equality aggregation.
Each pivot price is still converted to an exact rational first. A zero price
is reused directly as the ratio; a nonzero price retains exact division by the
pivot coefficient. This removes an unnecessary exact division for every
zero-cost elimination, including positive and negative nonunit pivots.

The existing objective-update guards, representability checks, candidate
selection, staging, row projections, and restoration remain unchanged.
Testing exact zero before division cannot discard tiny nonzero prices through
floating-point underflow. Reused rational values are not mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 88 allocation rounds. All 41 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each target probe has 128 equalities `c*x[i] + y = 5`. The `x[i]` columns have
bounds `[1,3]`, zero cost, and coefficient `c=2` or `c=-2`. The shared `y` column
is free and has cost two; the objective constant starts at seven. Singleton
aggregation can remove each `x[i]` directly. Sparse probes append
`sum(x) + 2*y <= 1000`, giving every pivot column degree two. All eliminated
column objective ratios are zero, so the final cost of `y` remains two and
the constant remains seven.

The nonzero-ratio control uses singleton aggregation with `c=2` and pivot cost
one. The no-candidate control uses zero pivot costs and row bounds `[0,1]`,
so no equality is eligible for singleton aggregation.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Singleton, coefficient 2 | 842,472 | 803,224 | 4.66% | 21,376 → 20,480 |
| Singleton, coefficient -2 | 844,632 | 804,584 | 4.74% | 21,376 → 20,480 |
| Sparse, coefficient 2 | 1,512,424 | 1,472,152 | 2.66% | 40,148 → 39,252 |
| Sparse, coefficient -2 | 1,513,584 | 1,473,584 | 2.64% | 40,151 → 39,255 |
| Nonzero-ratio control | 1,077,568 | 1,076,368 | — | 28,029 → 28,029 |
| No-candidate control | 15,256 | 15,256 | — | 278 → 278 |

Each target removes 896 allocations (seven per eliminated column). Both controls
retain their allocation counts; byte differences on unchanged paths alone establish no benefit.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 44,464 → 44,960 | 852 → 852 | 247,992 → 245,800 | 5,716 → 5,681 |
| adlittle | 61,120 → 60,816 | 615 → 608 | 181,104 → 179,968 | 2,929 → 2,915 |
| kb2 | 114,680 → 112,968 | 2,120 → 2,085 | 173,776 → 171,376 | 3,136 → 3,087 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 356,400 → 350,656 | 7,996 → 7,891 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 219,936 → 219,296 | 5,852 → 5,852 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 754,048 → 750,592 | 890,128 → 887,264 | 868,240 → 865,376 | 42 |
| adlittle | 3,358,800 → 3,355,760 | 4,147,680 → 4,145,280 | 4,424,336 → 4,422,752 | 21 |
| kb2 | 10,691,232 → 10,686,096 | 11,144,816 → 11,139,536 | 11,157,600 → 11,153,216 | 77 |
| sc50a | 2,936,944 → 2,926,336 | 3,282,688 → 3,271,888 | 3,235,728 → 3,224,928 | 210 |
| flugpl | 1,214,680 → 1,213,384 | 1,324,512 → 1,323,664 | 1,369,152 → 1,368,128 | 0 |

Full presolve and both whole solves remove 42 allocations for afiro, 21 for
adlittle, 77 for kb2, and 210 for sc50a. Flugpl retains its count. All
no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-zero-objective-ratio-allocations-before.toml`](aggregation-zero-objective-ratio-allocations-before.toml)
and [`aggregation-zero-objective-ratio-allocations-after.toml`](aggregation-zero-objective-ratio-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-zero-objective-ratio-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-zero-objective-ratio-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_zero_objective_ratio_probe(kind; count=128)
    sparse_pass = kind in (:sparse_positive, :sparse_negative)
    coefficient = kind in (:singleton_negative, :sparse_negative) ? -2.0 : 2.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    row_lower = Union{Nothing,Float64}[kind == :inequality ? 0.0 : 5.0 for _ in 1:count]
    row_upper = fill(kind == :inequality ? 1.0 : 5.0,count)
    if sparse_pass
        A = vcat(A,sparse(reshape(vcat(ones(count),2.0),1,count+1)))
        push!(row_lower,nothing); push!(row_upper,1000.0)
    end
    problem = LinearProblem(A,vcat(fill(kind == :nonzero ? 1.0 : 0.0,count),2.0);
        objective_constant=7.0,
        row_lower,row_upper,
        column_lower=vcat(fill(1.0,count),nothing),
        column_upper=vcat(fill(3.0,count),nothing))
    pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
    return problem,pass
end
for kind in (:singleton_positive, :singleton_negative, :sparse_positive,
             :sparse_negative, :nonzero, :inequality)
    problem, pass = aggregation_zero_objective_ratio_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused test file passed 532 assertions and failed the
four target allocation guards. The singleton probes allocated 21,421 and
21,384 objects, exceeding 20,900; the sparse probes allocated 40,156 and
40,159, exceeding 39,650. Both controls passed. All 536 new assertions now
pass as part of 7,259 targeted aggregation and presolve assertions.
Existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; both
aggregation passes; coefficients ±2, ±1, and ±1/2; signed zero pivot prices;
objective preservation, primal restoration, and unchanged source values.

The smallest nonzero Float32/Float64 prices, with both signs and pivot ±2,
would produce an unrepresentable nonzero objective constant. Both passes
must reject the only eligible pivot, retaining exact division for nonzero
prices. Stored 256-bit BigFloat prices ±2^-200 under ambient precision 32/64
exercise accepted nonzero ratios: their objective updates and primal
restoration remain exact, and source precision stays unchanged.

An independent read-only review found no issues. It reran all 536 focused
assertions and passed 1,232 additional baseline comparisons across 80 models,
including 320 basis restorations. It checked complete reduced results and
postsolve records, exact objectives, primal restoration, and unchanged source,
primal, and basis inputs across signed/unit/fractional pivots, sequential
zero/nonzero prices, subnormal rejection, and mixed-precision BigFloat cases.

The complete `test/runtests.jl` suite passed 32,655/32,655 assertions in
5m10.0s (exit code zero), including all existing allocation guards.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
