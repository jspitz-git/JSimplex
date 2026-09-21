# Reuse doubleton contributions for zero objective constants

Round 123 changes only the objective-constant update in the nonzero eliminated-cost
branch of `substitute_free_doubleton` in `src/presolve_substitution.jl`.
After the existing zero-alpha case, an exactly zero stored objective constant
now selects `constant_shift` directly, skipping conversion of zero to a rational
and addition of zero. Nonzero constants keep their exact conversion and addition.
The zero-alpha and zero eliminated-cost branches are unchanged.

Both `_represent_exact` gates remain. They still reject nonrepresentable costs
or constants and preserve BigFloat output precision and canonical zero signs.
Ratio computation, retained-cost arithmetic, matrix/bound staging, model
construction, and primal/basis restoration are unchanged. No approximate zero
test or source mutation is introduced.

## Method and results

The baseline includes the preceding 122 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 target has 128 equalities `2*x_i+y_i=4`, free `x_i`, and `y_i`
bounded by `[-10,10]`. Retained costs are the smallest positive Float64 subnormal.
The four targets use eliminated costs +3/-3/+1/-1 and objective constants
+0/-0/+0/-0, respectively. All candidates have exactly representable alpha=2
and beta=-1/2, but reject the retained-cost update `tiny-cost/2`. Constant
arithmetic runs before this rejection, so every probe visits the optimized
branch 128 times and returns the unchanged problem. No matrix working copies
are made in these probes.

The nonzero-constant control uses constant seven and eliminated cost three,
rejecting the same retained-cost update. The zero-alpha control uses rhs zero,
constant -0, and cost three, taking the unchanged zero-alpha constant branch
before the same cost rejection. Model construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Constant +0, cost +3 | 952,328 | 871,512 | 8.49% | 23,812 → 21,508 |
| Constant -0, cost -3 | 953,656 | 872,632 | 8.50% | 23,812 → 21,508 |
| Constant +0, cost +1 | 819,880 | 739,400 | 9.82% | 19,972 → 17,668 |
| Constant -0, cost -1 | 834,200 | 753,480 | 9.68% | 20,484 → 18,180 |
| Nonzero-constant control | 963,080 | 963,096 | — | 24,196 → 24,196 |
| Zero-alpha control | 794,056 | 793,800 | — | 19,204 → 19,204 |

All four targets save **2,304 allocations per call**, or **18 per candidate**.
Allocated bytes decrease by **8.49–9.82%**. Both controls retain their allocation
counts. Cross-process byte differences on unchanged paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,504 → 45,408 |
| afiro | sparse | 4,987 → 4,987 | 218,488 → 218,232 |
| afiro | presolve | 16,330 → 16,330 | 733,736 → 732,840 |
| afiro | dual | 17,145 → 17,145 | 869,112 → 868,840 |
| afiro | primal | 17,051 → 17,051 | 847,112 → 847,080 |
| afiro | dual_no_presolve | 555 → 555 | 89,936 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 178,160 → 177,584 |
| adlittle | presolve | 82,776 → 82,776 | 3,348,408 → 3,347,752 |
| adlittle | dual | 84,791 → 84,791 | 4,136,952 → 4,136,024 |
| adlittle | primal | 85,589 → 85,589 | 4,413,864 → 4,412,456 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,096 → 461,464 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,408 → 607,408 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,192 → 112,624 |
| kb2 | sparse | 2,836 → 2,836 | 161,840 → 161,104 |
| kb2 | presolve | 230,004 → 230,004 | 10,679,336 → 10,680,184 |
| kb2 | dual | 231,206 → 231,206 | 11,131,240 → 11,132,472 |
| kb2 | primal | 231,373 → 231,373 | 11,144,200 → 11,146,632 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,304 → 878,000 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,848 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 300,528 → 300,656 |
| sc50a | presolve | 67,634 → 67,634 | 2,854,080 → 2,852,800 |
| sc50a | dual | 68,706 → 68,706 | 3,200,160 → 3,198,720 |
| sc50a | primal | 68,651 → 68,651 | 3,153,120 → 3,151,360 |
| sc50a | dual_no_presolve | 961 → 961 | 306,112 → 306,320 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 217,560 → 217,240 |
| flugpl | presolve | 31,461 → 31,461 | 1,200,728 → 1,198,888 |
| flugpl | dual | 32,132 → 32,132 | 1,310,112 → 1,309,104 |
| flugpl | primal | 32,481 → 32,481 | 1,354,576 → 1,353,520 |
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
[`doubleton-zero-constant-allocations-before.toml`](doubleton-zero-constant-allocations-before.toml)
and [`doubleton-zero-constant-allocations-after.toml`](doubleton-zero-constant-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-zero-constant-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_zero_constant_probe(kind; count=128, T=Float64)
    cost = T(kind == :negative ? -3 : kind == :unit_positive ? 1 : kind == :unit_negative ? -1 : 3)
    constant = kind in (:negative,:unit_negative,:zero_alpha) ? -zero(T) : T(kind == :nonzero_constant ? 7 : 0)
    rhs = T(kind == :zero_alpha ? 0 : 4)
    tiny = T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),collect(count+1:2count)),vcat(fill(T(2),count),ones(T,count)),count,2count)
    problem = LinearProblem(A,vcat(fill(cost,count),fill(tiny,count));objective_constant=constant,
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end

for kind in (:positive,:negative,:unit_positive,:unit_negative,:nonzero_constant,:zero_alpha)
    problem, pass = doubleton_zero_constant_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,200** assertions and failed only
the four target allocation guards: 23,857 > 23,000; 23,820 > 23,000;
19,980 > 19,000; and 20,492 > 19,500. Both control budgets passed. There are
**2,204 new assertions**; existing allocation budgets were not relaxed.

Accepted substitutions cover Float32, Float64, BigFloat, and Rational{BigInt};
positive/negative zero constants; zero, signed-unit, and nonunit alpha;
zero, unit, and nonunit eliminated costs; matrix and row-bound results;
canonical output zeros; postsolve primal/basis; and source immutability.
BigFloat checks isolate cost and constant representability gates at ambient
precision 32/64/256 and verify output precision. Tiny nonzero constants retain
exact arithmetic and rejection behavior, while tiny constant contributions
are accepted exactly or reject half-subnormal results.

All **39,864/39,864** targeted assertions passed in 1m28.0s (exit 0), including
the 2,204 new checks and the existing basic, doubleton, aggregation, and related
presolve allocation guards.

Independent read-only review found no correctness issues. An AST-renamed
round-122 baseline comparison passed **4,306 additional assertions** across
140 deliberately selected differential models (108 accepted and 32 rejected),
excluding the focused tests. This included 560 basis cases, 280 primal-dimension
checks, and 280 basis-dimension checks. Coverage included signs, unit/nonunit
arithmetic, stored-256-bit BigFloat data at ambient precision 32/64/256, both
objective gates, canonical zeros, tiny constants, half-subnormal shifts,
overflow, matrix/bound rejection, later candidates, restoration, and source
immutability.

Rational{BigInt} scalar storage sharing changes on some accepted paths. The
new constant can share numerator and denominator with an input eliminated cost
or equality rhs when positive-unit shortcuts reuse those values; negative-unit
paths can share the denominator. The baseline zero addition allocated separate
internals. This is consistent with the existing shallow scalar ownership of
LinearProblem. Ordinary arithmetic, array assignment, and broadcasting preserved
source values. Independent ownership of mutable BigInt internals is not asserted.

The mandatory full package suite passed **64,749/64,749** assertions in
5m51.2s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
