# Reuse exact zero for nonunit doubleton alpha ratios

Round 117 changes only `substitute_free_doubleton` in `src/presolve_substitution.jl`.
For nonunit pivots and an exactly zero rhs, alpha now reuses the already computed
exact zero instead of dividing it by the exact pivot. Nonzero rhs values retain
the existing exact division. Both signed-unit pivot branches are unchanged.

Pivot conversion and beta division remain, even for zero rhs. Both ratio
representability checks, both objective representability checks, row updates,
rejection and staging, model construction, and primal/basis restoration remain.
No source value is mutated and no tolerance or rounded zero test is introduced.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 116 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each Float64 target has 128 independent equalities `pivot*x_i+y_i=0`, free `x_i`,
and retained `y_i` bounded by `[-10,10]`. Eliminated costs are three, retained
costs are the smallest positive Float64 subnormal, and the objective constant
is seven. Targets use pivots 2, -2, 1/2, and 3; the negative-pivot target stores
rhs=-0. Pivots 2/-2/1/2 pass both ratio checks but reject at the retained-cost
gate. Pivot 3 rejects at the beta gate. These probes measure candidate
evaluation rather than a successful model reduction.

The nonzero-rhs control uses pivot two and rhs four. The unit-pivot control uses
pivot one and rhs zero. Both controls reject at the retained-cost gate and retain
their preexisting ratio arithmetic. Model construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive pivot | 933,336 | 895,128 | 4.09% | 22,916 → 22,020 |
| Negative pivot and rhs -0 | 935,032 | 896,632 | 4.11% | 22,916 → 22,020 |
| Fractional pivot | 937,528 | 899,576 | 4.05% | 22,916 → 22,020 |
| Nonrepresentable beta | 391,400 | 352,856 | 9.85% | 9,988 → 9,092 |
| Nonzero-rhs control | 963,320 | 963,912 | — | 24,196 → 24,196 |
| Unit-pivot control | 808,120 | 808,984 | — | 19,332 → 19,332 |

All four targets save 896 allocations per call, or seven for each of the 128
candidates reaching the zero-alpha computation. Allocated bytes drop by
4.05–9.85%, with the largest percentage reduction at early beta rejection. Both controls retain their allocation counts; byte differences
on unchanged paths alone establish no benefit.

The following table gives all nine measured stages for each reference fixture.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,504 → 45,664 |
| afiro | sparse | 4,987 → 4,987 | 218,552 → 218,152 |
| afiro | presolve | 16,330 → 16,330 | 732,792 → 733,720 |
| afiro | dual | 17,145 → 17,145 | 868,392 → 868,808 |
| afiro | primal | 17,051 → 17,051 | 846,616 → 847,704 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 177,744 → 178,080 |
| adlittle | presolve | 82,776 → 82,776 | 3,347,656 → 3,346,680 |
| adlittle | dual | 84,791 → 84,791 | 4,136,088 → 4,135,336 |
| adlittle | primal | 85,589 → 85,589 | 4,412,824 → 4,412,152 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,320 → 461,448 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,280 → 607,408 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,704 → 112,816 |
| kb2 | sparse | 2,836 → 2,836 | 161,520 → 161,632 |
| kb2 | presolve | 230,004 → 230,004 | 10,679,272 → 10,679,192 |
| kb2 | dual | 231,206 → 231,206 | 11,131,832 → 11,130,968 |
| kb2 | primal | 231,373 → 231,373 | 11,145,368 → 11,145,976 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,224 → 878,128 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 300,176 → 300,208 |
| sc50a | presolve | 67,634 → 67,634 | 2,852,528 → 2,852,752 |
| sc50a | dual | 68,706 → 68,706 | 3,198,928 → 3,199,344 |
| sc50a | primal | 68,651 → 68,651 | 3,151,712 → 3,151,632 |
| sc50a | dual_no_presolve | 961 → 961 | 306,144 → 306,288 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,184 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 216,552 → 216,744 |
| flugpl | presolve | 31,461 → 31,461 | 1,199,464 → 1,199,448 |
| flugpl | dual | 32,132 → 32,132 | 1,309,184 → 1,309,552 |
| flugpl | primal | 32,481 → 32,481 | 1,353,728 → 1,354,208 |
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
[`doubleton-zero-alpha-allocations-before.toml`](doubleton-zero-alpha-allocations-before.toml)
and [`doubleton-zero-alpha-allocations-after.toml`](doubleton-zero-alpha-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-zero-alpha-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_zero_alpha_probe(kind; count=128, T=Float64)
    pivot = kind == :negative ? T(-2) : kind == :fractional ? T(1)/T(2) : T(kind == :inexact_beta ? 3 : kind == :unit_pivot ? 1 : 2)
    rhs = kind == :negative ? -zero(T) : T(kind == :nonzero_rhs ? 4 : 0)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(T(3),count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end
for kind in (:positive,:negative,:fractional,:inexact_beta,:nonzero_rhs,:unit_pivot)
    problem, pass = doubleton_zero_alpha_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 818 assertions and failed only the
four target allocation guards: 22,961 > 22,500; 22,924 > 22,500 (two cases);
and 9,996 > 9,500. Both controls passed. All 822 new assertions now pass as
part of 31,376 targeted assertions covering basic elimination, doubleton
substitution, and related guards. Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; accepted
zero-rhs substitutions with positive, negative, and fractional pivots; signed
zero; rejected candidate batches; retained matrices, row-bound identity,
objective costs/constants, primal/basis restoration, and source immutability.
Tiny nonzero rhs values still produce exact nonzero alpha; half-subnormal alpha
still rejects elimination. Stored-256-bit BigFloat inputs under ambient precision
32/64/256 retain beta and objective cost/constant representability gates, even
when alpha is zero. Earlier nonzero-rhs, unit-pivot, rejection-staging, and
row-bound checks remain in the targeted suite.

Independent read-only review found no issues. It passed 5,272 additional
assertions, separate from the focused 822, against an AST-renamed copy of
the preceding doubleton implementation: 194 models (126 accepted and 68
rejected), 776 basis cases, and 388 malformed-primal comparisons. Coverage
included signed zero, tiny nonzero/underflow rhs, stored-256-bit BigFloat inputs
under ambient precision 32/64/256, beta/objective/constant gates, unit/nonunit/
non-dyadic pivots, rational alias immutability, staged rejection, later candidates,
and primal/basis restoration. Outputs matched the saved baseline.

The mandatory full package suite passed **56,261/56,261** assertions in
5m31.8s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
