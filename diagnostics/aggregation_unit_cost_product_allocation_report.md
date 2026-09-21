# Unit cost products in sparse equality aggregation

Round 128 changes only multiplication inside the retained-objective update of
`aggregate_sparse_equalities` in `src/presolve_aggregation.jl`. A ratio of +1
reuses the exact equality term; -1 negates it. For other ratios, a term of +1
reuses the ratio and -1 negates it. Other products retain rational multiplication.
The preceding zero-ratio shortcut still returns the old exact cost.

Subtraction from the currently committed cost and the `_represent_exact` gate
are unchanged. Objective-constant arithmetic and its gate, pivot choice,
private staging, rejection ordering, matrix/bound updates, model reconstruction,
and primal/basis restoration are unchanged. All comparisons use exact rational
values, including when inputs retain higher BigFloat precision than ambient.
No input is mutated and no GMP internals or noncanonical constructor are used.

## Method and results

The baseline includes the preceding 127 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 probe contains 128 independent two-row blocks: equality
`2*x+term*y=4` and inequality `6*x+5*y<=20`. Variable x has bounds `[1,3]`,
y is free, objective costs are `[2*ratio,5]`, and the initial model constant is
seven. Every block eliminates x and retains the equality as a projection of its
bounds. The retained objective becomes `5-ratio*term`:

- Positive unit ratio: `ratio=1`, `term=3`, updated cost two.
- Negative unit ratio: `ratio=-1`, `term=3`, updated cost eight.
- Positive unit term: `ratio=3`, `term=1`, updated cost two.
- Negative unit term: `ratio=3`, `term=-1`, updated cost eight.

All 128 blocks aggregate successfully, returning a 256-by-128 matrix. The final
constant is `7+512*ratio`; each affected upper bound becomes eight. Measurement
includes staging, sparse reconstruction, model construction, and postsolve
metadata. The nonunit control uses ratio three and term three; the zero-ratio
control uses ratio zero and term three. Both also succeed. Input construction
occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive unit ratio | 2,076,704 | 2,031,632 | 2.17% | 54,085 → 52,933 |
| Negative unit ratio | 2,078,480 | 2,040,880 | 1.81% | 54,085 → 53,189 |
| Positive unit term | 2,035,072 | 1,990,272 | 2.20% | 52,933 → 51,781 |
| Negative unit term | 2,042,208 | 2,004,768 | 1.83% | 53,189 → 52,293 |
| Nonunit control | 2,078,176 | 2,076,544 | — | 54,085 → 54,085 |
| Zero-ratio control | 1,805,984 | 1,804,976 | — | 46,405 → 46,405 |

Positive-unit targets save **1,152 allocations per call (nine per product)**;
negative-unit targets save **896 (seven per product)**. Allocated bytes decrease
by **1.81–2.20%**. Both controls retain their allocation counts.
Cross-process byte differences on unchanged paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 44,768 → 44,736 |
| afiro | sparse | 4,987 → 4,950 | 218,712 → 216,104 |
| afiro | presolve | 16,330 → 16,293 | 733,080 → 730,088 |
| afiro | dual | 17,145 → 17,108 | 868,664 → 865,560 |
| afiro | primal | 17,051 → 17,014 | 846,696 → 844,680 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,842 → 2,824 | 177,560 → 176,552 |
| adlittle | presolve | 82,775 → 82,757 | 3,348,208 → 3,346,416 |
| adlittle | dual | 84,790 → 84,772 | 4,138,384 → 4,135,408 |
| adlittle | primal | 85,588 → 85,570 | 4,415,056 → 4,412,144 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,192 → 461,400 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,760 → 607,408 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,224 → 112,352 |
| kb2 | sparse | 2,836 → 2,836 | 161,424 → 161,248 |
| kb2 | presolve | 230,004 → 229,977 | 10,679,928 → 10,678,312 |
| kb2 | dual | 231,206 → 231,179 | 11,134,200 → 11,130,504 |
| kb2 | primal | 231,373 → 231,346 | 11,148,232 → 11,144,184 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,968 → 878,384 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,640 | 300,416 → 299,400 |
| sc50a | presolve | 67,634 → 67,613 | 2,853,664 → 2,851,800 |
| sc50a | dual | 68,706 → 68,685 | 3,198,688 → 3,197,704 |
| sc50a | primal | 68,651 → 68,630 | 3,151,472 → 3,150,728 |
| sc50a | dual_no_presolve | 961 → 961 | 306,144 → 306,192 |
| sc50a | primal_no_presolve | 964 → 964 | 232,232 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,763 | 217,240 → 216,872 |
| flugpl | presolve | 31,461 → 31,461 | 1,199,672 → 1,198,808 |
| flugpl | dual | 32,132 → 32,132 | 1,308,608 → 1,309,360 |
| flugpl | primal | 32,481 → 32,481 | 1,352,880 → 1,353,696 |
| flugpl | dual_no_presolve | 376 → 376 | 42,752 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each presolved solve save 37 allocations for afiro, 18 for
adlittle, 27 for kb2, and 21 for sc50a; flugpl is unchanged. Direct sparse
aggregation saves 37, 18, zero, seven, and nine allocations respectively.
Basic presolve, doubleton substitution, singleton aggregation, and all solves
without presolve retain their allocation counts. Direct-pass and full-presolve
savings differ because the full pipeline reaches aggregation with transformed
models.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, full primal vector, and
iteration count (`isequal`).

Machine-readable results:
[`aggregation-unit-cost-product-allocations-before.toml`](aggregation-unit-cost-product-allocations-before.toml)
and [`aggregation-unit-cost-product-allocations-after.toml`](aggregation-unit-cost-product-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-unit-cost-product-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_unit_cost_product_probe(kind; count=128)
    ratio = kind == :ratio_positive ? 1.0 : kind == :ratio_negative ? -1.0 : kind == :zero_ratio ? 0.0 : 3.0
    term = kind == :term_positive ? 1.0 : kind == :term_negative ? -1.0 : 3.0
    odd = collect(1:2:2count); even = odd .+ 1
    A = sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(2.0,count),fill(term,count),fill(6.0,count),fill(5.0,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 2ratio : 5.0 for i in 1:2count];objective_constant=7.0,
        row_lower=Union{Nothing,Float64}[isodd(i) ? 4.0 : nothing for i in 1:2count],
        row_upper=[isodd(i) ? 4.0 : 20.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:ratio_positive,:ratio_negative,:term_positive,:term_negative,:nonunit,:zero_ratio)
    problem, pass = aggregation_unit_cost_product_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **1,790** assertions and failed only
the four target allocation guards: 54,130 > 53,400; 54,093 > 53,500;
52,941 > 52,300; and 53,197 > 52,600. Both control budgets passed.
There are **1,794 new assertions**; existing allocation budgets were not relaxed.

Accepted aggregations cover Float32, Float64, BigFloat, and Rational{BigInt};
signed unit/nonunit/zero ratios, signed terms, finite and implied column-bound
projections, retained objective/constant, matrix and bound results, primal
restoration, exact objective equivalence, and source immutability. Sequential
candidates check use of committed objective costs. BigFloat checks cover stored
256-bit values under ambient precision 32/64/256, exact units and their neighbors,
tiny residuals, cancellation, output precision, and representability rejection.
Large rational cases use numerators derived from `2^300+1` and non-dyadic
denominators 5, 7, 15, and 21. Overflow and half-subnormal cases check rejection
of the first candidate while allowing a representable alternative pivot.

The combined presolve/basic/doubleton/aggregation targeted suite passed
**48,516 assertions** in **1m27.8s**, exit code zero.

Independent read-only differential review found no issues and passed
**4,099 assertions across 124 models** (103 accepted, 21 rejected; 122
aggregation records), exit code zero. It compared 372 primal restorations,
496 basis restorations, 248 primal-dimension cases, 248 basis-dimension cases,
and verified 18 late cost/matrix/bound rollbacks. Coverage included both
near-unit ratios and terms stored at 256-bit BigFloat precision under ambient
32/64/256, large rational arithmetic ownership, committed costs, and CSC
invariants. Exact result snapshots matched the pre-change function.

The complete `test/runtests.jl` suite passed **73,401 assertions** in
**5m44.2s**, exit code zero, using:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
