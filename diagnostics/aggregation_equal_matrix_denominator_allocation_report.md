# Equal-denominator matrix differences in sparse equality aggregation

Round 127 changes only the matrix subtraction in `aggregate_sparse_equalities`
in `src/presolve_aggregation.jl`. When the existing exact coefficient and its
substitution product have the same denominator, their BigInt numerators are
subtracted directly and the canonical `Rational{BigInt}` constructor reduces the
result. The preceding zero-multiplier, zero-old-coefficient, and exact-cancellation
shortcuts retain their behavior. Unequal denominators retain rational subtraction.

The matrix `_represent_exact` gate and its position after the bound checks are
unchanged. Product shortcuts, objective updates, rejection ordering, staged
changes, committed-matrix lookup, sparse reconstruction, and primal/basis
restoration are unchanged. No input is mutated, and no GMP internals or
noncanonical constructor are used.

## Method and results

The baseline includes the preceding 126 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 probe contains 128 independent two-row blocks: equality
`2*x+term*y=4` and inequality `6*x+old*y<=20`. Variable x has bounds `[1,3]`,
y is free, objective costs are `[0,2]`, and the model constant is seven. Every
block eliminates x with multiplier three and retains the equality row as a
projection of x's bounds. The matrix update is `old - 3*term`:

- Positive integer: `5 - 3 = 2`, common denominator one.
- Negative integer: `-5 - (-3) = -2`, common denominator one.
- Positive fractional operands: `1/2 - 3/2 = -1`, common denominator two.
- Negative fractional operands: `-1/2 - (-3/2) = 1`, common denominator two.

Every probe successfully aggregates all 128 blocks and returns a 256-by-128
reduced matrix. The objective remains all twos, the constant stays seven, and
the affected upper bounds become eight. Measurement includes staging, sparse
reconstruction, model construction, and postsolve metadata.

The unequal-denominator control computes `1 - 3/2`. The cancellation control
computes `3/2 - 3/2`, using the existing shortcut and removing the zero entry.
Both controls also succeed. Input construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive integers | 1,774,000 | 1,760,128 | 0.78% | 45,509 → 45,253 |
| Negative integers | 1,782,800 | 1,769,568 | 0.74% | 45,765 → 45,509 |
| Positive fractional operands | 1,817,120 | 1,805,728 | 0.63% | 46,533 → 46,405 |
| Negative fractional operands | 1,817,280 | 1,805,904 | 0.63% | 46,533 → 46,405 |
| Unequal-denominator control | 1,819,232 | 1,819,520 | — | 46,661 → 46,661 |
| Exact-cancellation control | 1,752,504 | 1,752,664 | — | 45,241 → 45,241 |

The four targets save **256, 256, 128, and 128 allocations per call**:
**two per integer difference and one per fractional difference**.
Allocated bytes decrease by **0.63–0.78%**. Both controls
retain their allocation counts. Cross-process byte differences on unchanged
paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,040 → 45,184 |
| afiro | sparse | 4,987 → 4,987 | 218,616 → 219,176 |
| afiro | presolve | 16,330 → 16,330 | 732,728 → 732,936 |
| afiro | dual | 17,145 → 17,145 | 868,312 → 868,280 |
| afiro | primal | 17,051 → 17,051 | 846,792 → 847,512 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,842 | 178,048 → 178,344 |
| adlittle | presolve | 82,776 → 82,775 | 3,347,768 → 3,348,992 |
| adlittle | dual | 84,791 → 84,790 | 4,136,968 → 4,137,776 |
| adlittle | primal | 85,589 → 85,588 | 4,413,752 → 4,414,560 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,432 → 461,144 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,472 → 607,392 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,240 → 112,832 |
| kb2 | sparse | 2,836 → 2,836 | 161,536 → 162,048 |
| kb2 | presolve | 230,004 → 230,004 | 10,678,200 → 10,682,056 |
| kb2 | dual | 231,206 → 231,206 | 11,131,128 → 11,133,464 |
| kb2 | primal | 231,373 → 231,373 | 11,145,256 → 11,146,856 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,256 → 878,176 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 299,712 → 300,624 |
| sc50a | presolve | 67,634 → 67,634 | 2,853,440 → 2,854,624 |
| sc50a | dual | 68,706 → 68,706 | 3,198,496 → 3,200,256 |
| sc50a | primal | 68,651 → 68,651 | 3,150,992 → 3,153,216 |
| sc50a | dual_no_presolve | 961 → 961 | 306,256 → 306,304 |
| sc50a | primal_no_presolve | 964 → 964 | 232,232 → 232,232 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 216,744 → 217,400 |
| flugpl | presolve | 31,461 → 31,461 | 1,198,920 → 1,199,640 |
| flugpl | dual | 32,132 → 32,132 | 1,308,560 → 1,309,856 |
| flugpl | primal | 32,481 → 32,481 | 1,353,328 → 1,354,320 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Adlittle saves one allocation in direct sparse aggregation, full presolve, and
both presolved solves. All other reference-stage allocation counts are unchanged,
including every solve without presolve. The reference benefit is small; most
measured reference paths do not use this shortcut.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, full primal vector, and
iteration count (`isequal`).

Machine-readable results:
[`aggregation-equal-matrix-denominator-allocations-before.toml`](aggregation-equal-matrix-denominator-allocations-before.toml)
and [`aggregation-equal-matrix-denominator-allocations-after.toml`](aggregation-equal-matrix-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-equal-matrix-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_equal_matrix_denominator_probe(kind; count=128)
    fractional = kind in (:fraction_positive,:fraction_negative,:unequal_denominator,:cancellation)
    direction = kind in (:integer_negative,:fraction_negative) ? -1.0 : 1.0
    term = direction * (fractional ? 0.5 : 1.0)
    old = kind == :unequal_denominator ? 1.0 : kind == :cancellation ? 1.5 :
        direction * (fractional ? 0.5 : 5.0)
    odd = collect(1:2:2count); even = odd .+ 1
    A = sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(2.0,count),fill(term,count),fill(6.0,count),fill(old,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 0.0 : 2.0 for i in 1:2count];objective_constant=7.0,
        row_lower=Union{Nothing,Float64}[isodd(i) ? 4.0 : nothing for i in 1:2count],
        row_upper=[isodd(i) ? 4.0 : 20.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:integer_positive,:integer_negative,:fraction_positive,:fraction_negative,:unequal_denominator,:cancellation)
    problem, pass = aggregation_equal_matrix_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,432** assertions and failed only
the four target allocation guards: 45,554 > 45,350; 45,773 > 45,650;
and 46,541 > 46,480 for each fractional probe. Both control budgets
passed. There are **2,436 new assertions**; existing allocation budgets were
not relaxed.

Accepted aggregations cover Float32, Float64, BigFloat, and Rational{BigInt};
positive/negative operands, fraction reduction, cancellation, unequal denominators,
zero old entries, finite and implied column-bound projections, reduced CSC
storage, objective results, row bounds, primal restoration, and source immutability.
Sequential candidates check that subtraction uses the already committed matrix
coefficient. BigFloat checks cover stored-256-bit coefficients under ambient
precision 32/64/256, exact tiny cancellation tails, zero removal, output precision,
and nonrepresentable matrix differences. Large rational cases use numerators
derived from `2^300+1` and non-dyadic denominators 5, 7, 15, and 21, including
further reduction. Overflow and half-subnormal matrix cases check rejection
without source storage changes.

The combined presolve/basic/doubleton/aggregation targeted suite passed
**46,722 assertions** in **1m27.2s**, exit code zero.

Independent read-only differential review found no issues. A separate harness
passed **4,680 assertions across 144 models** (124 accepted, 20 rejected),
including 432 primal restorations, 576 basis restorations, 288 primal-dimension
cases, 288 basis-dimension cases, and 24 late matrix/bound rollback checks.
Exact result snapshots matched the pre-change function; independent exact
matrix/CSC checks, rational canonicalization and ordinary-arithmetic ownership,
committed updates, and stored-precision BigFloat cases also passed.

The complete `test/runtests.jl` suite passed **71,607 assertions** in
**5m43.7s**, exit code zero, using:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
