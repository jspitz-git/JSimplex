# Equal-denominator candidate differences in bound propagation

Round 138 changes the four candidate-bound differences in `_propagate_row_bounds`
in `src/presolve_propagation.jl`: positive/negative coefficient crossed with
lower/upper row endpoint. When a nonzero endpoint and nonzero other activity
share a denominator, their BigInt numerators are subtracted directly and the
canonical `Rational{BigInt}` constructor reduces the result. Unequal denominators
retain general rational subtraction. Earlier zero-activity, zero-endpoint, and
cancellation branches retain their behavior and identities.

Division by the coefficient, non-improving-bound checks, representability gates,
worklist scheduling, failure handling, row deletion, and primal/basis restoration
are unchanged. No operands are mutated and no GMP internals are used.

## Method and results

The baseline includes the preceding 137 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 60 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

All eight targets contain 128 independent two-column rows with column bounds
`[1,5]`. Integer coefficients are `[1,3]` or `[-1,-3]`. Rows have one finite
endpoint: 13 for a positive upper endpoint, 11 for a positive lower endpoint,
-11 for a negative upper endpoint, or -13 for a negative lower endpoint.
Fractional variants divide coefficients and endpoints by two. Every row computes
two nonzero, noncancelling candidate differences with shared denominators.
Integer differences save two allocations each; fractional differences save one.

Positive-upper and negative-lower rows tighten the second upper column bound to
four. Positive-lower and negative-upper rows tighten the second lower bound to
two. The first column keeps its original bounds because its candidates do not
improve them. Both improving and non-improving candidates exercise the shortcut.

The unequal-denominator control uses `[1,3]` and upper endpoint 23/2, tightening
the second upper bound to 7/2 through the fallback. The zero-endpoint control
uses `[1,3]`, upper endpoint zero, and column bounds `[-1,5]`. It uses the existing
negation shortcut: the first upper bound tightens to three, while the second
candidate 1/3 is rejected for Float64. Input construction is outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Integer positive / upper | 931,048 | 903,208 | 2.99% | 26,444 → 25,932 |
| Integer positive / lower | 931,928 | 903,544 | 3.05% | 26,444 → 25,932 |
| Integer negative / upper | 962,168 | 933,816 | 2.95% | 27,468 → 26,956 |
| Integer negative / lower | 953,992 | 925,624 | 2.97% | 27,212 → 26,700 |
| Fractional positive / upper | 1,131,784 | 1,107,416 | 2.15% | 31,948 → 31,692 |
| Fractional positive / lower | 1,131,896 | 1,107,688 | 2.14% | 31,948 → 31,692 |
| Fractional negative / upper | 1,131,864 | 1,107,240 | 2.18% | 31,948 → 31,692 |
| Fractional negative / lower | 1,123,464 | 1,099,496 | 2.13% | 31,692 → 31,436 |
| Unequal-denominator control | 1,046,248 | 1,044,952 | — | 31,052 → 31,052 |
| Zero-endpoint control | 934,152 | 933,000 | — | 26,572 → 26,572 |

The integer targets save **512 allocations per call** (four per row); the
fractional targets save **256** (two per row). Allocated bytes decrease
by **2.13–3.05%**. Both controls retain their allocation counts.
Cross-process byte differences on unchanged paths alone establish no benefit.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,440 → 45,520 |
| afiro | sparse | 4,891 → 4,891 | 215,296 → 214,480 |
| afiro | propagation | 2,437 → 2,437 | 93,496 → 92,920 |
| afiro | presolve | 16,217 → 16,217 | 728,760 → 727,048 |
| afiro | dual | 17,032 → 17,032 | 863,432 → 862,712 |
| afiro | primal | 16,938 → 16,938 | 841,960 → 840,664 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,936 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,751 → 2,751 | 174,520 → 174,472 |
| adlittle | propagation | 18,219 → 18,219 | 643,544 → 641,864 |
| adlittle | presolve | 82,539 → 82,535 | 3,330,696 → 3,329,400 |
| adlittle | dual | 84,554 → 84,550 | 4,119,864 → 4,118,920 |
| adlittle | primal | 85,352 → 85,348 | 4,396,488 → 4,395,240 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,528 → 461,128 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,408 → 607,360 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,128 → 112,272 |
| kb2 | sparse | 2,836 → 2,836 | 162,176 → 161,616 |
| kb2 | propagation | 13,096 → 13,096 | 460,464 → 458,976 |
| kb2 | presolve | 229,496 → 229,496 | 10,652,192 → 10,651,648 |
| kb2 | dual | 230,698 → 230,698 | 11,104,896 → 11,105,024 |
| kb2 | primal | 230,865 → 230,865 | 11,118,176 → 11,117,328 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,968 → 878,144 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 299,552 → 298,384 |
| sc50a | propagation | 6,056 → 6,044 | 224,112 → 221,648 |
| sc50a | presolve | 67,481 → 67,473 | 2,847,384 → 2,844,920 |
| sc50a | dual | 68,553 → 68,545 | 3,192,968 → 3,191,256 |
| sc50a | primal | 68,498 → 68,490 | 3,145,768 → 3,143,896 |
| sc50a | dual_no_presolve | 961 → 961 | 306,128 → 306,352 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 210,680 → 209,336 |
| flugpl | propagation | 3,269 → 3,257 | 124,720 → 122,752 |
| flugpl | presolve | 30,893 → 30,847 | 1,174,968 → 1,170,528 |
| flugpl | dual | 31,564 → 31,518 | 1,284,768 → 1,280,744 |
| flugpl | primal | 31,913 → 31,867 | 1,329,312 → 1,325,624 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Complete presolve and both solves with presolve save four allocations for
adlittle, eight for sc50a, and 46 for flugpl; afiro and kb2 retain their counts.
Standalone propagation saves twelve allocations for both sc50a and flugpl,
and retains its counts for the other three fixtures. Distinct standalone and
complete-presolve savings reflect different input models and scheduling.
Basic, doubleton, singleton, sparse aggregation, and solves without presolve
retain their allocation counts.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`propagation-equal-candidate-denominator-allocations-before.toml`](propagation-equal-candidate-denominator-allocations-before.toml)
and [`propagation-equal-candidate-denominator-allocations-after.toml`](propagation-equal-candidate-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-equal-candidate-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function propagation_equal_candidate_denominator_probe(kind; count=128, T=Float64)
    name = string(kind)
    direction = occursin("negative",name) ? -1 : 1
    scale = startswith(name,"fraction") ? T(1)/2 : one(T)
    upper_side = endswith(name,"upper") || kind in (:unequal_denominator,:zero_endpoint)
    endpoint = T(direction>0 ? (upper_side ? 13 : 11) : (upper_side ? -11 : -13))*scale
    kind == :unequal_denominator && (endpoint=T(23)/2)
    kind == :zero_endpoint && (endpoint=zero(T))
    A = sparse(repeat(collect(1:count),inner=2),collect(1:2count),
        repeat(T[1,3].*scale.*direction,count),count,2count)
    problem = LinearProblem(A,ones(T,2count);objective_constant=T(7),
        row_lower=upper_side ? fill(nothing,count) : fill(endpoint,count),
        row_upper=upper_side ? fill(endpoint,count) : fill(nothing,count),
        column_lower=fill(T(kind==:zero_endpoint ? -1 : 1),2count),
        column_upper=fill(T(5),2count))
    return problem,JSimplex.propagate_row_bounds
end

for kind in (:integer_positive_upper,:integer_positive_lower,:integer_negative_upper,:integer_negative_lower,:fraction_positive_upper,:fraction_positive_lower,:fraction_negative_upper,:fraction_negative_lower,:unequal_denominator,:zero_endpoint)
    problem, pass = propagation_equal_candidate_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **678 assertions** and failed only
the eight target allocation guards: 26,489 > 26,200; 26,452 > 26,200;
27,476 > 27,200; 27,220 > 27,000; three cases of 31,956 > 31,830;
and 31,700 > 31,570. Both control budgets passed. There are **686 new assertions**;
existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}, all four
candidate paths, shared and unequal denominators, non-improving candidates,
canonical reduction, zero endpoints, source immutability, incremental worklist
activation, changed-column masks, failure after an earlier tightening, redundant
row deletion, and primal/basis restoration. BigFloat checks preserve stored
256-bit operands under ambient precision 32/64/256. Shared-denominator differences
produce exact integers or dyadic residuals: exact bounds are accepted at all
precisions, while residuals are accepted only when exactly representable.
Large rational cases use numerators derived from `2^300+1` and denominators
5, 7, 15, and 21, for both signs and lower/upper tightening.

The combined presolve/basic/doubleton/aggregation/propagation targeted suite
passed **75,149 assertions** in **1m50.4s**, exit code zero.

Independent read-only differential review found no issues and passed
**5,840 assertions across 156 models** (150 successful, six infeasible;
34 identity results), exit code zero. It included 156 full-wrapper comparisons,
450 primal restorations, 450 basis restorations, and 288 extracted-expression
arithmetic/ownership cases. Baseline functions were renamed to keep the old
arithmetic independent. All four candidate paths, exact values, canonical
reduction, source preservation, partial worklists, cascades, failure side effects,
row deletion, and stored BigFloat precision gates matched the baseline. The
canonical constructor copies both BigInt operands before reduction; the new
branch introduces no input aliasing.

The complete `test/runtests.jl` suite passed **94,646 assertions** in
**6m00.1s**, exit code zero.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
