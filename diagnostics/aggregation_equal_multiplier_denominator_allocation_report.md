# Equal-denominator elimination multipliers in sparse equality aggregation

Round 143 changes only the matrix elimination multiplier in
`aggregate_sparse_equalities` in `src/presolve_aggregation.jl`. When the other
row's coefficient and the pivot share a denominator, the quotient is constructed
directly from their BigInt numerators with the canonical `Rational{BigInt}`
constructor. It reduces the fraction and normalizes a negative pivot's sign.
Unequal denominators retain general rational division. Earlier signed-unit-pivot
shortcuts retain their behavior. Stored zero coefficients still produce canonical
zero, including with negative pivots.

Bound projection, objective arithmetic, finite/unbounded bound shifts, matrix
updates, representability gates, candidate ordering, staged updates, rollback,
and primal/basis restoration are unchanged. No operands are mutated and no GMP
internals or noncanonical constructors are used.

## Method and results

The baseline includes the preceding 142 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each target contains 128 independent two-row, two-column blocks:
`pivot*x+y=4` and `coefficient*x+5*y<=100`. Variable x has bounds `[1,3]`, y is
free, objective costs are `[0,2]`, and the objective constant is seven. Integer
variants use pivot 2 or -2 and other-row coefficient six. Fractional variants
use pivot 1/2 or -1/2 and other-row coefficient 3/2. Each block therefore computes
one shared-denominator multiplier, three or minus three, saving four allocations.

All 128 pivots are accepted. The projected equality row is retained, the second
row's retained coefficient becomes two or eight, and its upper bound becomes
88 or 112. Measurement includes projection, staging, bound and matrix updates,
and successful sparse reconstruction as well as multiplier calculation.

The unequal-denominator control uses pivot two and other-row coefficient 3/2,
retaining general division to produce multiplier 3/4. The unit-pivot control
uses pivot one and other-row coefficient six, retaining direct reuse. Both
controls accept all pivots. Input construction is outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive integer pivot | 1,733,024 | 1,711,248 | 1.26% | 44,741 → 44,229 |
| Negative integer pivot | 1,734,608 | 1,713,056 | 1.24% | 44,741 → 44,229 |
| Positive fractional pivot | 1,762,128 | 1,740,080 | 1.25% | 45,253 → 44,741 |
| Negative fractional pivot | 1,761,936 | 1,740,240 | 1.23% | 45,253 → 44,741 |
| Unequal-denominator control | 1,748,384 | 1,747,248 | — | 44,997 → 44,997 |
| Unit-pivot control | 1,648,192 | 1,647,088 | — | 42,437 → 42,437 |

All four targets save **512 allocations per call** (four per eliminated column). Allocated bytes decrease
by **1.23–1.26%**. Both controls retain their allocation counts.
Cross-process byte differences on unchanged paths alone establish no benefit.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 44,960 → 45,152 |
| afiro | sparse | 4,891 → 4,891 | 214,720 → 213,808 |
| afiro | propagation | 2,437 → 2,437 | 92,360 → 92,504 |
| afiro | presolve | 16,217 → 16,217 | 727,640 → 727,080 |
| afiro | dual | 17,032 → 17,032 | 863,528 → 862,728 |
| afiro | primal | 16,938 → 16,938 | 841,752 → 840,632 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,760 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,747 → 2,747 | 174,744 → 173,560 |
| adlittle | propagation | 18,182 → 18,182 | 641,096 → 640,104 |
| adlittle | presolve | 82,433 → 82,433 | 3,327,688 → 3,327,224 |
| adlittle | dual | 84,448 → 84,448 | 4,116,760 → 4,115,496 |
| adlittle | primal | 85,246 → 85,246 | 4,393,464 → 4,391,928 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,656 → 461,320 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,152 → 607,440 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,000 → 112,208 |
| kb2 | sparse | 2,836 → 2,836 | 161,984 → 161,008 |
| kb2 | propagation | 12,948 → 12,948 | 453,920 → 453,456 |
| kb2 | presolve | 229,194 → 229,194 | 10,641,744 → 10,639,152 |
| kb2 | dual | 230,396 → 230,396 | 11,094,016 → 11,093,264 |
| kb2 | primal | 230,563 → 230,563 | 11,107,392 → 11,106,080 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,176 → 877,920 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,848 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 299,568 → 298,768 |
| sc50a | propagation | 6,020 → 6,020 | 222,272 → 221,440 |
| sc50a | presolve | 67,457 → 67,457 | 2,846,488 → 2,845,880 |
| sc50a | dual | 68,529 → 68,529 | 3,191,912 → 3,191,960 |
| sc50a | primal | 68,474 → 68,474 | 3,145,048 → 3,144,632 |
| sc50a | dual_no_presolve | 961 → 961 | 306,416 → 306,288 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 210,328 → 209,336 |
| flugpl | propagation | 3,253 → 3,253 | 123,392 → 121,952 |
| flugpl | presolve | 30,791 → 30,791 | 1,169,632 → 1,169,088 |
| flugpl | dual | 31,462 → 31,462 | 1,279,128 → 1,278,616 |
| flugpl | primal | 31,811 → 31,811 | 1,323,880 → 1,323,208 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All five reference fixtures retain their allocation counts in all ten stages,
including sparse aggregation and solves without presolve. These fixtures show
unchanged behavior and no allocation-count benefit from this particular
shortcut; measured savings are confined to the four targeted multiplier probes.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-equal-multiplier-denominator-allocations-before.toml`](aggregation-equal-multiplier-denominator-allocations-before.toml)
and [`aggregation-equal-multiplier-denominator-allocations-after.toml`](aggregation-equal-multiplier-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-equal-multiplier-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_equal_multiplier_denominator_probe(kind; count=128, T=Float64)
    name=string(kind)
    direction=endswith(name,"negative") ? -1 : 1
    fractional=startswith(name,"fraction")
    pivot=T(direction)*(fractional ? T(1)/2 : T(2))
    coefficient=fractional || kind==:unequal_denominator ? T(3)/2 : T(6)
    kind==:unit_pivot && (pivot=one(T))
    odd=collect(1:2:2count);even=odd.+1
    A=sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(pivot,count),ones(T,count),fill(coefficient,count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,[isodd(i) ? zero(T) : T(2) for i in 1:2count];objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? one(T) : nothing for i in 1:2count],
        column_upper=[isodd(i) ? T(3) : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:integer_positive,:integer_negative,:fraction_positive,:fraction_negative,:unequal_denominator,:unit_pivot)
    problem, pass = aggregation_equal_multiplier_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **786 assertions** and failed only
the four target allocation guards: 44,786 > 44,500; 44,749 > 44,500;
and two cases of 45,261 > 45,000. Both control budgets passed.
There are **790 new assertions**; existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}, signed
integer/fractional pivots, shared and unequal denominators, stored zero
coefficients with finite or unbounded row endpoints, canonical signs and
reduction, projected matrix/bounds/objective, primal and basis restoration,
objective equivalence, and source preservation.

BigFloat checks use stored 256-bit coefficients at ambient precision 32/64/256.
Integer inputs produce multiplier three or `3+2^-200`, accepting the residual
only at sufficient precision. Fractional inputs produce three or a non-dyadic
residual that rejects the matrix update at all tested binary precisions. Rejected
models give the retained column degree one to prevent unrelated alternate
pivots. Large rational cases use numerators derived from `2^300+1` and
denominators 5, 7, 15, and 21, with both pivot and coefficient signs.

The combined presolve/basic/doubleton/aggregation/propagation targeted suite
passed **79,666 assertions** in **1m56.6s**, exit code zero.

Independent read-only differential review found no issues and passed
**4,294 assertions across 150 models** (136 accepted, 14 rejected; 154
substitutions), exit code zero. It compared 450 primal restorations and 600
basis restorations, with eight protected late rollback cases and twelve rational
ownership checks. Only the baseline sparse-pass function was renamed; helpers
remained unchanged. Canonical zero, negative-pivot signs, exactness rejection,
source ownership, projected/shifted bounds, stored zeros, and repeated dictionary
updates matched the saved baseline.

The complete `test/runtests.jl` suite passed **99,163 assertions** in
**6m00.9s**, exit code zero.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
