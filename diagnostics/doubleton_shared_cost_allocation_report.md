# Share the exact eliminated objective cost in doubleton substitution

Round 114 changes only `substitute_free_doubleton` in `src/presolve_substitution.jl`.
Each candidate now converts the eliminated variable's objective cost once and
reuses it in both the retained-cost and objective-constant updates. Previously
these two expressions independently converted the same stored value.

Both exact products, exact sums, and representability checks remain. Conversion
still occurs after alpha/beta have passed their representability checks. The
cached value belongs to the current candidate only. Row updates, rejection and
staging, canonical model construction, and primal/basis restoration are unchanged.
No source value is mutated and no approximate arithmetic is introduced.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 113 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each Float64 target has 128 independent equalities `2*x_i+y_i=rhs`, free `x_i`,
and retained `y_i` bounded by `[-10,10]`. Every retained cost is the smallest
positive Float64 subnormal; the objective constant is seven. Eliminated costs
are 3, -3, or 3/2 with rhs=4; the fourth target uses cost 3 and rhs=0.
All 128 candidates pass alpha/beta checks and reach both objective updates,
but their retained cost (tiny minus half the eliminated cost) is not exactly
representable. All are rejected, so these probes measure candidate evaluation
rather than a successful model reduction.

The inexact-ratio control uses `3*x_i+y_i=4`, rejecting candidates before
objective conversion. The no-substitution control bounds both variables by
`[-10,10]`, so neither is eligible. Model construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive eliminated cost | 1,053,880 | 1,008,136 | 4.34% | 27,268 → 25,732 |
| Negative eliminated cost | 1,055,672 | 1,009,944 | 4.33% | 27,268 → 25,732 |
| Fractional eliminated cost | 1,055,800 | 1,009,912 | 4.35% | 27,268 → 25,732 |
| Zero equality rhs | 1,028,344 | 981,736 | 4.53% | 25,988 → 24,452 |
| Inexact-ratio control | 462,280 | 462,008 | — | 12,548 → 12,548 |
| No-substitution control | 4,312 | 4,312 | — | 4 → 4 |

All four targets save 1,536 allocations per call, or 12 for each of the 128
candidates reaching objective updates. Allocated bytes drop by 4.33–4.53%. Both controls retain their allocation counts; byte differences
on unchanged paths alone establish no benefit.

The following table gives all nine measured stages for each reference fixture.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,616 → 45,760 |
| afiro | sparse | 4,987 → 4,987 | 217,928 → 218,280 |
| afiro | presolve | 16,330 → 16,330 | 732,136 → 732,296 |
| afiro | dual | 17,145 → 17,145 | 868,056 → 867,800 |
| afiro | primal | 17,051 → 17,051 | 846,392 → 845,848 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 177,600 → 177,728 |
| adlittle | presolve | 82,776 → 82,776 | 3,348,584 → 3,347,144 |
| adlittle | dual | 84,791 → 84,791 | 4,136,792 → 4,137,352 |
| adlittle | primal | 85,589 → 85,589 | 4,413,528 → 4,414,168 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,464 → 461,336 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,664 → 607,232 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,688 → 113,120 |
| kb2 | sparse | 2,836 → 2,836 | 161,248 → 161,792 |
| kb2 | presolve | 230,004 → 230,004 | 10,678,136 → 10,678,296 |
| kb2 | dual | 231,206 → 231,206 | 11,132,120 → 11,132,232 |
| kb2 | primal | 231,373 → 231,373 | 11,145,944 → 11,145,336 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,064 → 878,128 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,864 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 299,872 → 300,384 |
| sc50a | presolve | 67,634 → 67,634 | 2,853,232 → 2,853,216 |
| sc50a | dual | 68,706 → 68,706 | 3,199,792 → 3,199,280 |
| sc50a | primal | 68,651 → 68,651 | 3,152,400 → 3,151,856 |
| sc50a | dual_no_presolve | 961 → 961 | 306,144 → 306,304 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 217,192 → 217,224 |
| flugpl | presolve | 31,461 → 31,461 | 1,199,480 → 1,199,224 |
| flugpl | dual | 32,132 → 32,132 | 1,309,024 → 1,309,616 |
| flugpl | primal | 32,481 → 32,481 | 1,353,504 → 1,353,952 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

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
[`doubleton-shared-cost-allocations-before.toml`](doubleton-shared-cost-allocations-before.toml)
and [`doubleton-shared-cost-allocations-after.toml`](doubleton-shared-cost-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-shared-cost-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_shared_cost_probe(kind; count=128, T=Float64)
    pivot = T(kind == :inexact_ratio ? 3 : 2)
    cost = kind == :negative ? T(-3) : kind == :fractional ? T(3)/T(2) : T(3)
    rhs = T(kind == :zero_rhs ? 0 : 4)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(cost,count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(kind == :no_substitution ? T(-10) : nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(kind == :no_substitution ? T(10) : nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end
for kind in (:positive,:negative,:fractional,:zero_rhs,:inexact_ratio,:no_substitution)
    problem, pass = doubleton_shared_cost_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 704 assertions and failed only the
four target allocation guards: 27,313 > 26,500; 27,276 > 26,500 (two cases);
and 25,996 > 25,250. Both controls passed. All 708 new assertions now pass as
part of 28,844 targeted assertions covering basic elimination, doubleton
substitution, and related presolve guards. Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; accepted
substitutions with positive, negative, zero, unit, and fractional eliminated
costs; positive/zero/negative equality rhs; rejected candidate batches; retained
matrices, row bounds, objective costs/constants, primal/basis restoration,
and source immutability. Stored-256-bit BigFloat costs under ambient precision
32/64/256 retain exact cancellation and reject unrepresentable cost/constant
updates. A rejected candidate followed by one with a different eliminated cost
verifies that reuse stays within a candidate. Earlier row-bound representability
and doubleton checks remain in the targeted suite.

Independent read-only review found no issues. Besides rerunning the 708
focused assertions, it passed 3,138 additional assertions against an AST-renamed
copy of the preceding doubleton implementation: 120 models (90 accepted and
30 rejected), 480 basis cases, and 240 malformed-primal outcome comparisons.
Coverage included all four numeric types, stored-256-bit BigFloat costs under
ambient precision 32/64/256, exact cancellation and objective representability,
zero/unit/fractional/negative costs, large non-dyadic rational aliases, objective/
row-staging rejection followed by a different eliminated cost, repeatability,
and source immutability. Outputs and restoration outcomes matched the baseline.

The mandatory full package suite passed **53,729/53,729** assertions in
5m37.4s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
