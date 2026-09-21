# Reuse the exact row shift in free-doubleton substitution

Round 100 changes only `substitute_free_doubleton` in `src/presolve_substitution.jl`.
For each affected row, `coefficient_exact * alpha_exact` is now computed once
and passed to both lower- and upper-bound shifts. Previously the identical exact
product was computed twice. Both calls to `_shift_bound_exact`, all exact
representability checks, and the order of row updates remain unchanged.

The shared rational is read-only. Zero coefficients still skip the row, the
eliminated equality is still skipped, and invalid candidates still discard all
staged matrix/bound changes. Objective arithmetic, primal restoration, and
basis restoration are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 99 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Every target eliminates free `x` from `2*x+y=rhs` and 128 rows `3*x+2*y`.
The retained `y` has bounds `[-10,10]`. Costs are `[2,3]` and the objective
constant is seven. Positive/negative/zero-shift probes use `rhs=4/-4/0`, with
other row bounds `[-100,100]`. One-sided and unbounded probes use `rhs=4`,
with other row bounds `[-Inf,100]` and `[-Inf,Inf]`, respectively.

The control uses `rhs=4` and also bounds `x` by `[-10,10]`, preventing free
substitution. Model construction occurs outside all measurements.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive shift | 746,144 | 701,648 | 5.96% | 19,106 → 17,954 |
| Negative shift | 747,584 | 703,040 | 5.96% | 19,106 → 17,954 |
| Zero shift | 389,792 | 350,288 | 10.13% | 9,368 → 8,472 |
| One-sided bounds | 573,904 | 529,216 | 7.79% | 14,498 → 13,346 |
| Unbounded rows | 400,032 | 355,776 | 11.06% | 9,890 → 8,738 |
| No-substitution control | 4,376 | 4,376 | — | 4 → 4 |

Nonzero-shift probes remove 1,152 allocations (nine per affected row). The
zero-shift probe removes 896 allocations (seven per row). Allocated bytes
fall by 5.96–11.06%. The control retains its allocation count; byte differences
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
| afiro | 45,824 → 45,088 | 843 → 843 | 218,136 → 217,720 | 4,987 → 4,987 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 177,872 → 177,584 | 2,843 → 2,843 |
| kb2 | 112,576 → 111,856 | 2,060 → 2,060 | 161,664 → 161,360 | 2,836 → 2,836 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 300,576 → 299,696 | 6,647 → 6,647 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 217,640 → 216,840 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 733,256 → 731,800 | 868,616 → 866,808 | 847,592 → 845,224 | 0 |
| adlittle | 3,354,496 → 3,353,200 | 4,143,120 → 4,140,976 | 4,419,744 → 4,417,936 | 0 |
| kb2 | 10,680,264 → 10,677,336 | 11,133,960 → 11,129,784 | 11,146,520 → 11,144,744 | 0 |
| sc50a | 2,854,240 → 2,851,904 | 3,198,992 → 3,197,264 | 3,152,192 → 3,149,792 | 0 |
| flugpl | 1,202,248 → 1,201,096 | 1,312,272 → 1,310,816 | 1,356,880 → 1,355,264 | 0 |

All reference fixtures retain their allocation counts at every measured stage.
The benefit in this round is demonstrated by the targeted substitution probes.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`doubleton-shared-shift-allocations-before.toml`](doubleton-shared-shift-allocations-before.toml)
and [`doubleton-shared-shift-allocations-after.toml`](doubleton-shared-shift-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=doubleton-shared-shift-basic-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-shared-shift-doubleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=doubleton-shared-shift-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_shared_shift_probe(kind; count=128, T=Float64)
    rhs = T(kind == :negative ? -4 : kind == :zero_shift ? 0 : 4)
    A = sparse(hcat(vcat(T(2),fill(T(3),count)),vcat(T(1),fill(T(2),count))))
    lower = Union{Nothing,T}[rhs; fill(kind in (:one_sided,:unbounded) ? nothing : T(-100),count)]
    upper = Union{Nothing,T}[rhs; fill(kind == :unbounded ? nothing : T(100),count)]
    problem = LinearProblem(A,T[2,3];objective_constant=T(7),row_lower=lower,row_upper=upper,
        column_lower=Union{Nothing,T}[kind == :no_substitution ? T(-10) : nothing,T(-10)],
        column_upper=Union{Nothing,T}[kind == :no_substitution ? T(10) : nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end
for kind in (:positive, :negative, :zero_shift, :one_sided, :unbounded, :no_substitution)
    problem, pass = doubleton_shared_shift_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 169 assertions and failed the five
target allocation guards. Positive/negative probes measured 19,151 / 19,114 allocations against 18,650;
zero-shift measured 9,376 against 9,000; one-sided measured 14,506 against
14,050; unbounded measured 9,898 against 9,450. The no-substitution control passed.
All 174 new assertions now pass as part of 17,314 targeted assertions
covering presolve, free-doubleton substitution, and related allocation guards.
Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; positive,
negative, and zero shifts; finite, one-sided, and unbounded row endpoints.
They compare matrices, row bounds, objective/constant, primal and basis
restoration, and source immutability. Bounded-variable controls preserve identity.
Existing regression tests cover exact representability rejection, tiny BigFloat
residuals under reduced ambient precision, cancelled bounds, and explicit CSC zeros.

Independent read-only review found no issues. Its 13,082 assertions passed:
174 focused assertions plus 12,908 independent checks against the AST-renamed
baseline substitution function. It compared 540 models and 2,160 basis
restorations, including stored-256-bit BigFloat at ambient precision 32/64,
explicit CSC zeros, unrepresentable lower/upper shifts, rejected staged
candidates followed by successful candidates, and input immutability.

The full repository suite passed **42,199 / 42,199** assertions in 5m14.0s
(exit status 0).
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
