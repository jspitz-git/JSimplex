# Signed-unit pivot ratios in doubleton substitution

Round 116 changes only `substitute_free_doubleton` in `src/presolve_substitution.jl`.
For a stored pivot of +1, alpha reuses the exact rhs and beta negates the exact
retained coefficient. For a pivot of -1, alpha negates the exact rhs and beta
reuses the exact retained coefficient. This skips exact pivot conversion and
both divisions. Nonunit pivots retain the shared exact pivot and divisions.

Unit comparisons use the stored coefficient exactly; no tolerance or rounded
classification is introduced. Both `_represent_exact` calls remain, including
when an exact numerator is reused. Objective updates, row updates, rejection
and staging, model construction, and primal/basis restoration are unchanged.
No source value is mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 115 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each Float64 target has 128 independent equalities `pivot*x_i+y_i=rhs`, free
`x_i`, and retained `y_i` bounded by `[-10,10]`. Eliminated costs are three,
retained costs are the smallest positive Float64 subnormal, and the objective
constant is seven. Positive/negative targets use pivots +1/-1 with rhs=4.
Zero-rhs targets use pivot +1 with rhs=+0, and pivot -1 with rhs=-0.
All targets have representable ratios but nonrepresentable retained objective
costs; every candidate is rejected at the objective gate. These probes measure
candidate evaluation rather than a successful model reduction.

The nonunit control uses pivot two and rhs four, reaching objective rejection.
The inexact-ratio control uses pivot three and rhs four, rejecting candidates
at the ratio gates. Model construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Pivot +1 | 963,960 | 829,704 | 13.93% | 24,196 → 20,356 |
| Pivot -1 | 964,840 | 830,696 | 13.90% | 24,196 → 20,356 |
| Pivot +1, rhs +0 | 936,632 | 807,096 | 13.83% | 22,916 → 19,332 |
| Pivot -1, rhs -0 | 936,664 | 807,304 | 13.81% | 22,916 → 19,332 |
| Nonunit control | 962,104 | 962,312 | — | 24,196 → 24,196 |
| Inexact-ratio control | 414,776 | 414,456 | — | 11,012 → 11,012 |

Nonzero-rhs targets save 3,840 allocations per call (30 per candidate);
zero-rhs targets save 3,584 (28 per candidate). Allocated bytes drop by
13.81–13.93% across the four targets. Both controls retain their allocation counts; byte differences
on unchanged paths alone establish no benefit.

The following table gives all nine measured stages for each reference fixture.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,184 → 45,888 |
| afiro | sparse | 4,987 → 4,987 | 218,056 → 217,304 |
| afiro | presolve | 16,330 → 16,330 | 733,112 → 731,672 |
| afiro | dual | 17,145 → 17,145 | 867,656 → 867,432 |
| afiro | primal | 17,051 → 17,051 | 846,904 → 845,944 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 176,880 → 176,848 |
| adlittle | presolve | 82,776 → 82,776 | 3,347,352 → 3,345,304 |
| adlittle | dual | 84,791 → 84,791 | 4,136,008 → 4,134,776 |
| adlittle | primal | 85,589 → 85,589 | 4,413,080 → 4,411,208 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,368 → 461,384 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,552 → 607,520 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 111,552 → 112,864 |
| kb2 | sparse | 2,836 → 2,836 | 160,656 → 160,640 |
| kb2 | presolve | 230,004 → 230,004 | 10,678,568 → 10,677,576 |
| kb2 | dual | 231,206 → 231,206 | 11,131,944 → 11,131,368 |
| kb2 | primal | 231,373 → 231,373 | 11,143,752 → 11,145,032 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,176 → 878,240 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 300,112 → 300,192 |
| sc50a | presolve | 67,634 → 67,634 | 2,852,912 → 2,853,008 |
| sc50a | dual | 68,706 → 68,706 | 3,199,360 → 3,198,192 |
| sc50a | primal | 68,651 → 68,651 | 3,152,000 → 3,151,040 |
| sc50a | dual_no_presolve | 961 → 961 | 306,096 → 306,512 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 216,312 → 216,712 |
| flugpl | presolve | 31,461 → 31,461 | 1,199,800 → 1,199,528 |
| flugpl | dual | 32,132 → 32,132 | 1,309,552 → 1,308,912 |
| flugpl | primal | 32,481 → 32,481 | 1,353,936 → 1,353,760 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All five reference fixtures retain their allocation counts in every measured
stage. They establish unchanged behavior; they show no allocation-count benefit
from this particular shortcut.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, complete primal vector,
and iteration count (`isequal`).

Machine-readable results:
[`doubleton-unit-pivot-allocations-before.toml`](doubleton-unit-pivot-allocations-before.toml)
and [`doubleton-unit-pivot-allocations-after.toml`](doubleton-unit-pivot-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-unit-pivot-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_unit_pivot_probe(kind; count=128, T=Float64)
    pivot = T(kind in (:negative,:negative_zero_rhs) ? -1 : kind == :nonunit ? 2 : kind == :inexact_ratio ? 3 : 1)
    rhs = kind == :negative_zero_rhs ? -zero(T) : T(kind == :zero_rhs ? 0 : 4)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(T(3),count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end
for kind in (:positive,:negative,:zero_rhs,:negative_zero_rhs,:nonunit,:inexact_ratio)
    problem, pass = doubleton_unit_pivot_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 980 assertions and failed only the
four target allocation guards: 24,241 > 22,000; 24,204 > 22,000;
and 22,924 > 20,500 (two cases). Both controls passed. All 984 new assertions
now pass as part of 30,554 targeted assertions covering basic elimination,
doubleton substitution, and related guards. Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; accepted
substitutions with pivots ±1 and positive/negative retained coefficients;
positive/zero/negative equality rhs; rejected candidate batches; retained
matrices, row bounds, objective costs/constants, primal/basis restoration,
and source immutability. Near-unit pivots retain exact division, including
stored-256-bit BigFloat values under ambient precision 32/64/256. Unit pivots
still reject separately nonrepresentable alpha and beta when their reused
numerators exceed ambient precision. Near-unit values do not bypass ratio
rejection. Earlier signed-zero, nonunit, staging, objective, and row-bound
checks remain in the targeted suite.

Independent read-only review found no issues. It passed 7,741 additional
assertions, separate from the focused 984, against an AST-renamed copy of
the preceding doubleton implementation: 295 models (183 accepted and 112
rejected), 1,180 basis cases, and 590 primal dimension/failure comparisons.
Coverage included near ±1 above/below under ambient precision 32/64/256,
separate/both high-precision ratio gates, signed zero, signed-unit/nonunit/
non-dyadic pivots, aliased large rationals, overflow/underflow, same-row branch
switches, and objective/matrix/bound rejection followed by later unit/nonunit
candidates. Full outputs (including BigFloat exact value, precision, and sign),
repeatability, and source immutability matched the saved baseline.

The mandatory full package suite passed **55,439/55,439** assertions in
5m35.4s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
