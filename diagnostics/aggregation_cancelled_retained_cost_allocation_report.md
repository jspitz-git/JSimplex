# Cancelled retained costs in sparse equality aggregation

Round 132 changes only subtraction in the retained-objective update of
`aggregate_sparse_equalities` in `src/presolve_aggregation.jl`. When a nonzero
current exact cost equals the exact substitution product, the update now creates
canonical exact zero directly. Unequal operands retain rational subtraction.
The earlier zero-ratio, zero-old-cost, and signed-unit product shortcuts are
unchanged.

Equality is checked against the cost obtained from the committed update
dictionary, so preceding substitutions remain visible. The `_represent_exact`
gate still runs after the update. Constant arithmetic, pivot choice, staging and
rejection ordering, matrix/bound updates, model reconstruction, and primal/basis
restoration are unchanged. No input is mutated and no GMP internals or
noncanonical constructor are used.

## Method and results

The baseline includes the preceding 131 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 probe contains 128 independent two-row blocks: equality
`2*x+3*y=4` and inequality `6*x+5*y<=20`. Variable x has bounds `[1,3]`,
y is free, objective costs are `[2*ratio,old_cost]`, and the initial model
constant is seven. Every block eliminates x and retains the equality as a
projection of its bounds. Four targets use ratios +3, -3, +1, and -1 respectively,
with old cost `3*ratio`, yielding exact cancellation in the retained objective.

All 128 blocks aggregate successfully, returning a 256-by-128 matrix. The constant
becomes `7+512*ratio`, each affected upper bound becomes eight, and every target
retained cost becomes canonical zero. Measurement includes staging, sparse
reconstruction, model construction, and postsolve metadata. The unequal-cost
control uses ratio three and old cost five; the zero-old-cost control uses ratio
three and old cost zero. Both succeed. Input construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive nonunit ratio | 2,056,432 | 2,027,776 | 1.39% | 53,317 → 52,677 |
| Negative nonunit ratio | 2,058,336 | 2,029,520 | 1.40% | 53,317 → 52,677 |
| Positive unit ratio | 1,972,112 | 1,942,848 | 1.48% | 51,013 → 50,373 |
| Negative unit ratio | 1,986,704 | 1,957,360 | 1.48% | 51,525 → 50,885 |
| Unequal-cost control | 2,077,280 | 2,077,104 | — | 54,085 → 54,085 |
| Zero-old-cost control | 2,031,776 | 2,031,776 | — | 52,805 → 52,805 |

All four targets save **640 allocations per call (five per cancelled cost)**.
Allocated bytes decrease by **1.39–1.48%**.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,616 → 45,216 |
| afiro | sparse | 4,900 → 4,900 | 214,992 → 214,976 |
| afiro | presolve | 16,242 → 16,242 | 729,136 → 728,080 |
| afiro | dual | 17,057 → 17,057 | 864,592 → 863,232 |
| afiro | primal | 16,963 → 16,963 | 842,832 → 842,080 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,778 → 2,778 | 175,224 → 174,856 |
| adlittle | presolve | 82,679 → 82,679 | 3,345,024 → 3,343,280 |
| adlittle | dual | 84,694 → 84,694 | 4,133,680 → 4,132,832 |
| adlittle | primal | 85,492 → 85,492 | 4,410,464 → 4,409,136 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,400 → 461,384 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,520 → 607,536 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,992 → 112,448 |
| kb2 | sparse | 2,836 → 2,836 | 161,904 → 161,232 |
| kb2 | presolve | 229,911 → 229,911 | 10,676,192 → 10,673,632 |
| kb2 | dual | 231,113 → 231,113 | 11,126,704 → 11,127,408 |
| kb2 | primal | 231,280 → 231,280 | 11,140,816 → 11,141,872 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,016 → 878,112 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 299,104 → 298,336 |
| sc50a | presolve | 67,503 → 67,503 | 2,847,728 → 2,847,344 |
| sc50a | dual | 68,575 → 68,575 | 3,193,952 → 3,192,880 |
| sc50a | primal | 68,520 → 68,520 | 3,146,992 → 3,145,408 |
| sc50a | dual_no_presolve | 961 → 961 | 306,544 → 306,112 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 210,200 → 209,496 |
| flugpl | presolve | 31,011 → 31,011 | 1,180,280 → 1,179,048 |
| flugpl | dual | 31,682 → 31,682 | 1,290,864 → 1,288,880 |
| flugpl | primal | 32,031 → 32,031 | 1,335,264 → 1,333,392 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All five reference fixtures retain their allocation counts in all nine measured
stages, including solves without presolve. These fixtures show unchanged
behavior and no allocation-count benefit from this particular shortcut; the
measured savings are confined to the four targeted cancellation probes.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, full primal vector, and
iteration count (`isequal`).

Machine-readable results:
[`aggregation-cancelled-retained-cost-allocations-before.toml`](aggregation-cancelled-retained-cost-allocations-before.toml)
and [`aggregation-cancelled-retained-cost-allocations-after.toml`](aggregation-cancelled-retained-cost-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-cancelled-retained-cost-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_cancelled_retained_cost_probe(kind; count=128)
    ratio = kind == :unit_positive ? 1.0 : kind == :unit_negative ? -1.0 : kind == :negative ? -3.0 : 3.0
    rhs = 4.0
    term = 3.0
    old_cost = kind == :unequal ? 5.0 : kind == :zero_old ? 0.0 : ratio*term
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

for kind in (:positive,:negative,:unit_positive,:unit_negative,:unequal,:zero_old)
    problem, pass = aggregation_cancelled_retained_cost_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,306 assertions** and failed only
the four target allocation guards: 53,362 > 53,000; 53,325 > 53,000;
51,021 > 50,700; and 51,533 > 51,200. Both control budgets
passed. There are **2,310 new assertions**; existing allocation budgets were not relaxed.

Accepted aggregations cover Float32, Float64, BigFloat, and Rational{BigInt};
signed integer/fractional ratios and signed terms, finite and implied
column-bound projections, canonical zero costs, objective constants, matrix and
bound results, primal restoration, exact objective equivalence, and source
immutability. Sequential candidates check cancellation against committed costs,
including transitions into and out of zero. BigFloat checks cover stored 256-bit
values under ambient precision 32/64/256, exact cancellation, tiny residuals,
output precision, and representability rejection. Adjacent Float32/Float64
costs retain nonzero residuals. Large rational cases use numerators derived from
`2^300+1` and non-dyadic denominators 5, 7, 15, and 21; cancelled outputs have
numerator zero and denominator one.

The combined presolve/basic/doubleton/aggregation targeted suite passed
**58,580 assertions** in **1m29.9s**, exit code zero.

Independent read-only differential review found no issues and passed
**4,530 assertions across 136 models** (117 accepted, 19 rejected; 144
aggregation records), exit code zero. It compared 408 primal restorations
plus 24 explicit known-value checks, 544 basis restorations, 272 malformed-primal
cases, and 272 malformed-basis cases. Eighteen floating late cost/matrix/bound
rollback cases and eight rational ownership cases passed. Canonical zero,
stored BigFloat precision gates, tiny residuals, committed costs, CSC structure,
and restoration matched the pre-change function. Newly constructed rational
zeros do not alias input numerator/denominator storage; ordinary output arithmetic
and replacement preserve the source.

The complete `test/runtests.jl` suite passed **83,465 assertions** in
**5m51.5s**, exit code zero, using:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
