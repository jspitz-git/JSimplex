# Equal-denominator activity subtraction in bound propagation

Round 136 changes only the final subtraction in `_other_activity` in
`src/presolve_propagation.jl`. When the total activity and the removed term share
a denominator, their BigInt numerators are subtracted directly and the canonical
`Rational{BigInt}` constructor reduces the result. Unequal denominators retain
general rational subtraction. Earlier unbounded, missing-term, zero-term,
zero-total, and cancellation branches retain their behavior and shared identities.

The change leaves row activity accumulation, worklist scheduling, bound updates,
representability gates, row deletion, failure handling, and primal/basis
restoration unchanged. Arithmetic does not mutate operands or use GMP internals.

## Method and results

The baseline includes the preceding 135 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.
This round adds a separate propagation measurement to the nine existing reference
stages, allowing its savings to be distinguished from complete presolve.

Each target contains 128 independent rows and 384 columns, with column bounds
`[1,3]`. Positive integer rows have coefficients `[1,3,5]` and row bounds
`[0,33/2]`; negative rows negate coefficients and reverse/negate row endpoints.
Fractional rows divide both coefficients and row endpoints by two. Every row
has six nonzero, noncancelling activity subtractions with a shared denominator.
Integer activities save two allocations per subtraction; fractional activities
save one, including reduction of half-integer differences to integers.
All targets tighten the third column of each row to upper bound 5/2.

The unequal-denominator control uses `[1/2,3/2]`, row bounds `[0,5/2]`, and
column bounds `[1,3]`. Its integer activity totals and half-integer terms use the
fallback; the first upper bound tightens to two and the nonrepresentable Float64
bound 4/3 is rejected. The unbounded control has three free columns per row and
uses the earlier unbounded branch without changing the model.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive integer activities | 1,955,928 | 1,873,032 | 4.24% | 57,164 → 55,628 |
| Negative integer activities | 1,982,856 | 1,899,912 | 4.18% | 58,060 → 56,524 |
| Positive fractional activities | 2,154,296 | 2,085,464 | 3.20% | 62,284 → 61,516 |
| Negative fractional activities | 2,142,456 | 2,072,968 | 3.24% | 61,900 → 61,132 |
| Unequal-denominator control | 1,479,688 | 1,478,408 | — | 41,292 → 41,292 |
| Unbounded control | 312,128 | 310,976 | — | 9,635 → 9,635 |

The integer targets save **1,536 allocations per call** (12 per row), and the
fractional targets save **768** (six per row). Allocated bytes decrease by
**3.20–4.24%**. Both controls retain their allocation counts.
Cross-process byte differences on unchanged paths alone establish no benefit.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 44,736 → 45,120 |
| afiro | sparse | 4,891 → 4,891 | 214,976 → 214,256 |
| afiro | propagation | 2,437 → 2,437 | 92,536 → 92,232 |
| afiro | presolve | 16,242 → 16,229 | 730,512 → 729,200 |
| afiro | dual | 17,057 → 17,044 | 865,168 → 864,336 |
| afiro | primal | 16,963 → 16,950 | 843,920 → 842,224 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,751 → 2,751 | 174,472 → 173,576 |
| adlittle | propagation | 18,243 → 18,234 | 647,032 → 644,264 |
| adlittle | presolve | 82,661 → 82,632 | 3,344,128 → 3,338,936 |
| adlittle | dual | 84,676 → 84,647 | 4,134,480 → 4,128,408 |
| adlittle | primal | 85,474 → 85,445 | 4,411,648 → 4,404,392 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,416 → 461,432 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,504 → 607,104 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 111,856 → 112,064 |
| kb2 | sparse | 2,836 → 2,836 | 161,840 → 161,088 |
| kb2 | propagation | 13,262 → 13,194 | 472,376 → 466,824 |
| kb2 | presolve | 229,911 → 229,721 | 10,676,256 → 10,664,168 |
| kb2 | dual | 231,113 → 230,923 | 11,131,056 → 11,118,120 |
| kb2 | primal | 231,280 → 231,090 | 11,144,400 → 11,132,120 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,160 → 877,968 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,848 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 299,328 → 298,608 |
| sc50a | propagation | 6,064 → 6,058 | 224,728 → 223,016 |
| sc50a | presolve | 67,503 → 67,503 | 2,849,936 → 2,848,768 |
| sc50a | dual | 68,575 → 68,575 | 3,195,072 → 3,194,544 |
| sc50a | primal | 68,520 → 68,520 | 3,147,808 → 3,147,600 |
| sc50a | dual_no_presolve | 961 → 961 | 306,208 → 306,368 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,248 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 209,784 → 209,608 |
| flugpl | propagation | 3,297 → 3,283 | 126,168 → 123,800 |
| flugpl | presolve | 31,011 → 30,959 | 1,182,536 → 1,178,176 |
| flugpl | dual | 31,682 → 31,630 | 1,291,008 → 1,287,112 |
| flugpl | primal | 32,031 → 31,979 | 1,335,712 → 1,331,992 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Complete presolve and both solves with presolve save 13 allocations for afiro,
29 for adlittle, 190 for kb2, and 52 for flugpl; sc50a is unchanged. Standalone
propagation saves respectively 0, 9, 68, 6, and 14 allocations for afiro,
adlittle, kb2, sc50a, and flugpl. The distinct standalone and complete-presolve
savings reflect their different input models and scheduling. Basic, doubleton,
singleton, sparse aggregation, and solves without presolve retain their counts.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`propagation-equal-activity-denominator-allocations-before.toml`](propagation-equal-activity-denominator-allocations-before.toml)
and [`propagation-equal-activity-denominator-allocations-after.toml`](propagation-equal-activity-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-equal-activity-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function propagation_equal_activity_denominator_probe(kind; count=128, T=Float64)
    unequal = kind == :unequal_denominator
    width = unequal ? 2 : 3
    direction = kind in (:integer_negative,:fraction_negative) ? -1 : 1
    scale = kind in (:fraction_positive,:fraction_negative,:unequal_denominator) ? T(1)/2 : one(T)
    coefficients = unequal ? T[1,3].*scale : T[1,3,5].*scale.*direction
    rows = repeat(collect(1:count),inner=width)
    A = sparse(rows,collect(1:width*count),repeat(coefficients,count),count,width*count)
    lower = fill(T(direction>0 ? 0 : -33//2)*scale,count)
    upper = fill(T(direction>0 ? 33//2 : 0)*scale,count)
    unequal && (upper .= T(5)/2)
    problem = LinearProblem(A,ones(T,width*count);objective_constant=T(7),
        row_lower=lower,row_upper=upper,
        column_lower=kind == :unbounded ? fill(nothing,width*count) : ones(T,width*count),
        column_upper=kind == :unbounded ? fill(nothing,width*count) : fill(T(3),width*count))
    return problem,JSimplex.propagate_row_bounds
end

for kind in (:integer_positive,:integer_negative,:fraction_positive,:fraction_negative,:unequal_denominator,:unbounded)
    problem, pass = propagation_equal_activity_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **645 assertions** and failed only
the four target allocation guards: 57,209 > 56,500; 58,068 > 57,400;
62,292 > 61,900; and 61,908 > 61,500. Both control budgets passed.
There are **649 new assertions**; existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}, both signs,
shared and unequal denominators, canonical reduction, earlier zero and unbounded
branches and their identity guarantees, source immutability, incremental worklist
activation, changed-column masks, failure after an earlier tightening, redundant
row deletion, and primal/basis restoration. BigFloat tests preserve stored
256-bit operands under ambient precision 32/64/256, accepting representable bounds
and rejecting inexact bounds. Direct helper tests also use large rational
numerators derived from `2^300+1` and denominators 5, 7, 15, and 21.

The combined presolve/basic/doubleton/aggregation/propagation targeted suite
passed **73,403 assertions** in **1m45.6s**, exit code zero.

Independent read-only differential review found no issues and passed
**3,515 assertions across 132 models** (120 successful, 12 infeasible;
25 identity outcomes), exit code zero. It included 132 full-wrapper comparisons,
360 primal restorations, 360 basis restorations, and 123 scalar arithmetic cases.
All three baseline functions were renamed to ensure the baseline pass called
the old helper. Partial worklists, cascades, changed-column side effects, source
preservation, canonical reduction, and stored BigFloat precision gates matched.
The canonical rational constructor copies both BigInt operands before reduction;
the new branch introduces no input aliasing.

The complete `test/runtests.jl` suite passed **92,900 assertions** in
**5m48.5s**, exit code zero.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
