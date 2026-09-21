# Avoid general projection products for unit column bounds

Round 85 extends the product shortcuts in `_project_equality_bound`, shared
by singleton and sparse aggregation. After the existing coefficient-unit
checks, an exact column bound of one reuses the coefficient and a bound of
minus one negates it. Other bounds retain general multiplication. The checks
for unit coefficients keep their previous precedence.

The bound is converted to an exact rational before testing for a unit. Stored
BigFloat values just above or below either unit retain their full precision.
The shortcut uses nonmutating arithmetic. Unbounded and zero-bound returns,
zero-RHS handling, representability checks, candidate selection, objective
updates, and primal/basis restoration are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 84 allocation rounds. All 41 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each target probe has 128 equalities `c*x[i] + y = 5`. The `x[i]` columns have
bounds `[-1,1]`, cost one, and coefficient `c=2` or `c=-2`. The shared `y` column
is free and has cost two. Singleton aggregation can remove each `x[i]`
directly. Sparse probes append `sum(x) + 2*y <= 1000`, giving every pivot column
degree two. Each removed column has one positive and one negative unit bound.

The nonunit-bound control uses singleton aggregation with `c=2` and pivot
bounds `[2,4]`; the unbounded control uses `c=2` and free pivot columns.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Singleton, coefficient 2 | 1,117,640 | 1,039,432 | 7.00% | 29,178 → 27,130 |
| Singleton, coefficient -2 | 1,118,816 | 1,040,880 | 6.97% | 29,181 → 27,133 |
| Sparse, coefficient 2 | 1,785,576 | 1,708,712 | 4.30% | 47,950 → 45,902 |
| Sparse, coefficient -2 | 1,786,776 | 1,709,992 | 4.30% | 47,956 → 45,908 |
| Nonunit-bound control | 1,119,560 | 1,122,040 | — | 29,178 → 29,178 |
| Unbounded-pivot control | 685,768 | 687,864 | — | 17,658 → 17,658 |

Each target removes 2,048 allocations. Both controls retain their allocation
counts. Byte differences on unchanged paths do not establish a benefit.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 45,168 → 45,104 | 852 → 852 | 270,208 → 270,944 | 6,312 → 6,312 |
| adlittle | 66,712 → 66,712 | 768 → 768 | 185,232 → 186,224 | 3,069 → 3,069 |
| kb2 | 135,728 → 136,304 | 2,600 → 2,600 | 198,184 → 198,568 | 3,755 → 3,755 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 391,864 → 393,304 | 8,951 → 8,951 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 219,312 → 219,920 | 5,852 → 5,852 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 775,152 → 777,264 | 911,392 → 913,104 | 888,912 → 891,392 | 0 |
| adlittle | 3,370,600 → 3,370,936 | 4,160,680 → 4,161,400 | 4,437,384 → 4,438,168 | 0 |
| kb2 | 10,742,664 → 10,743,736 | 11,195,208 → 11,197,208 | 11,208,232 → 11,210,392 | 0 |
| sc50a | 3,008,632 → 3,010,824 | 3,354,488 → 3,357,528 | 3,307,288 → 3,310,104 | 0 |
| flugpl | 1,218,048 → 1,219,872 | 1,327,880 → 1,329,272 | 1,372,936 → 1,373,880 | 0 |

All five fixtures retain their allocation counts in both direct aggregation
passes, full presolve, and whole dual/primal solves, including paths without
presolve. Cross-process exact-arithmetic byte variations alone establish no
benefit on these fixtures. The measured reduction is confined to the targeted
unit-bound probes.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-unit-bound-projection-allocations-before.toml`](aggregation-unit-bound-projection-allocations-before.toml)
and [`aggregation-unit-bound-projection-allocations-after.toml`](aggregation-unit-bound-projection-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-unit-bound-projection-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-unit-bound-projection-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_unit_bound_projection_probe(kind; count=128)
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
        column_lower=vcat(fill(kind == :free ? nothing : kind == :nonunit_bound ? 2.0 : -1.0,count),nothing),
        column_upper=vcat(fill(kind == :free ? nothing : kind == :nonunit_bound ? 4.0 : 1.0,count),nothing))
    pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
    return problem,pass
end
for kind in (:singleton_positive, :singleton_negative, :sparse_positive,
             :sparse_negative, :nonunit_bound, :free)
    problem, pass = aggregation_unit_bound_projection_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused test file passed 884 assertions and failed the
four target allocation guards. The singleton probes allocated 29,223 and
29,189 objects, exceeding 28,000; the sparse probes allocated 47,958 and
47,964, exceeding 46,800. Both controls passed. All 888 new assertions now pass
as part of 4,159 targeted aggregation and presolve assertions. Existing
allocation budgets were not relaxed.

Helper cases cover both signs of coefficient and bound, coefficient-unit
precedence, fractional coefficients, nonunit and zero controls, absent bounds,
zero RHS, nonrepresentable products, and unchanged inputs. Whole-model coverage
includes Float32, Float64, BigFloat, and Rational{BigInt}; both aggregation
passes; both/one-sided and free pivot bounds. Tests check projected rows, costs
and constant, primal restoration, and unchanged source rows, column bounds,
matrix, and costs.

BigFloat bounds `±1 ± 2^-200` stored at 256-bit precision yield unrepresentable
projected endpoints at ambient precision 32/64. The helper must reject those
endpoints, and both aggregation passes must reject the only eligible pivot.
These tests prevent near-unit bounds from taking the unit shortcuts and verify
preservation of stored precision.

Independent review found no issues. All 888 focused assertions passed again.
A saved-baseline comparison passed 1,824 assertions covering 400 helper cases,
96 models, and 256 basis restorations, including unchanged inputs, exact model
and postsolve results, objective preservation, and stored BigFloat precision.

The full mandatory test suite passed **29,555/29,555 assertions** in 5m08.4s
with exit code zero.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
