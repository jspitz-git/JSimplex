# Avoid general products for unit equality-projection coefficients

Round 82 changes `_project_equality_bound`, used by singleton and sparse
aggregation. After converting a finite column bound to an exact rational,
a coefficient of one reuses that value and a coefficient of minus one negates
it. Other coefficients retain general multiplication. The existing unbounded
return and exact representability check are unchanged.

Conversion precedes negation, so a BigFloat bound stored at higher precision
than the working precision retains all of its information. Coefficient tests
also use the exact rational, preserving the distinction between a unit and a
near-unit value. Neither reuse nor negation mutates the original bound.
Candidate selection, row projection, objective updates, and restoration keep
their previous behavior.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 81 allocation rounds. All 41 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each probe has 128 equalities `c*x[i] + y = 5`. The `x[i]` columns have bounds
`[1,3]`, cost one, and coefficient `c=1` or `c=-1`. The shared `y` column is
free and has cost two. Singleton aggregation can remove each `x[i]` directly.
Sparse probes append `sum(x) + 2*y <= 1000`, giving each pivot column degree
two. Both passes project the finite pivot bounds onto the retained equality
rows. The nonunit control uses singleton aggregation with `c=2`; the free
control uses singleton aggregation with `c=1` and unbounded pivot columns.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Singleton, coefficient 1 | 1,119,976 | 1,031,928 | 7.86% | 29,306 → 27,002 |
| Singleton, coefficient -1 | 1,121,808 | 1,047,920 | 6.59% | 29,309 → 27,517 |
| Sparse, coefficient 1 | 1,791,000 | 1,702,456 | 4.94% | 48,206 → 45,902 |
| Sparse, coefficient -1 | 1,792,552 | 1,718,584 | 4.13% | 48,212 → 46,420 |
| Nonunit control | 1,120,824 | 1,118,776 | — | 29,178 → 29,178 |
| Unbounded-pivot control | 689,368 | 687,784 | — | 17,786 → 17,786 |

The positive-unit probes each remove 2,304 allocations, and the negative-unit
probes each remove 1,792. Both controls retain their allocation counts.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 45,568 → 46,096 | 877 → 870 | 273,552 → 270,664 | 6,386 → 6,367 |
| adlittle | 67,640 → 67,392 | 793 → 788 | 193,056 → 191,152 | 3,267 → 3,232 |
| kb2 | 148,520 → 141,912 | 2,918 → 2,794 | 197,784 → 197,960 | 3,755 → 3,755 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 403,848 → 399,696 | 9,239 → 9,173 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 235,944 → 228,664 | 6,248 → 6,098 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 783,104 → 778,624 | 919,168 → 915,168 | 896,336 → 892,784 | 52 |
| adlittle | 3,382,520 → 3,377,696 | 4,171,896 → 4,167,856 | 4,448,728 → 4,444,320 | 72 |
| kb2 | 10,757,608 → 10,753,464 | 11,211,832 → 11,206,152 | 11,225,976 → 11,219,592 | 124 |
| sc50a | 3,029,000 → 3,023,016 | 3,375,992 → 3,371,304 | 3,328,488 → 3,323,736 | 91 |
| flugpl | 1,265,496 → 1,247,000 | 1,374,848 → 1,356,576 | 1,419,568 → 1,401,328 | 426 |

Full presolve and both whole solves remove allocations on all five fixtures:
52 for afiro, 72 for adlittle, 124 for kb2, 91 for sc50a, and 426 for flugpl.
Every no-presolve solve retains its allocation count.

Cross-process exact-arithmetic byte variations can mask small changes: for
example, afiro's singleton pass removes seven allocations while its byte total
increases by 528. Allocation counts establish the reduction there. Conversely,
byte changes on paths with unchanged counts do not establish a benefit.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-unit-projection-allocations-before.toml`](aggregation-unit-projection-allocations-before.toml)
and [`aggregation-unit-projection-allocations-after.toml`](aggregation-unit-projection-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-unit-projection-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-unit-projection-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_unit_projection_probe(kind; count=128)
    sparse_pass = kind in (:sparse_positive, :sparse_negative)
    coefficient = kind in (:singleton_negative, :sparse_negative) ? -1.0 : kind == :nonunit ? 2.0 : 1.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    row_lower = Union{Nothing,Float64}[5.0 for _ in 1:count]
    row_upper = fill(5.0,count)
    if sparse_pass
        A = vcat(A,sparse(reshape(vcat(ones(count),2.0),1,count+1)))
        push!(row_lower,nothing); push!(row_upper,1000.0)
    end
    problem = LinearProblem(A,vcat(ones(count),2.0);
        row_lower,row_upper,
        column_lower=vcat(fill(kind == :free ? nothing : 1.0,count),nothing),
        column_upper=vcat(fill(kind == :free ? nothing : 3.0,count),nothing))
    pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
    return problem,pass
end
for kind in (:singleton_positive, :singleton_negative, :sparse_positive,
             :sparse_negative, :nonunit, :free)
    problem, pass = aggregation_unit_projection_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused test file passed 724 assertions and failed the
four target allocation guards. The singleton probes allocated 29,351 and
29,317 objects, exceeding 28,000; the sparse probes allocated 48,214 and
48,220, exceeding 47,000. Both controls passed. All 728 new assertions now pass
as part of 1,707 targeted aggregation and presolve assertions. Existing
allocation budgets were not relaxed.

Helper cases cover finite, zero, negative, and absent bounds; both unit signs;
nonunit coefficients; exact near-unit coefficients; and source preservation.
Whole-model cases cover Float32, Float64, BigFloat, and Rational{BigInt},
both aggregation passes, both unit signs, and both/one-sided/free pivot bounds.
They check projected rows, costs and constant, primal restoration, and unchanged
source rows, column bounds, matrix, and objective.

BigFloat bounds `1 + 2^-200` stored at 256-bit precision yield unrepresentable
projected endpoints at ambient precision 32/64. The helper must reject those
endpoints, and both aggregation passes must reject the only eligible pivot.
These tests detect rounding before exact conversion, including premature
negation of the stored BigFloat for a negative unit coefficient.

Independent review found no issues. All 728 focused assertions passed again.
A saved-baseline comparison passed 960 additional assertions: 128 helper cases,
64 model cases, and 256 basis-restoration comparisons, including precise result
and postsolve snapshots, primal restoration, and source preservation.

The full mandatory test suite passed **27,103/27,103 assertions** in 5m04.8s
with exit code zero.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
