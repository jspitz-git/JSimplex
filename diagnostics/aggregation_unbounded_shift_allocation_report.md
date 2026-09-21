# Avoid unused bound shifts in sparse equality aggregation

Round 106 changes only `aggregate_sparse_equalities` in `src/presolve_aggregation.jl`.
For an affected row with neither finite endpoint, both bounds are kept directly
and its exact shift is not computed. If either endpoint is finite, the existing
exact shift calculation and both `_shift_bound_exact` calls remain in place.

Every affected row still undergoes matrix updates and their exact representability
checks. Bound changes are still staged and committed, so modified-row bookkeeping
and later candidate selection remain unchanged. Objective arithmetic, candidate
rollback, and primal/basis restoration are unchanged. Original unbounded `Bound`
values retain identity, including their stored BigFloat precision.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 105 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Every target contains 128 independent pairs: `2*x[i]+y[i]=rhs` and an
unbounded row `c*x[i]+3*y[i]`. Each `x[i]` is free, each `y[i]` has bounds
`[-10,10]`, costs are zero/two respectively, and the objective constant is seven.
Four targets cover `c=4/-4` and `rhs=4/-4`; the multiplier is two/minus two,
so each skipped shift is a nonunit exact product. All 128 equalities are removed.

Controls use `c=4`, `rhs=4` with other row bounds `[-100,100]` or `[-Inf,100]`.
Model construction occurs outside all measurements.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive operands | 1,011,752 | 969,720 | 4.15% | 24,631 → 23,479 |
| Negative coefficient | 1,013,064 | 970,984 | 4.15% | 24,631 → 23,479 |
| Negative right-hand side | 1,013,336 | 970,984 | 4.18% | 24,631 → 23,479 |
| Both operands negative | 1,013,224 | 971,144 | 4.15% | 24,631 → 23,479 |
| Two finite bounds control | 1,359,608 | 1,360,968 | — | 33,847 → 33,847 |
| One finite bound control | 1,186,440 | 1,187,848 | — | 29,239 → 29,239 |

Each target removes 1,152 allocations (nine per affected unbounded row),
reducing allocated bytes by 4.15–4.18%. Both controls retain their allocation counts; byte differences
on unchanged paths alone establish no benefit.

| Model | Basic before → after | Basic allocations before → after | Doubleton before → after | Doubleton allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 1,392 → 1,392 | 15 → 15 | 1,072 → 1,072 | 3 → 3 |
| adlittle | 2,928 → 2,928 | 15 → 15 | 2,208 → 2,208 | 3 → 3 |
| kb2 | 1,680 → 1,680 | 15 → 15 | 1,664 → 1,664 | 3 → 3 |
| sc50a | 17,760 → 17,760 | 60 → 60 | 1,808 → 1,808 | 3 → 3 |
| flugpl | 1,056 → 1,056 | 15 → 15 | 800 → 800 | 3 → 3 |

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 44,800 → 45,200 | 843 → 843 | 218,968 → 219,064 | 4,987 → 4,987 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 178,288 → 177,664 | 2,843 → 2,843 |
| kb2 | 112,368 → 112,320 | 2,060 → 2,060 | 161,968 → 161,536 | 2,836 → 2,836 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 300,736 → 300,128 | 6,647 → 6,647 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 217,576 → 217,320 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 733,624 → 733,512 | 868,744 → 868,024 | 846,920 → 846,680 | 0 |
| adlittle | 3,353,920 → 3,353,072 | 4,144,080 → 4,142,880 | 4,420,080 → 4,418,832 | 0 |
| kb2 | 10,679,624 → 10,678,632 | 11,133,320 → 11,132,200 | 11,147,240 → 11,145,016 | 0 |
| sc50a | 2,854,560 → 2,853,872 | 3,199,792 → 3,199,408 | 3,152,320 → 3,152,432 | 0 |
| flugpl | 1,202,888 → 1,202,616 | 1,312,304 → 1,312,320 | 1,356,992 → 1,356,944 | 0 |

All reference fixtures retain their allocation counts at every measured stage.
The benefit in this round is demonstrated by the targeted unbounded-row probes.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-unbounded-shift-allocations-before.toml`](aggregation-unbounded-shift-allocations-before.toml)
and [`aggregation-unbounded-shift-allocations-after.toml`](aggregation-unbounded-shift-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=aggregation-unbounded-shift-basic-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=aggregation-unbounded-shift-doubleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-unbounded-shift-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_unbounded_shift_probe(kind; count=128, T=Float64)
    coefficient = T(kind in (:negative_coefficient,:both_negative) ? -4 : 4)
    rhs = T(kind in (:negative_rhs,:both_negative) ? -4 : 4)
    odd = collect(1:2:2count); even = odd .+ 1
    A = sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(T(2),count),fill(T(1),count),fill(coefficient,count),fill(T(3),count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? T(0) : T(2) for i in 1:2count];objective_constant=T(7),
        row_lower=Union{Nothing,T}[isodd(i) ? rhs : kind == :finite ? T(-100) : nothing for i in 1:2count],
        row_upper=Union{Nothing,T}[isodd(i) ? rhs : kind in (:finite,:one_sided) ? T(100) : nothing for i in 1:2count],
        column_lower=Union{Nothing,T}[isodd(i) ? nothing : T(-10) for i in 1:2count],
        column_upper=Union{Nothing,T}[isodd(i) ? nothing : T(10) for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end
for kind in (:positive, :negative_coefficient, :negative_rhs, :both_negative, :finite, :one_sided)
    problem, pass = aggregation_unbounded_shift_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 450 assertions and failed the four
target allocation guards. The positive-operands probe measured 24,676 allocations; the other three
targets each measured 24,639, against limits of 24,000. Both controls passed.
All 454 new assertions now pass as part of 20,852 targeted assertions
covering presolve, sparse equality aggregation, and related allocation guards.
Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; both operand
signs; zero/nonzero right-hand sides; and unbounded, one-sided, and finite rows.
They compare matrices, bounds and unbounded identity, objective/constant,
primal and basis restoration, and source immutability.
Unbounded rows still reject unrepresentable matrix products. A half-subnormal
shift accepts an otherwise valid unbounded row but rejects either finite endpoint;
the retained column is either degree one or has bounds whose projection is
unrepresentable, so an alternative pivot cannot mask rejection.
Stored-256-bit unbounded BigFloat endpoints retain identity under ambient
precision 32/64. Existing exact shift and matrix-product regression guards run.

Independent read-only review found no issues. It passed 95,016 assertions:
454 focused assertions plus 94,562 independent checks against the AST-renamed
baseline aggregation function. Differential coverage included 2,200 models
and 8,800 basis restorations; all bound patterns; signed/zero/unit/nonunit
arithmetic; explicit CSC zeros; stored BigFloat identity and precision; matrix
and finite-bound rejection; staged rollback and later candidates; shared
matrix/objective/bound updates; source preservation; and postsolve equivalence.
The finite-bound guard leaves staging, commit, and modified-row bookkeeping intact.

The full repository suite passed **45,737 / 45,737** assertions in 5m29.9s
(exit status 0).
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
