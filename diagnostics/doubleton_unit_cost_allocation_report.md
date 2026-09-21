# Reuse exact ratios for signed-unit doubleton objective costs

Round 120 changes only the nonzero eliminated-cost branch in
`substitute_free_doubleton` in `src/presolve_substitution.jl`. If the eliminated
variable's stored objective cost is exactly +1, its two objective contributions
reuse `beta_exact` and `alpha_exact`. For exactly -1, they use the negated ratios,
with zero alpha reused directly. This skips conversion of the unit cost and
multiplication by ±1. Other nonzero costs retain their shared exact conversion
and products. The previous zero-cost shortcut is unchanged.

Retained-cost and nonzero constant additions still use exact rationals. The
zero-alpha shortcut and both `_represent_exact` gates remain. BigFloat precision
and rejection behavior, canonical output zeros, matrix/bound staging, model
construction, and primal/basis restoration are preserved. No approximate unit
test, internal rational mutation, or direct reuse of stored floating output
values is introduced.

## Method and results

The baseline includes the preceding 119 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 target has 128 equalities `2*x_i+y_i=rhs`, free `x_i`, and
`y_i` bounded by `[-10,10]`. Retained costs are the smallest positive Float64
subnormal and the objective constant is seven. The four targets use eliminated
costs +1/-1/+1/-1 and rhs 4/4/0/0, respectively. All candidates have exactly
representable alpha/beta, but reject the nonrepresentable retained-cost update
`tiny+cost*beta`. Both objective contributions are evaluated before this
rejection, so every probe visits the optimized branch 128 times and returns the
unchanged problem. No matrix working copies are made in these probes.

The nonunit-cost control uses cost three, pivot two, and rhs four, rejecting
the same objective update. The inexact-beta control uses cost one, pivot three,
and rhs four, rejecting before objective arithmetic. Model construction occurs
outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Cost +1, rhs 4 | 960,424 | 828,312 | 13.76% | 24,196 → 20,356 |
| Cost -1, rhs 4 | 962,008 | 844,392 | 12.23% | 24,196 → 20,868 |
| Cost +1, rhs 0 | 812,168 | 723,736 | 10.89% | 19,972 → 17,284 |
| Cost -1, rhs 0 | 811,976 | 730,952 | 9.98% | 19,972 → 17,540 |
| Nonunit-cost control | 961,896 | 963,672 | — | 24,196 → 24,196 |
| Inexact-beta control | 414,232 | 416,120 | — | 11,012 → 11,012 |

For nonzero alpha, cost +1 saves **3,840 allocations** (30 per candidate), and
cost -1 saves **3,328** (26 per candidate). For zero alpha, the savings are
**2,688** and **2,432**, respectively (21 and 19 per candidate). Allocated bytes
decrease by **9.98–13.76%**. Both controls retain their allocation counts.
Cross-process byte differences on unchanged paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,344 → 45,520 |
| afiro | sparse | 4,987 → 4,987 | 217,816 → 218,216 |
| afiro | presolve | 16,330 → 16,330 | 732,040 → 733,064 |
| afiro | dual | 17,145 → 17,145 | 867,784 → 868,792 |
| afiro | primal | 17,051 → 17,051 | 846,200 → 846,952 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 177,616 → 177,440 |
| adlittle | presolve | 82,776 → 82,776 | 3,348,088 → 3,346,440 |
| adlittle | dual | 84,791 → 84,791 | 4,135,448 → 4,136,152 |
| adlittle | primal | 85,589 → 85,589 | 4,412,696 → 4,413,160 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,640 → 461,352 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,728 → 606,960 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,528 → 112,400 |
| kb2 | sparse | 2,836 → 2,836 | 161,328 → 161,248 |
| kb2 | presolve | 230,004 → 230,004 | 10,678,392 → 10,678,152 |
| kb2 | dual | 231,206 → 231,206 | 11,131,560 → 11,131,384 |
| kb2 | primal | 231,373 → 231,373 | 11,144,280 → 11,146,104 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,112 → 878,176 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,944 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 299,968 → 300,560 |
| sc50a | presolve | 67,634 → 67,634 | 2,853,216 → 2,852,688 |
| sc50a | dual | 68,706 → 68,706 | 3,198,544 → 3,198,400 |
| sc50a | primal | 68,651 → 68,651 | 3,150,992 → 3,151,008 |
| sc50a | dual_no_presolve | 961 → 961 | 306,320 → 306,528 |
| sc50a | primal_no_presolve | 964 → 964 | 232,232 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 216,808 → 217,016 |
| flugpl | presolve | 31,461 → 31,461 | 1,199,176 → 1,199,448 |
| flugpl | dual | 32,132 → 32,132 | 1,309,456 → 1,309,040 |
| flugpl | primal | 32,481 → 32,481 | 1,354,016 → 1,353,712 |
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
[`doubleton-unit-cost-allocations-before.toml`](doubleton-unit-cost-allocations-before.toml)
and [`doubleton-unit-cost-allocations-after.toml`](doubleton-unit-cost-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-unit-cost-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_unit_cost_probe(kind; count=128, T=Float64)
    pivot = T(kind == :inexact_beta ? 3 : 2)
    rhs = kind in (:zero_positive,:zero_negative) ? zero(T) : T(4)
    cost = T(kind in (:negative,:zero_negative) ? -1 : kind == :nonunit_cost ? 3 : 1)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(cost,count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end

for kind in (:positive,:negative,:zero_positive,:zero_negative,:nonunit_cost,:inexact_beta)
    problem, pass = doubleton_unit_cost_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **1,092** assertions and failed only
the four target allocation guards: 24,241 > 22,000; 24,204 > 22,500;
19,980 > 18,300; and 19,980 > 18,550. Both control budgets passed. There are
**1,096 new assertions**; existing allocation budgets were not relaxed.

Accepted substitutions cover Float32, Float64, BigFloat, and Rational{BigInt};
positive/negative pivots and retained coefficients, costs ±1, signed-zero and
nonzero rhs, matrix and row-bound results, postsolve primal/basis, and source
immutability. Cancellation and negative-zero input cases check canonical output
zeros. BigFloat checks retain cost/constant representability gates at ambient
precision 32/64/256 and check accepted output precision. Costs just above or
below ±1 preserve their exact nonunit contributions.

All **34,348/34,348** targeted assertions passed in 1m26.2s (exit 0), including
the 1,096 new checks and the existing basic, doubleton, aggregation, and related
presolve allocation guards.

Independent read-only review found no correctness issues. An AST-renamed
round-119 baseline comparison passed **78,244 additional assertions**, excluding
the 1,096 focused tests: 2,760 models (1,480 accepted and 1,280 rejected),
11,040 basis-state comparisons, 5,520 primal-dimension checks, and 5,520
malformed-basis dimension comparisons. It covered signed-unit and nearby
nonunit costs, zero and signed alpha, canonical zeros, objective/matrix/bound
representability gates, later-candidate selection, exact stored-256-bit
BigFloat data at ambient precision 32/64/256, source and Rational{BigInt}
alias immutability, and postsolve/basis results and errors.

The mandatory full package suite passed **59,233/59,233** assertions in
5m59.3s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
