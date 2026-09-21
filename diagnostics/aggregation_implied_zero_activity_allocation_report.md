# Zero activities in implied-bound differences

Round 155 changes only the two final bound comparisons in
`_equality_implies_column_bounds` in `src/presolve_aggregation.jl`. When the
relevant exact activity is zero, the numerator reuses the exact RHS instead of
subtracting zero. Nonzero activities retain general subtraction. Division by
the signed pivot and comparison with the exact bound remain unchanged.

The existing free-bound and unbounded-activity guards still run first. Each
bound uses its own activity extreme, selected by the pivot sign. Zero from
cancellation receives the same shortcut as zero endpoints. Stored RHS precision
is preserved, and tiny nonzero activities are not treated as zero. Projection,
row-removal decisions, representation gates, staged updates, rollback and
postsolve are unchanged. Inputs are not mutated.

## Method and results

The baseline includes the preceding 154 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent blocks `pivot*x+3*y=4` and
`6*x+5*y<=100`. The cost of x is zero, y's cost is two, and the objective constant
is seven. All 128 pivots are accepted. The second row's retained coefficient
becomes `5-18/pivot` and its upper bound becomes `100-24/pivot`. Measurement
includes the full sparse aggregation pass, with input construction outside.

The positive-pivot target uses pivot two and x in `[1,3]`; the negative-pivot
target uses pivot minus two and x in `[-3,-1]`. Both fix y to zero and remove
the equality row. Both activity extremes are zero, giving 256 zero subtractions.
The lower-zero target uses pivot two, x in `[1,3]` and y in `[0,2]`; the
upper-zero target instead uses y in `[-2,0]`. These keep the equality projected
with coefficient three and bounds `[-2,2]`, and give 128 zero subtractions each.

The nonzero control uses pivot two, x in `[1,3]` and y in `[1/2,1]`. Neither
activity is zero, and the equality remains projected. The free-pivot control
uses pivot two, free x and y fixed to zero; the helper returns early and the
equality is removed. Both controls accept every pivot.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive_pivot | 1,610,920 | 1,523,912 | 5.40% | 42,423 → 40,119 |
| negative_pivot | 1,612,760 | 1,525,672 | 5.40% | 42,423 → 40,119 |
| lower_zero | 2,121,888 | 2,078,400 | 2.05% | 56,005 → 54,853 |
| upper_zero | 2,121,888 | 2,078,112 | 2.06% | 56,005 → 54,853 |
| nonzero | 2,205,168 | 2,205,008 | — | 59,077 → 59,077 |
| free_pivot | 1,196,872 | 1,196,616 | — | 29,623 → 29,623 |

Target allocated bytes decrease by **2.05–5.40%**.
Both controls retain allocation counts. Cross-process byte differences on
unchanged paths alone establish no benefit.

- `positive_pivot` saves **2,304 allocations per call**, or 9 per zero subtraction.
- `negative_pivot` saves **2,304 allocations per call**, or 9 per zero subtraction.
- `lower_zero` saves **1,152 allocations per call**, or 9 per zero subtraction.
- `upper_zero` saves **1,152 allocations per call**, or 9 per zero subtraction.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,512 → 41,632 |
| afiro | sparse | 4,243 → 4,202 | 190,816 → 188,496 |
| afiro | propagation | 2,437 → 2,437 | 92,488 → 92,776 |
| afiro | presolve | 15,713 → 15,681 | 709,912 → 708,392 |
| afiro | dual | 16,528 → 16,496 | 844,984 → 843,816 |
| afiro | primal | 16,434 → 16,402 | 823,528 → 822,104 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,936 |
| afiro | primal_no_presolve | 759 → 759 | 121,776 → 121,776 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,339 → 2,339 | 156,488 → 157,592 |
| adlittle | propagation | 18,182 → 18,182 | 642,456 → 642,488 |
| adlittle | presolve | 81,483 → 81,465 | 3,292,376 → 3,291,272 |
| adlittle | dual | 83,498 → 83,480 | 4,082,184 → 4,081,032 |
| adlittle | primal | 84,296 → 84,278 | 4,359,048 → 4,358,632 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,768 → 461,320 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,504 → 607,424 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,080 → 106,008 |
| kb2 | sparse | 2,364 → 2,308 | 141,864 → 140,232 |
| kb2 | propagation | 12,948 → 12,948 | 454,848 → 455,360 |
| kb2 | presolve | 228,104 → 228,008 | 10,600,344 → 10,595,096 |
| kb2 | dual | 229,306 → 229,210 | 11,052,072 → 11,049,032 |
| kb2 | primal | 229,473 → 229,377 | 11,066,680 → 11,062,392 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,016 → 878,240 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,848 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,234 → 6,202 | 285,392 → 284,112 |
| sc50a | propagation | 6,020 → 6,020 | 222,928 → 222,624 |
| sc50a | presolve | 66,497 → 66,393 | 2,811,016 → 2,806,248 |
| sc50a | dual | 67,569 → 67,465 | 3,155,848 → 3,151,768 |
| sc50a | primal | 67,514 → 67,410 | 3,108,808 → 3,104,760 |
| sc50a | dual_no_presolve | 961 → 961 | 306,128 → 306,256 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 4,849 → 4,841 | 182,512 → 181,360 |
| flugpl | propagation | 3,253 → 3,253 | 124,432 → 123,392 |
| flugpl | presolve | 28,618 → 28,618 | 1,087,552 → 1,086,496 |
| flugpl | dual | 29,289 → 29,289 | 1,196,200 → 1,196,472 |
| flugpl | primal | 29,638 → 29,638 | 1,241,128 → 1,241,096 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save 32 allocations on afiro,
18 on adlittle, 96 on kb2 and 104 on sc50a. Standalone sparse aggregation
saves 41 on afiro, 56 on kb2, 32 on sc50a and eight on flugpl. The other
34 reference measurements retain their allocation counts.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-zero-activity-allocations-before.toml`](aggregation-implied-zero-activity-allocations-before.toml)
and [`aggregation-implied-zero-activity-allocations-after.toml`](aggregation-implied-zero-activity-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-zero-activity-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_zero_activity_probe(kind; count=128, T=Float64)
    pivot=kind==:negative_pivot ? T(-2) : T(2)
    low=kind==:upper_zero ? T(-2) : kind==:nonzero ? T(1)/2 : zero(T)
    high=kind==:lower_zero ? T(2) : kind==:nonzero ? one(T) : zero(T)
    xlo=kind==:free_pivot ? nothing : pivot<0 ? T(-3) : one(T)
    xhi=kind==:free_pivot ? nothing : pivot<0 ? T(-1) : T(3)
    odd=collect(1:2:2count);even=odd.+1
    A=sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(pivot,count),fill(T(3),count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,[isodd(i) ? zero(T) : T(2) for i in 1:2count];objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? xlo : low for i in 1:2count],
        column_upper=[isodd(i) ? xhi : high for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:positive_pivot,:negative_pivot,:lower_zero,:upper_zero,:nonzero,:free_pivot)
    problem, pass = aggregation_implied_zero_activity_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,914 assertions** and failed only
the four target allocation guards. Both controls passed. There are **2,918 new
assertions**; existing allocation budgets were not relaxed.

An independent endpoint oracle covers 1,200 helper models across Float32,
Float64, BigFloat and Rational{BigInt}, signed pivots and RHS values, zero
endpoints, exact cancellation, one versus two zero extremes, nonzero controls,
and finite/free/one-sided bounds. The ±1000 witnesses suffice for these small
bounded-size fixtures. BigFloat cases store RHS or activity residuals of
±2^-200 at 256 bits and run at ambient 32/64/256, both with and without cancelling
terms. Large rational cases check RHS thresholds using 300-bit numerators,
denominators 5, 7, 15 and 21, and both pivot and RHS signs.

Full aggregation checks cover matrix/bounds/objective, projected/removed rows,
primal/basis restoration, objective equivalence and source preservation after
ordinary output mutation.

The targeted presolve/allocation suite passed **114,992 / 114,992 assertions**
in **2m15.3s**, including every new allocation guard.

Independent read-only review found no issues. AST-renamed baseline helper and
sparse aggregation functions passed **5,231 assertions across 152 differential
models**, including 540 helper comparisons against baseline and an independent
exact interval oracle, 456 primal and 608 basis restoration comparisons. There
were 140 accepted models and 12 rejected models, with 88 removed and 68 projected
rows across 156 records. Coverage included eight late rejection/rollback cases,
all four numeric types, stored-256 BigFloat at ambient 32/64/256, cancellation,
one/both zero extremes, tiny residuals, non-dyadic rational thresholds, unbounded
ordering and source preservation.

The full test suite passed **134,489 / 134,489 assertions** in **6m31.9s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
