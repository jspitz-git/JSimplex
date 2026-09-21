# Construct exact zero for cancelled equality projections

Round 86 adds an exact-equality shortcut in `_project_equality_bound`, shared
by singleton and sparse aggregation. When the nonzero exact right-hand side
equals the computed product, a new exact zero replaces general subtraction
of the equal values. The existing zero-RHS branch remains first, as do the
unbounded and zero-column-bound returns. Product shortcuts and the final
`_represent_exact` check retain their behavior.

The equality test uses exact rationals. Tiny nonzero differences therefore
remain nonzero even when the original BigFloat input was stored at higher
precision than the working precision. Arithmetic is nonmutating, including
construction of the zero. Candidate selection, objective updates, projected
rows, and primal/basis restoration are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 85 allocation rounds. All 41 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each target probe has 128 equalities `c*x[i] + y = 2*c`. The `x[i]` columns
have bounds `[2,4]`, cost one, and coefficient `c=2` or `c=-2`. The shared `y`
column is free and has cost two. Singleton aggregation can remove each `x[i]`
directly. Sparse probes append `sum(x) + 2*y <= 1000`, giving every pivot column
degree two. The lower column endpoint projects to exact zero in every row.

The unequal-value control uses singleton aggregation with `c=2`, pivot bounds
`[2,4]`, and RHS five. The unbounded control uses `c=2`, RHS four, and free
pivot columns.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Singleton, coefficient 2 | 1,111,176 | 1,081,560 | 2.67% | 28,858 → 28,218 |
| Singleton, coefficient -2 | 1,112,352 | 1,082,672 | 2.67% | 28,861 → 28,221 |
| Sparse, coefficient 2 | 1,780,008 | 1,750,600 | 1.65% | 47,694 → 47,054 |
| Sparse, coefficient -2 | 1,782,136 | 1,752,232 | 1.68% | 47,700 → 47,060 |
| Unequal-value control | 1,121,624 | 1,121,464 | — | 29,178 → 29,178 |
| Unbounded-pivot control | 689,256 | 688,552 | — | 17,722 → 17,722 |

Each target removes 640 allocations. Both controls retain their allocation
counts. Byte differences on unchanged paths do not establish a benefit.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 45,328 → 44,720 | 852 → 852 | 271,632 → 270,912 | 6,312 → 6,312 |
| adlittle | 66,712 → 66,712 | 768 → 768 | 185,408 → 186,416 | 3,069 → 3,069 |
| kb2 | 135,760 → 135,456 | 2,600 → 2,600 | 197,640 → 197,848 | 3,755 → 3,755 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 393,016 → 393,016 | 8,951 → 8,951 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 220,352 → 219,824 | 5,852 → 5,852 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 777,312 → 777,120 | 912,576 → 911,792 | 890,784 → 890,640 | 0 |
| adlittle | 3,372,280 → 3,370,328 | 4,162,120 → 4,159,912 | 4,438,808 → 4,435,528 | 8 |
| kb2 | 10,744,680 → 10,744,408 | 11,198,184 → 11,193,928 | 11,211,752 → 11,208,056 | 0 |
| sc50a | 3,010,760 → 3,009,784 | 3,356,872 → 3,355,960 | 3,309,672 → 3,308,600 | 0 |
| flugpl | 1,220,144 → 1,219,296 | 1,330,520 → 1,329,144 | 1,374,920 → 1,373,688 | 0 |

Full presolve and both whole solves remove eight allocations for adlittle.
The other four fixtures retain their counts. All direct aggregation passes
and no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on those unchanged paths.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-cancelled-projection-allocations-before.toml`](aggregation-cancelled-projection-allocations-before.toml)
and [`aggregation-cancelled-projection-allocations-after.toml`](aggregation-cancelled-projection-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-cancelled-projection-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-cancelled-projection-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_cancelled_projection_probe(kind; count=128)
    sparse_pass = kind in (:sparse_positive, :sparse_negative)
    coefficient = kind in (:singleton_negative, :sparse_negative) ? -2.0 : 2.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    row_lower = Union{Nothing,Float64}[kind == :unequal ? 5.0 : 2coefficient for _ in 1:count]
    row_upper = fill(kind == :unequal ? 5.0 : 2coefficient,count)
    if sparse_pass
        A = vcat(A,sparse(reshape(vcat(ones(count),2.0),1,count+1)))
        push!(row_lower,nothing); push!(row_upper,1000.0)
    end
    problem = LinearProblem(A,vcat(ones(count),2.0);
        row_lower,row_upper,
        column_lower=vcat(fill(kind == :free ? nothing : 2.0,count),nothing),
        column_upper=vcat(fill(kind == :free ? nothing : 4.0,count),nothing))
    pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
    return problem,pass
end
for kind in (:singleton_positive, :singleton_negative, :sparse_positive,
             :sparse_negative, :unequal, :free)
    problem, pass = aggregation_cancelled_projection_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused test file passed 816 assertions and failed the
four target allocation guards. The singleton probes allocated 28,903 and
28,869 objects, exceeding 28,300; the sparse probes allocated 47,702 and
47,708, exceeding 47,100. Both controls passed. All 820 new assertions now pass
as part of 4,979 targeted aggregation and presolve assertions. Existing
allocation budgets were not relaxed.

Helper cases cover both signs of coefficient and bound, unit and fractional
coefficients, unrepresentable RHS/product values that cancel exactly, zero and
unbounded controls, unequal nonrepresentable results, and unchanged inputs.
Whole-model coverage includes Float32, Float64, BigFloat, and Rational{BigInt};
both aggregation passes; both-sided, lower-only, fixed, and free pivot bounds.
Tests check projected rows, costs and constant, primal restoration, and
unchanged source rows, column bounds, matrix, and costs.

BigFloat right-hand sides `2*c ± 2^-200` stored at 256-bit precision produce
representable residual endpoints `±2^-200` at ambient precision 32/64.
Only the lower pivot bound is finite; the second model row is unconstrained,
so sparse aggregation can also preserve these residuals without requiring
an unrepresentable shifted finite endpoint. Both passes must accept the
projection, retain its nonzero value, and restore the primal solution.
These tests distinguish exact cancellation from nearby values.

Independent review found no issues. All 820 focused assertions passed again.
A saved-baseline comparison passed 1,826 assertions covering 406 helper cases,
80 models, and 256 basis cases. All 16 reduced-precision residual models kept
their nonzero endpoints. Inputs, objectives, and restoration remained equivalent.

The full mandatory test suite passed **30,375/30,375 assertions** in 5m03.3s
with exit code zero.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
