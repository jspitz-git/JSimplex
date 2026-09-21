# Equal-denominator objective-constant sums in doubleton substitution

Round 125 changes only the nonzero objective-constant addition in
`substitute_free_doubleton` in `src/presolve_substitution.jl`. When the exact
stored constant and exact contribution have the same denominator, their BigInt
numerators are added directly. A zero numerator becomes canonical exact zero;
otherwise the canonical `Rational{BigInt}` constructor reduces the resulting
fraction. Unequal denominators retain the existing rational addition.
This follows the established equal-denominator sums in basic presolve and the
retained-cost update in doubleton substitution.

Both `_represent_exact` gates remain. Zero-cost, signed-unit, zero-alpha, and
zero-constant shortcuts are unchanged. Retained-cost arithmetic, matrix/bound
staging, model construction, and primal/basis restoration are unchanged. No
input is mutated and no GMP internals or noncanonical constructor are used.

## Method and results

The baseline includes the preceding 124 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 target has 128 equalities `2*x_i+y_i=rhs`, free `x_i`, and `y_i`
bounded by `[-10,10]`. Eliminated costs are three; retained costs are the smallest
positive Float64 subnormal. Integer probes use rhs -2, giving alpha=-1 and a
constant contribution of -3; fractional probes use rhs -1, giving alpha=-1/2
and a contribution of -3/2. Stored constants and sums are:

- Integer cancellation: `3 + (-3) = 0`, common denominator one.
- Fractional cancellation: `3/2 + (-3/2) = 0`, common denominator two.
- Nonzero integer sum: `5 + (-3) = 2`, common denominator one.
- Reduced fractional sum: `1/2 + (-3/2) = -1`, common denominator two.

All candidates pass ratio checks but reject the updated retained cost
`tiny-3/2`. Constant arithmetic runs before this rejection, so every probe
visits its optimized branch 128 times and returns the unchanged problem. No
matrix working copies are made. The unequal-denominator control computes
`1 + (-3/2)`; the zero-constant control reuses -3/2 through the prior shortcut.
Both reject the same retained-cost update. Model construction is outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Integer cancellation | 916,552 | 893,960 | 2.46% | 22,916 → 22,532 |
| Fractional cancellation | 951,688 | 931,448 | 2.13% | 23,684 → 23,428 |
| Nonzero integer sum | 927,208 | 912,520 | 1.58% | 23,300 → 23,044 |
| Reduced fractional sum | 961,192 | 949,128 | 1.26% | 24,068 → 23,940 |
| Unequal-denominator control | 963,416 | 962,984 | — | 24,196 → 24,196 |
| Zero-constant control | 873,016 | 872,328 | — | 21,508 → 21,508 |

The four targets save **384, 256, 256, and 128 allocations per call**, respectively:
**3, 2, 2, and 1 per candidate**. Allocated bytes decrease by **1.26–2.46%**.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,568 → 45,584 |
| afiro | sparse | 4,987 → 4,987 | 218,568 → 218,488 |
| afiro | presolve | 16,330 → 16,330 | 732,568 → 733,096 |
| afiro | dual | 17,145 → 17,145 | 868,504 → 868,424 |
| afiro | primal | 17,051 → 17,051 | 846,600 → 846,584 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,952 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,776 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 178,032 → 177,824 |
| adlittle | presolve | 82,776 → 82,776 | 3,346,776 → 3,348,616 |
| adlittle | dual | 84,791 → 84,791 | 4,136,152 → 4,136,904 |
| adlittle | primal | 85,589 → 85,589 | 4,413,208 → 4,413,112 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,368 → 461,352 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,552 → 607,776 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,368 → 112,464 |
| kb2 | sparse | 2,836 → 2,836 | 161,584 → 161,424 |
| kb2 | presolve | 230,004 → 230,004 | 10,679,944 → 10,678,328 |
| kb2 | dual | 231,206 → 231,206 | 11,131,816 → 11,132,168 |
| kb2 | primal | 231,373 → 231,373 | 11,146,552 → 11,146,232 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,256 → 877,840 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 299,952 → 300,256 |
| sc50a | presolve | 67,634 → 67,634 | 2,853,536 → 2,853,440 |
| sc50a | dual | 68,706 → 68,706 | 3,198,496 → 3,198,784 |
| sc50a | primal | 68,651 → 68,651 | 3,151,056 → 3,151,648 |
| sc50a | dual_no_presolve | 961 → 961 | 306,112 → 306,208 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 217,080 → 217,368 |
| flugpl | presolve | 31,461 → 31,461 | 1,199,448 → 1,199,736 |
| flugpl | dual | 32,132 → 32,132 | 1,309,216 → 1,309,360 |
| flugpl | primal | 32,481 → 32,481 | 1,353,792 → 1,354,000 |
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
[`doubleton-equal-constant-denominator-allocations-before.toml`](doubleton-equal-constant-denominator-allocations-before.toml)
and [`doubleton-equal-constant-denominator-allocations-after.toml`](doubleton-equal-constant-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-equal-constant-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_equal_constant_denominator_probe(kind; count=128, T=Float64)
    rhs = T(kind in (:cancel_integer,:sum_integer) ? -2 : -1)
    constant = kind == :cancel_fraction ? T(3)/2 : kind == :sum_fraction ? T(1)/2 : T(kind == :cancel_integer ? 3 : kind == :sum_integer ? 5 : kind == :zero_constant ? 0 : 1)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(T(2),count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(T(3),count),fill(tiny,count));objective_constant=constant,
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end

for kind in (:cancel_integer,:cancel_fraction,:sum_integer,:sum_fraction,:unequal_denominator,:zero_constant)
    problem, pass = doubleton_equal_constant_denominator_probe(kind)
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
constant/contribution signs, matrix and row-bound results, canonical output zeros,
postsolve primal/basis, and source immutability. BigFloat checks cover stored
256-bit values under ambient precision 32/64/256, exact tiny cancellation tails,
canonical zero and output precision, and sums that cannot be represented at the
ambient precision. Large rational cases use numerators derived from `2^300+1` and non-dyadic
denominators 5, 7, 15, and 21, including sums requiring further reduction.

All **42,704/42,704** targeted assertions passed in 1m30.3s (exit 0), including
the 1,420 new checks and the existing basic, doubleton, aggregation, and related
presolve allocation guards.

Independent read-only review found no correctness issues. An AST-renamed
round-124 baseline comparison passed **4,934 additional assertions** across
156 deliberately selected differential models (122 accepted and 34 rejected),
excluding the focused tests. This included 468 ordinary primal comparisons,
624 basis cases, 312 primal-dimension cases, and 312 basis-dimension cases.
Coverage included constant cancellation/reduction, equal/unequal denominators,
large non-dyadic rationals, stored-256-bit BigFloat data under ambient precision
32/64/256, exact tiny cancellation tails, both objective gates, overflow,
zero/unit controls, matrix/bound rejection, later candidates, and source
immutability. Constructor inspection and selected ownership checks found no
new source scalar sharing in the changed branch; public arithmetic preserved
source values. Existing shortcut ownership is unchanged.

The mandatory full package suite passed **67,589/67,589** assertions in
5m52.0s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
