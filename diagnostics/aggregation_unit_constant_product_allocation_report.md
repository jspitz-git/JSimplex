# Unit constant products in sparse equality aggregation

Round 129 changes only multiplication inside the objective-constant update of
`aggregate_sparse_equalities` in `src/presolve_aggregation.jl`. A ratio of +1
reuses the exact equality right-hand side; -1 negates it. For other ratios,
a right-hand side of +1 reuses the ratio and -1 negates it. Other products
retain rational multiplication. The preceding zero-ratio shortcut still returns
the currently committed exact constant.

Addition to the committed constant and the `_represent_exact` gate are unchanged.
Objective-cost arithmetic and its gates, pivot choice, private staging, rejection
ordering, matrix/bound updates, model reconstruction, and primal/basis restoration
are unchanged. Comparisons use exact rational values, including when inputs
retain higher BigFloat precision than ambient. No input is mutated and no GMP
internals or noncanonical constructor are used.

## Method and results

The baseline includes the preceding 128 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 probe contains 128 independent two-row blocks: equality
`2*x+3*y=rhs` and inequality `6*x+5*y<=20`. Variable x has bounds `[1,3]`,
y is free, objective costs are `[2*ratio,5]`, and the initial model constant is
seven. Every block eliminates x and retains the equality as a projection of its
bounds. Each committed constant increases by `ratio*rhs`:

- Positive unit ratio: `ratio=1`, `rhs=4`, constant shift four.
- Negative unit ratio: `ratio=-1`, `rhs=4`, constant shift minus four.
- Positive unit right-hand side: `ratio=3`, `rhs=1`, constant shift three.
- Negative unit right-hand side: `ratio=3`, `rhs=-1`, constant shift minus three.

All 128 blocks aggregate successfully, returning a 256-by-128 matrix. The final
constant is `7+128*ratio*rhs`; each affected upper bound becomes `20-3*rhs`.
Retained costs become `5-3*ratio`. Measurement includes staging, sparse
reconstruction, model construction, and postsolve metadata. The nonunit control
uses ratio three and rhs four; the zero-ratio control uses ratio zero and rhs
four. Both succeed. Input construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive unit ratio | 2,031,552 | 1,988,880 | 2.10% | 52,933 → 51,781 |
| Negative unit ratio | 2,041,216 | 2,005,728 | 1.74% | 53,189 → 52,293 |
| Positive unit right-hand side | 2,033,824 | 1,991,232 | 2.09% | 52,933 → 51,781 |
| Negative unit right-hand side | 2,041,104 | 2,005,696 | 1.73% | 53,189 → 52,293 |
| Nonunit control | 2,076,864 | 2,077,952 | — | 54,085 → 54,085 |
| Zero-ratio control | 1,805,216 | 1,805,792 | — | 46,405 → 46,405 |

Positive-unit targets save **1,152 allocations per call (nine per product)**;
negative-unit targets save **896 (seven per product)**. Allocated bytes decrease
by **1.73–2.10%**. Both controls retain their allocation counts.
Cross-process byte differences on unchanged paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 44,864 → 44,992 |
| afiro | sparse | 4,950 → 4,950 | 217,064 → 217,000 |
| afiro | presolve | 16,293 → 16,293 | 730,872 → 731,320 |
| afiro | dual | 17,108 → 17,108 | 866,424 → 867,176 |
| afiro | primal | 17,014 → 17,014 | 844,328 → 845,464 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,824 → 2,824 | 177,080 → 177,624 |
| adlittle | presolve | 82,757 → 82,757 | 3,346,272 → 3,348,544 |
| adlittle | dual | 84,772 → 84,772 | 4,135,984 → 4,136,944 |
| adlittle | primal | 85,570 → 85,570 | 4,413,232 → 4,413,328 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,704 → 461,432 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,616 → 607,408 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 111,840 → 112,512 |
| kb2 | sparse | 2,836 → 2,836 | 161,424 → 161,936 |
| kb2 | presolve | 229,977 → 229,977 | 10,678,152 → 10,678,904 |
| kb2 | dual | 231,179 → 231,179 | 11,131,752 → 11,132,312 |
| kb2 | primal | 231,346 → 231,346 | 11,145,256 → 11,144,392 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,000 → 878,096 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,864 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,640 → 6,635 | 299,784 → 299,888 |
| sc50a | presolve | 67,613 → 67,608 | 2,852,312 → 2,853,248 |
| sc50a | dual | 68,685 → 68,680 | 3,196,952 → 3,199,120 |
| sc50a | primal | 68,630 → 68,625 | 3,149,512 → 3,151,536 |
| sc50a | dual_no_presolve | 961 → 961 | 306,144 → 306,192 |
| sc50a | primal_no_presolve | 964 → 964 | 232,232 → 232,184 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,763 → 5,763 | 215,912 → 217,016 |
| flugpl | presolve | 31,461 → 31,461 | 1,198,376 → 1,200,408 |
| flugpl | dual | 32,132 → 32,132 | 1,308,000 → 1,310,048 |
| flugpl | primal | 32,481 → 32,481 | 1,352,544 → 1,354,528 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,728 → 91,680 |

Sc50a saves five allocations in direct sparse aggregation, full presolve, and
both presolved solves. Every other reference-stage allocation count is unchanged,
including all solves without presolve. The reference benefit is small; the
remaining measured paths do not benefit from this particular shortcut.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, full primal vector, and
iteration count (`isequal`).

Machine-readable results:
[`aggregation-unit-constant-product-allocations-before.toml`](aggregation-unit-constant-product-allocations-before.toml)
and [`aggregation-unit-constant-product-allocations-after.toml`](aggregation-unit-constant-product-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-unit-constant-product-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_unit_constant_product_probe(kind; count=128)
    ratio = kind == :ratio_positive ? 1.0 : kind == :ratio_negative ? -1.0 : kind == :zero_ratio ? 0.0 : 3.0
    rhs = kind == :rhs_positive ? 1.0 : kind == :rhs_negative ? -1.0 : 4.0
    term = 3.0
    odd = collect(1:2:2count); even = odd .+ 1
    A = sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(2.0,count),fill(term,count),fill(6.0,count),fill(5.0,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 2ratio : 5.0 for i in 1:2count];objective_constant=7.0,
        row_lower=Union{Nothing,Float64}[isodd(i) ? rhs : nothing for i in 1:2count],
        row_upper=[isodd(i) ? rhs : 20.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:ratio_positive,:ratio_negative,:rhs_positive,:rhs_negative,:nonunit,:zero_ratio)
    problem, pass = aggregation_unit_constant_product_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,282 assertions** and failed only
the four target allocation guards: 52,978 > 52,300; 53,197 > 52,600;
52,941 > 52,300; and 53,197 > 52,600. Both control budgets
passed. There are **2,286 new assertions**; existing allocation budgets were not relaxed.

Accepted aggregations cover Float32, Float64, BigFloat, and Rational{BigInt};
signed unit/nonunit/zero ratios and right-hand sides, finite and implied
column-bound projections, updated constants and costs, matrix and bound results,
primal restoration, exact objective equivalence, and source immutability.
Sequential candidates check accumulation into the committed constant. BigFloat
checks cover stored 256-bit values under ambient precision 32/64/256, exact units
and their neighbors in either operand, tiny residuals, cancellation, output
precision, and representability rejection. Large rational cases use numerators
derived from `2^300+1` and non-dyadic denominators 5, 7, 15, and 21. Overflow and
half-subnormal cases check rejection of the first candidate while permitting
representable alternative pivots. Signed-zero cases preserve the source and
canonicalize zero output.

The combined presolve/basic/doubleton/aggregation targeted suite passed
**50,802 assertions** in **1m28.8s**, exit code zero.

Independent read-only differential review found no issues and passed
**4,867 assertions across 148 models** (123 accepted, 25 rejected; 142
aggregation records), exit code zero. It compared 444 primal restorations,
592 basis restorations, 296 primal-dimension cases, 296 basis-dimension cases,
and verified 18 late cost/matrix/bound rollbacks. Coverage included both
near-unit ratios and right-hand sides stored at 256-bit BigFloat precision under
ambient 32/64/256, rational canonicalization and ordinary-arithmetic ownership,
committed constant accumulation, rejection gates, and CSC invariants. Exact
result snapshots matched the pre-change function.

The complete `test/runtests.jl` suite passed **75,687 assertions** in
**5m49.7s**, exit code zero, using:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
