# Avoid unused coefficient conversion and shifts in basic presolve

Round 107 changes only `_presolve_basic` in `src/presolve.jl`.
When an eliminated variable touches a row with neither finite endpoint, both
bounds are kept directly. Neither the row coefficient's exact conversion nor
its product with the eliminated value is computed. If either endpoint is finite,
the existing conversion, multiplication, and both bound-shift calls remain.

Existing objective-contribution and constant checks still precede row processing.
All touched row bounds are still staged and committed, and the variable's
removed value/state and retained matrix are recorded as before. Empty-row
checks, rejection, and primal/basis restoration are unchanged. Unbounded
bounds and unchanged BigFloat values preserve their stored identity/precision.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 106 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Every target fixes `x=value` in 128 unbounded rows `c*x+2*y`. The retained
`y` has bounds `[-10,10]`, costs are `[2,3]`, and the objective constant is seven.
Four targets cover `c=3/-3` and `value=2/-2`; every affected row avoids one
exact coefficient conversion and one exact product. The reduced objective
constant is `7+2*value`, so the objective contribution must still be applied.

Controls use `c=3`, `value=2` with row bounds `[-100,100]` or `[-Inf,100]`.
Model construction occurs outside all measurements.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive operands | 128,712 | 30,760 | 76.10% | 2,829 → 141 |
| Negative coefficient | 129,720 | 30,760 | 76.29% | 2,829 → 141 |
| Negative eliminated value | 129,704 | 30,760 | 76.28% | 2,829 → 141 |
| Both operands negative | 129,672 | 30,760 | 76.28% | 2,829 → 141 |
| Two finite bounds control | 478,888 | 477,368 | — | 12,045 → 12,045 |
| One finite bound control | 305,464 | 304,584 | — | 7,437 → 7,437 |

Each target removes 2,688 allocations (21 per affected unbounded row),
reducing allocated bytes by 76.10–76.29%. Both controls retain their allocation counts; byte differences
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
| afiro | 44,800 → 45,344 | 843 → 843 | 219,288 → 218,680 | 4,987 → 4,987 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 178,608 → 177,952 | 2,843 → 2,843 |
| kb2 | 112,144 → 113,104 | 2,060 → 2,060 | 161,968 → 161,648 | 2,836 → 2,836 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 301,776 → 299,968 | 6,647 → 6,647 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 218,392 → 216,360 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 733,576 → 732,296 | 869,160 → 868,216 | 847,752 → 845,672 | 0 |
| adlittle | 3,354,432 → 3,352,720 | 4,142,480 → 4,142,176 | 4,419,232 → 4,418,784 | 0 |
| kb2 | 10,680,136 → 10,678,312 | 11,132,504 → 11,132,360 | 11,147,512 → 11,146,456 | 0 |
| sc50a | 2,854,208 → 2,853,760 | 3,199,696 → 3,199,312 | 3,152,560 → 3,152,112 | 0 |
| flugpl | 1,203,560 → 1,202,760 | 1,313,680 → 1,312,112 | 1,358,176 → 1,356,800 | 0 |

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
[`basic-unbounded-shift-allocations-before.toml`](basic-unbounded-shift-allocations-before.toml)
and [`basic-unbounded-shift-allocations-after.toml`](basic-unbounded-shift-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=basic-unbounded-shift-basic-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=basic-unbounded-shift-doubleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=basic-unbounded-shift-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function basic_unbounded_shift_probe(kind; count=128, T=Float64)
    coefficient = T(kind in (:negative_coefficient,:both_negative) ? -3 : 3)
    value = T(kind in (:negative_value,:both_negative) ? -2 : 2)
    problem = LinearProblem(sparse(hcat(fill(coefficient,count),fill(T(2),count))),T[2,3];objective_constant=T(7),
        row_lower=fill(kind == :finite ? T(-100) : nothing,count),
        row_upper=fill(kind in (:finite,:one_sided) ? T(100) : nothing,count),
        column_lower=T[value,-10],column_upper=T[value,10])
    return problem,JSimplex._presolve_basic
end
for kind in (:positive, :negative_coefficient, :negative_value, :both_negative, :finite, :one_sided)
    problem, pass = basic_unbounded_shift_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 462 assertions and failed the four
target allocation guards. The positive-operands probe measured 2,874 allocations; the other three
targets each measured 2,837, against limits of 1,800. Both controls passed.
All 466 new assertions now pass as part of 21,318 targeted assertions
covering presolve, basic elimination, and related allocation guards.
Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; both operand
signs; zero/nonzero eliminated values; and unbounded, one-sided, and finite rows.
They compare matrices, bounds and unbounded identity, objective/constant,
primal and basis restoration, removed-variable state, and source immutability.
Half-subnormal shifts accept otherwise valid unbounded rows but reject either
finite endpoint. Unbounded rows still reject an unrepresentable objective
contribution. Stored-256-bit BigFloat bounds, removed values, and unchanged
objective constants retain precision under ambient precision 32/64.

Independent read-only review found no issues. It passed 32,100 additional
assertions against the AST-renamed baseline basic-presolve function, covering
1,104 differential models, 4,288 basis comparisons, and 32 matching infeasibility
results. Cases included mixed bounds, zero/unit/nonunit values and coefficients,
cached selections and states, shared rows, explicit CSC zeros and empty columns,
staged rejection followed by later success, exact objective checks, stored
BigFloat identity/precision, empty-row failures, and source/selection/primal/basis
immutability. Postsolve and exact objectives matched the baseline.

The full repository suite passed **46,203 / 46,203** assertions in 5m20.8s
(exit status 0).
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
