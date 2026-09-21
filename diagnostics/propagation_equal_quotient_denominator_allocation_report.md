# Equal-denominator candidate quotients in bound propagation

Round 139 changes the four candidate-bound divisions in `_propagate_row_bounds`
in `src/presolve_propagation.jl`: positive/negative coefficient crossed with
lower/upper row endpoint. When a nonzero difference and its nonunit coefficient
share a denominator, their quotient is constructed directly from their BigInt
numerators with the canonical `Rational{BigInt}` constructor. It reduces the
fraction and normalizes a negative coefficient's sign. Unequal denominators
retain general rational division. Earlier zero-difference and signed-unit
coefficient shortcuts retain their behavior and identities.

Difference computation, non-improving-bound checks, representability gates,
worklist scheduling, failure handling, row deletion, and primal/basis restoration
are unchanged. No operands are mutated and no GMP internals are used.

## Method and results

The baseline includes the preceding 138 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 60 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

All eight targets contain 128 independent two-column rows with column bounds
`[1,5]`. Integer coefficients are `[3,5]` or `[-3,-5]`. Rows have one finite
endpoint: 18 for a positive upper endpoint, 30 for a positive lower endpoint,
-30 for a negative upper endpoint, or -18 for a negative lower endpoint.
Fractional variants divide coefficients and endpoints by two. Every row computes
two nonzero quotients with shared denominators. Each division saves four
allocations, for eight per row.

Positive-upper and negative-lower rows tighten the second upper column bound to
three. Positive-lower and negative-upper rows tighten the second lower bound to
three. Float64 cannot represent the first column's candidate 13/3 or 5/3 exactly,
so it retains the original bound; Rational{BigInt} regression cases accept it.
Both accepted and rejected candidates exercise the shortcut.

The unequal-denominator control uses `[3/2,5/2]` and upper endpoint 17/2,
producing integer differences divided by half-integer coefficients. It tightens
the first upper bound to four through the fallback, while Float64 rejects the
second candidate 14/5. The unit-coefficient control uses `[1,1]` and upper
endpoint four, tightening both upper bounds to three through the earlier unit
shortcut. Input construction is outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Integer positive / upper | 1,162,904 | 1,120,408 | 3.65% | 33,100 → 32,076 |
| Integer positive / lower | 1,164,600 | 1,122,936 | 3.58% | 33,100 → 32,076 |
| Integer negative / upper | 1,164,520 | 1,122,856 | 3.58% | 33,100 → 32,076 |
| Integer negative / lower | 1,156,328 | 1,114,536 | 3.61% | 32,844 → 31,820 |
| Fractional positive / upper | 1,218,856 | 1,177,448 | 3.40% | 34,124 → 33,100 |
| Fractional positive / lower | 1,218,968 | 1,177,416 | 3.41% | 34,124 → 33,100 |
| Fractional negative / upper | 1,218,728 | 1,177,416 | 3.39% | 34,124 → 33,100 |
| Fractional negative / lower | 1,210,728 | 1,169,272 | 3.42% | 33,868 → 32,844 |
| Unequal-denominator control | 1,229,672 | 1,229,352 | — | 35,148 → 35,148 |
| Unit-coefficient control | 852,984 | 852,728 | — | 24,268 → 24,268 |

All eight targets save **1,024 allocations per call** (eight per row). Allocated bytes decrease
by **3.39–3.65%**. Both controls retain their allocation counts.
Cross-process byte differences on unchanged paths alone establish no benefit.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,024 → 45,456 |
| afiro | sparse | 4,891 → 4,891 | 214,720 → 214,784 |
| afiro | propagation | 2,437 → 2,437 | 92,392 → 93,096 |
| afiro | presolve | 16,217 → 16,217 | 728,824 → 728,200 |
| afiro | dual | 17,032 → 17,032 | 863,992 → 863,352 |
| afiro | primal | 16,938 → 16,938 | 842,424 → 841,512 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,808 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,751 → 2,751 | 174,728 → 174,808 |
| adlittle | propagation | 18,219 → 18,182 | 643,464 → 641,336 |
| adlittle | presolve | 82,535 → 82,433 | 3,333,064 → 3,326,616 |
| adlittle | dual | 84,550 → 84,448 | 4,122,664 → 4,114,792 |
| adlittle | primal | 85,348 → 85,246 | 4,399,432 → 4,391,624 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,064 → 461,736 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,024 → 607,328 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,288 → 112,512 |
| kb2 | sparse | 2,836 → 2,836 | 162,112 → 161,856 |
| kb2 | propagation | 13,096 → 12,948 | 461,280 → 454,064 |
| kb2 | presolve | 229,496 → 229,194 | 10,654,528 → 10,640,064 |
| kb2 | dual | 230,698 → 230,396 | 11,106,864 → 11,090,928 |
| kb2 | primal | 230,865 → 230,563 | 11,120,448 → 11,104,816 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,192 → 878,240 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 299,936 → 298,912 |
| sc50a | propagation | 6,044 → 6,020 | 223,888 → 221,248 |
| sc50a | presolve | 67,473 → 67,457 | 2,848,456 → 2,846,392 |
| sc50a | dual | 68,545 → 68,529 | 3,194,008 → 3,191,912 |
| sc50a | primal | 68,490 → 68,474 | 3,146,904 → 3,144,664 |
| sc50a | dual_no_presolve | 961 → 961 | 306,352 → 306,128 |
| sc50a | primal_no_presolve | 964 → 964 | 232,184 → 232,232 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 210,952 → 209,576 |
| flugpl | propagation | 3,257 → 3,253 | 123,792 → 122,544 |
| flugpl | presolve | 30,847 → 30,791 | 1,172,272 → 1,169,424 |
| flugpl | dual | 31,518 → 31,462 | 1,281,736 → 1,279,384 |
| flugpl | primal | 31,867 → 31,811 | 1,326,040 → 1,324,232 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,752 |
| flugpl | primal_no_presolve | 739 → 739 | 91,728 → 91,680 |

Complete presolve and both solves with presolve save 102 allocations for
adlittle, 302 for kb2, 16 for sc50a, and 56 for flugpl; afiro retains its counts.
Standalone propagation saves respectively 0, 37, 148, 24, and four allocations
for afiro, adlittle, kb2, sc50a, and flugpl. Distinct standalone and complete-
presolve savings reflect different input models and scheduling. Basic,
doubleton, singleton, sparse aggregation, and solves without presolve retain
their allocation counts.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`propagation-equal-quotient-denominator-allocations-before.toml`](propagation-equal-quotient-denominator-allocations-before.toml)
and [`propagation-equal-quotient-denominator-allocations-after.toml`](propagation-equal-quotient-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-equal-quotient-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function propagation_equal_quotient_denominator_probe(kind; count=128, T=Float64)
    name = string(kind)
    direction = occursin("negative",name) ? -1 : 1
    scale = startswith(name,"fraction") || kind==:unequal_denominator ? T(1)/2 : one(T)
    upper_side = endswith(name,"upper") || kind in (:unequal_denominator,:unit_coefficient)
    endpoint = T(direction>0 ? (upper_side ? 18 : 30) : (upper_side ? -30 : -18))*scale
    kind == :unequal_denominator && (endpoint=T(17)/2)
    kind == :unit_coefficient && (endpoint=T(4))
    coefficients = kind==:unit_coefficient ? ones(T,2) : T[3,5].*scale.*direction
    A = sparse(repeat(collect(1:count),inner=2),collect(1:2count),
        repeat(coefficients,count),count,2count)
    problem = LinearProblem(A,ones(T,2count);objective_constant=T(7),
        row_lower=upper_side ? fill(nothing,count) : fill(endpoint,count),
        row_upper=upper_side ? fill(endpoint,count) : fill(nothing,count),
        column_lower=ones(T,2count),column_upper=fill(T(5),2count))
    return problem,JSimplex.propagate_row_bounds
end

for kind in (:integer_positive_upper,:integer_positive_lower,:integer_negative_upper,:integer_negative_lower,:fraction_positive_upper,:fraction_positive_lower,:fraction_negative_upper,:fraction_negative_lower,:unequal_denominator,:unit_coefficient)
    problem, pass = propagation_equal_quotient_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

There are **850 new assertions**. Initial test budgets assumed a larger saving
than the measured four allocations per division, so the first combined targeted
run passed 75,991 assertions and failed only its eight new allocation guards
(75,999 total, 1m54.0s). Those provisional budgets were calibrated between the
measured before/after counts. No pre-existing allocation budget was changed.

The final file was rerun against the saved baseline functions in an isolated
Julia process, without changing production files. It passed **842 assertions**
and failed only the eight final allocation guards: 33,145 > 32,600;
two cases of 33,108 > 32,600; 32,852 > 32,350; three cases of 34,132 > 33,600;
and 33,876 > 33,350. Both control budgets passed. This confirms the final guards
still detect the original implementation.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}, all four
candidate paths, shared and unequal denominators, signed-unit controls, accepted
and inexact candidates, canonical reduction/signs, source immutability,
incremental worklist activation, changed-column masks, failure after an earlier
tightening, redundant row deletion, and primal/basis restoration. BigFloat checks
preserve stored 256-bit operands under ambient precision 32/64/256. Large integer
coefficients produce either three or `3+2^-200`, accepting the residual only at
sufficient precision. Fractional coefficients produce either three or a rational
with a non-dyadic residual, rejected at every tested binary precision. Large
rational cases use numerators derived from `2^300+1` and denominators 5, 7, 15,
and 21, for both coefficient and quotient signs and lower/upper tightening.

With the final budgets, the focused file passed all **850 assertions** in
**7.1s**, exit code zero. The complete suite below also rechecks every assertion
from the initial combined targeted run with those final budgets.

Independent read-only differential review found no issues and passed
**5,936 assertions across 156 models** (150 successful, six infeasible), exit
code zero. It included 156 full-wrapper comparisons, 450 primal restorations,
450 basis restorations, and 336 actual quotient-expression arithmetic/ownership
cases. Baseline functions were renamed to keep the old arithmetic independent.
All four candidate paths, canonical signs and reduction, source ownership,
zero/unit identities, representability gates, structural-zero filtering,
partial worklists, cascades, row removal, and failure side effects matched the
saved baseline.

The complete `test/runtests.jl` suite passed **95,496 assertions** in
**5m54.9s**, exit code zero.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
