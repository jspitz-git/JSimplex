# Construct exact zero directly for cancelled matrix updates

Round 97 extends the final subtraction in sparse equality matrix updates.
After the existing zero-old-value case, an exact match between the current
coefficient and the product produces `zero(ExactValue)` directly. Unequal
values retain the previous subtraction.

The equality comparison uses the current coefficient fetched from
`matrix_updates`, preserving prior substitutions. Both operands are already
exact rationals, so near-cancellation retains even tiny nonzero residuals.
Zero-multiplier and zero-old-value paths, product calculation, representability
checks, staging, bounds, objectives, and restoration remain unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 96 allocation rounds. All 41 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each probe has 128 independent pairs of rows: `2*x[i] + t*y[i] = 5` and
`2*m*x[i] + old*y[i] <= 20`. Each `x[i]` has zero cost and bounds `[1,3]`;
all `y[i]` are free with cost two, and the objective constant is seven.
Targets use `old=m*t`, so substitution makes the second row's y coefficient
exactly zero. The four targets cover `m=±2` and `t=±3`; each second-row upper
bound becomes `20-5*m`.

Independent row pairs exercise cancellation at all 128 update sites. The
unequal control uses `old=1,m=2,t=3`, and the zero-old control uses
`old=0,m=2,t=3`. Both controls retain their previous arithmetic paths.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Multiplier 2, term 3 | 1,780,472 | 1,751,304 | 1.64% | 45,881 → 45,241 |
| Multiplier 2, term -3 | 1,782,584 | 1,753,384 | 1.64% | 45,881 → 45,241 |
| Multiplier -2, term 3 | 1,782,776 | 1,753,176 | 1.66% | 45,881 → 45,241 |
| Multiplier -2, term -3 | 1,782,648 | 1,753,272 | 1.65% | 45,881 → 45,241 |
| Unequal-coefficient control | 1,820,544 | 1,819,600 | — | 46,661 → 46,661 |
| Zero-old-coefficient control | 1,768,800 | 1,768,144 | — | 45,253 → 45,253 |

Each target removes 640 allocations (five per cancellation). Both controls
retain their allocation counts; byte differences on unchanged paths alone
establish no benefit.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 45,504 → 44,624 | 843 → 843 | 219,392 → 218,432 | 5,003 → 5,003 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 177,456 → 177,088 | 2,843 → 2,843 |
| kb2 | 112,624 → 112,448 | 2,060 → 2,060 | 161,216 → 160,864 | 2,836 → 2,836 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 300,000 → 299,456 | 6,647 → 6,647 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 217,352 → 216,280 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 733,320 → 732,680 | 869,048 → 867,368 | 847,192 → 846,424 | 0 |
| adlittle | 3,354,672 → 3,353,760 | 4,144,112 → 4,142,304 | 4,420,752 → 4,418,944 | 0 |
| kb2 | 10,680,264 → 10,680,376 | 11,132,888 → 11,131,784 | 11,145,960 → 11,145,608 | 0 |
| sc50a | 2,854,304 → 2,853,296 | 3,200,560 → 3,198,816 | 3,153,440 → 3,152,000 | 0 |
| flugpl | 1,205,920 → 1,204,656 | 1,315,992 → 1,315,064 | 1,360,424 → 1,359,608 | 0 |

All five fixtures retain their allocation counts for both aggregation passes,
full presolve, and both whole solves. The measured savings occur in the probes
constructed to cancel coefficients exactly.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-cancelled-matrix-allocations-before.toml`](aggregation-cancelled-matrix-allocations-before.toml)
and [`aggregation-cancelled-matrix-allocations-after.toml`](aggregation-cancelled-matrix-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-cancelled-matrix-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-cancelled-matrix-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_cancelled_matrix_probe(kind; count=128)
    multiplier = kind in (:negative_positive,:negative_negative) ? -2.0 : 2.0
    term = kind in (:positive_negative,:negative_negative) ? -3.0 : 3.0
    old = kind == :unequal ? 1.0 : kind == :zero_old ? 0.0 : multiplier*term
    odd = collect(1:2:2count); even = odd .+ 1
    rows = vcat(odd,odd,even); columns = vcat(odd,even,odd)
    values = vcat(fill(2.0,count),fill(term,count),fill(2multiplier,count))
    if !iszero(old)
        append!(rows,even); append!(columns,even); append!(values,fill(old,count))
    end
    A = sparse(rows,columns,values,2count,2count)
    lower = Union{Nothing,Float64}[isodd(i) ? 5.0 : nothing for i in 1:2count]
    upper = [isodd(i) ? 5.0 : 20.0 for i in 1:2count]
    problem = LinearProblem(A,[isodd(i) ? 0.0 : 2.0 for i in 1:2count];objective_constant=7.0,
        row_lower=lower,row_upper=upper,
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end
for kind in (:positive_positive, :positive_negative, :negative_positive,
             :negative_negative, :unequal, :zero_old)
    problem, pass = aggregation_cancelled_matrix_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 746 assertions and failed the
four target allocation guards. The four targets allocated 45,926,
45,889, 45,889, and 45,889 objects, each exceeding 45,550. Both controls passed. All 750 new
assertions now pass as part of 14,997 targeted aggregation and presolve
assertions. Existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; signed unit,
nonunit, and fractional factors; implied/projected pivot bounds; cancellation,
shifted bounds, objectives, restoration, and unchanged source storage/bounds.
Sequential substitutions include coefficients that only match the second
product after the first committed update, plus zero/nonzero controls.

Stored 256-bit factors 1 ± 2^-200 cancel against their exact products under
ambient precision 32/64. Nearly equal coefficients with residuals ±2^-200
retain those residuals exactly. Adjacent Float32/Float64 values also remain
nonzero after subtraction. These cases distinguish exact cancellation from
approximate comparisons while checking preserved source precision and primal
restoration.

An independent read-only review found no issues. It reran all 750 focused
assertions and passed 2,864 additional baseline comparisons across 160 models
and 640 basis cases. Coverage included signed/fractional factors, sequential
committed coefficients, reduced-precision BigFloat cancellation and residuals,
adjacent floating values, staged rejection, and source/primal/basis immutability.

The complete `test/runtests.jl` suite passed 40,393/40,393 assertions in
5m13.3s (exit code zero), including all existing allocation guards.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
