# Skip zero-alpha constant arithmetic in doubleton substitution

Round 119 changes only the objective-constant update in the nonzero eliminated-cost
branch of `substitute_free_doubleton` in `src/presolve_substitution.jl`.
When `alpha_exact` is zero, the update converts the existing constant directly
to an exact rational, skipping multiplication by zero and addition of zero.
The nonzero-alpha calculation and the previous zero-cost shortcut are unchanged.

Both objective `_represent_exact` gates remain. An unchanged BigFloat constant
can still reject substitution under insufficient ambient precision, and accepted
outputs retain the previous output precision and canonical positive zero sign.
Ratio computation, retained-cost updates, matrix/bound staging, model construction,
and primal/basis restoration are unchanged. No approximate zero test or mutation
of source values is introduced.

## Method and results

The baseline includes the preceding 118 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 target has 128 equalities `pivot*x_i+y_i=0`, free `x_i`, and
`y_i` bounded by `[-10,10]`. Eliminated costs are three, retained costs are the
smallest positive Float64 subnormal, and the objective constant is seven.
The four target pivots are 2, -2, 1/2, and 1; the negative-pivot target stores
rhs -0. All candidates have exactly representable alpha/beta, but reject the
nonrepresentable retained-cost update `tiny+3*beta`. Constant arithmetic is
performed before this rejection, so each probe measures 128 visits to the
optimized branch and returns the unchanged problem. No matrix working copies
are made in these probes.

The nonzero-rhs control uses pivot 2 and rhs 4, rejecting the same objective
update. The inexact-beta control uses pivot 3 and rhs zero, rejecting before
objective arithmetic. Model construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Zero rhs, pivot 2 | 893,800 | 813,016 | 9.04% | 22,020 → 19,972 |
| Negative-zero rhs, pivot -2 | 895,272 | 814,136 | 9.06% | 22,020 → 19,972 |
| Zero rhs, pivot 1/2 | 897,816 | 816,568 | 9.05% | 22,020 → 19,972 |
| Zero rhs, pivot 1 | 807,352 | 726,488 | 10.02% | 19,332 → 17,284 |
| Nonzero-rhs control | 962,312 | 963,336 | — | 24,196 → 24,196 |
| Inexact-beta control | 351,880 | 353,256 | — | 9,092 → 9,092 |

All four targets save **2,048 allocations per call**, or **16 per candidate**.
Allocated bytes decrease by **9.04–10.02%**. Both controls retain their
allocation counts. Cross-process byte differences on unchanged paths alone
establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,504 → 44,880 |
| afiro | sparse | 4,987 → 4,987 | 217,704 → 218,616 |
| afiro | presolve | 16,330 → 16,330 | 732,712 → 733,720 |
| afiro | dual | 17,145 → 17,145 | 868,312 → 868,872 |
| afiro | primal | 17,051 → 17,051 | 846,760 → 847,144 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,952 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,776 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 177,408 → 177,920 |
| adlittle | presolve | 82,776 → 82,776 | 3,347,880 → 3,347,384 |
| adlittle | dual | 84,791 → 84,791 | 4,137,272 → 4,137,000 |
| adlittle | primal | 85,589 → 85,589 | 4,413,864 → 4,413,752 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,224 → 461,400 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,424 → 607,520 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,464 → 112,272 |
| kb2 | sparse | 2,836 → 2,836 | 161,168 → 161,712 |
| kb2 | presolve | 230,004 → 230,004 | 10,679,656 → 10,679,656 |
| kb2 | dual | 231,206 → 231,206 | 11,132,632 → 11,133,544 |
| kb2 | primal | 231,373 → 231,373 | 11,145,848 → 11,147,496 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,952 → 878,416 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 299,888 → 300,944 |
| sc50a | presolve | 67,634 → 67,634 | 2,854,400 → 2,853,088 |
| sc50a | dual | 68,706 → 68,706 | 3,199,392 → 3,199,472 |
| sc50a | primal | 68,651 → 68,651 | 3,152,272 → 3,152,256 |
| sc50a | dual_no_presolve | 961 → 961 | 306,368 → 306,512 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 216,968 → 217,256 |
| flugpl | presolve | 31,461 → 31,461 | 1,199,432 → 1,200,648 |
| flugpl | dual | 32,132 → 32,132 | 1,309,680 → 1,309,360 |
| flugpl | primal | 32,481 → 32,481 | 1,354,080 → 1,353,776 |
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
[`doubleton-zero-constant-shift-allocations-before.toml`](doubleton-zero-constant-shift-allocations-before.toml)
and [`doubleton-zero-constant-shift-allocations-after.toml`](doubleton-zero-constant-shift-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-zero-constant-shift-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_zero_constant_shift_probe(kind; count=128, T=Float64)
    pivot = kind == :negative ? T(-2) : kind == :fractional ? T(1)/T(2) : T(kind == :unit_pivot ? 1 : kind == :inexact_beta ? 3 : 2)
    rhs = kind == :negative ? -zero(T) : T(kind == :nonzero_rhs ? 4 : 0)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(pivot,count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(T(3),count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end

for kind in (:positive,:negative,:fractional,:unit_pivot,:nonzero_rhs,:inexact_beta)
    problem, pass = doubleton_zero_constant_shift_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **1,186** assertions and failed only
the four target allocation guards: 22,065 > 21,000; 22,028 > 21,000 (twice);
and 19,340 > 18,300. Both control budgets passed. There are **1,190 new assertions**;
existing allocation budgets were not relaxed.

Accepted substitutions cover Float32, Float64, BigFloat, and Rational{BigInt};
positive/negative unit and nonunit pivots, positive/negative nonzero costs,
signed-zero rhs/constants, matrix and row-bound results, postsolve primal/basis,
and source immutability. BigFloat checks retain cost/constant representability
gates at ambient precision 32/64/256 and check accepted output precision. Tiny
nonzero alpha values still produce exact nonzero constant contributions or
reject half-subnormal constants, rather than taking the zero shortcut.

All **33,252/33,252** targeted assertions passed in 1m25.6s (exit 0), including
the 1,190 new checks and the existing basic, doubleton, aggregation, and related
presolve allocation guards.

Independent read-only review found no issues. An AST-renamed round-118 baseline
comparison passed **24,385 additional assertions**, excluding the focused tests:
928 models (673 accepted and 255 rejected), 3,712 basis comparisons, and 1,856
primal-dimension checks (1,601 expected errors and 255 unchanged oversized-input
identity passthroughs). It compared model/source/postsolve/basis snapshots,
including exact BigFloat values and precision, signed zeros, rational aliases,
zero/nonzero/tiny alpha and costs, matrix rejection, and selection of later
candidates after objective-gate rejection. Zero shifts still preserve existing
row-bound values and precision, while constants retain their representability
gate and ambient output precision.

The mandatory full package suite passed **58,137/58,137** assertions in
5m51.3s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
