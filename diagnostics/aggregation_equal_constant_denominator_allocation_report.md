# Equal-denominator constant sums in sparse equality aggregation

Round 135 changes only the nonzero objective-constant addition in
`aggregate_sparse_equalities` in `src/presolve_aggregation.jl`. When the current
exact constant and substitution product share a denominator, their BigInt
numerators are added directly. A zero numerator produces canonical exact zero;
otherwise the canonical `Rational{BigInt}` constructor reduces the result.
Unequal denominators retain rational addition. The preceding zero-ratio,
zero-rhs, zero-constant, and signed-unit product shortcuts retain their behavior.

The update uses the current committed constant. The `_represent_exact` gate still
runs after it. Objective-cost arithmetic, pivot choice, staging and rejection
ordering, matrix/bound updates, model reconstruction, and primal/basis restoration
are unchanged. No input is mutated and no GMP internals or noncanonical
constructor are used.

## Method and results

The baseline includes the preceding 134 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 probe contains 128 independent two-row blocks: equality
`2*x+3*y=rhs` and inequality `6*x<=20`. Variable x has bounds `[1,3]`, y is free,
and objective costs are `[-6,nextfloat(0.0)]`, giving ratio -3. The four targets
exercise these exact constant updates:

- Integer cancellation: constant three, rhs one, `3 + (-3) = 0`.
- Fractional cancellation: constant 3/2, rhs 1/2, `3/2 + (-3/2) = 0`.
- Nonzero integer sum: constant five, rhs one, `5 + (-3) = 2`.
- Reduced fractional sum: constant 1/2, rhs 1/2, `1/2 + (-3/2) = -1`.

Each candidate computes a representable constant, then fails the retained-cost
gate: `nextfloat(0.0)+9` is not exactly representable as Float64. The retained
column has degree one, preventing an alternative pivot. All 128 candidates are
therefore rejected, the committed constant stays at its initial value, and the
pass returns the original model with an empty postsolve stack. Measurement
covers discovery, projection, objective arithmetic, and rejection, not successful
sparse reconstruction. Successful reductions and restoration have separate
regression and differential coverage.

The unequal-denominator control computes `1 + (-3/2)`; the zero-constant control
reuses -3/2 through the preceding shortcut. Both also reject every candidate at
the retained-cost gate. Input construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Integer cancellation | 1,231,192 | 1,208,632 | 1.83% | 32,675 → 32,291 |
| Fractional cancellation | 1,274,296 | 1,254,536 | 1.55% | 33,699 → 33,443 |
| Nonzero integer sum | 1,242,536 | 1,228,840 | 1.10% | 33,059 → 32,803 |
| Reduced fractional sum | 1,283,832 | 1,272,008 | 0.92% | 34,083 → 33,955 |
| Unequal-denominator control | 1,285,720 | 1,285,656 | — | 34,211 → 34,211 |
| Zero-constant control | 1,242,368 | 1,242,400 | — | 33,056 → 33,056 |

The four targets save **384, 256, 256, and 128 allocations per call**, respectively:
**three, two, two, and one per rejected candidate**.
Allocated bytes decrease by **0.92–1.83%**.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,504 → 44,704 |
| afiro | sparse | 4,891 → 4,891 | 215,296 → 214,448 |
| afiro | presolve | 16,242 → 16,242 | 730,976 → 729,808 |
| afiro | dual | 17,057 → 17,057 | 866,000 → 865,552 |
| afiro | primal | 16,963 → 16,963 | 843,232 → 843,360 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,936 |
| afiro | primal_no_presolve | 759 → 759 | 121,792 → 121,776 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,751 → 2,751 | 174,760 → 174,104 |
| adlittle | presolve | 82,661 → 82,661 | 3,343,504 → 3,342,720 |
| adlittle | dual | 84,676 → 84,676 | 4,134,000 → 4,133,456 |
| adlittle | primal | 85,474 → 85,474 | 4,410,064 → 4,409,712 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,432 → 461,256 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,648 → 607,664 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,352 → 111,520 |
| kb2 | sparse | 2,836 → 2,836 | 162,128 → 161,568 |
| kb2 | presolve | 229,911 → 229,911 | 10,676,096 → 10,676,576 |
| kb2 | dual | 231,113 → 231,113 | 11,130,432 → 11,130,080 |
| kb2 | primal | 231,280 → 231,280 | 11,144,496 → 11,143,888 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,936 → 877,856 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,864 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 299,584 → 299,744 |
| sc50a | presolve | 67,503 → 67,503 | 2,848,896 → 2,849,200 |
| sc50a | dual | 68,575 → 68,575 | 3,194,560 → 3,194,208 |
| sc50a | primal | 68,520 → 68,520 | 3,147,664 → 3,146,368 |
| sc50a | dual_no_presolve | 961 → 961 | 306,160 → 306,112 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,184 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 210,744 → 210,216 |
| flugpl | presolve | 31,011 → 31,011 | 1,181,512 → 1,182,184 |
| flugpl | dual | 31,682 → 31,682 | 1,289,904 → 1,290,928 |
| flugpl | primal | 32,031 → 32,031 | 1,334,720 → 1,335,616 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All five reference fixtures retain their allocation counts in all nine measured
stages, including solves without presolve. These fixtures show unchanged
behavior and no allocation-count benefit from this particular shortcut; the
measured savings are confined to the four targeted constant-sum probes.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, full primal vector, and
iteration count (`isequal`).

Machine-readable results:
[`aggregation-equal-constant-denominator-allocations-before.toml`](aggregation-equal-constant-denominator-allocations-before.toml)
and [`aggregation-equal-constant-denominator-allocations-after.toml`](aggregation-equal-constant-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-equal-constant-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_equal_constant_denominator_probe(kind; count=128)
    ratio = -3.0
    rhs = kind in (:cancel_integer,:sum_integer) ? 1.0 : 0.5
    constant = kind == :cancel_integer ? 3.0 : kind == :cancel_fraction ? 1.5 :
        kind == :sum_integer ? 5.0 : kind == :sum_fraction ? 0.5 : kind == :zero_constant ? 0.0 : 1.0
    odd = collect(1:2:2count); even = odd .+ 1
    # The retained column has degree one, so a rejected x pivot cannot be
    # replaced by a y pivot. Every block fails the retained-cost exactness gate.
    A = sparse(vcat(odd,odd,even),vcat(odd,even,odd),
        vcat(fill(2.0,count),fill(3.0,count),fill(6.0,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 2ratio : nextfloat(0.0) for i in 1:2count];objective_constant=constant,
        row_lower=Union{Nothing,Float64}[isodd(i) ? rhs : nothing for i in 1:2count],
        row_upper=[isodd(i) ? rhs : 20.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:cancel_integer,:cancel_fraction,:sum_integer,:sum_fraction,:unequal_denominator,:zero_constant)
    problem, pass = aggregation_equal_constant_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **3,746 assertions** and failed only
the four target allocation guards: 32,720 > 32,500; 33,707 > 33,580;
33,067 > 32,950; and 34,091 > 34,030. Both control budgets
passed. There are **3,750 new assertions**; existing allocation budgets were not relaxed.

Successful aggregations cover Float32, Float64, BigFloat, and Rational{BigInt};
signed unit/nonunit ratios and right-hand sides, shared/unequal denominators,
exact cancellation, nonzero sums, zero old constants, fraction reduction, finite
and implied column-bound projections, objective costs, matrix/bound results,
primal restoration, exact objective equivalence, and source immutability.
Three sequential candidates check use of the committed constant as its value
and denominator change. BigFloat checks cover stored 256-bit values under ambient
precision 32/64/256, exact cancellation, tiny residuals, nonrepresentable sums,
and output precision. Large rational cases use numerators derived from `2^300+1`
and non-dyadic denominators 5, 7, 15, and 21, including further reduction. Overflow
and half-subnormal cases retain rejection without source mutation; retained-column
degree one prevents unrelated alternative pivots.

The combined presolve/basic/doubleton/aggregation targeted suite passed
**67,366 assertions** in **1m33.1s**, exit code zero.

Independent read-only differential review found no issues and passed
**5,236 assertions across 156 models** (127 accepted, 29 rejected; 178
aggregation records), exit code zero. It compared 468 primal restorations,
624 basis restorations, 312 primal-dimension cases, and 312 basis-dimension cases.
Eighteen late cost/matrix/bound rollback cases and 24 rational ownership cases
passed. Canonical zero/reduction, committed constant transitions, stored
BigFloat precision gates, tiny residuals, exact objective/matrix reconstruction,
CSC structure, and restoration matched baseline. Ordinary arithmetic and
output-container changes preserved input values; the newly constructed constant
numerators and denominators did not alias the original constant in the ownership
cases.

The complete `test/runtests.jl` suite passed **92,251 assertions** in
**5m54.4s**, exit code zero, using:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
