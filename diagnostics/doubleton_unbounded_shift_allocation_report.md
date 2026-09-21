# Avoid unused bound shifts for unbounded doubleton rows

Round 105 changes only `substitute_free_doubleton` in `src/presolve_substitution.jl`.
After computing the matrix-update candidate, a row with neither
finite endpoint keeps both bounds directly. Its exact shift is not computed.
If either endpoint is finite, the existing exact shift calculation and both
calls to `_shift_bound_exact` remain in place.

Every affected row still undergoes its matrix update and exact representability
check, including entirely unbounded rows. Zero eliminated-column coefficients
still skip the row. Objective arithmetic, candidate staging/rejection, and
primal/basis restoration are unchanged. Original unbounded `Bound` values are
preserved, including their stored BigFloat precision.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 104 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Every target eliminates free `x` from `2*x+y=rhs` and 128 unbounded rows
`c*x+2*y`. The retained `y` has bounds `[-10,10]`, costs are `[2,3]`, and the
objective constant is seven. Four targets cover `c=3/-3` and `rhs=4/-4`
(alpha two/minus two), so each skipped shift is a nonunit exact product.

Controls use `c=3`, `rhs=4` with other row bounds `[-100,100]` or `[-Inf,100]`.
Model construction occurs outside all measurements.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive operands | 354,704 | 309,712 | 12.68% | 8,738 → 7,586 |
| Negative coefficient | 356,064 | 311,584 | 12.49% | 8,738 → 7,586 |
| Negative alpha | 356,016 | 311,568 | 12.48% | 8,738 → 7,586 |
| Both operands negative | 356,000 | 311,600 | 12.47% | 8,738 → 7,586 |
| Two finite bounds control | 702,688 | 701,728 | — | 17,954 → 17,954 |
| One finite bound control | 529,616 | 528,688 | — | 13,346 → 13,346 |

Each target removes 1,152 allocations (nine per unbounded row), reducing
allocated bytes by 12.47–12.68%. Both controls retain their allocation counts; byte differences
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
| afiro | 45,312 → 45,120 | 843 → 843 | 218,936 → 218,520 | 4,987 → 4,987 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 178,208 → 177,872 | 2,843 → 2,843 |
| kb2 | 112,128 → 112,336 | 2,060 → 2,060 | 161,856 → 161,600 | 2,836 → 2,836 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 301,424 → 300,336 | 6,647 → 6,647 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 217,816 → 216,872 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 734,280 → 733,096 | 869,976 → 868,216 | 848,392 → 846,408 | 0 |
| adlittle | 3,355,056 → 3,352,256 | 4,144,672 → 4,141,344 | 4,420,848 → 4,418,112 | 0 |
| kb2 | 10,680,648 → 10,678,552 | 11,133,352 → 11,132,040 | 11,146,184 → 11,145,256 | 0 |
| sc50a | 2,854,000 → 2,851,776 | 3,200,096 → 3,197,776 | 3,152,672 → 3,150,400 | 0 |
| flugpl | 1,203,496 → 1,201,896 | 1,312,176 → 1,311,440 | 1,356,752 → 1,355,792 | 0 |

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
[`doubleton-unbounded-shift-allocations-before.toml`](doubleton-unbounded-shift-allocations-before.toml)
and [`doubleton-unbounded-shift-allocations-after.toml`](doubleton-unbounded-shift-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=doubleton-unbounded-shift-basic-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-unbounded-shift-doubleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=doubleton-unbounded-shift-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_unbounded_shift_probe(kind; count=128, T=Float64)
    coefficient = T(kind in (:negative_coefficient,:both_negative) ? -3 : 3)
    rhs = T(kind in (:negative_alpha,:both_negative) ? -4 : 4)
    A = sparse(hcat(vcat(T(2),fill(coefficient,count)),vcat(T(1),fill(T(2),count))))
    problem = LinearProblem(A,T[2,3];objective_constant=T(7),
        row_lower=Union{Nothing,T}[rhs;fill(kind == :finite ? T(-100) : nothing,count)],
        row_upper=Union{Nothing,T}[rhs;fill(kind in (:finite,:one_sided) ? T(100) : nothing,count)],
        column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end
for kind in (:positive, :negative_coefficient, :negative_alpha, :both_negative, :finite, :one_sided)
    problem, pass = doubleton_unbounded_shift_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 450 assertions and failed the four
target allocation guards. The positive-operands probe measured 8,783 allocations; the other three
targets each measured 8,746, against limits of 8,200. Both controls passed.
All 454 new assertions now pass as part of 20,398 targeted assertions
covering presolve, free-doubleton substitution, and related allocation guards.
Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; both operand
signs; zero/nonzero right-hand sides; and unbounded, one-sided, and finite rows.
They compare matrices, bounds and unbounded identity, objective/constant,
primal and basis restoration, and source immutability.
Unbounded rows still reject unrepresentable matrix products. A half-subnormal
shift accepts an otherwise valid unbounded row but rejects either finite endpoint;
the retained variable is bounded so an alternative pivot cannot mask rejection.
Stored-256-bit unbounded BigFloat endpoints retain identity under ambient
precision 32/64. Existing exact shift and matrix-product regression guards run.

Independent read-only review found no issues. It passed 37,922 assertions:
454 focused assertions plus 37,468 independent checks against the AST-renamed
baseline substitution function. Differential coverage included 944 models,
2,832 primal comparisons, and 3,776 basis restorations; mixed boundedness and
zero/unit/nonunit shifts; stored BigFloat identity and precision; unbounded-row
matrix rejection; finite-endpoint rejection after unbounded staging; later
candidates; objective equivalence; and source immutability. Matrix exactness
and staged commit/rejection checks remain outside the finite-bound guard.

The full repository suite passed **45,283 / 45,283** assertions in 5m18.1s
(exit status 0).
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
