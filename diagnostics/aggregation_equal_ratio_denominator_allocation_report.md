# Equal-denominator objective ratios in equality aggregation

Round 142 changes the objective-price/pivot quotient in both
`aggregate_singleton_equalities` and `aggregate_sparse_equalities` in
`src/presolve_aggregation.jl`. When a nonzero price and nonunit pivot share a
denominator, their quotient is constructed directly from their BigInt numerators
with the canonical `Rational{BigInt}` constructor. It reduces the fraction and
normalizes negative pivot signs. Unequal denominators retain general rational
division. Earlier zero-price and signed-unit-pivot shortcuts retain their behavior.

Bound projection, implied-bound detection, objective updates and exactness gates,
singleton objective rounding and exact-candidate preference, staged updates,
rollback, and primal/basis restoration are unchanged. No operands are mutated
and no GMP internals or noncanonical constructors are used.

## Method and results

The baseline includes the preceding 141 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 60 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each target has 128 independent pivot columns and one shared retained column y.
The rows are `a*x_i+y=rhs`, with x_i bounded by `[1,3]`, y free, retained objective
cost two, and initial objective constant seven. Integer variants have pivot
`a=2` or `a=-2` and pivot-column price six. Fractional variants have `a=1/2` or
`a=-1/2` and price 3/2. The right-hand side is four times the pivot sign. All
eight targets therefore compute objective ratio three or minus three with a
shared denominator, saving four allocations per eliminated column.

Singleton targets use the 128 equality rows directly. Sparse targets add
`sum(x_i)+2*y<=1000`, giving every pivot column degree two while keeping fill
within budget. Both passes accept all 128 eliminations and retain projected
rows. Measurement includes successful reconstruction, projection, objective
updates, and sparse matrix/bound updates as well as ratio calculation.

Both controls use singleton aggregation. The unequal-denominator control uses
pivot two and price 3/2, retaining general division to produce ratio 3/4.
The unit-pivot control uses pivot one and price six, retaining direct reuse.
Both have right-hand side four and accept all eliminations. Input construction
is outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Singleton integer positive | 1,047,784 | 1,026,936 | 1.99% | 27,648 → 27,136 |
| Singleton integer negative | 1,049,416 | 1,027,640 | 2.08% | 27,648 → 27,136 |
| Singleton fractional positive | 1,076,712 | 1,055,000 | 2.02% | 28,160 → 27,648 |
| Singleton fractional negative | 1,076,408 | 1,054,536 | 2.03% | 28,160 → 27,648 |
| Sparse integer positive | 1,597,480 | 1,576,920 | 1.29% | 43,594 → 43,082 |
| Sparse integer negative | 1,599,600 | 1,578,720 | 1.31% | 43,607 → 43,095 |
| Sparse fractional positive | 1,618,360 | 1,597,992 | 1.26% | 43,953 → 43,441 |
| Sparse fractional negative | 1,618,504 | 1,598,328 | 1.25% | 43,964 → 43,452 |
| Unequal-denominator control | 1,048,920 | 1,049,144 | — | 27,552 → 27,552 |
| Unit-coefficient control | 963,816 | 963,592 | — | 25,344 → 25,344 |

All eight targets save **512 allocations per call** (four per eliminated column). Allocated bytes decrease
by **1.25–2.08%**. Both controls retain their allocation counts.
Cross-process byte differences on unchanged paths alone establish no benefit.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,088 → 44,496 |
| afiro | sparse | 4,891 → 4,891 | 213,376 → 213,456 |
| afiro | propagation | 2,437 → 2,437 | 91,848 → 91,752 |
| afiro | presolve | 16,217 → 16,217 | 727,688 → 726,776 |
| afiro | dual | 17,032 → 17,032 | 863,480 → 861,736 |
| afiro | primal | 16,938 → 16,938 | 841,688 → 841,272 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,751 → 2,747 | 173,928 → 173,272 |
| adlittle | propagation | 18,182 → 18,182 | 641,032 → 640,584 |
| adlittle | presolve | 82,433 → 82,433 | 3,326,600 → 3,326,584 |
| adlittle | dual | 84,448 → 84,448 | 4,116,104 → 4,115,576 |
| adlittle | primal | 85,246 → 85,246 | 4,393,240 → 4,391,960 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,432 → 461,656 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,728 → 607,744 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,096 → 111,824 |
| kb2 | sparse | 2,836 → 2,836 | 161,552 → 160,752 |
| kb2 | propagation | 12,948 → 12,948 | 454,352 → 453,024 |
| kb2 | presolve | 229,194 → 229,194 | 10,639,792 → 10,638,032 |
| kb2 | dual | 230,396 → 230,396 | 11,093,088 → 11,091,072 |
| kb2 | primal | 230,563 → 230,563 | 11,107,120 → 11,105,424 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,528 → 878,144 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 299,280 → 298,144 |
| sc50a | propagation | 6,020 → 6,020 | 222,000 → 220,720 |
| sc50a | presolve | 67,457 → 67,457 | 2,845,224 → 2,846,216 |
| sc50a | dual | 68,529 → 68,529 | 3,190,952 → 3,191,944 |
| sc50a | primal | 68,474 → 68,474 | 3,143,688 → 3,144,520 |
| sc50a | dual_no_presolve | 961 → 961 | 306,144 → 306,192 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 209,880 → 209,128 |
| flugpl | propagation | 3,253 → 3,253 | 123,008 → 121,552 |
| flugpl | presolve | 30,791 → 30,791 | 1,169,424 → 1,169,504 |
| flugpl | dual | 31,462 → 31,462 | 1,278,680 → 1,278,168 |
| flugpl | primal | 31,811 → 31,811 | 1,323,240 → 1,322,808 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Standalone sparse aggregation saves four allocations on adlittle. Every other
reference measurement retains its allocation count, including complete presolve,
both solves with presolve, and solves without presolve. The standalone pass and
complete presolve receive different model states and candidate opportunities.
The main measured benefit is in the eight targeted objective-ratio probes.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-equal-ratio-denominator-allocations-before.toml`](aggregation-equal-ratio-denominator-allocations-before.toml)
and [`aggregation-equal-ratio-denominator-allocations-after.toml`](aggregation-equal-ratio-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-equal-ratio-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_equal_ratio_denominator_probe(kind; count=128, T=Float64)
    name=string(kind)
    sparse_pass=startswith(name,"sparse")
    direction=endswith(name,"negative") ? -1 : 1
    fractional=occursin("fraction",name)
    coefficient=T(direction)*(fractional ? T(1)/2 : T(2))
    price=fractional || kind==:unequal_denominator ? T(3)/2 : T(6)
    kind==:unit_coefficient && (coefficient=one(T))
    rhs=T(4direction)
    A=hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(T,count,1)))
    lower=Union{Nothing,T}[rhs for _ in 1:count];upper=fill(rhs,count)
    if sparse_pass
        A=vcat(A,sparse(reshape([ones(T,count);T(2)],1,count+1)))
        push!(lower,nothing);push!(upper,T(1000))
    end
    problem=LinearProblem(A,[fill(price,count);T(2)];objective_constant=T(7),
        row_lower=lower,row_upper=upper,
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
end

for kind in (:singleton_integer_positive,:singleton_integer_negative,:singleton_fraction_positive,:singleton_fraction_negative,:sparse_integer_positive,:sparse_integer_negative,:sparse_fraction_positive,:sparse_fraction_negative,:unequal_denominator,:unit_coefficient)
    problem, pass = aggregation_equal_ratio_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **1,162 assertions** and failed only
the eight target allocation guards: 27,693 > 27,400; 27,656 > 27,400;
two cases of 28,168 > 27,900; 43,602 > 43,350; 43,615 > 43,360;
43,961 > 43,700; and 43,972 > 43,710. Both control budgets passed.
There are **1,170 new assertions**; existing allocation budgets were not relaxed.

Coverage includes both aggregation passes with Float32, Float64, BigFloat, and
Rational{BigInt}, signed integer/fractional pivots, shared and unequal denominators,
canonical signs and reduction, projected matrix/bounds/objective, primal and
basis restoration, objective equivalence, and source preservation. Explicit
Float32/64 checks accept permitted singleton objective rounding and reject the
same ratio in sparse aggregation. Rejected models prevent unrelated alternate
pivots using pass-appropriate column degrees.

BigFloat checks use stored 256-bit coefficients and prices at ambient precision
32/64/256. Integer inputs produce ratio three or `3+2^-200`, accepting the
residual only at sufficient precision; fractional inputs produce three or a
non-dyadic rational residual, which both passes reject at all tested binary
precisions. Large rational cases use numerators derived from `2^300+1` and
denominators 5, 7, 15, and 21, with both coefficient and price signs.

The combined presolve/basic/doubleton/aggregation/propagation targeted suite
passed **78,876 assertions** in **1m54.2s**, exit code zero.

Independent read-only differential review found no issues and passed
**3,844 assertions across 144 models** (110 accepted, 34 rejected), exit code
zero. Both aggregation passes were compared, with 432 primal restorations,
576 basis restorations, 16 rollback cases, eight objective-rounding/preference
cases, and eight rational ownership cases. Only the baseline pass functions
were AST-renamed; helpers remained unchanged. Guards, canonical signs and
reduction, exactness policy, singleton candidate preference, staging, source
ownership, and restoration matched the baseline. The canonical constructor
copies both BigInt inputs before reduction, including negative denominator
normalization.

The complete `test/runtests.jl` suite passed **98,373 assertions** in
**5m55.6s**, exit code zero.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
