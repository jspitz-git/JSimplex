# Project zero column bounds without general exact arithmetic

Round 83 adds a finite-zero shortcut to `_project_equality_bound`, shared by
singleton and sparse aggregation. A zero column bound projects directly to the
exact right-hand side, so conversion of zero, multiplication, and subtraction
are unnecessary. The shortcut still calls `_represent_exact`; an endpoint
that cannot be stored exactly is rejected as before. The existing unbounded
return remains first, and nonzero bounds retain the prior arithmetic path.

The zero check operates on the stored value without reducing its precision.
Both signed floating zeros qualify; tiny nonzero BigFloat values do not.
The shortcut uses nonmutating exact arithmetic and preserves the existing
candidate selection, objective updates, projected rows, and restoration.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 82 allocation rounds. All 41 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each target probe has 128 equalities `c*x[i] + y = 5`. The `x[i]` columns have
bounds `[0,3]`, cost one, and coefficient `c=2` or `c=-2`. The shared `y` column
is free and has cost two. Singleton aggregation can remove each `x[i]`
directly. Sparse probes append `sum(x) + 2*y <= 1000`, giving every pivot column
degree two. Each removed column has one zero endpoint to project.

The nonzero-bound control uses singleton aggregation with `c=2` and pivot
bounds `[1,3]`; the unbounded control uses `c=2` with free pivot columns.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Singleton, coefficient 2 | 1,104,760 | 985,368 | 10.81% | 28,538 → 25,338 |
| Singleton, coefficient -2 | 1,105,968 | 986,720 | 10.78% | 28,541 → 25,341 |
| Sparse, coefficient 2 | 1,773,032 | 1,653,608 | 6.74% | 47,310 → 44,110 |
| Sparse, coefficient -2 | 1,774,584 | 1,655,160 | 6.73% | 47,316 → 44,116 |
| Nonzero-bound control | 1,120,680 | 1,121,560 | — | 29,178 → 29,178 |
| Unbounded-pivot control | 687,320 | 687,480 | — | 17,658 → 17,658 |

Each target removes 3,200 allocations. Both controls retain their allocation
counts. Byte differences on unchanged paths do not establish a benefit.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 45,280 → 44,816 | 870 → 852 | 272,920 → 269,776 | 6,367 → 6,312 |
| adlittle | 67,392 → 66,712 | 788 → 768 | 191,248 → 185,152 | 3,232 → 3,069 |
| kb2 | 143,000 → 137,888 | 2,794 → 2,656 | 197,480 → 197,592 | 3,755 → 3,755 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 400,768 → 392,392 | 9,173 → 8,951 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 229,544 → 225,336 | 6,098 → 6,013 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 782,016 → 777,232 | 916,640 → 912,816 | 894,816 → 890,752 | 107 |
| adlittle | 3,380,688 → 3,370,280 | 4,170,336 → 4,159,496 | 4,446,496 → 4,436,568 | 242 |
| kb2 | 10,753,656 → 10,744,640 | 11,208,360 → 11,198,720 | 11,221,832 → 11,211,280 | 210 |
| sc50a | 3,025,944 → 3,008,520 | 3,371,752 → 3,354,472 | 3,324,776 → 3,307,352 | 437 |
| flugpl | 1,248,632 → 1,239,512 | 1,358,384 → 1,348,720 | 1,403,008 → 1,393,200 | 221 |

Full presolve and both whole solves remove allocations on all five fixtures:
107 for afiro, 242 for adlittle, 210 for kb2, 437 for sc50a, and 221 for flugpl.
Every no-presolve solve retains its allocation count. Small cross-process byte
variations on unchanged paths reflect exact-arithmetic allocation variation;
no benefit is claimed from those byte differences alone.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-zero-projection-allocations-before.toml`](aggregation-zero-projection-allocations-before.toml)
and [`aggregation-zero-projection-allocations-after.toml`](aggregation-zero-projection-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-zero-projection-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-zero-projection-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_zero_projection_probe(kind; count=128)
    sparse_pass = kind in (:sparse_positive, :sparse_negative)
    coefficient = kind in (:singleton_negative, :sparse_negative) ? -2.0 : 2.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    row_lower = Union{Nothing,Float64}[5.0 for _ in 1:count]
    row_upper = fill(5.0,count)
    if sparse_pass
        A = vcat(A,sparse(reshape(vcat(ones(count),2.0),1,count+1)))
        push!(row_lower,nothing); push!(row_upper,1000.0)
    end
    problem = LinearProblem(A,vcat(ones(count),2.0);
        row_lower,row_upper,
        column_lower=vcat(fill(kind == :free ? nothing : kind == :nonzero ? 1.0 : 0.0,count),nothing),
        column_upper=vcat(fill(kind == :free ? nothing : 3.0,count),nothing))
    pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
    return problem,pass
end
for kind in (:singleton_positive, :singleton_negative, :sparse_positive,
             :sparse_negative, :nonzero, :free)
    problem, pass = aggregation_zero_projection_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused test file passed 628 assertions and failed the
four target allocation guards. The singleton probes allocated 28,583 and
28,549 objects, exceeding 27,000; the sparse probes allocated 47,318 and
47,324, exceeding 46,000. Both controls passed. All 632 new assertions now pass
as part of 2,339 targeted aggregation and presolve assertions. Existing
allocation budgets were not relaxed.

Helper cases cover both signed zeros, both coefficient signs, unit and nonunit
coefficients, nonzero controls, unbounded endpoints, and unrepresentable exact
right-hand sides such as `1/3`. Whole-model coverage includes Float32, Float64,
BigFloat, and Rational{BigInt}; both aggregation passes; lower-zero, upper-zero,
and fixed-zero pivot bounds. Tests check projected rows, costs and constant,
primal restoration, and unchanged source rows, column bounds, matrix, and costs.

BigFloat bounds `±2^-200` stored at 256-bit precision yield unrepresentable
projected endpoints near five at ambient precision 32/64. The helper must
reject those endpoints, and both aggregation passes must reject the only
eligible pivot. These tests prevent tiny nonzero bounds from taking the zero
shortcut and check preservation of stored precision.

Independent review found no issues. All 632 focused assertions passed again.
A saved-baseline comparison passed 2,016 assertions covering 480 helper cases,
96 models, and 384 basis restorations. Three additional assertions checked
rational identity reuse under the existing nonmutating arithmetic contract.

The full mandatory test suite passed **27,735/27,735 assertions** in 5m09.5s
with exit code zero.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
