# Reuse exact zero for basic-presolve row shifts

Round 108 changes only `_presolve_basic` in `src/presolve.jl`.
When a removed variable has an exactly zero value, rows with finite endpoints
reuse its already computed exact rational zero instead of converting their
coefficients and multiplying by zero. Nonzero eliminated values retain the
existing exact product. The unbounded-row shortcut from round 107 is unchanged.

Both `_shift_bound_exact` calls remain in place, so unchanged endpoint values
retain identity and stored precision. Objective contributions, constant checks,
staged row changes, rejection, removed-variable values/states, empty-row checks,
and primal/basis restoration are unchanged. The zero test uses the exact value;
no tolerance or rounded comparison is introduced.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 107 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Every target fixes `x=0` in 128 rows `c*x+2*y`. The retained `y` has bounds
`[-10,10]`, costs are `[2,3]`, and the objective constant is seven. Positive and
negative probes use `c=3/-3` and row bounds `[-100,100]`; the negative probe
stores negative zero for the removed value. Lower-only and upper-only probes
use `c=3` with `[-100,Inf]` and `[-Inf,100]` row bounds.

The nonzero-value control uses `x=2`, `c=3`, and `[-100,100]` row bounds.
The unbounded-row control uses `x=0`, `c=3`, and neither finite endpoint.
Model construction occurs outside all measurements.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive coefficient | 121,792 | 29,312 | 75.93% | 2,532 → 100 |
| Negative coefficient and signed zero | 122,544 | 29,312 | 76.08% | 2,532 → 100 |
| Lower bound only | 122,704 | 29,312 | 76.11% | 2,532 → 100 |
| Upper bound only | 122,928 | 29,312 | 76.16% | 2,532 → 100 |
| Nonzero-value control | 479,480 | 477,256 | — | 12,045 → 12,045 |
| Unbounded-row control | 29,312 | 29,312 | — | 100 → 100 |

Each target removes 2,432 allocations (19 per affected row), reducing
allocated bytes by 75.93–76.16%. Both controls retain their allocation counts; byte differences
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
| afiro | 45,984 → 45,792 | 843 → 843 | 218,696 → 219,240 | 4,987 → 4,987 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 177,536 → 177,936 | 2,843 → 2,843 |
| kb2 | 112,864 → 113,312 | 2,060 → 2,060 | 161,536 → 161,680 | 2,836 → 2,836 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 300,288 → 300,320 | 6,647 → 6,647 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 216,248 → 217,544 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 732,632 → 732,392 | 868,264 → 868,856 | 845,944 → 847,032 | 0 |
| adlittle | 3,351,824 → 3,347,928 | 4,142,624 → 4,137,912 | 4,419,248 → 4,414,920 | 133 |
| kb2 | 10,676,024 → 10,679,368 | 11,130,312 → 11,132,072 | 11,144,632 → 11,145,960 | 0 |
| sc50a | 2,852,768 → 2,853,280 | 3,198,768 → 3,200,080 | 3,151,376 → 3,152,560 | 0 |
| flugpl | 1,201,800 → 1,202,672 | 1,311,664 → 1,312,680 | 1,356,240 → 1,357,144 | 19 |

Full presolve and each whole primal/dual solve remove 133 allocations for
`adlittle` and 19 for `flugpl`. The other three fixtures retain their allocation
counts at those stages. Direct basic/doubleton/singleton/sparse passes retain
allocation counts for all five fixtures; the benefit appears in basic passes
reached later in the full presolve pipeline. The measured `flugpl` byte totals
rose despite the lower allocation count; no whole-solve byte reduction is
claimed for that fixture.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`basic-zero-shift-allocations-before.toml`](basic-zero-shift-allocations-before.toml)
and [`basic-zero-shift-allocations-after.toml`](basic-zero-shift-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=basic-zero-shift-basic-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=basic-zero-shift-doubleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=basic-zero-shift-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function basic_zero_shift_probe(kind; count=128, T=Float64)
    coefficient = T(kind == :negative ? -3 : 3)
    value = kind == :nonzero ? T(2) : kind == :negative ? -zero(T) : zero(T)
    problem = LinearProblem(sparse(hcat(fill(coefficient,count),fill(T(2),count))),T[2,3];objective_constant=T(7),
        row_lower=fill(kind in (:upper_only,:unbounded) ? nothing : T(-100),count),
        row_upper=fill(kind in (:lower_only,:unbounded) ? nothing : T(100),count),
        column_lower=T[value,-10],column_upper=T[value,10])
    return problem,JSimplex._presolve_basic
end
for kind in (:positive, :negative, :lower_only, :upper_only, :nonzero, :unbounded)
    problem, pass = basic_zero_shift_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 530 assertions and failed the four
target allocation guards. The positive-coefficient probe measured 2,577 allocations; the other three
targets each measured 2,540, against limits of 600. Both controls passed.
All 534 new assertions now pass as part of 21,852 targeted assertions
covering presolve, basic elimination, and related allocation guards.
Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; signed zero;
positive/negative coefficients; finite, one-sided, and unbounded rows; and
computed/cached selections. They compare matrices, endpoint identity, objective/
constant, primal and basis restoration, removed-variable state, source values,
and selection immutability.
Tiny nonzero fixed values still produce exact nonzero shifts. Half-subnormal
shifts still reject every finite endpoint. Stored-256-bit finite BigFloat
bounds and unchanged objective constants retain identity/precision under ambient
precision 32/64, and the restored removed value preserves signed zero.

Independent read-only review found no issues. It passed 53,517 additional
assertions against the AST-renamed baseline basic-presolve function, covering
1,883 differential models, 7,404 basis comparisons, and 32 matching infeasibility
results. Cases included signed/exact zero, tiny nonzero values, coefficient and
bound patterns, cached selection states, candidate rejection/commit ordering,
empty structures, primal/objective restoration, stored BigFloat object
identities, and repeated Rational{BigInt} reuse without mutation.

The full repository suite passed **46,737 / 46,737** assertions in 5m31.4s
(exit status 0).
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
