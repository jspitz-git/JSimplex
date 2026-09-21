# Signed-unit objective contributions in basic presolve

Round 111 changes only `_presolve_basic` in `src/presolve.jl`.
For nonzero objective contributions, cost +1 reuses the already exact eliminated
value, while cost -1 negates it. Other costs are converted exactly once, then
reused or negated for eliminated values +1 or -1. Nonunit products retain exact
multiplication. The zero-contribution shortcut from round 110 is unchanged.

The stored cost is compared exactly with integer units; eliminated-value
comparisons use its already computed exact rational. No tolerance or rounded
comparison is introduced. Exact constant addition and `_represent_exact` remain
before row staging. Row-bound checks, rejection, staged updates, removed values/
states, empty-row checks, and primal/basis restoration are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 110 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each probe has 128 rows `x_i+2*y`, both row endpoints unbounded, fixed `x_i`, and
retained `y` with bounds `[-10,10]` and cost three. The objective constant is
seven. Cost probes use `cost=+1/-1` and `x_i=2`; value probes use `cost=3` and
`x_i=+1/-1`. The nonunit control uses `cost=3`, `x_i=2`; the zero-value control
uses `cost=3`, `x_i=0`. Model construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Cost +1 | 341,312 | 251,328 | 26.36% | 8,900 → 6,212 |
| Cost -1 | 342,128 | 260,032 | 24.00% | 8,900 → 6,468 |
| Eliminated value +1 | 342,176 | 299,600 | 12.44% | 8,900 → 7,748 |
| Eliminated value -1 | 342,144 | 307,008 | 10.27% | 8,900 → 8,004 |
| Nonunit contribution control | 342,144 | 343,504 | — | 8,900 → 8,900 |
| Zero-value control | 64,112 | 64,496 | — | 1,220 → 1,220 |

Cost +1 saves 2,688 allocations (21 per eliminated variable); cost -1 saves
2,432 (19 per variable). Eliminated value +1 saves 1,152 (9 per variable);
value -1 saves 896 (7 per variable). Allocated bytes drop by 10.27–26.36%
across the four targets. Both controls retain their allocation counts; byte differences
on unchanged paths alone establish no benefit.

The following table gives all nine measured stages for each reference fixture.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,232 → 45,200 |
| afiro | sparse | 4,987 → 4,987 | 218,744 → 218,488 |
| afiro | presolve | 16,330 → 16,330 | 732,472 → 732,136 |
| afiro | dual | 17,145 → 17,145 | 868,616 → 867,848 |
| afiro | primal | 17,051 → 17,051 | 846,776 → 846,440 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 178,224 → 177,536 |
| adlittle | presolve | 82,776 → 82,776 | 3,347,800 → 3,346,360 |
| adlittle | dual | 84,791 → 84,791 | 4,136,168 → 4,137,096 |
| adlittle | primal | 85,589 → 85,589 | 4,413,080 → 4,412,536 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,464 → 461,704 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,056 → 607,264 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,736 → 112,592 |
| kb2 | sparse | 2,836 → 2,836 | 161,808 → 161,472 |
| kb2 | presolve | 230,004 → 230,004 | 10,680,552 → 10,676,712 |
| kb2 | dual | 231,206 → 231,206 | 11,131,976 → 11,132,088 |
| kb2 | primal | 231,373 → 231,373 | 11,145,944 → 11,145,544 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,048 → 877,968 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,864 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 300,368 → 300,224 |
| sc50a | presolve | 67,634 → 67,634 | 2,852,992 → 2,852,704 |
| sc50a | dual | 68,706 → 68,706 | 3,199,264 → 3,196,912 |
| sc50a | primal | 68,651 → 68,651 | 3,152,160 → 3,150,048 |
| sc50a | dual_no_presolve | 961 → 961 | 306,176 → 306,208 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 217,128 → 216,472 |
| flugpl | presolve | 31,497 → 31,497 | 1,201,528 → 1,200,536 |
| flugpl | dual | 32,168 → 32,168 | 1,311,424 → 1,309,760 |
| flugpl | primal | 32,517 → 32,517 | 1,356,032 → 1,354,560 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,752 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,728 |

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
[`basic-unit-objective-allocations-before.toml`](basic-unit-objective-allocations-before.toml)
and [`basic-unit-objective-allocations-after.toml`](basic-unit-objective-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=basic-unit-objective-basic-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function basic_unit_objective_probe(kind; count=128, T=Float64)
    cost = T(kind == :positive_cost ? 1 : kind == :negative_cost ? -1 : 3)
    value = T(kind == :positive_value ? 1 : kind == :negative_value ? -1 : kind == :zero_value ? 0 : 2)
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),fill(count+1,count)),vcat(ones(T,count),fill(T(2),count)),count,count+1)
    problem = LinearProblem(A,vcat(fill(cost,count),T[3]);objective_constant=T(7),
        row_lower=fill(nothing,count),row_upper=fill(nothing,count),
        column_lower=vcat(fill(value,count),T[-10]),column_upper=vcat(fill(value,count),T[10]))
    return problem,JSimplex._presolve_basic
end
for kind in (:positive_cost,:negative_cost,:positive_value,:negative_value,:nonunit,:zero_value)
    problem, pass = basic_unit_objective_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 1,514 assertions and failed only the
four target allocation guards: 8,945 > 7,000; 8,908 > 7,250; 8,908 > 8,200;
and 8,908 > 8,450. Both controls passed. All 1,518 new assertions now pass as
part of 26,094 targeted assertions covering basic elimination and
related presolve allocation guards. Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; signed-unit
costs and eliminated values; zero/nonunit controls; computed/cached selections;
retained matrices, bounds, objective values, primal/basis restoration,
removed-variable states, and source/selection immutability. Near-unit operands
retain exact nonzero residuals after cancellation, including stored-256-bit
BigFloat values under ambient precision 32/64/256. Unit contributions still
reject unrepresentable objective constants under reduced ambient precision;
unit costs do not bypass rejection of half-subnormal finite row shifts.
Earlier tiny nonzero and zero-contribution checks remain in the targeted suite.

Independent read-only review found no issues. It passed 15,070 additional
assertions, separate from the focused 1,518, against an AST-renamed copy of
the preceding basic-presolve implementation: 642 model comparisons, 2,312
basis-restoration comparisons, and 64 matching failure cases. Coverage included
stored-256-bit BigFloat values near both signed units under ambient precision
32/64/256, exact cancellation and representability rejection, Float32/64
objective-sum overflow, shared-row staging rejection followed by unit acceptance,
empty/free cached selections, signed zero, object/scalar identity, rational
aliases, primal/objective equivalence, and complete failure records.

The mandatory full package suite passed **50,979/50,979** assertions in
5m35.3s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
