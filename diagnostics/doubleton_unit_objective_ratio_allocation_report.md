# Reuse exact costs for signed-unit doubleton objective ratios

Round 121 changes only the nonzero, nonunit eliminated-cost branch in
`substitute_free_doubleton` in `src/presolve_substitution.jl`. When `beta_exact`
or `alpha_exact` is +1, its objective contribution reuses the already converted
exact cost. For -1, it uses the negated exact cost. Other ratios retain their
exact products. The previous zero-alpha, zero-cost, and unit-cost shortcuts
are unchanged.

Exact objective additions and both `_represent_exact` gates remain in place.
BigFloat output precision and rejection behavior, canonical output zeros,
matrix/bound staging, model construction, and primal/basis restoration are
preserved. No approximate unit test, internal rational mutation, or direct
reuse of stored floating output values is introduced.

## Method and results

The baseline includes the preceding 120 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 target has 128 equalities `2*x_i+retained*y_i=rhs`, free `x_i`,
and `y_i` bounded by `[-10,10]`. Eliminated costs are three, retained costs are
the smallest positive Float64 subnormal, and the objective constant is seven.
The beta targets use retained coefficients -2/+2 and rhs four, giving beta
+1/-1 and alpha two. The alpha targets use retained coefficient one and rhs
+2/-2, giving alpha +1/-1 and beta -1/2. Each probe thus isolates one shortcut.

All candidates have exactly representable alpha/beta, but reject the retained-cost
update `tiny+3*beta`. Both objective contributions are evaluated before rejection,
so each probe visits its optimized branch 128 times and returns the unchanged
problem. No matrix working copies are made in these probes.

The nonunit-ratios control uses retained coefficient one and rhs four, giving
alpha two and beta -1/2, and rejects the same objective update. The inexact-beta
control uses pivot three, retained coefficient one, and rhs four, rejecting
before objective arithmetic. Model construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Beta +1 | 963,976 | 919,496 | 4.61% | 24,196 → 23,044 |
| Beta -1 | 966,120 | 928,216 | 3.92% | 24,196 → 23,300 |
| Alpha +1 | 963,480 | 917,672 | 4.75% | 24,196 → 23,044 |
| Alpha -1 | 963,544 | 925,288 | 3.97% | 24,196 → 23,300 |
| Nonunit-ratios control | 963,544 | 961,608 | — | 24,196 → 24,196 |
| Inexact-beta control | 415,496 | 414,008 | — | 11,012 → 11,012 |

Either +1 ratio saves **1,152 allocations per call** (9 per candidate), and
either -1 ratio saves **896** (7 per candidate). Allocated bytes decrease by
**3.92–4.75%**. Both controls retain their allocation counts.
Cross-process byte differences on unchanged paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 44,560 → 45,280 |
| afiro | sparse | 4,987 → 4,987 | 218,344 → 218,088 |
| afiro | presolve | 16,330 → 16,330 | 733,464 → 731,624 |
| afiro | dual | 17,145 → 17,145 | 869,720 → 867,880 |
| afiro | primal | 17,051 → 17,051 | 847,896 → 846,408 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,952 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,888 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 177,520 → 177,680 |
| adlittle | presolve | 82,776 → 82,776 | 3,348,536 → 3,347,240 |
| adlittle | dual | 84,791 → 84,791 | 4,137,816 → 4,135,640 |
| adlittle | primal | 85,589 → 85,589 | 4,414,456 → 4,412,712 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,416 → 461,816 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,616 → 607,552 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 111,808 → 112,368 |
| kb2 | sparse | 2,836 → 2,836 | 161,056 → 161,408 |
| kb2 | presolve | 230,004 → 230,004 | 10,680,696 → 10,677,720 |
| kb2 | dual | 231,206 → 231,206 | 11,134,424 → 11,130,984 |
| kb2 | primal | 231,373 → 231,373 | 11,146,392 → 11,143,992 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,936 → 878,000 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 300,944 → 300,064 |
| sc50a | presolve | 67,634 → 67,634 | 2,853,776 → 2,852,736 |
| sc50a | dual | 68,706 → 68,706 | 3,199,584 → 3,198,576 |
| sc50a | primal | 68,651 → 68,651 | 3,152,384 → 3,151,232 |
| sc50a | dual_no_presolve | 961 → 961 | 306,144 → 306,144 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 216,600 → 216,696 |
| flugpl | presolve | 31,461 → 31,461 | 1,200,680 → 1,199,272 |
| flugpl | dual | 32,132 → 32,132 | 1,309,888 → 1,309,200 |
| flugpl | primal | 32,481 → 32,481 | 1,354,816 → 1,353,792 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,728 → 91,680 |

All five fixtures retain their allocation counts in every measured stage,
including solves without presolve. They establish unchanged behavior and show
no allocation-count benefit from this particular shortcut.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, full primal vector, and
iteration count (`isequal`).

Machine-readable results:
[`doubleton-unit-objective-ratio-allocations-before.toml`](doubleton-unit-objective-ratio-allocations-before.toml)
and [`doubleton-unit-objective-ratio-allocations-after.toml`](doubleton-unit-objective-ratio-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-unit-objective-ratio-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_unit_objective_ratio_probe(kind; count=128, T=Float64)
    pivot = T(kind == :inexact_beta ? 3 : 2)
    retained = T(kind == :beta_positive ? -2 : kind == :beta_negative ? 2 : 1)
    rhs = T(kind == :alpha_positive ? 2 : kind == :alpha_negative ? -2 : 4)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),fill(retained,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(T(3),count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end

for kind in (:beta_positive,:beta_negative,:alpha_positive,:alpha_negative,:nonunit_ratios,:inexact_beta)
    problem, pass = doubleton_unit_objective_ratio_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **1,464** assertions and failed only
the four target allocation guards: 24,241 > 23,500; 24,204 > 23,750;
24,204 > 23,500; and 24,204 > 23,750. Both control budgets passed. There are
**1,468 new assertions**; existing allocation budgets were not relaxed.

Accepted substitutions cover Float32, Float64, BigFloat, and Rational{BigInt};
positive/negative unit and nonunit alpha/beta, zero alpha, nonunit costs of
both signs, matrix and row-bound results, postsolve primal/basis, and source
immutability. Exact cancellation checks canonical output zeros. BigFloat
checks retain objective representability gates at ambient precision 32/64/256,
including stored high-precision eliminated costs, and verify accepted output
precision. Ratios just above or below ±1 preserve exact nonunit contributions.

All **35,816/35,816** targeted assertions passed in 1m28.9s (exit 0), including
the 1,468 new checks and the existing basic, doubleton, aggregation, and related
presolve allocation guards.

Independent read-only review found no correctness issues. An AST-renamed
round-120 baseline comparison passed **54,252 additional assertions**, excluding
the focused tests: 1,756 models (1,564 accepted and 192 rejected), 7,024 basis
cases, 3,512 primal-dimension checks, and 3,512 basis-dimension checks. It covered
signed-unit and neighboring ratios, stored-256-bit BigFloat data at ambient
precision 32/64/256, exact cancellation, objective overflow, matrix/bound rejection,
later candidates, postsolve/basis results and errors, and Rational{BigInt}
alias behavior. Additional mutation probes matched the baseline, including the
pre-existing shared rational constant on the unchanged zero-alpha path.

The mandatory full package suite passed **60,701/60,701** assertions in
5m53.0s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
