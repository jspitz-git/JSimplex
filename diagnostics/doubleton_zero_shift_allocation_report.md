# Reuse exact zero for free-doubleton row shifts

Round 101 changes only `substitute_free_doubleton` in `src/presolve_substitution.jl`.
After converting a row coefficient exactly and skipping explicit zero entries,
the row shift reuses `alpha_exact` when it is zero. Nonzero `alpha_exact` retains
the existing exact product. This removes multiplication by exact zero for
eliminations whose equality has a zero right-hand side.

The existing exact representation checks on alpha/beta still precede all row
updates. Both bound shifts use the same exact rational as in round 100.
Matrix and objective arithmetic, candidate staging, rejection, and primal/basis
restoration remain unchanged. No tolerance or rounded zero comparison is used.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 100 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Every target eliminates free `x` from `2*x+y=0` and 128 rows `c*x+2*y`.
The retained `y` has bounds `[-10,10]`. Costs are `[2,3]` and the objective
constant is seven. Positive/negative-coefficient probes use `c=3/-3`, with
other row bounds `[-100,100]`. One-sided and unbounded probes use `c=3`,
with other row bounds `[-Inf,100]` and `[-Inf,Inf]`, respectively.

The nonzero-shift control uses `2*x+y=4` and `c=3` with finite bounds.
The no-substitution control additionally bounds `x` by `[-10,10]`.
Model construction occurs outside all measurements.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive coefficient | 351,344 | 310,704 | 11.57% | 8,472 → 7,576 |
| Negative coefficient | 352,240 | 312,928 | 11.16% | 8,472 → 7,576 |
| One-sided bounds | 352,192 | 312,848 | 11.17% | 8,472 → 7,576 |
| Unbounded rows | 352,352 | 312,896 | 11.20% | 8,472 → 7,576 |
| Nonzero-shift control | 704,176 | 703,488 | — | 17,954 → 17,954 |
| No-substitution control | 4,376 | 4,376 | — | 4 → 4 |

Each target removes 896 allocations (seven per affected row), reducing
allocated bytes by 11.16–11.57%. Both controls retain their allocation counts; byte differences
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
| afiro | 45,632 → 45,104 | 843 → 843 | 218,104 → 218,184 | 4,987 → 4,987 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 177,872 → 177,568 | 2,843 → 2,843 |
| kb2 | 112,864 → 112,672 | 2,060 → 2,060 | 161,440 → 161,296 | 2,836 → 2,836 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 299,632 → 299,904 | 6,647 → 6,647 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 217,368 → 217,512 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 731,704 → 731,336 | 867,944 → 867,352 | 845,384 → 845,400 | 0 |
| adlittle | 3,353,184 → 3,350,640 | 4,142,000 → 4,142,640 | 4,418,752 → 4,419,136 | 0 |
| kb2 | 10,678,824 → 10,677,960 | 11,131,752 → 11,132,088 | 11,146,024 → 11,146,184 | 0 |
| sc50a | 2,852,448 → 2,851,840 | 3,198,752 → 3,197,296 | 3,151,472 → 3,149,808 | 0 |
| flugpl | 1,201,128 → 1,200,840 | 1,310,976 → 1,311,152 | 1,355,456 → 1,355,648 | 0 |

All reference fixtures retain their allocation counts at every measured stage.
The benefit in this round is demonstrated by the targeted zero-shift probes.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`doubleton-zero-shift-allocations-before.toml`](doubleton-zero-shift-allocations-before.toml)
and [`doubleton-zero-shift-allocations-after.toml`](doubleton-zero-shift-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=doubleton-zero-shift-basic-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-zero-shift-doubleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=doubleton-zero-shift-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_zero_shift_probe(kind; count=128, T=Float64)
    rhs = T(kind in (:nonzero_shift,:no_substitution) ? 4 : 0)
    coefficient = T(kind == :negative ? -3 : 3)
    A = sparse(hcat(vcat(T(2),fill(coefficient,count)),vcat(T(1),fill(T(2),count))))
    lower = Union{Nothing,T}[rhs; fill(kind in (:one_sided,:unbounded) ? nothing : T(-100),count)]
    upper = Union{Nothing,T}[rhs; fill(kind == :unbounded ? nothing : T(100),count)]
    problem = LinearProblem(A,T[2,3];objective_constant=T(7),row_lower=lower,row_upper=upper,
        column_lower=Union{Nothing,T}[kind == :no_substitution ? T(-10) : nothing,T(-10)],
        column_upper=Union{Nothing,T}[kind == :no_substitution ? T(10) : nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end
for kind in (:positive, :negative, :one_sided, :unbounded, :nonzero_shift, :no_substitution)
    problem, pass = doubleton_zero_shift_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 290 assertions and failed the four
target allocation guards. The positive-coefficient probe measured 8,517 allocations, and the negative,
one-sided, and unbounded probes each measured 8,480, against limits of 8,050. Both controls passed.
All 294 new assertions now pass as part of 17,608 targeted assertions
covering presolve, free-doubleton substitution, and related allocation guards.
Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; positive and
negative coefficients; finite, one-sided, and unbounded row endpoints.
They compare matrices, row bounds, objective/constant, primal and basis
restoration, and source immutability. Bounded-variable controls preserve identity.
Tiny nonzero shifts survive with both signs, including stored-256-bit BigFloat
at ambient precision 32/64. Half-subnormal lower and upper shifts reject the
candidate; the retained variable is bounded to prevent an alternative pivot
from masking rejection.

Independent read-only review found no issues. It passed 15,106 assertions:
294 focused assertions plus 14,812 independent checks against the AST-renamed
baseline substitution function. Differential coverage included 620 models and
2,480 basis restorations, signed-zero right-hand sides and endpoints, stored
256-bit BigFloat bounds at ambient precision 32/64, tiny nonzero exact shifts,
unrepresentable high-mantissa tiny shifts, explicit CSC zeros, staged rejection
and subsequent valid candidates, objective/primal restoration, and input
immutability.

The full repository suite passed **42,493 / 42,493** assertions in 5m11.4s
(exit status 0).
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
