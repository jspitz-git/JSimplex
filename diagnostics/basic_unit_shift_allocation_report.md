# Signed-unit products in basic-presolve row shifts

Round 109 changes only `_presolve_basic` in `src/presolve.jl`.
For finite row endpoints, a stored coefficient of +1 reuses the already exact
eliminated value; -1 negates it. Other coefficients are converted exactly once,
then reused or negated when the eliminated value is +1 or -1. Other nonzero
products keep the existing exact multiplication. Zero eliminated values and
unbounded rows retain the shortcuts from rounds 108 and 107.

The coefficient comparisons are exact comparisons with integer units, including
for stored high-precision BigFloat values. No tolerance or rounded arithmetic
is introduced. Both `_shift_bound_exact` calls and their representability checks
remain. Objective contributions, constant checks, staged row changes, rejection,
removed values/states, empty-row checks, and primal/basis restoration are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 108 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each probe fixes `x` in 128 rows `c*x+2*y`, with row bounds `[-100,100]`,
retained-variable bounds `[-10,10]`, costs `[2,3]`, and objective constant seven.
The coefficient probes use `c=+1/-1`, `x=2`; the value probes use `c=3`,
`x=+1/-1`. The nonunit control uses `c=3`, `x=2`; the zero-value control uses
`c=3`, `x=0`. Model construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Coefficient +1 | 477,592 | 385,976 | 19.18% | 12,045 → 9,357 |
| Coefficient -1 | 478,584 | 394,968 | 17.47% | 12,045 → 9,613 |
| Eliminated value +1 | 478,712 | 434,008 | 9.34% | 12,045 → 10,893 |
| Eliminated value -1 | 478,664 | 441,144 | 7.84% | 12,045 → 11,149 |
| Nonunit control | 478,712 | 477,688 | — | 12,045 → 12,045 |
| Zero-value control | 29,312 | 29,312 | — | 100 → 100 |

Coefficient +1 saves 2,688 allocations (21 per row); coefficient -1 saves
2,432 (19 per row). Eliminated value +1 saves 1,152 (9 per row); value -1
saves 896 (7 per row). Allocated bytes drop by 7.84–19.18% across these probes. Both controls retain their allocation counts; byte differences
on unchanged paths alone establish no benefit.

The following table gives allocation counts for all nine measured stages.
Full measurement details, including bytes, are in the linked TOML artifacts.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,312 → 45,632 |
| afiro | sparse | 4,987 → 4,987 | 218,376 → 218,680 |
| afiro | presolve | 16,330 → 16,330 | 732,712 → 732,104 |
| afiro | dual | 17,145 → 17,145 | 868,104 → 868,024 |
| afiro | primal | 17,051 → 17,051 | 846,456 → 845,976 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,936 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,776 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 178,208 → 177,232 |
| adlittle | presolve | 82,814 → 82,814 | 3,349,480 → 3,347,352 |
| adlittle | dual | 84,829 → 84,829 | 4,137,928 → 4,136,712 |
| adlittle | primal | 85,627 → 85,627 | 4,414,600 → 4,413,336 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,368 → 461,608 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,440 → 606,944 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,384 → 113,040 |
| kb2 | sparse | 2,836 → 2,836 | 161,840 → 161,264 |
| kb2 | presolve | 230,004 → 230,004 | 10,680,600 → 10,676,152 |
| kb2 | dual | 231,206 → 231,206 | 11,132,856 → 11,131,480 |
| kb2 | primal | 231,373 → 231,373 | 11,146,760 → 11,146,168 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,936 → 878,176 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,864 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 300,608 → 300,304 |
| sc50a | presolve | 67,634 → 67,634 | 2,853,680 → 2,852,864 |
| sc50a | dual | 68,706 → 68,706 | 3,199,248 → 3,197,808 |
| sc50a | primal | 68,651 → 68,651 | 3,152,192 → 3,150,560 |
| sc50a | dual_no_presolve | 961 → 961 | 306,512 → 306,144 |
| sc50a | primal_no_presolve | 964 → 964 | 232,232 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 217,464 → 216,264 |
| flugpl | presolve | 31,516 → 31,516 | 1,202,672 → 1,201,232 |
| flugpl | dual | 32,187 → 32,187 | 1,311,272 → 1,311,928 |
| flugpl | primal | 32,536 → 32,536 | 1,355,912 → 1,356,232 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All five reference fixtures retain their allocation counts in every measured
stage. These fixtures establish unchanged behavior; they show no allocation-count
benefit from this particular shortcut.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, complete primal vector,
and iteration count (`isequal`).

Machine-readable results:
[`basic-unit-shift-allocations-before.toml`](basic-unit-shift-allocations-before.toml)
and [`basic-unit-shift-allocations-after.toml`](basic-unit-shift-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=basic-unit-shift-basic-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function basic_unit_shift_probe(kind; count=128, T=Float64)
    coefficient = T(kind == :positive_coefficient ? 1 : kind == :negative_coefficient ? -1 : 3)
    value = T(kind == :positive_value ? 1 : kind == :negative_value ? -1 : kind == :zero_value ? 0 : 2)
    problem = LinearProblem(sparse(hcat(fill(coefficient,count),fill(T(2),count))),T[2,3];objective_constant=T(7),
        row_lower=fill(T(-100),count),row_upper=fill(T(100),count),
        column_lower=T[value,-10],column_upper=T[value,10])
    return problem,JSimplex._presolve_basic
end
for kind in (:positive_coefficient,:negative_coefficient,:positive_value,:negative_value,:nonunit,:zero_value)
    problem, pass = basic_unit_shift_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 2,034 assertions and failed only the
four target allocation guards: 12,090 > 10,000; 12,053 > 10,250;
12,053 > 11,300; and 12,053 > 11,550. Both controls passed.
All 2,038 new assertions now pass as part of 23,890 targeted assertions
covering presolve, basic elimination, and related allocation guards.
Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; both signs
of unit coefficients and eliminated values; zero/nonunit controls; finite,
one-sided, and unbounded rows; computed/cached selections; matrices, bounds,
objective/constant, primal/basis restoration, and source/selection immutability.
Near-unit operands produce their exact nonzero residuals, including stored
256-bit BigFloat values under ambient precision 32/64/256. Unit products with
unrepresentable finite endpoint shifts still reject elimination. Earlier tests
for tiny fixed values, half-subnormal shifts, and signed-zero restoration also
remain in the targeted suite.

Independent read-only review found no correctness issues. Besides rerunning
the 2,038 focused assertions, it passed 22,681 additional differential checks
against an AST-renamed copy of the preceding basic-presolve implementation:
859 model comparisons, 3,052 basis-restoration comparisons, and 96 matching
expected presolve failures. It covered near-unit values above and below both
signed units under ambient BigFloat precision 32/64/256, source storage identity
and precision, rational aliases, shared/rejected staging and later empty columns,
cached states, signed zero, empty rows, objective equivalence, and primal
restoration.

The mandatory full package suite passed **48,775/48,775** assertions in
5m32.3s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
