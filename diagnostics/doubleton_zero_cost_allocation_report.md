# Skip zero-cost objective arithmetic in doubleton substitution

Round 118 changes only `substitute_free_doubleton` in `src/presolve_substitution.jl`.
When the eliminated variable has exactly zero objective cost, the two objective
updates now directly convert the retained cost and constant to exact rationals.
This skips conversion of the zero eliminated cost, both zero products, and both
additions of zero. Nonzero eliminated costs retain their existing shared exact
conversion, products, and sums.

Both `_represent_exact` calls remain after the branch. Thus unchanged stored
BigFloat costs/constants still undergo the same precision and representability
checks, and output zeros retain canonical signs. Alpha/beta computation and
gates, matrix/bound updates, staging and rejection, model construction, and
primal/basis restoration are unchanged. No source value is mutated and no
approximate zero test is introduced.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 117 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each Float64 target has 128 equalities `2*x_i+y_i=rhs` and 128 affected rows
`a*x_i+y_i`, free `x_i`, and retained `y_i` bounded by `[-10,10]`. Retained costs
are three and the objective constant is seven. The first three targets use
eliminated costs +0/-0/+0 with rhs=4/-4/0, respectively.
Their affected rows are unbounded and use `a=tiny`, the smallest positive
Float64 subnormal. Every candidate passes objective checks but rejects the
nonrepresentable matrix update `1-tiny/2` after creating private working copies.

The bound-rejection target uses eliminated cost zero, rhs=`2*tiny`, `a=1/2`,
and affected-row bounds `[0,Inf]`. Its matrix update is representable, but the
half-subnormal bound shift rejects every candidate. These probes measure all
128 rejected candidates, including their private copies, rather than a
successful reduction.

The nonzero-cost control uses eliminated cost two, rhs four, and the same
matrix rejection. The inexact-ratio control uses pivot three and rhs four,
rejecting before objective arithmetic or working copies. Model construction
occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Zero cost, positive rhs | 3,647,160 | 3,446,216 | 5.51% | 32,516 → 27,268 |
| Negative-zero cost, negative rhs | 3,649,608 | 3,446,840 | 5.56% | 32,516 → 27,268 |
| Zero cost and rhs | 3,586,936 | 3,384,424 | 5.65% | 30,596 → 25,348 |
| Zero cost, bound rejection | 3,792,536 | 3,590,008 | 5.34% | 35,588 → 30,340 |
| Nonzero-cost control | 3,668,408 | 3,667,608 | — | 33,412 → 33,412 |
| Inexact-ratio control | 419,544 | 418,616 | — | 11,012 → 11,012 |

All four targets save 5,248 allocations per call, or 41 for each of the 128
candidates reaching objective updates. Allocated bytes drop by 5.34–5.65%,
including the unchanged private-copy work performed before matrix/bound rejection.
Both controls retain their allocation counts; byte differences
on unchanged paths alone establish no benefit.

The following table gives all nine measured stages for each reference fixture.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,728 → 45,456 |
| afiro | sparse | 4,987 → 4,987 | 218,392 → 217,896 |
| afiro | presolve | 16,330 → 16,330 | 732,776 → 732,168 |
| afiro | dual | 17,145 → 17,145 | 868,808 → 867,352 |
| afiro | primal | 17,051 → 17,051 | 846,888 → 846,232 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 177,568 → 177,856 |
| adlittle | presolve | 82,776 → 82,776 | 3,347,448 → 3,347,800 |
| adlittle | dual | 84,791 → 84,791 | 4,136,136 → 4,136,456 |
| adlittle | primal | 85,589 → 85,589 | 4,413,032 → 4,412,648 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,480 → 461,240 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,360 → 607,376 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,464 → 112,352 |
| kb2 | sparse | 2,836 → 2,836 | 161,456 → 161,600 |
| kb2 | presolve | 230,004 → 230,004 | 10,679,128 → 10,679,864 |
| kb2 | dual | 231,206 → 231,206 | 11,132,216 → 11,131,768 |
| kb2 | primal | 231,373 → 231,373 | 11,146,232 → 11,145,592 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,968 → 878,176 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,848 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 300,240 → 300,272 |
| sc50a | presolve | 67,634 → 67,634 | 2,853,024 → 2,853,376 |
| sc50a | dual | 68,706 → 68,706 | 3,199,056 → 3,199,008 |
| sc50a | primal | 68,651 → 68,651 | 3,151,760 → 3,152,096 |
| sc50a | dual_no_presolve | 961 → 961 | 306,112 → 306,288 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 217,080 → 217,640 |
| flugpl | presolve | 31,461 → 31,461 | 1,199,896 → 1,198,840 |
| flugpl | dual | 32,132 → 32,132 | 1,309,168 → 1,309,504 |
| flugpl | primal | 32,481 → 32,481 | 1,353,440 → 1,354,064 |
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
[`doubleton-zero-cost-allocations-before.toml`](doubleton-zero-cost-allocations-before.toml)
and [`doubleton-zero-cost-allocations-after.toml`](doubleton-zero-cost-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-zero-cost-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_zero_cost_probe(kind; count=128, T=Float64)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    pivot = T(kind == :inexact_ratio ? 3 : 2)
    cost = kind == :negative_zero ? -zero(T) : T(kind == :nonzero_cost ? 2 : 0)
    rhs = kind == :bound_rejection ? 2tiny : T(kind == :zero_rhs ? 0 : kind == :negative_zero ? -4 : 4)
    affected = kind == :bound_rejection ? T(1)/T(2) : tiny
    rows = vcat(collect(1:count),collect(count+1:2count),collect(1:count),collect(count+1:2count))
    columns = vcat(collect(1:count),collect(1:count),collect(count+1:2count),collect(count+1:2count))
    A = sparse(rows,columns,vcat(fill(pivot,count),fill(affected,count),ones(T,2count)),2count,2count)
    problem = LinearProblem(A,vcat(fill(cost,count),fill(T(3),count));objective_constant=T(7),
        row_lower=vcat(fill(T(rhs),count),fill(kind == :bound_rejection ? zero(T) : nothing,count)),
        row_upper=vcat(fill(T(rhs),count),fill(nothing,count)),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end
for kind in (:positive,:negative_zero,:zero_rhs,:bound_rejection,:nonzero_cost,:inexact_ratio)
    problem, pass = doubleton_zero_cost_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 682 assertions and failed only the
four target allocation guards: 32,561 > 29,000; 32,524 > 29,000;
30,604 > 27,000; and 35,596 > 32,000. Both controls passed. All 686 new
assertions now pass as part of 32,062 targeted assertions covering basic
elimination, doubleton substitution, and related guards. Existing allocation
budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; accepted
substitutions with eliminated cost ±0; positive/negative pivots and rhs, zero
rhs, matrix/bound rejection, retained matrices/bounds, objective costs/constants,
primal/basis restoration, and source immutability. Output zeros keep their
canonical positive sign. Stored-256-bit BigFloat retained costs/constants still
reject insufficient ambient precision 32/64; accepted outputs retain the prior
ambient output precision. Tiny nonzero eliminated costs produce nonzero exact
contributions, and half-subnormal objective updates still reject substitution.
Rejected candidates can switch from zero to nonzero costs or back without
leaking staged objective changes. Earlier ratio and row-bound gates remain
in the targeted suite.

Independent read-only review found no issues. An AST-renamed baseline comparison
passed **9,084 additional assertions** across 346 models (242 accepted and 104
rejected), 1,384 basis cases, and 692 malformed-primal-length cases, excluding
the 686 focused assertions. It checked exact BigFloat values, output precision
and zero signs, sparse storage, bounds, postsolve maps, primal/basis results and
errors, tiny nonzero costs, rejection staging, rational aliases, and input
immutability.

The mandatory full package suite passed **56,947/56,947** assertions in
5m43.6s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
