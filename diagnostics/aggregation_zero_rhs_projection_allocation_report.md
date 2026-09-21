# Negate projected products for zero equality right-hand sides

Round 84 changes one expression in `_project_equality_bound`, shared by
singleton and sparse aggregation. If the exact right-hand side is zero,
negating the already computed product replaces general subtraction
`0 - product`. Nonzero right-hand sides retain their previous path.
The existing unbounded and zero-column-bound returns stay first; exact
conversion, product shortcuts, and representability checks are unchanged.

The zero test uses the exact rational right-hand side. Tiny nonzero BigFloat
values remain distinct from zero, including when stored precision exceeds
working precision. Negation is nonmutating. Candidate selection, objective
updates, projected rows, and primal/basis restoration retain their behavior.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 83 allocation rounds. All 41 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each target probe has 128 equalities `c*x[i] + y = 0`. The `x[i]` columns have
bounds `[1,3]`, cost one, and coefficient `c=2` or `c=-2`. The shared `y` column
is free and has cost two. Singleton aggregation can remove each `x[i]`
directly. Sparse probes append `sum(x) + 2*y <= 1000`, giving every pivot column
degree two. Each removed column has two finite nonzero endpoints to project.

The nonzero-RHS control uses singleton aggregation with `c=2` and right-hand
side five; the unbounded control uses `c=2`, zero RHS, and free pivot columns.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Singleton, coefficient 2 | 1,093,136 | 1,022,176 | 6.49% | 28,087 → 26,295 |
| Singleton, coefficient -2 | 1,094,376 | 1,023,576 | 6.47% | 28,090 → 26,298 |
| Sparse, coefficient 2 | 1,585,264 | 1,515,008 | 4.43% | 42,059 → 40,267 |
| Sparse, coefficient -2 | 1,586,512 | 1,516,432 | 4.42% | 42,065 → 40,273 |
| Nonzero-RHS control | 1,119,592 | 1,122,184 | — | 29,178 → 29,178 |
| Unbounded-pivot control | 660,752 | 662,560 | — | 16,567 → 16,567 |

Each target removes 1,792 allocations. Both controls retain their allocation
counts. Byte differences on unchanged paths do not establish a benefit.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 45,440 → 44,960 | 852 → 852 | 269,616 → 270,832 | 6,312 → 6,312 |
| adlittle | 66,712 → 66,712 | 768 → 768 | 185,056 → 185,072 | 3,069 → 3,069 |
| kb2 | 137,776 → 135,376 | 2,656 → 2,600 | 197,768 → 197,000 | 3,755 → 3,755 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 391,976 → 391,848 | 8,951 → 8,951 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 225,608 → 218,800 | 6,013 → 5,852 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 776,368 → 775,984 | 911,728 → 911,280 | 889,424 → 889,600 | 14 |
| adlittle | 3,369,640 → 3,370,232 | 4,159,816 → 4,159,272 | 4,437,048 → 4,436,152 | 0 |
| kb2 | 10,745,424 → 10,742,040 | 11,197,856 → 11,193,976 | 11,211,808 → 11,208,920 | 77 |
| sc50a | 3,008,792 → 3,008,360 | 3,354,728 → 3,354,456 | 3,307,912 → 3,307,016 | 0 |
| flugpl | 1,239,336 → 1,218,272 | 1,349,072 → 1,328,456 | 1,393,840 → 1,373,032 | 511 |

Full presolve and both whole solves remove 14 allocations for afiro, 77 for kb2,
and 511 for flugpl. Adlittle and sc50a retain their counts. Direct singleton
aggregation removes 56 allocations on kb2; direct sparse aggregation removes
161 on flugpl. Other direct passes and every no-presolve solve retain their
counts.

Small cross-process byte variations can mask small savings: afiro's whole
primal solve removes 14 allocations while its byte total increases by 176.
Allocation counts establish that reduction. Byte differences on unchanged
paths alone do not establish a benefit.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-zero-rhs-projection-allocations-before.toml`](aggregation-zero-rhs-projection-allocations-before.toml)
and [`aggregation-zero-rhs-projection-allocations-after.toml`](aggregation-zero-rhs-projection-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-zero-rhs-projection-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-zero-rhs-projection-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_zero_rhs_projection_probe(kind; count=128)
    sparse_pass = kind in (:sparse_positive, :sparse_negative)
    coefficient = kind in (:singleton_negative, :sparse_negative) ? -2.0 : 2.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    row_lower = Union{Nothing,Float64}[kind == :nonzero ? 5.0 : 0.0 for _ in 1:count]
    row_upper = fill(kind == :nonzero ? 5.0 : 0.0,count)
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
             :sparse_negative, :nonzero, :free)
    problem, pass = aggregation_zero_rhs_projection_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused test file passed 928 assertions and failed the
four target allocation guards. The singleton probes allocated 28,132 and
28,098 objects, exceeding 27,000; the sparse probes allocated 42,067 and
42,073, exceeding 41,000. Both controls passed. All 932 new assertions now pass
as part of 3,271 targeted aggregation and presolve assertions. Existing
allocation budgets were not relaxed.

Helper cases cover both signs of coefficient and bound, unit and fractional
coefficients, zero and absent bounds, nonzero RHS controls, nonrepresentable
products, and unchanged inputs. Whole-model coverage includes Float32,
Float64, BigFloat, and Rational{BigInt}; both aggregation passes; both/one-sided,
free, and fixed pivot bounds. Tests check projected rows, costs and constant,
primal restoration, and unchanged source rows, column bounds, matrix, and costs.

BigFloat right-hand sides `±2^-200` stored at 256-bit precision yield
unrepresentable projected endpoints at ambient precision 32/64. The helper
must reject those endpoints, and both aggregation passes must reject the only
eligible pivot. These tests prevent tiny nonzero right-hand sides from taking
the zero shortcut and verify preservation of stored precision.

Independent review found no issues. All 932 focused assertions passed again.
A saved-baseline comparison passed 2,464 assertions covering 272 helper cases,
192 models, and 640 basis restorations, including exact result/model equality,
primal restoration, precision preservation, and unchanged inputs.

The full mandatory test suite passed **28,667/28,667 assertions** in 5m03.5s
with exit code zero.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
