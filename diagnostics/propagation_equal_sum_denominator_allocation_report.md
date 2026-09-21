# Equal-denominator activity sums in bound propagation

Round 137 changes the minimum and maximum activity accumulators in
`_propagate_row_bounds` in `src/presolve_propagation.jl`. When the running sum and
a nonzero term share a denominator, their BigInt numerators are added directly.
A zero numerator reuses the existing activity-zero seed; otherwise the canonical
`Rational{BigInt}` constructor reduces the result. Unequal denominators retain
general rational addition. Existing zero-term skipping and zero-total reuse
remain in place, including restarting accumulation after cancellation.

The two symmetric accumulator branches keep the change local. Other-activity
subtraction, worklist scheduling, bound representability gates, row deletion,
failure handling, and primal/basis restoration are unchanged. Arithmetic does
not mutate operands or use GMP internals.

## Method and results

The baseline includes the preceding 136 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 58 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

All six targets contain 128 independent rows and 384 columns. The four nonzero-sum
probes have column bounds `[1,3]`. Positive integer rows use coefficients `[1,3,5]`
and row bounds `[0,33/2]`; negative rows negate coefficients and reverse/negate row
endpoints. Fractional rows divide both coefficients and row endpoints by two.
Every integer row uses four shared-denominator additions, saving two allocations
each. Fractional rows use two such additions, saving one each; adding the third
term uses unequal denominators and retains the fallback.

Cancellation probes use coefficients `[1,-1,1]`, column bounds `[1,1]`, `[1,1]`,
and `[1,3]`, and row bounds `[0,5/2]`. The fractional variant divides coefficients
and row endpoints by two. In each accumulator the first two terms cancel and the
third restarts the sum from zero. Each row saves fourteen allocations for integer
cancellation and twelve for fractional cancellation. All six targets tighten the
third column's upper bound to 5/2.

The unequal-denominator control uses `[1,1/2]`, row bounds `[0,5/2]`, and column
bounds `[1,3]`. Both accumulators use the fallback, and the first upper bound
tightens to two. The unbounded control has three free columns per row and uses
the earlier unbounded path without changing the model.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive integer sums | 1,873,400 | 1,820,168 | 2.84% | 55,628 → 54,604 |
| Negative integer sums | 1,900,440 | 1,847,400 | 2.79% | 56,524 → 55,500 |
| Positive fractional sums | 2,085,880 | 2,063,912 | 1.05% | 61,516 → 61,260 |
| Negative fractional sums | 2,073,432 | 2,051,512 | 1.06% | 61,132 → 60,876 |
| Integer cancellation | 1,118,840 | 1,047,368 | 6.39% | 33,996 → 32,204 |
| Fractional cancellation | 1,528,104 | 1,461,224 | 4.38% | 45,004 → 43,468 |
| Unequal-denominator control | 1,189,176 | 1,190,232 | — | 34,124 → 34,124 |
| Unbounded control | 312,032 | 311,712 | — | 9,635 → 9,635 |

The six targets save **256–1,792 allocations per call**. Allocated bytes decrease
by **1.05–6.39%**. Both controls retain their allocation counts.
Cross-process byte differences on unchanged paths alone establish no benefit.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,616 → 45,840 |
| afiro | sparse | 4,891 → 4,891 | 215,792 → 215,008 |
| afiro | propagation | 2,437 → 2,437 | 93,496 → 92,872 |
| afiro | presolve | 16,229 → 16,217 | 729,984 → 728,600 |
| afiro | dual | 17,044 → 17,032 | 865,712 → 863,752 |
| afiro | primal | 16,950 → 16,938 | 844,000 → 841,944 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,776 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,751 → 2,751 | 174,984 → 174,856 |
| adlittle | propagation | 18,234 → 18,219 | 645,992 → 642,856 |
| adlittle | presolve | 82,632 → 82,539 | 3,339,896 → 3,331,464 |
| adlittle | dual | 84,647 → 84,554 | 4,128,808 → 4,119,752 |
| adlittle | primal | 85,445 → 85,352 | 4,405,272 → 4,396,680 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,384 → 461,384 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,376 → 607,152 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,224 → 112,144 |
| kb2 | sparse | 2,836 → 2,836 | 162,480 → 162,128 |
| kb2 | propagation | 13,194 → 13,096 | 468,088 → 460,864 |
| kb2 | presolve | 229,721 → 229,496 | 10,665,496 → 10,651,568 |
| kb2 | dual | 230,923 → 230,698 | 11,118,648 → 11,102,432 |
| kb2 | primal | 231,090 → 230,865 | 11,132,488 → 11,116,848 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,968 → 877,904 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 300,176 → 299,360 |
| sc50a | propagation | 6,058 → 6,056 | 225,416 → 223,936 |
| sc50a | presolve | 67,503 → 67,481 | 2,849,248 → 2,847,448 |
| sc50a | dual | 68,575 → 68,553 | 3,194,944 → 3,192,728 |
| sc50a | primal | 68,520 → 68,498 | 3,147,584 → 3,145,304 |
| sc50a | dual_no_presolve | 961 → 961 | 306,272 → 306,480 |
| sc50a | primal_no_presolve | 964 → 964 | 232,232 → 232,232 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 211,368 → 209,816 |
| flugpl | propagation | 3,283 → 3,269 | 125,944 → 124,272 |
| flugpl | presolve | 30,959 → 30,893 | 1,179,424 → 1,175,016 |
| flugpl | dual | 31,630 → 31,564 | 1,290,040 → 1,284,080 |
| flugpl | primal | 31,979 → 31,913 | 1,334,696 → 1,328,656 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Complete presolve and both solves with presolve save 12 allocations for afiro,
93 for adlittle, 225 for kb2, 22 for sc50a, and 66 for flugpl. Standalone
propagation saves respectively 0, 15, 98, 2, and 14 allocations. The distinct
standalone and complete-presolve savings reflect different input models and
scheduling. Basic, doubleton, singleton, sparse aggregation, and solves without
presolve retain their allocation counts.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`propagation-equal-sum-denominator-allocations-before.toml`](propagation-equal-sum-denominator-allocations-before.toml)
and [`propagation-equal-sum-denominator-allocations-after.toml`](propagation-equal-sum-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-equal-sum-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function propagation_equal_sum_denominator_probe(kind; count=128, T=Float64)
    unequal = kind == :unequal_denominator
    cancelled = kind in (:cancel_integer,:cancel_fraction)
    width = unequal ? 2 : 3
    direction = kind in (:integer_negative,:fraction_negative) ? -1 : 1
    scale = kind in (:fraction_positive,:fraction_negative,:cancel_fraction) ? T(1)/2 : one(T)
    coefficients = unequal ? T[1,1//2] : (cancelled ? T[1,-1,1] : T[1,3,5]).*scale.*direction
    rows = repeat(collect(1:count),inner=width)
    A = sparse(rows,collect(1:width*count),repeat(coefficients,count),count,width*count)
    lower = fill(T(direction>0 ? 0 : -33//2)*scale,count)
    upper = fill(T(direction>0 ? 33//2 : 0)*scale,count)
    (unequal || cancelled) && (upper .= T(5)/2*scale)
    high = cancelled ? repeat(T[1,1,3],count) : fill(T(3),width*count)
    problem = LinearProblem(A,ones(T,width*count);objective_constant=T(7),
        row_lower=lower,row_upper=upper,
        column_lower=kind == :unbounded ? fill(nothing,width*count) : ones(T,width*count),
        column_upper=kind == :unbounded ? fill(nothing,width*count) : high)
    return problem,JSimplex.propagate_row_bounds
end

for kind in (:integer_positive,:integer_negative,:fraction_positive,:fraction_negative,:cancel_integer,:cancel_fraction,:unequal_denominator,:unbounded)
    problem, pass = propagation_equal_sum_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **1,054 assertions** and failed only
the six target allocation guards: 55,673 > 55,100; 56,532 > 56,000;
61,524 > 61,400; 61,140 > 61,000; 34,004 > 33,600; and 45,012 > 44,700.
Both control budgets passed. There are **1,060 new assertions**; existing
allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}, both signs,
shared and unequal denominators, fractional reduction, cancellation followed by
later terms, zero terms, unbounded terms, source immutability, changed-column
masks, incremental worklist activation, failure after an earlier tightening,
redundant row deletion, and primal/basis restoration. BigFloat tests preserve
stored 256-bit operands under ambient precision 32/64/256, accepting representable
bounds and rejecting inexact bounds. Large rational accumulation tests use
numerators derived from `2^300+1` and denominators 5, 7, 15, and 21.

The combined presolve/basic/doubleton/aggregation/propagation targeted suite
passed **74,463 assertions** in **1m47.0s**, exit code zero.

Independent read-only differential review found no issues and passed
**5,318 assertions across 144 models** (132 successful, 12 infeasible;
24 identity results), exit code zero. It included 144 full-wrapper comparisons,
396 primal restorations, 396 basis restorations, and 276 intermediate
accumulation checks. Baseline functions were renamed to keep the old arithmetic
independent. Canonical values, partial worklists, cascades, changed-column side
effects, source preservation, and stored BigFloat precision gates matched the
baseline. Separate accumulation checks verified cancellation and restart, reuse
of the shared zero, and nonmutating arithmetic on shared values.

The complete `test/runtests.jl` suite passed **93,960 assertions** in
**5m47.1s**, exit code zero.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
