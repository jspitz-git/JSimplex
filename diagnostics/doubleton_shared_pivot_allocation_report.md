# Share the exact pivot in doubleton substitution

Round 115 changes only `substitute_free_doubleton` in `src/presolve_substitution.jl`.
Each candidate now converts the pivot coefficient once and reuses the exact
rational for both alpha and beta. Previously the two divisions independently
converted the same stored pivot.

Both exact divisions and both representability checks remain. The cached pivot
belongs to the current candidate only. Objective updates, row updates, rejection
and staging, canonical model construction, and primal/basis restoration are
unchanged. No source value is mutated and no approximate arithmetic is introduced.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 114 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each Float64 target has 128 independent equalities `pivot*x_i+y_i=4`, free `x_i`,
and retained `y_i` bounded by `[-10,10]`. Eliminated costs are three, retained
costs are the smallest positive Float64 subnormal, and the objective constant
is seven. Pivots 2, -2, and 1/2 produce exactly representable alpha/beta but
nonrepresentable retained objective costs, so all candidates are rejected at
the objective gate. Pivot 3 rejects all candidates at the ratio gates. These
probes measure candidate evaluation rather than a successful model reduction.

The no-substitution control bounds both variables by `[-10,10]`, so neither
is eligible. The inequality control uses row bounds `[4,5]`, so no equality
is eligible. Both controls use pivot two. Model construction occurs outside
measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive pivot | 1,007,528 | 961,960 | 4.52% | 25,732 → 24,196 |
| Negative pivot | 1,009,000 | 963,848 | 4.47% | 25,732 → 24,196 |
| Fractional pivot | 1,011,880 | 966,728 | 4.46% | 25,732 → 24,196 |
| Nonrepresentable ratios | 461,640 | 415,960 | 9.90% | 12,548 → 11,012 |
| No-substitution control | 4,312 | 4,312 | — | 4 → 4 |
| Inequality control | 4,312 | 4,312 | — | 4 → 4 |

All four targets save 1,536 allocations per call, or 12 for each of the 128
candidates reaching ratio computation. Allocated bytes drop by 4.46–9.90%,
with the largest percentage reduction in the early ratio-rejection probe. Both controls retain their allocation counts; byte differences
on unchanged paths alone establish no benefit.

The following table gives all nine measured stages for each reference fixture.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,440 → 45,568 |
| afiro | sparse | 4,987 → 4,987 | 218,504 → 218,168 |
| afiro | presolve | 16,330 → 16,330 | 732,552 → 732,616 |
| afiro | dual | 17,145 → 17,145 | 867,592 → 868,264 |
| afiro | primal | 17,051 → 17,051 | 846,856 → 846,840 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 178,224 → 177,296 |
| adlittle | presolve | 82,776 → 82,776 | 3,347,992 → 3,348,168 |
| adlittle | dual | 84,791 → 84,791 | 4,136,744 → 4,136,376 |
| adlittle | primal | 85,589 → 85,589 | 4,413,160 → 4,413,592 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,336 → 461,448 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,584 → 607,472 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,800 → 112,976 |
| kb2 | sparse | 2,836 → 2,836 | 161,984 → 161,136 |
| kb2 | presolve | 230,004 → 230,004 | 10,679,416 → 10,678,568 |
| kb2 | dual | 231,206 → 231,206 | 11,131,832 → 11,131,208 |
| kb2 | primal | 231,373 → 231,373 | 11,146,792 → 11,144,792 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,032 → 878,192 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,944 → 260,848 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 299,888 → 299,824 |
| sc50a | presolve | 67,634 → 67,634 | 2,852,912 → 2,852,992 |
| sc50a | dual | 68,706 → 68,706 | 3,198,704 → 3,198,896 |
| sc50a | primal | 68,651 → 68,651 | 3,151,936 → 3,151,648 |
| sc50a | dual_no_presolve | 961 → 961 | 306,112 → 306,144 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 217,304 → 216,904 |
| flugpl | presolve | 31,461 → 31,461 | 1,199,640 → 1,200,008 |
| flugpl | dual | 32,132 → 32,132 | 1,309,136 → 1,309,296 |
| flugpl | primal | 32,481 → 32,481 | 1,353,792 → 1,353,840 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,728 → 91,680 |

All five reference fixtures retain their allocation counts in every measured
stage. They establish unchanged behavior; they show no allocation-count benefit
from this particular reuse.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, complete primal vector,
and iteration count (`isequal`).

Machine-readable results:
[`doubleton-shared-pivot-allocations-before.toml`](doubleton-shared-pivot-allocations-before.toml)
and [`doubleton-shared-pivot-allocations-after.toml`](doubleton-shared-pivot-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-shared-pivot-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_shared_pivot_probe(kind; count=128, T=Float64)
    pivot = kind == :negative ? T(-2) : kind == :fractional ? T(1)/T(2) : T(kind == :inexact_ratio ? 3 : 2)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(T(3),count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(T(4),count),row_upper=fill(T(kind == :inequality ? 5 : 4),count),
        column_lower=vcat(fill(kind == :no_substitution ? T(-10) : nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(kind == :no_substitution ? T(10) : nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end
for kind in (:positive,:negative,:fractional,:inexact_ratio,:no_substitution,:inequality)
    problem, pass = doubleton_shared_pivot_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 722 assertions and failed only the
four target allocation guards: 25,777 > 25,000; 25,740 > 25,000 (two cases);
and 12,556 > 11,800. Both controls passed. All 726 new assertions now pass as
part of 29,570 targeted assertions covering basic elimination, doubleton
substitution, and related presolve guards. Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; accepted
substitutions with positive, negative, unit, and fractional pivots; positive/
zero/negative equality rhs; rejected candidate batches; retained matrices,
row bounds, objective costs/constants, primal/basis restoration, and source
immutability. Stored-256-bit BigFloat pivots under ambient precision 32/64/256
retain exact ratios and reject separately nonrepresentable alpha and beta.
A rejected pivot-three candidate followed by an accepted pivot-minus-two
candidate verifies that reuse stays within a candidate. Earlier objective
and row-bound representability checks remain in the targeted suite.

Independent read-only review found no issues. It passed 4,723 additional
assertions, separate from the focused 726, against an AST-renamed copy of
the preceding doubleton implementation: 182 models (109 accepted and 73
rejected), 728 basis comparisons, and 364 primal dimension/failure comparisons.
Coverage included pivot signs and explicit zero coefficients, non-dyadic ratios,
stored/ambient BigFloat precision, rational aliases, overflow/underflow in
individual ratios, changed-pivot fallback on the same or a later row, staging,
primal restoration, and source immutability. Results matched the saved baseline.

The mandatory full package suite passed **54,455/54,455** assertions in
5m32.6s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
