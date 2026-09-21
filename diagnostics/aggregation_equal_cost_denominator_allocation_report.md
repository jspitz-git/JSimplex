# Equal-denominator cost differences in sparse equality aggregation

Round 133 changes only the retained-objective subtraction in
`aggregate_sparse_equalities` in `src/presolve_aggregation.jl`. When the current
exact cost and substitution product share a denominator, their BigInt numerators
are subtracted directly and the canonical `Rational{BigInt}` constructor reduces
the result. Unequal denominators retain rational subtraction. The preceding
zero-ratio, zero-old-cost, exact-cancellation, and signed-unit product shortcuts
retain their behavior.

The update uses the cost obtained from the committed objective dictionary, so
preceding substitutions remain visible. The `_represent_exact` gate still runs
after the update. Constant arithmetic, pivot choice, staging and rejection
ordering, matrix/bound updates, model reconstruction, and primal/basis restoration
are unchanged. No input is mutated and no GMP internals or noncanonical
constructor are used.

## Method and results

The baseline includes the preceding 132 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 probe contains 128 independent two-row blocks: equality
`2*x+3*y=4` and inequality `6*x+5*y<=20`. Variable x has bounds `[1,3]`,
y is free, objective costs are `[2*ratio,old_cost]`, and the initial model
constant is seven. Every block eliminates x and retains the equality as a
projection of its bounds. Retained objective updates are:

- Positive integers: ratio +1, `5 - 3 = 2`, common denominator one.
- Negative integers: ratio -1, `-5 - (-3) = -2`, common denominator one.
- Positive fractional operands: ratio +1/2, `1/2 - 3/2 = -1`, denominator two.
- Negative fractional operands: ratio -1/2, `-1/2 - (-3/2) = 1`, denominator two.

All 128 blocks aggregate successfully, returning a 256-by-128 matrix. The constant
becomes `7+512*ratio` and each affected upper bound becomes eight. Measurement
includes staging, sparse reconstruction, model construction, and postsolve
metadata. The unequal-denominator control computes `1 - 3/2`; the cancellation
control computes `3/2 - 3/2` using the preceding shortcut. Both succeed. Input
construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive integer operands | 1,988,192 | 1,974,672 | 0.68% | 51,781 → 51,525 |
| Negative integer operands | 2,004,768 | 1,991,024 | 0.69% | 52,293 → 52,037 |
| Positive fractional operands | 2,074,592 | 2,063,600 | 0.53% | 53,957 → 53,829 |
| Negative fractional operands | 2,074,656 | 2,063,632 | 0.53% | 53,957 → 53,829 |
| Unequal-denominator control | 2,076,640 | 2,076,976 | — | 54,085 → 54,085 |
| Exact-cancellation control | 2,029,200 | 2,029,200 | — | 52,677 → 52,677 |

The integer targets save **256 allocations per call (two per updated cost)**;
the fractional targets save **128 (one per updated cost)**.
Allocated bytes decrease by **0.53–0.69%**.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 44,688 → 44,560 |
| afiro | sparse | 4,900 → 4,900 | 214,752 → 214,112 |
| afiro | presolve | 16,242 → 16,242 | 728,624 → 727,248 |
| afiro | dual | 17,057 → 17,057 | 864,016 → 863,872 |
| afiro | primal | 16,963 → 16,963 | 842,592 → 842,112 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,936 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,778 → 2,778 | 175,192 → 174,984 |
| adlittle | presolve | 82,679 → 82,679 | 3,343,872 → 3,343,904 |
| adlittle | dual | 84,694 → 84,694 | 4,132,848 → 4,132,576 |
| adlittle | primal | 85,492 → 85,492 | 4,409,584 → 4,409,408 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,352 → 461,720 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,632 → 607,440 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,192 → 111,744 |
| kb2 | sparse | 2,836 → 2,836 | 161,728 → 161,328 |
| kb2 | presolve | 229,911 → 229,911 | 10,674,912 → 10,676,176 |
| kb2 | dual | 231,113 → 231,113 | 11,126,656 → 11,127,344 |
| kb2 | primal | 231,280 → 231,280 | 11,140,720 → 11,141,776 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,064 → 877,888 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 298,816 → 298,288 |
| sc50a | presolve | 67,503 → 67,503 | 2,847,712 → 2,847,888 |
| sc50a | dual | 68,575 → 68,575 | 3,193,872 → 3,193,808 |
| sc50a | primal | 68,520 → 68,520 | 3,146,624 → 3,146,592 |
| sc50a | dual_no_presolve | 961 → 961 | 306,128 → 306,128 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 209,640 → 209,064 |
| flugpl | presolve | 31,011 → 31,011 | 1,179,816 → 1,179,832 |
| flugpl | dual | 31,682 → 31,682 | 1,289,760 → 1,289,344 |
| flugpl | primal | 32,031 → 32,031 | 1,334,288 → 1,333,904 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All five reference fixtures retain their allocation counts in all nine measured
stages, including solves without presolve. These fixtures show unchanged
behavior and no allocation-count benefit from this particular shortcut; the
measured savings are confined to the four targeted common-denominator probes.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, full primal vector, and
iteration count (`isequal`).

Machine-readable results:
[`aggregation-equal-cost-denominator-allocations-before.toml`](aggregation-equal-cost-denominator-allocations-before.toml)
and [`aggregation-equal-cost-denominator-allocations-after.toml`](aggregation-equal-cost-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-equal-cost-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_equal_cost_denominator_probe(kind; count=128)
    fractional = kind in (:fraction_positive,:fraction_negative,:unequal_denominator,:cancellation)
    direction = kind in (:integer_negative,:fraction_negative) ? -1.0 : 1.0
    ratio = direction * (fractional ? 0.5 : 1.0)
    rhs = 4.0
    term = 3.0
    old_cost = kind == :unequal_denominator ? 1.0 : kind == :cancellation ? 1.5 :
        direction * (fractional ? 0.5 : 5.0)
    odd = collect(1:2:2count); even = odd .+ 1
    A = sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(2.0,count),fill(term,count),fill(6.0,count),fill(5.0,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 2ratio : old_cost for i in 1:2count];objective_constant=7.0,
        row_lower=Union{Nothing,Float64}[isodd(i) ? rhs : nothing for i in 1:2count],
        row_upper=[isodd(i) ? rhs : 20.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:integer_positive,:integer_negative,:fraction_positive,:fraction_negative,:unequal_denominator,:cancellation)
    problem, pass = aggregation_equal_cost_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,202 assertions** and failed only
the four target allocation guards: 51,826 > 51,700; 52,301 > 52,200;
and 53,965 > 53,900 for each fractional probe. Both control budgets
passed. There are **2,206 new assertions**; existing allocation budgets were not relaxed.

Accepted aggregations cover Float32, Float64, BigFloat, and Rational{BigInt};
signed integer/fractional ratios and costs, fraction reduction, cancellation,
zero old costs, unequal denominators, finite and implied column-bound projections,
objective constants, matrix and bound results, primal restoration, exact
objective equivalence, and source immutability. Sequential candidates check use
of committed costs, including fractions created by an earlier update. BigFloat
checks cover stored 256-bit values under ambient precision 32/64/256, exact
cancellation, tiny residuals, output precision, and representability rejection.
Large rational cases use numerators derived from `2^300+1` and non-dyadic
denominators 5, 7, 15, and 21 with further reduction. Overflow and half-subnormal
cases retain rejection without source mutation; retained-column degree one
prevents unrelated alternative pivots.

The combined presolve/basic/doubleton/aggregation targeted suite passed
**60,786 assertions** in **1m29.9s**, exit code zero.

Independent read-only differential review found no issues and passed
**4,554 assertions across 136 models** (117 accepted, 19 rejected; 144
aggregation records), exit code zero. It compared 408 primal restorations,
544 basis restorations, 272 primal-dimension cases, and 272 basis-dimension cases.
Eighteen late cost/matrix/bound rollback cases and eight rational ownership
cases passed. Committed costs, shared/unequal denominators, stored BigFloat
precision gates, tiny residuals, exact objective/CSC structure, and restoration
matched the pre-change function. The canonical two-BigInt rational constructor
copies both inputs before reduction, so the new branch introduces no input
numerator/denominator aliases or mutation.

The complete `test/runtests.jl` suite passed **85,671 assertions** in
**5m53.0s**, exit code zero, using:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
