# Reuse doubleton objective contributions for zero retained costs

Round 122 changes only the retained-cost update in the nonzero eliminated-cost
branch of `substitute_free_doubleton` in `src/presolve_substitution.jl`.
If the retained variable's stored cost is exactly zero, its new exact cost now
reuses `cost_shift`. This skips conversion of zero to a rational and addition
of zero. Nonzero retained costs keep their exact conversion and addition.
The zero eliminated-cost branch and all constant arithmetic are unchanged.

Both `_represent_exact` gates remain. They still reject nonrepresentable costs
or constants, including tiny and overflowing contributions, and preserve
BigFloat output precision and canonical zero signs. Ratio computation,
matrix/bound staging, model construction, and primal/basis restoration are
unchanged. No approximate zero test or source mutation is introduced.

## Method and results

The baseline includes the preceding 121 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 target has 128 equalities `2*x_i+y_i=4`, free `x_i`, and `y_i`
bounded by `[-10,10]`. The objective constant is the smallest positive Float64
subnormal. The four targets use eliminated costs +3/-3/+1/-1 and retained costs
+0/-0/+0/-0, respectively. All candidates have exactly representable alpha=2,
beta=-1/2, and updated retained cost. They reject the nonrepresentable constant
update `tiny+2*cost`. Each probe therefore visits the optimized branch 128 times
and returns the unchanged problem. No matrix working copies are made.

The nonzero-retained control uses retained cost three and eliminated cost three,
rejecting the same constant update. The inexact-beta control uses pivot three,
retained cost zero, and eliminated cost three, rejecting before objective
arithmetic. Model construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Retained +0, eliminated +3 | 955,176 | 873,832 | 8.52% | 23,812 → 21,508 |
| Retained -0, eliminated -3 | 956,904 | 875,176 | 8.54% | 23,812 → 21,508 |
| Retained +0, eliminated +1 | 823,320 | 741,592 | 9.93% | 19,972 → 17,668 |
| Retained -0, eliminated -1 | 837,992 | 755,928 | 9.79% | 20,484 → 18,180 |
| Nonzero-retained control | 966,584 | 965,272 | — | 24,196 → 24,196 |
| Inexact-beta control | 416,504 | 415,096 | — | 11,012 → 11,012 |

All four targets save **2,304 allocations per call**, or **18 per candidate**.
Allocated bytes decrease by **8.52–9.93%**. Both controls retain their allocation
counts. Cross-process byte differences on unchanged paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,296 → 45,520 |
| afiro | sparse | 4,987 → 4,987 | 218,216 → 218,072 |
| afiro | presolve | 16,330 → 16,330 | 733,240 → 732,408 |
| afiro | dual | 17,145 → 17,145 | 868,856 → 868,120 |
| afiro | primal | 17,051 → 17,051 | 847,176 → 846,584 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,936 |
| afiro | primal_no_presolve | 759 → 759 | 121,776 → 121,776 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 177,232 → 177,888 |
| adlittle | presolve | 82,776 → 82,776 | 3,347,064 → 3,346,792 |
| adlittle | dual | 84,791 → 84,791 | 4,135,752 → 4,136,168 |
| adlittle | primal | 85,589 → 85,589 | 4,412,936 → 4,412,776 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,704 → 461,560 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,744 → 607,264 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,336 → 112,624 |
| kb2 | sparse | 2,836 → 2,836 | 161,088 → 161,456 |
| kb2 | presolve | 230,004 → 230,004 | 10,678,792 → 10,679,448 |
| kb2 | dual | 231,206 → 231,206 | 11,130,616 → 11,130,632 |
| kb2 | primal | 231,373 → 231,373 | 11,146,520 → 11,145,160 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,112 → 877,952 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 300,016 → 299,808 |
| sc50a | presolve | 67,634 → 67,634 | 2,853,008 → 2,853,104 |
| sc50a | dual | 68,706 → 68,706 | 3,199,312 → 3,199,680 |
| sc50a | primal | 68,651 → 68,651 | 3,151,968 → 3,152,576 |
| sc50a | dual_no_presolve | 961 → 961 | 306,224 → 306,192 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 216,360 → 216,920 |
| flugpl | presolve | 31,461 → 31,461 | 1,199,544 → 1,199,416 |
| flugpl | dual | 32,132 → 32,132 | 1,309,568 → 1,309,536 |
| flugpl | primal | 32,481 → 32,481 | 1,354,064 → 1,354,016 |
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
[`doubleton-zero-retained-cost-allocations-before.toml`](doubleton-zero-retained-cost-allocations-before.toml)
and [`doubleton-zero-retained-cost-allocations-after.toml`](doubleton-zero-retained-cost-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-zero-retained-cost-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_zero_retained_cost_probe(kind; count=128, T=Float64)
    pivot = T(kind == :inexact_beta ? 3 : 2)
    cost = T(kind == :negative ? -3 : kind == :unit_positive ? 1 : kind == :unit_negative ? -1 : 3)
    retained_cost = kind in (:negative,:unit_negative) ? -zero(T) : T(kind == :nonzero_retained ? 3 : 0)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(cost,count),fill(retained_cost,count));objective_constant=tiny,
        row_lower=fill(T(4),count),row_upper=fill(T(4),count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end

for kind in (:positive,:negative,:unit_positive,:unit_negative,:nonzero_retained,:inexact_beta)
    problem, pass = doubleton_zero_retained_cost_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **1,840** assertions and failed only
the four target allocation guards: 23,857 > 23,000; 23,820 > 23,000;
19,980 > 19,000; and 20,492 > 19,500. Both control budgets passed. There are
**1,844 new assertions**; existing allocation budgets were not relaxed.

Accepted substitutions cover Float32, Float64, BigFloat, and Rational{BigInt};
positive/negative zero retained costs; positive/negative unit and nonunit beta;
zero, unit, and nonunit eliminated costs; matrix and row-bound results;
canonical output zeros; postsolve primal/basis; and source immutability.
BigFloat checks preserve objective representability gates and output precision
at ambient precision 32/64/256. Tiny nonzero retained costs retain exact arithmetic
and rejection behavior, while tiny updated costs are accepted exactly or reject
half-subnormal results.

All **37,660/37,660** targeted assertions passed in 1m28.1s (exit 0), including
the 1,844 new checks and the existing basic, doubleton, aggregation, and related
presolve allocation guards.

Independent read-only review found no blocking issues. An AST-renamed round-121
baseline comparison passed **166,360 additional assertions**, excluding the
focused tests: 5,524 models (4,132 accepted and 1,392 rejected), 22,096 basis
cases, 11,048 primal-dimension checks, and 11,048 basis-dimension checks. It
covered signed zeros, zero/unit/nonunit costs and ratios, exact BigFloat values
and precision, tiny and overflowing costs, objective/matrix/bound rejection,
later candidates, source immutability, and postsolve/basis results and errors.

For Rational{BigInt}, scalar storage sharing changes on some accepted paths:
a nonunit eliminated cost with beta=+1 can now share its numerator and denominator
with the updated objective; beta=-1 can share the denominator. The baseline
addition allocated both. This is consistent with the model's shallow scalar
ownership and existing zero-cost sharing. Explicit checks found no source
mutation during transformation, restoration, ordinary rational arithmetic,
output objective `.+=`, or output element assignment. Independent ownership of
mutable BigInt internals is not asserted.

The mandatory full package suite passed **62,545/62,545** assertions in
6m01.7s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
