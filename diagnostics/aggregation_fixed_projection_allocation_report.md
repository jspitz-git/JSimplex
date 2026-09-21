# Reuse the projection of equal column bounds

Round 87 changes the two aggregation call sites of `_project_equality_bound`.
Singleton and sparse aggregation reuse `projected_lower` for `projected_upper`
when the original stored column bounds compare equal. Finite fixed columns
therefore need one projection. Two unbounded endpoints also share the same
unbounded result. If the first projection failed, its `nothing` result still
rejects the candidate. Sparse aggregation retains its `implied` guard first,
so equality-implied column bounds still bypass projection altogether.

Equality is checked on the stored bounds without reducing precision. Equal
BigFloat values with different stored precisions qualify; close unequal values
do not. Bound and exact-arithmetic values are shared under the existing
nonmutating contract. The projection helper, candidate selection, objective
updates, and primal/basis restoration retain their behavior.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 86 allocation rounds. All 41 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each target probe has 128 equalities `c*x[i] + y = 5`. The `x[i]` columns are
fixed at two, have cost one, and use coefficient `c=2` or `c=-2`. The shared
`y` column is free and has cost two. Singleton aggregation can remove each
`x[i]` directly. Sparse probes append `sum(x) + 2*y <= 1000`, giving every pivot
column degree two. Both projected endpoints are one for `c=2` and nine for
`c=-2`.

The unequal-bound control uses singleton aggregation with `c=2` and pivot
bounds `[2,4]`. The unbounded probe uses `c=2` and free pivot columns.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Singleton, coefficient 2 | 1,117,672 | 886,840 | 20.65% | 29,178 → 22,906 |
| Singleton, coefficient -2 | 1,118,480 | 889,040 | 20.51% | 29,181 → 22,909 |
| Sparse, coefficient 2 | 1,785,960 | 1,556,328 | 12.86% | 47,950 → 41,678 |
| Sparse, coefficient -2 | 1,786,680 | 1,557,752 | 12.81% | 47,956 → 41,684 |
| Unequal-bound control | 1,119,624 | 1,120,792 | — | 29,178 → 29,178 |
| Unbounded-pivot probe | 686,456 | 672,664 | 2.01% | 17,658 → 17,146 |

Each fixed-bound target removes 6,272 allocations. The unbounded probe removes
512 by sharing the first unbounded projection. The unequal-bound control
retains its allocation count; its byte difference alone establishes no benefit.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 45,616 → 45,744 | 852 → 852 | 270,352 → 269,616 | 6,312 → 6,312 |
| adlittle | 66,712 → 66,712 | 768 → 768 | 185,600 → 185,856 | 3,069 → 3,069 |
| kb2 | 135,920 → 135,632 | 2,600 → 2,600 | 197,944 → 198,792 | 3,755 → 3,755 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 391,960 → 392,872 | 8,951 → 8,951 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 219,616 → 219,392 | 5,852 → 5,852 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 776,000 → 775,888 | 912,160 → 911,088 | 889,728 → 888,672 | 0 |
| adlittle | 3,368,312 → 3,368,984 | 4,159,432 → 4,158,504 | 4,436,248 → 4,435,368 | 0 |
| kb2 | 10,744,040 → 10,742,920 | 11,196,072 → 11,195,864 | 11,209,896 → 11,209,720 | 0 |
| sc50a | 3,008,696 → 3,009,304 | 3,354,712 → 3,355,832 | 3,307,576 → 3,308,344 | 0 |
| flugpl | 1,218,320 → 1,214,312 | 1,328,296 → 1,324,368 | 1,372,648 → 1,369,168 | 126 |

Full presolve and both whole solves remove 126 allocations for flugpl.
The other four fixtures retain their counts. All direct aggregation passes
and no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on those unchanged paths.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-fixed-projection-allocations-before.toml`](aggregation-fixed-projection-allocations-before.toml)
and [`aggregation-fixed-projection-allocations-after.toml`](aggregation-fixed-projection-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-fixed-projection-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-fixed-projection-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_fixed_projection_probe(kind; count=128)
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
        column_lower=vcat(fill(kind == :free ? nothing : 2.0,count),nothing),
        column_upper=vcat(fill(kind == :free ? nothing : kind == :unequal ? 4.0 : 2.0,count),nothing))
    pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
    return problem,pass
end
for kind in (:singleton_positive, :singleton_negative, :sparse_positive,
             :sparse_negative, :unequal, :free)
    problem, pass = aggregation_fixed_projection_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused test file passed 756 assertions and failed the
four target allocation guards. The singleton probes allocated 29,223 and
29,189 objects, exceeding 27,000; the sparse probes allocated 47,958 and
47,964, exceeding 45,900. Both other probes passed. All 760 new assertions now
pass as part of 5,739 targeted aggregation and presolve assertions. Existing
allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; both
aggregation passes; positive/negative coefficients; negative, zero, unit, and
nonunit fixed values. Tests check projected intervals, costs and constant,
primal restoration, and unchanged source rows, column bounds, matrix, and costs.
Separate sparse cases confirm that fixed bounds implied by the equality still
allow the equality row to be removed.

Equal BigFloat endpoints stored at 64 and 256 bits project identically at
ambient precision 32/64. Near-equal endpoints are arranged so that the first
projection is representable and the second is not; incorrectly treating them
as equal would accept a candidate that must be rejected. Equal fixed endpoints
whose projection is unrepresentable are also rejected. Stored inputs retain
their values and precisions.

Independent review found no issues. All 760 focused assertions passed again.
A saved-baseline comparison passed 1,384 assertions across 88 models and 352
basis restorations, covering fixed/free/implied paths, rejected projections,
near-unequal endpoints, stored precision, and complete result/input preservation.

The full mandatory test suite passed **31,135/31,135 assertions** in 5m08.1s
with exit code zero.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
