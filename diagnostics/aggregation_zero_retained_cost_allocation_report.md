# Zero retained costs in sparse equality aggregation

Round 131 changes only subtraction in the retained-objective update of
`aggregate_sparse_equalities` in `src/presolve_aggregation.jl`. When the current
exact retained cost is zero, the update now negates the substitution product
instead of subtracting it from zero. Nonzero costs retain rational subtraction.
The earlier zero-ratio shortcut and signed-unit product shortcuts are unchanged.

The check uses the cost obtained from the committed objective-update dictionary,
not just the original model. This preserves sequential updates that change a
cost to or from zero. The `_represent_exact` gate remains after the update.
Constant arithmetic, pivot choice, staging and rejection ordering, matrix/bound
updates, model reconstruction, and primal/basis restoration are unchanged.
No input is mutated and no GMP internals or noncanonical constructor are used.

## Method and results

The baseline includes the preceding 130 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 probe contains 128 independent two-row blocks: equality
`2*x+3*y=4` and inequality `6*x+5*y<=20`. Variable x has bounds `[1,3]`,
y is free, objective costs are `[2*ratio,old_cost]`, and the initial model
constant is seven. Every block eliminates x and retains the equality as a
projection of its bounds. Four targets use ratios +3, -3, +1, and -1 respectively.
Positive ratios use old cost +0.0 and negative ratios use old cost -0.0.

All 128 blocks aggregate successfully, returning a 256-by-128 matrix. The constant
becomes `7+512*ratio` and each affected upper bound becomes eight. Retained costs
become `old_cost-3*ratio`. Measurement includes staging, sparse reconstruction,
model construction, and postsolve metadata. The nonzero-cost control uses ratio
three and old cost five; the zero-ratio control uses ratio zero and old cost zero.
Both succeed. Input construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive nonunit ratio | 2,066,352 | 2,030,432 | 1.74% | 53,701 → 52,805 |
| Negative nonunit ratio | 2,068,576 | 2,032,208 | 1.76% | 53,701 → 52,805 |
| Positive unit ratio | 1,981,264 | 1,945,824 | 1.79% | 51,397 → 50,501 |
| Negative unit ratio | 1,996,288 | 1,959,984 | 1.82% | 51,909 → 51,013 |
| Nonzero-cost control | 2,077,488 | 2,077,568 | — | 54,085 → 54,085 |
| Zero-ratio control | 1,777,424 | 1,777,600 | — | 45,253 → 45,253 |

All four targets save **896 allocations per call (seven per updated cost)**.
Allocated bytes decrease by **1.74–1.82%**.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 44,720 → 45,232 |
| afiro | sparse | 4,935 → 4,900 | 217,080 → 214,528 |
| afiro | presolve | 16,277 → 16,242 | 731,560 → 728,784 |
| afiro | dual | 17,092 → 17,057 | 866,664 → 864,128 |
| afiro | primal | 16,998 → 16,963 | 844,696 → 843,104 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,792 → 2,778 | 175,832 → 175,304 |
| adlittle | presolve | 82,693 → 82,679 | 3,344,960 → 3,343,792 |
| adlittle | dual | 84,708 → 84,694 | 4,133,520 → 4,132,544 |
| adlittle | primal | 85,506 → 85,492 | 4,410,800 → 4,409,648 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,224 → 461,432 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,344 → 607,424 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,320 → 112,624 |
| kb2 | sparse | 2,836 → 2,836 | 161,808 → 161,744 |
| kb2 | presolve | 229,932 → 229,911 | 10,677,496 → 10,675,424 |
| kb2 | dual | 231,134 → 231,113 | 11,131,144 → 11,128,976 |
| kb2 | primal | 231,301 → 231,280 | 11,144,472 → 11,142,624 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,288 → 878,192 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,848 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,625 → 6,618 | 299,976 → 299,184 |
| sc50a | presolve | 67,538 → 67,503 | 2,849,848 → 2,847,968 |
| sc50a | dual | 68,610 → 68,575 | 3,196,216 → 3,193,184 |
| sc50a | primal | 68,555 → 68,520 | 3,148,808 → 3,145,776 |
| sc50a | dual_no_presolve | 961 → 961 | 306,112 → 306,144 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,184 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 210,168 → 209,928 |
| flugpl | presolve | 31,011 → 31,011 | 1,181,896 → 1,180,216 |
| flugpl | dual | 31,682 → 31,682 | 1,290,864 → 1,290,160 |
| flugpl | primal | 32,031 → 32,031 | 1,335,472 → 1,334,816 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each presolved solve save 35 allocations for afiro, 14 for
adlittle, 21 for kb2, and 35 for sc50a; flugpl is unchanged. Direct sparse
aggregation saves 35, 14, zero, seven, and zero respectively. All other measured
stages retain their allocation counts, including every solve without presolve.
Direct-pass and full-pipeline savings differ because preceding passes transform
the models.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, full primal vector, and
iteration count (`isequal`).

Machine-readable results:
[`aggregation-zero-retained-cost-allocations-before.toml`](aggregation-zero-retained-cost-allocations-before.toml)
and [`aggregation-zero-retained-cost-allocations-after.toml`](aggregation-zero-retained-cost-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-zero-retained-cost-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_zero_retained_cost_probe(kind; count=128)
    ratio = kind == :unit_positive ? 1.0 : kind == :unit_negative ? -1.0 : kind == :zero_ratio ? 0.0 : kind == :negative ? -3.0 : 3.0
    rhs = 4.0
    old_cost = kind == :nonzero_cost ? 5.0 : kind in (:negative,:unit_negative) ? -0.0 : 0.0
    term = 3.0
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

for kind in (:positive,:negative,:unit_positive,:unit_negative,:nonzero_cost,:zero_ratio)
    problem, pass = aggregation_zero_retained_cost_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **3,206 assertions** and failed only
the four target allocation guards: 53,746 > 53,300; 53,709 > 53,300;
51,405 > 51,000; and 51,917 > 51,500. Both control budgets
passed. There are **3,210 new assertions**; existing allocation budgets were not relaxed.

Accepted aggregations cover Float32, Float64, BigFloat, and Rational{BigInt};
signed unit/nonunit/zero ratios and signed terms, positive and negative zero old
costs, finite and implied column-bound projections, objective/constant and matrix
results, shifted bounds, primal restoration, exact objective equivalence, and
source immutability. Sequential candidates check detection of zero against the
committed cost, including transitions into and out of zero. BigFloat checks cover
stored 256-bit values under ambient precision 32/64/256, tiny/exact/inexact
products, output precision, and representability rejection. Large rational cases
use numerators derived from `2^300+1` and non-dyadic denominators 5, 7, 15, and 21.
Overflow, half-subnormal products, and tiny nonzero old costs check rejection
without source mutation; retained-column degree one blocks alternative pivots.

The combined presolve/basic/doubleton/aggregation targeted suite passed
**56,270 assertions** in **1m31.7s**, exit code zero.

Independent read-only differential review found no actionable issues and passed
**4,591 assertions across 140 models** (111 accepted, 29 rejected; 138
aggregation records), exit code zero. It compared 420 primal restorations,
560 basis restorations, 280 primal-dimension cases, 280 basis-dimension cases,
and verified 18 late rejection rollbacks plus eight rational ownership cases.
Committed zero/nonzero cost transitions, stored BigFloat precision gates and
tiny values, exact objective/CSC structure, source immutability, and restoration
matched the pre-change function.

Ownership note: for `Rational{BigInt}`, negating a substitution product can newly
share its denominator with an input scalar. Ordinary public arithmetic and
assignment preserve source values. This matches the shallow scalar ownership
of the model constructor (`src/model.jl:105`); no guarantee of independently
mutable internal BigInts is introduced.

The complete `test/runtests.jl` suite passed **81,155 assertions** in
**5m45.7s**, exit code zero, using:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
