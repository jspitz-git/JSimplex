# Preserve objective values directly when the elimination ratio is zero

Round 88 changes four expressions in singleton and sparse equality aggregation.
When the exact objective ratio is zero, the candidate constant reuses
`constant_exact` and each other column's candidate cost reuses `old_cost`.
This avoids products and sums/differences with zero, including an unnecessary
coefficient conversion in the cost update. Nonzero ratios retain their path.

Ratio calculation and all representability checks remain in place. Existing
objective updates are still looked up before choosing `old_cost`; the change
therefore preserves updates committed by earlier eliminations. Candidate
selection, staging, row projections, and restoration are unchanged. Exact
arithmetic replaces values, so reusing a constant or cost does not mutate it.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 87 allocation rounds. All 41 measurements in each run
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
| Singleton, coefficient 2 | 1,053,656 | 842,920 | 20.00% | 27,008 → 21,376 |
| Singleton, coefficient -2 | 1,054,936 | 843,960 | 20.00% | 27,008 → 21,376 |
| Sparse, coefficient 2 | 1,721,896 | 1,511,720 | 12.21% | 45,780 → 40,148 |
| Sparse, coefficient -2 | 1,722,896 | 1,513,392 | 12.16% | 45,783 → 40,151 |
| Nonzero-ratio control | 1,076,096 | 1,077,664 | — | 28,029 → 28,029 |
| No-candidate control | 15,256 | 15,256 | — | 278 → 278 |

Each target removes 5,632 allocations. Both controls retain their allocation
counts; byte differences on unchanged paths alone establish no benefit.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 44,688 → 44,944 | 852 → 852 | 269,488 → 247,960 | 6,312 → 5,716 |
| adlittle | 66,712 → 61,120 | 768 → 615 | 185,904 → 180,944 | 3,069 → 2,929 |
| kb2 | 135,696 → 114,952 | 2,600 → 2,120 | 198,904 → 173,648 | 3,755 → 3,136 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 392,776 → 356,112 | 8,951 → 7,996 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 218,928 → 220,080 | 5,852 → 5,852 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 774,320 → 753,296 | 911,088 → 889,280 | 888,832 → 868,032 | 594 |
| adlittle | 3,368,424 → 3,358,608 | 4,158,104 → 4,147,424 | 4,434,856 → 4,423,728 | 293 |
| kb2 | 10,745,240 → 10,690,960 | 11,195,960 → 11,141,808 | 11,209,304 → 11,155,488 | 1,390 |
| sc50a | 3,009,944 → 2,936,352 | 3,355,960 → 3,283,536 | 3,308,456 → 3,235,584 | 1,942 |
| flugpl | 1,213,864 → 1,214,632 | 1,324,032 → 1,324,176 | 1,368,480 → 1,368,768 | 0 |

Full presolve and both whole solves remove 594 allocations for afiro, 293 for
adlittle, 1,390 for kb2, and 1,942 for sc50a. Flugpl retains its count. All
no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-zero-objective-updates-allocations-before.toml`](aggregation-zero-objective-updates-allocations-before.toml)
and [`aggregation-zero-objective-updates-allocations-after.toml`](aggregation-zero-objective-updates-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-zero-objective-updates-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-zero-objective-updates-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_zero_objective_updates_probe(kind; count=128)
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
    problem, pass = aggregation_zero_objective_updates_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused test file passed 980 assertions and failed the
four target allocation guards. The singleton probes allocated 27,053 and
27,016 objects, exceeding 24,000; the sparse probes allocated 45,788 and
45,791, exceeding 43,000. Both controls passed. All 984 new assertions now
pass as part of 6,723 targeted aggregation and presolve assertions. Existing
allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; both
aggregation passes; both coefficient signs; signed zero pivot prices; zero
and nonzero remaining costs/constants. Tests check projected rows, costs and
constant, primal restoration, and unchanged source bounds and objective.
Sequential eliminations mix zero/nonzero ratios in both orders and verify
that the current cost from prior committed updates is retained.

Stored 256-bit BigFloat values under ambient precision 32/64 exercise three
rejection paths: a tiny nonzero pivot price changes the constant by a quantity
that cannot be represented exactly; an unchanged constant remains
unrepresentable; and an unchanged other-column cost remains unrepresentable.
Both aggregation passes must still reject the only eligible pivot in each
case. The tests prevent approximate zero tests and accidental omission of
representation checks on the reused values.

Independent review found no issues. All 984 focused assertions passed again.
A saved-baseline comparison passed 1,480 assertions across 96 models and 384
basis restorations. It also checked signed costs/constants, accepted tiny
nonzero prices, retained rejection checks, sequential updates, and immutable
model/primal/basis inputs.

The full mandatory test suite passed **32,119/32,119 assertions** in 5m06.0s
with exit code zero.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
