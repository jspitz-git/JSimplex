# Equal denominators in implied-bound quotients

Round 159 changes only the two candidate quotient computations in
`_equality_implies_column_bounds` in `src/presolve_aggregation.jl`. If the exact
difference and pivot share a denominator, their quotient is constructed directly
from their numerators with `Rational{BigInt}`. The constructor reduces the result
and normalizes a negative pivot numerator. Unequal denominators retain general
rational division.

The existing exact ±1 pivot shortcuts still run first. All prior free-bound,
unbounded-activity, exact-cancellation and zero-activity guards remain, as does
the exact difference computation. Stored values retain their full precision,
including BigFloat inputs stored above the ambient precision. Projection,
row-removal decisions, representation gates, staged updates, rollback and
postsolve are unchanged. Inputs are not mutated.

## Method and results

The baseline includes the preceding 158 allocation rounds. Measurements used
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
The difference is two, sharing denominator one with the pivot. Fraction targets
use pivots ±1/2, x in `[-2,2]`, y fixed to one and RHS 7/2. The difference is 1/2,
sharing denominator two with the pivot. Every target executes 256 quotients
with shared denominators; inferred x is one or minus one.

The unequal-denominator control uses pivot 1/2, x in `[-2,2]`, y fixed to one
and RHS 13/4. The difference is 1/4, whose denominator differs from the pivot's.
The free-pivot control uses pivot two, free x, y fixed to one and RHS five;
the helper returns early. Both controls accept all pivots and remove the rows.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| integer_positive | 1,675,432 | 1,633,976 | 2.47% | 44,983 → 43,959 |
| integer_negative | 1,677,384 | 1,635,880 | 2.47% | 44,983 → 43,959 |
| fraction_positive | 1,725,192 | 1,683,656 | 2.41% | 46,007 → 44,983 |
| fraction_negative | 1,725,416 | 1,683,688 | 2.42% | 46,007 → 44,983 |
| unequal | 1,762,904 | 1,762,744 | — | 47,543 → 47,543 |
| free_pivot | 1,196,600 | 1,196,920 | — | 29,623 → 29,623 |

Target allocated bytes decrease by **2.41–2.47%**.
Both controls retain allocation counts. Cross-process byte differences on
unchanged paths alone establish no benefit.

- `integer_positive` saves **1,024 allocations per call**, or 4 per shared-denominator quotient.
- `integer_negative` saves **1,024 allocations per call**, or 4 per shared-denominator quotient.
- `fraction_positive` saves **1,024 allocations per call**, or 4 per shared-denominator quotient.
- `fraction_negative` saves **1,024 allocations per call**, or 4 per shared-denominator quotient.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 41,056 → 40,976 |
| afiro | sparse | 4,167 → 4,167 | 187,304 → 186,872 |
| afiro | propagation | 2,437 → 2,437 | 93,400 → 92,408 |
| afiro | presolve | 15,653 → 15,653 | 707,816 → 707,016 |
| afiro | dual | 16,468 → 16,468 | 842,248 → 842,424 |
| afiro | primal | 16,374 → 16,374 | 820,552 → 820,744 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,339 → 2,339 | 156,776 → 157,096 |
| adlittle | propagation | 18,182 → 18,182 | 641,928 → 642,056 |
| adlittle | presolve | 81,429 → 81,429 | 3,290,344 → 3,289,880 |
| adlittle | dual | 83,444 → 83,444 | 4,080,104 → 4,078,952 |
| adlittle | primal | 84,242 → 84,242 | 4,356,104 → 4,355,528 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,032 → 461,176 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,056 → 607,536 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,576 → 105,800 |
| kb2 | sparse | 2,259 → 2,259 | 137,480 → 137,688 |
| kb2 | propagation | 12,948 → 12,948 | 454,592 → 454,560 |
| kb2 | presolve | 227,909 → 227,909 | 10,591,456 → 10,590,912 |
| kb2 | dual | 229,111 → 229,111 | 11,044,096 → 11,045,712 |
| kb2 | primal | 229,278 → 229,278 | 11,057,568 → 11,058,592 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,224 → 878,000 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,864 → 260,848 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,174 → 6,174 | 282,880 → 282,208 |
| sc50a | propagation | 6,020 → 6,020 | 222,704 → 221,936 |
| sc50a | presolve | 66,302 → 66,302 | 2,803,128 → 2,802,344 |
| sc50a | dual | 67,374 → 67,374 | 3,149,048 → 3,147,048 |
| sc50a | primal | 67,319 → 67,319 | 3,102,104 → 3,099,624 |
| sc50a | dual_no_presolve | 961 → 961 | 306,176 → 306,320 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 4,677 → 4,677 | 174,496 → 173,616 |
| flugpl | propagation | 3,253 → 3,253 | 124,688 → 123,104 |
| flugpl | presolve | 28,078 → 28,078 | 1,064,464 → 1,064,512 |
| flugpl | dual | 28,749 → 28,749 | 1,174,024 → 1,174,088 |
| flugpl | primal | 29,098 → 29,098 | 1,218,376 → 1,218,664 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All 50 reference-stage measurements retain their allocation counts. This round
demonstrates a reduction on the targeted probes; it establishes no allocation
benefit on these five reference models. Cross-process byte differences alone
on those unchanged-count paths are not treated as a gain.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-equal-quotient-denominator-allocations-before.toml`](aggregation-implied-equal-quotient-denominator-allocations-before.toml)
and [`aggregation-implied-equal-quotient-denominator-allocations-after.toml`](aggregation-implied-equal-quotient-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-equal-quotient-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_equal_quotient_denominator_probe(kind; count=128, T=Float64)
    fractional=kind in (:fraction_positive,:fraction_negative,:unequal)
    magnitude=fractional ? T(1)/2 : T(2)
    pivot=kind in (:integer_negative,:fraction_negative) ? -magnitude : magnitude
    y=one(T)
    rhs=kind==:unequal ? T(13)/4 : fractional ? T(7)/2 : T(5)
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
    problem, pass = aggregation_implied_equal_quotient_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,824 assertions** and failed only
the four target allocation guards. Both controls passed. There are **2,828 new
assertions**; existing allocation budgets were not relaxed.

An independent endpoint oracle covers 1,200 helper models across Float32,
Float64, BigFloat and Rational{BigInt}, signed fractional pivots, integer/fraction
RHS, shared/different denominators, cancellation and finite/free/one-sided bounds.
The ±1000 witnesses suffice for these small bounded-size fixtures. BigFloat
cases store pivots ±(3+2^-200) at 256 bits and run at ambient 32/64/256. A matching
exact difference yields one, whereas an additional ±2^-200 RHS residual violates
the fixed bound. Large rational cases use signed 300-bit pivot numerators and
odd denominators 5, 7, 15 and 21; the quotient must reduce to positive two,
including when both numerator operands are negative.

Full aggregation checks cover matrix/bounds/objective, projected/removed rows,
primal/basis restoration, objective equivalence and source preservation after
ordinary output mutation.

The targeted presolve/allocation suite passed **126,934 / 126,934 assertions**
in **2m23.2s**, including every new allocation guard.

Independent read-only review found no issues. AST-renamed baseline helper and
sparse aggregation functions passed **5,197 assertions across 160 differential
models**, including 460 helper comparisons against baseline and an independent
exact interval oracle, 480 primal and 640 basis restoration comparisons. There
were 132 accepted and 28 rejected models, with 112 removed and 20 projected
rows. Coverage included eight late rejection/rollback cases, all four numeric
types, MIN/MAX senses, signed unit/nonunit pivots, matching/different denominators,
cancellation, free/unbounded cases, stored-256 BigFloat at ambient 32/64/256,
300-bit non-dyadic pivots, canonical rational reduction and source preservation.

The full test suite passed **146,431 / 146,431 assertions** in **6m22.7s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
