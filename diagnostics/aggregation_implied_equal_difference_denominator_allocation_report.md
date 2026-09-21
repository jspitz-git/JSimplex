# Equal denominators in implied-bound differences

Round 158 changes only the two difference computations in
`_equality_implies_column_bounds` in `src/presolve_aggregation.jl`. When the exact
RHS and activity share a denominator, their numerators are subtracted directly
and the result is constructed with `Rational{BigInt}` to retain canonical
reduction. Different denominators still use general rational subtraction.

The prior free-bound, unbounded-activity, exact-cancellation and zero-activity
guards retain their order and behavior. Signed-unit division and general
pivot division remain unchanged. Stored values are converted exactly, including
BigFloat inputs stored with higher precision than the ambient context.
Projection, row-removal decisions, representation gates, staged updates,
rollback and postsolve are unchanged. Inputs are not mutated.

## Method and results

The baseline includes the preceding 157 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent blocks `pivot*x+3*y=rhs` and
`6*x+5*y<=100`. The cost of x is zero, y's cost is two, and the objective constant
is seven. All 128 pivots are accepted and all equality rows are removed. The
second row's coefficient becomes `5-18/pivot` and its upper bound becomes
`100-6*rhs/pivot`. Measurement includes the full sparse aggregation pass, with
input construction outside measurement.

Integer targets use pivots ±2, x in `[-2,2]`, y fixed to one and RHS five.
Both activity extremes are three, so the RHS and activities share denominator
one. Fraction targets use pivots ±2, x in `[-2,2]`, y fixed to one half and RHS
5/2. Both activity extremes are 3/2; subtracting numerators reduces 2/2 to one.
Every target exercises 256 shared-denominator differences.

The unequal-denominator control uses pivot two, x in `[-2,2]`, y fixed to one
half and RHS 1/4; the activity is 3/2 and uses general subtraction. The free-pivot
control uses pivot two, free x, y fixed to one and RHS five; the helper returns
early. Both controls accept all pivots and remove the equality rows.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| integer_positive | 1,702,104 | 1,675,064 | 1.59% | 45,495 → 44,983 |
| integer_negative | 1,704,584 | 1,677,064 | 1.61% | 45,495 → 44,983 |
| fraction_positive | 1,824,504 | 1,800,632 | 1.31% | 49,079 → 48,823 |
| fraction_negative | 1,824,440 | 1,800,584 | 1.31% | 49,079 → 48,823 |
| unequal | 1,824,344 | 1,823,800 | — | 49,079 → 49,079 |
| free_pivot | 1,195,704 | 1,196,280 | — | 29,623 → 29,623 |

Target allocated bytes decrease by **1.31–1.61%**.
Both controls retain allocation counts. Cross-process byte differences on
unchanged paths alone establish no benefit.

- `integer_positive` saves **512 allocations per call**, or 2 per shared-denominator difference.
- `integer_negative` saves **512 allocations per call**, or 2 per shared-denominator difference.
- `fraction_positive` saves **256 allocations per call**, or 1 per shared-denominator difference.
- `fraction_negative` saves **256 allocations per call**, or 1 per shared-denominator difference.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,256 → 40,896 |
| afiro | sparse | 4,167 → 4,167 | 187,432 → 186,904 |
| afiro | propagation | 2,437 → 2,437 | 92,568 → 92,616 |
| afiro | presolve | 15,653 → 15,653 | 707,752 → 705,864 |
| afiro | dual | 16,468 → 16,468 | 842,616 → 841,592 |
| afiro | primal | 16,374 → 16,374 | 820,552 → 819,864 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,339 → 2,339 | 155,896 → 156,664 |
| adlittle | propagation | 18,182 → 18,182 | 642,744 → 641,512 |
| adlittle | presolve | 81,429 → 81,429 | 3,291,848 → 3,288,600 |
| adlittle | dual | 83,444 → 83,444 | 4,083,352 → 4,077,720 |
| adlittle | primal | 84,242 → 84,242 | 4,360,328 → 4,355,080 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,000 → 461,416 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 606,944 → 607,488 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 104,616 → 105,080 |
| kb2 | sparse | 2,259 → 2,259 | 136,504 → 137,000 |
| kb2 | propagation | 12,948 → 12,948 | 456,400 → 453,936 |
| kb2 | presolve | 227,915 → 227,909 | 10,594,072 → 10,590,400 |
| kb2 | dual | 229,117 → 229,111 | 11,046,296 → 11,043,680 |
| kb2 | primal | 229,284 → 229,278 | 11,061,384 → 11,058,256 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,080 → 878,160 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,174 → 6,174 | 283,680 → 282,288 |
| sc50a | propagation | 6,020 → 6,020 | 223,792 → 222,224 |
| sc50a | presolve | 66,302 → 66,302 | 2,804,024 → 2,800,840 |
| sc50a | dual | 67,374 → 67,374 | 3,149,656 → 3,146,728 |
| sc50a | primal | 67,319 → 67,319 | 3,102,616 → 3,099,512 |
| sc50a | dual_no_presolve | 961 → 961 | 306,144 → 306,320 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 4,697 → 4,677 | 176,208 → 173,920 |
| flugpl | propagation | 3,253 → 3,253 | 123,968 → 123,248 |
| flugpl | presolve | 28,138 → 28,078 | 1,069,344 → 1,063,984 |
| flugpl | dual | 28,809 → 28,749 | 1,178,792 → 1,172,760 |
| flugpl | primal | 29,158 → 29,098 | 1,223,448 → 1,217,800 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save six allocations on kb2 and
60 on flugpl. Standalone sparse aggregation saves 20 on flugpl. The remaining
43 reference measurements retain their allocation counts.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-equal-difference-denominator-allocations-before.toml`](aggregation-implied-equal-difference-denominator-allocations-before.toml)
and [`aggregation-implied-equal-difference-denominator-allocations-after.toml`](aggregation-implied-equal-difference-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-equal-difference-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_equal_difference_denominator_probe(kind; count=128, T=Float64)
    pivot=kind in (:integer_negative,:fraction_negative) ? T(-2) : T(2)
    fractional=kind in (:fraction_positive,:fraction_negative,:unequal)
    y=fractional ? T(1)/2 : one(T)
    rhs=kind==:unequal ? T(1)/4 : fractional ? T(5)/2 : T(5)
    xlo=kind==:free_pivot ? nothing : T(-2)
    xhi=kind==:free_pivot ? nothing : T(2)
    odd=collect(1:2:2count);even=odd.+1
    A=sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(pivot,count),fill(T(3),count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,[isodd(i) ? zero(T) : T(2) for i in 1:2count];objective_constant=T(7),
        row_lower=[isodd(i) ? rhs : nothing for i in 1:2count],
        row_upper=[isodd(i) ? rhs : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? xlo : y for i in 1:2count],
        column_upper=[isodd(i) ? xhi : y for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:integer_positive,:integer_negative,:fraction_positive,:fraction_negative,:unequal,:free_pivot)
    problem, pass = aggregation_implied_equal_difference_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,986 assertions** and failed only
the four target allocation guards. Both controls passed. There are **2,990 new
assertions**; existing allocation budgets were not relaxed.

An independent endpoint oracle covers 1,200 helper models across Float32,
Float64, BigFloat and Rational{BigInt}, signed pivots, integer/fraction RHS,
shared/different denominators, cancellation and finite/free/one-sided bounds.
The ±1000 witnesses suffice for these small bounded-size fixtures. BigFloat
cases store matching low bits in RHS and activity at 256 bits and run at ambient
32/64/256; exact cancellation of those bits yields the expected bound, while
an additional ±2^-200 residual invalidates it. Large rational cases use 300-bit
numerators congruent to one modulo denominators 5, 7, 15 and 21; subtraction
must reduce the result to the signed integer two before pivot division.

Full aggregation checks cover matrix/bounds/objective, projected/removed rows,
primal/basis restoration, objective equivalence and source preservation after
ordinary output mutation.

The targeted presolve/allocation suite passed **124,106 / 124,106 assertions**
in **2m20.3s**, including every new allocation guard.

Independent read-only review found no issues. AST-renamed baseline helper and
sparse aggregation functions passed **4,821 assertions across 152 differential
models**, including 412 helper comparisons against baseline and an independent
exact interval oracle, 456 primal and 608 basis restoration comparisons. There
were 116 accepted and 36 rejected models, with 80 removed and 36 projected rows.
Coverage included eight rollback cases, all four numeric types, shared/different
denominators, signed unit/nonunit pivots, canonical reduction, near cancellation,
stored-256 BigFloat at ambient 32/64/256, large non-dyadic rationals, free/unbounded
controls and source preservation.

The full test suite passed **143,603 / 143,603 assertions** in **6m25.4s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
