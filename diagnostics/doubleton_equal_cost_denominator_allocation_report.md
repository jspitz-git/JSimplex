# Equal-denominator objective-cost sums in doubleton substitution

Round 124 changes only the nonzero retained-cost addition in
`substitute_free_doubleton` in `src/presolve_substitution.jl`. When the exact
retained cost and exact contribution have the same denominator, their BigInt
numerators are added directly. A zero numerator becomes canonical exact zero;
otherwise the canonical `Rational{BigInt}` constructor reduces the resulting
fraction. Unequal denominators retain the existing rational addition.
This follows the established equal-denominator constant update in basic presolve.

Both `_represent_exact` gates remain. Zero-cost, signed-unit, zero-alpha, and
zero-constant shortcuts are unchanged. Matrix/bound staging, model construction,
and primal/basis restoration are unchanged. No input is mutated and no GMP
internals or noncanonical rational constructor are used.

## Method and results

The baseline includes the preceding 123 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 target has 128 equalities `2*x_i+retained_coefficient*y_i=4`, free
`x_i`, and `y_i` bounded by `[-10,10]`. Eliminated costs are three and the
objective constant is the smallest positive Float64 subnormal. The integer
probes use retained coefficient two, so the contribution is -3; the fractional
probes use retained coefficient one, so it is -3/2. Retained costs and sums are:

- Integer cancellation: `3 + (-3) = 0`, common denominator one.
- Fractional cancellation: `3/2 + (-3/2) = 0`, common denominator two.
- Nonzero integer sum: `5 + (-3) = 2`, common denominator one.
- Reduced fractional sum: `1/2 + (-3/2) = -1`, common denominator two.

All candidates pass ratio and updated-cost checks, then reject the constant
update `tiny+6`. Each probe visits its optimized branch 128 times and returns
the unchanged problem. No matrix working copies are made in these probes.
The unequal-denominator control computes `1 + (-3/2)`; the zero-retained control
uses retained cost zero and reuses the contribution through the prior shortcut.
Both reject the same constant update. Model construction is outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Integer cancellation | 917,320 | 896,264 | 2.30% | 22,916 → 22,532 |
| Fractional cancellation | 953,384 | 933,336 | 2.10% | 23,684 → 23,428 |
| Nonzero integer sum | 928,888 | 914,728 | 1.52% | 23,300 → 23,044 |
| Reduced fractional sum | 963,208 | 950,968 | 1.27% | 24,068 → 23,940 |
| Unequal-denominator control | 965,544 | 965,080 | — | 24,196 → 24,196 |
| Zero-retained control | 875,160 | 874,440 | — | 21,508 → 21,508 |

The four targets save **384, 256, 256, and 128 allocations per call**, respectively:
**3, 2, 2, and 1 per candidate**. Allocated bytes decrease by **1.27–2.30%**.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,232 → 45,440 |
| afiro | sparse | 4,987 → 4,987 | 217,992 → 218,904 |
| afiro | presolve | 16,330 → 16,330 | 731,960 → 733,496 |
| afiro | dual | 17,145 → 17,145 | 867,544 → 869,032 |
| afiro | primal | 17,051 → 17,051 | 846,184 → 847,432 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,936 |
| afiro | primal_no_presolve | 759 → 759 | 121,776 → 121,776 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 177,904 → 177,728 |
| adlittle | presolve | 82,776 → 82,776 | 3,347,704 → 3,348,200 |
| adlittle | dual | 84,791 → 84,791 | 4,135,560 → 4,137,560 |
| adlittle | primal | 85,589 → 85,589 | 4,412,520 → 4,413,816 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,304 → 461,320 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,376 → 607,616 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,496 → 112,512 |
| kb2 | sparse | 2,836 → 2,836 | 161,648 → 161,536 |
| kb2 | presolve | 230,004 → 230,004 | 10,679,688 → 10,679,800 |
| kb2 | dual | 231,206 → 231,206 | 11,131,656 → 11,131,784 |
| kb2 | primal | 231,373 → 231,373 | 11,144,680 → 11,145,544 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,576 → 878,016 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 299,808 → 300,048 |
| sc50a | presolve | 67,634 → 67,634 | 2,853,328 → 2,853,744 |
| sc50a | dual | 68,706 → 68,706 | 3,199,616 → 3,199,648 |
| sc50a | primal | 68,651 → 68,651 | 3,152,208 → 3,152,576 |
| sc50a | dual_no_presolve | 961 → 961 | 306,528 → 306,288 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 216,744 → 217,016 |
| flugpl | presolve | 31,461 → 31,461 | 1,198,760 → 1,200,024 |
| flugpl | dual | 32,132 → 32,132 | 1,308,416 → 1,310,144 |
| flugpl | primal | 32,481 → 32,481 | 1,352,880 → 1,354,528 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All five fixtures retain their allocation counts in every measured stage,
including solves without presolve. They establish unchanged behavior and show
no allocation-count benefit from this particular shortcut.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, full primal vector, and
iteration count (`isequal`).

Machine-readable results:
[`doubleton-equal-cost-denominator-allocations-before.toml`](doubleton-equal-cost-denominator-allocations-before.toml)
and [`doubleton-equal-cost-denominator-allocations-after.toml`](doubleton-equal-cost-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-equal-cost-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_equal_cost_denominator_probe(kind; count=128, T=Float64)
    retained_coefficient = T(kind in (:cancel_integer,:sum_integer) ? 2 : 1)
    retained_cost = kind == :cancel_fraction ? T(3)/2 : kind == :sum_fraction ? T(1)/2 : T(kind == :cancel_integer ? 3 : kind == :sum_integer ? 5 : kind == :zero_retained ? 0 : 1)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(T(2),count),fill(retained_coefficient,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(T(3),count),fill(retained_cost,count));objective_constant=tiny,
        row_lower=fill(T(4),count),row_upper=fill(T(4),count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end

for kind in (:cancel_integer,:cancel_fraction,:sum_integer,:sum_fraction,:unequal_denominator,:zero_retained)
    problem, pass = doubleton_equal_cost_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **1,416** assertions and failed only
the four target allocation guards: 22,961 > 22,700; 23,692 > 23,550;
23,308 > 23,150; and 24,076 > 24,020. Both control budgets passed. There are
**1,420 new assertions**; existing allocation budgets were not relaxed.

Accepted substitutions cover Float32, Float64, BigFloat, and Rational{BigInt};
cancellation, nonzero sums, fraction reduction, unequal denominators, both
cost/contribution signs, matrix and row-bound results, canonical output zeros,
postsolve primal/basis, and source immutability. BigFloat checks cover stored
256-bit values under ambient precision 32/64/256, exact tiny cancellation tails,
canonical zero and output precision, and sums that cannot be represented at the
ambient precision. Large rational cases use numerators derived from `2^300+1` and non-dyadic
denominators 5, 7, 15, and 21, including sums requiring further reduction.

All **41,284/41,284** targeted assertions passed in 1m29.2s (exit 0), including
the 1,420 new checks and the existing basic, doubleton, aggregation, and related
presolve allocation guards.

Independent read-only review found no issues. An AST-renamed round-123 baseline
comparison passed **4,846 additional assertions** across 156 deliberately
selected differential models (124 accepted and 32 rejected), excluding the
focused tests. This included 468 primal restoration comparisons, 624 basis
comparisons, 312 primal-dimension cases, and 312 basis-dimension cases.
Coverage included equal/unequal denominators, canonical cancellation and reduction,
large non-dyadic rationals, stored-256-bit BigFloat data at ambient precision
32/64/256, cancellation tails, both objective gates, overflow, staged matrix/bound
rejection, later candidates, and source immutability. Inspection and selected
probes found no new source scalar sharing from the canonical rational constructor.
Ordinary arithmetic and reduced-objective updates preserved the source model.

The mandatory full package suite passed **66,169/66,169** assertions in
5m34.9s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
