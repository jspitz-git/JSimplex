# Equal-denominator bound projection in equality aggregation

Round 141 changes only the final difference in `_project_equality_bound` in
`src/presolve_aggregation.jl`. The helper projects an eliminated column bound
onto the retained expression of an equality. When a nonzero right-hand side and
nonzero coefficient-bound product share a denominator, their BigInt numerators
are subtracted directly and the canonical `Rational{BigInt}` constructor reduces
the result. Unequal denominators retain general rational subtraction.

The helper is shared by singleton and sparse equality aggregation. Earlier
unbounded/zero-bound, zero-rhs, cancellation, and signed-unit product shortcuts
retain their behavior. The exact representability gate remains after the
difference. Candidate selection, implied-bound detection, fixed-bound projection
reuse, objective rounding policy, staged updates, rollback, and primal/basis
restoration are unchanged. No operands are mutated and no GMP internals are used.

## Method and results

The baseline includes the preceding 140 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 60 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each target has 128 independent pivot columns and one shared retained column y.
The rows are `a*x_i+y=rhs`, with x_i bounded by `[1,3]`, y free, objective costs
one for each x_i and two for y, and initial objective constant seven. Integer
variants use `(a,rhs)=(2,5)` or `(-2,-5)`; fractional variants use `(1/2,5/2)` or
`(-1/2,-5/2)`. Every eliminated column requires two nonzero, noncancelling
shared-denominator projections. Each integer projection saves two allocations;
each fractional projection saves one, including fraction reduction.

Singleton targets use the 128 equality rows directly. Sparse targets add
`sum(x_i)+2*y<=1000`, giving every pivot column degree two while keeping fill
within budget. Both passes accept all 128 eliminations and retain the projected
rows. Positive integer rows project to `-1<=y<=3`, negative integer rows to
`-3<=y<=1`; fractional rows project to `[1,2]` or `[-2,-1]`. Measurement includes
successful reconstruction and objective updates as well as projection.

Both controls use singleton aggregation. The unequal-denominator control has
`a=1/2` and `rhs=9/4`, projecting to `[3/4,7/4]` through the fallback. The zero-rhs
control uses `a=2`, projecting to `[-6,-2]` through the earlier negation shortcut.
Input construction is outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Singleton integer positive | 1,074,080 | 1,046,688 | 2.55% | 28,029 → 27,517 |
| Singleton integer negative | 1,075,208 | 1,047,880 | 2.54% | 28,032 → 27,520 |
| Singleton fractional positive | 1,072,480 | 1,050,096 | 2.09% | 27,901 → 27,645 |
| Singleton fractional negative | 1,073,144 | 1,049,864 | 2.17% | 27,904 → 27,648 |
| Sparse integer positive | 1,637,728 | 1,610,576 | 1.66% | 44,285 → 43,773 |
| Sparse integer negative | 1,639,920 | 1,612,912 | 1.65% | 44,311 → 43,799 |
| Sparse fractional positive | 1,615,424 | 1,592,944 | 1.39% | 43,713 → 43,457 |
| Sparse fractional negative | 1,616,192 | 1,593,520 | 1.40% | 43,735 → 43,479 |
| Unequal-denominator control | 1,073,200 | 1,072,512 | — | 27,837 → 27,837 |
| Zero-rhs control | 991,232 | 990,512 | — | 25,661 → 25,661 |

The integer targets save **512 allocations per call** (four per eliminated column); the
fractional targets save **256** (two per eliminated column). Allocated bytes decrease
by **1.39–2.55%**. Both controls retain their allocation counts.
Cross-process byte differences on unchanged paths alone establish no benefit.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 44,800 → 44,704 |
| afiro | sparse | 4,891 → 4,891 | 214,800 → 214,208 |
| afiro | propagation | 2,437 → 2,437 | 92,152 → 91,768 |
| afiro | presolve | 16,217 → 16,217 | 727,992 → 727,960 |
| afiro | dual | 17,032 → 17,032 | 864,232 → 863,864 |
| afiro | primal | 16,938 → 16,938 | 842,264 → 841,608 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,751 → 2,751 | 173,896 → 173,656 |
| adlittle | propagation | 18,182 → 18,182 | 641,800 → 641,064 |
| adlittle | presolve | 82,433 → 82,433 | 3,326,744 → 3,326,904 |
| adlittle | dual | 84,448 → 84,448 | 4,117,480 → 4,115,928 |
| adlittle | primal | 85,246 → 85,246 | 4,395,080 → 4,392,024 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,400 → 461,272 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,776 → 607,376 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,160 → 112,096 |
| kb2 | sparse | 2,836 → 2,836 | 161,376 → 161,040 |
| kb2 | propagation | 12,948 → 12,948 | 454,784 → 454,112 |
| kb2 | presolve | 229,194 → 229,194 | 10,639,872 → 10,639,664 |
| kb2 | dual | 230,396 → 230,396 | 11,093,200 → 11,092,896 |
| kb2 | primal | 230,563 → 230,563 | 11,106,048 → 11,106,400 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,336 → 878,656 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 299,216 → 299,312 |
| sc50a | propagation | 6,020 → 6,020 | 221,904 → 222,000 |
| sc50a | presolve | 67,457 → 67,457 | 2,846,792 → 2,846,424 |
| sc50a | dual | 68,529 → 68,529 | 3,192,264 → 3,191,480 |
| sc50a | primal | 68,474 → 68,474 | 3,145,192 → 3,144,168 |
| sc50a | dual_no_presolve | 961 → 961 | 306,320 → 306,144 |
| sc50a | primal_no_presolve | 964 → 964 | 232,248 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 209,496 → 209,512 |
| flugpl | propagation | 3,253 → 3,253 | 121,952 → 122,160 |
| flugpl | presolve | 30,791 → 30,791 | 1,169,808 → 1,170,160 |
| flugpl | dual | 31,462 → 31,462 | 1,278,920 → 1,278,664 |
| flugpl | primal | 31,811 → 31,811 | 1,323,736 → 1,322,952 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,728 |

All five reference fixtures retain their allocation counts in all ten stages,
including both aggregation passes and solves without presolve. These fixtures
show unchanged behavior and no allocation-count benefit from this particular
shortcut; measured savings are confined to the eight targeted projection probes.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-equal-projection-denominator-allocations-before.toml`](aggregation-equal-projection-denominator-allocations-before.toml)
and [`aggregation-equal-projection-denominator-allocations-after.toml`](aggregation-equal-projection-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-equal-projection-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_equal_projection_denominator_probe(kind; count=128, T=Float64)
    name=string(kind)
    sparse_pass=startswith(name,"sparse")
    direction=endswith(name,"negative") ? -1 : 1
    fractional=occursin("fraction",name) || kind==:unequal_denominator
    coefficient=T(direction)*(fractional ? T(1)/2 : T(2))
    rhs=T(direction)*(fractional ? T(5)/2 : T(5))
    kind==:unequal_denominator && (rhs=T(9)/4)
    kind==:zero_rhs && (rhs=zero(T))
    A=hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(T,count,1)))
    lower=Union{Nothing,T}[rhs for _ in 1:count];upper=fill(rhs,count)
    if sparse_pass
        A=vcat(A,sparse(reshape([ones(T,count);T(2)],1,count+1)))
        push!(lower,nothing);push!(upper,T(1000))
    end
    problem=LinearProblem(A,[ones(T,count);T(2)];objective_constant=T(7),
        row_lower=lower,row_upper=upper,
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
end

for kind in (:singleton_integer_positive,:singleton_integer_negative,:singleton_fraction_positive,:singleton_fraction_negative,:sparse_integer_positive,:sparse_integer_negative,:sparse_fraction_positive,:sparse_fraction_negative,:unequal_denominator,:zero_rhs)
    problem, pass = aggregation_equal_projection_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **1,095 assertions** and failed only
the eight target allocation guards: 28,074 > 27,800; 28,040 > 27,800;
27,909 > 27,800; 27,912 > 27,800; 44,293 > 44,050; 44,319 > 44,070;
43,721 > 43,600; and 43,743 > 43,610. Both control budgets passed.
There are **1,103 new assertions**; existing allocation budgets were not relaxed.

Coverage includes both aggregation passes with Float32, Float64, BigFloat, and
Rational{BigInt}, signed integer/fractional coefficients, canonical reduction,
equal and unequal denominators, zero and unbounded endpoints, cancellation,
projection exactness, projected matrix/bounds/objective, primal and basis
restoration, objective equivalence, and source preservation. BigFloat integration
checks preserve stored 256-bit operands under ambient precision 32/64/256:
representable differences are accepted, while nonrepresentable differences reject
the candidate without mutation. Sparse rejected cases give the retained column
degree one, preventing an unrelated alternative pivot; singleton cases give it
degree two. Large rational helper checks use numerators derived from `2^300+1`
and denominators 5, 7, 15, and 21, including further reduction and cancellation.

The combined presolve/basic/doubleton/aggregation/propagation targeted suite
passed **77,706 assertions** in **1m53.4s**, exit code zero.

Independent read-only differential review found no issues and passed
**3,500 assertions across 128 models** (104 accepted, 24 rejected), exit code
zero. Both aggregation passes were compared, with 384 primal restorations,
512 basis restorations, 24 late rejection/rollback cases, eight singleton-versus-
sparse objective-rounding cases, and eight large-rational canonicalization and
ownership cases. The helper and both baseline passes were AST-renamed so the old
passes used the old projection arithmetic; no structs were redefined. Earlier
guards, representability gates, projected results, restoration, input ownership,
and pass-specific objective-rounding behavior matched the baseline.

The complete `test/runtests.jl` suite passed **97,203 assertions** in
**6m05.2s**, exit code zero.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
