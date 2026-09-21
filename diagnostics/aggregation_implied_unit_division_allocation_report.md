# Signed-unit division in implied-bound checks

Round 156 changes only the two final bound comparisons in
`_equality_implies_column_bounds` in `src/presolve_aggregation.jl`. For an exact
pivot of one, the inferred bound reuses the exact numerator; for minus one,
it negates the numerator. Other pivots retain general exact division.

The conditions are expressed as explicit branches so each numerator is
computed once. Free bounds still succeed before inspecting the activity;
unbounded activities still fail before arithmetic. Each bound uses its own
activity extreme selected by the pivot sign. The prior zero-activity subtraction
shortcut remains. Exact comparison excludes near-unit pivots, including stored
BigFloat values with greater precision than the ambient context. Projection,
row-removal decisions, representation gates, staged updates, rollback and
postsolve are unchanged. No inputs are mutated.

## Method and results

The baseline includes the preceding 155 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent blocks `pivot*x+3*y=4` and
`6*x+5*y<=100`. The cost of x is zero, y's cost is two, and the objective constant
is seven. All 128 pivots are accepted. The second row's coefficient becomes
`5-18/pivot` and its upper bound becomes `100-24/pivot`. Measurement includes
the full sparse aggregation pass, with input construction outside measurement.

The positive and negative targets use pivots ±1, respectively x in `[1,3]`
or `[-3,-1]`, and y in `[0,2]`. The equality remains projected with coefficient
three and row bounds `[1,3]`. Fixed targets instead fix y to zero and use x in
`[3,5]` or `[-5,-3]`; these remove the equality row and also exercise the existing
zero-activity subtraction path. Each target performs 256 signed-unit divisions.

The nonunit control uses pivot two, x in `[1,3]` and y in `[0,2]`; its equality
remains projected with bounds `[-2,2]`. The free-pivot control uses pivot one,
free x and y in `[0,2]`; the helper returns early and the equality is removed.
Both controls accept all pivots.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive | 2,008,928 | 1,921,328 | 4.36% | 53,061 → 50,757 |
| negative | 2,032,896 | 1,960,192 | 3.58% | 53,829 → 52,037 |
| fixed_positive | 1,501,544 | 1,414,440 | 5.80% | 39,479 → 37,175 |
| fixed_negative | 1,509,064 | 1,436,424 | 4.81% | 39,735 → 37,943 |
| nonunit | 2,077,024 | 2,076,656 | — | 54,853 → 54,853 |
| free_pivot | 1,172,168 | 1,173,400 | — | 28,983 → 28,983 |

Target allocated bytes decrease by **3.58–5.80%**.
Both controls retain allocation counts. Cross-process byte differences on
unchanged paths alone establish no benefit.

- `positive` saves **2,304 allocations per call**, or 9 per signed-unit division.
- `negative` saves **1,792 allocations per call**, or 7 per signed-unit division.
- `fixed_positive` saves **2,304 allocations per call**, or 9 per signed-unit division.
- `fixed_negative` saves **1,792 allocations per call**, or 7 per signed-unit division.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,976 → 41,072 |
| afiro | sparse | 4,202 → 4,171 | 188,240 → 186,360 |
| afiro | propagation | 2,437 → 2,437 | 92,552 → 92,232 |
| afiro | presolve | 15,681 → 15,657 | 706,968 → 706,472 |
| afiro | dual | 16,496 → 16,472 | 842,584 → 842,296 |
| afiro | primal | 16,402 → 16,378 | 820,952 → 820,408 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,339 → 2,339 | 156,760 → 157,240 |
| adlittle | propagation | 18,182 → 18,182 | 641,048 → 641,448 |
| adlittle | presolve | 81,465 → 81,429 | 3,290,712 → 3,288,856 |
| adlittle | dual | 83,480 → 83,444 | 4,079,336 → 4,077,256 |
| adlittle | primal | 84,278 → 84,242 | 4,356,680 → 4,354,360 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,384 → 461,704 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,648 → 607,488 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,176 → 105,608 |
| kb2 | sparse | 2,308 → 2,284 | 139,464 → 138,664 |
| kb2 | propagation | 12,948 → 12,948 | 453,968 → 454,032 |
| kb2 | presolve | 228,008 → 227,965 | 10,593,496 → 10,591,896 |
| kb2 | dual | 229,210 → 229,167 | 11,047,384 → 11,044,840 |
| kb2 | primal | 229,377 → 229,334 | 11,061,880 → 11,059,432 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,416 → 878,304 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,202 → 6,180 | 283,392 → 281,992 |
| sc50a | propagation | 6,020 → 6,020 | 221,920 → 221,536 |
| sc50a | presolve | 66,393 → 66,361 | 2,805,160 → 2,803,760 |
| sc50a | dual | 67,465 → 67,433 | 3,151,208 → 3,149,568 |
| sc50a | primal | 67,410 → 67,378 | 3,103,752 → 3,101,936 |
| sc50a | dual_no_presolve | 961 → 961 | 306,128 → 306,304 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 4,841 → 4,699 | 180,656 → 174,984 |
| flugpl | propagation | 3,253 → 3,253 | 122,960 → 123,024 |
| flugpl | presolve | 28,618 → 28,138 | 1,085,664 → 1,067,104 |
| flugpl | dual | 29,289 → 28,809 | 1,195,544 → 1,176,424 |
| flugpl | primal | 29,638 → 29,158 | 1,240,408 → 1,221,176 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save 24 allocations on afiro,
36 on adlittle, 43 on kb2, 32 on sc50a and 480 on flugpl. Standalone sparse
aggregation saves 31 on afiro, 24 on kb2, 22 on sc50a and 142 on flugpl. The
remaining 31 reference measurements retain their allocation counts.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-unit-division-allocations-before.toml`](aggregation-implied-unit-division-allocations-before.toml)
and [`aggregation-implied-unit-division-allocations-after.toml`](aggregation-implied-unit-division-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-unit-division-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_unit_division_probe(kind; count=128, T=Float64)
    pivot=kind in (:negative,:fixed_negative) ? -one(T) : kind==:nonunit ? T(2) : one(T)
    fixed=kind in (:fixed_positive,:fixed_negative)
    low=zero(T);high=fixed ? zero(T) : T(2)
    xlo=kind==:free_pivot ? nothing : pivot<0 ? (fixed ? T(-5) : T(-3)) : (fixed ? T(3) : one(T))
    xhi=kind==:free_pivot ? nothing : pivot<0 ? (fixed ? T(-3) : T(-1)) : (fixed ? T(5) : T(3))
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

for kind in (:positive,:negative,:fixed_positive,:fixed_negative,:nonunit,:free_pivot)
    problem, pass = aggregation_implied_unit_division_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,962 assertions** and failed only
the four target allocation guards. Both controls passed. There are **2,966 new
assertions**; existing allocation budgets were not relaxed.

An independent endpoint oracle covers 1,200 helper models across Float32,
Float64, BigFloat and Rational{BigInt}, signed unit pivots and signed/zero RHS,
zero endpoints, exact cancellation, one versus two zero extremes, nonzero
activities and finite/free/one-sided bounds. The ±1000 witnesses suffice for
these small bounded-size fixtures. BigFloat cases store RHS or activity
residuals of ±2^-200 at 256 bits and run at ambient 32/64/256, both with and
without cancelling terms. Separate cases distinguish ±1 from ±(1+2^-200) pivots
under all three ambient precisions. Large rational cases check RHS thresholds
using 300-bit numerators, denominators 5, 7, 15 and 21, and both pivot/RHS signs.

Full aggregation checks cover matrix/bounds/objective, projected/removed rows,
primal/basis restoration, objective equivalence and source preservation after
ordinary output mutation.

The targeted presolve/allocation suite passed **117,958 / 117,958 assertions**
in **2m15.3s**, including every new allocation guard.

Independent read-only review found no issues. AST-renamed baseline helper and
sparse aggregation functions passed **5,178 assertions across 152 differential
models**, including 540 helper comparisons against baseline and an independent
exact interval oracle, 456 primal and 608 basis restoration comparisons. There
were 120 accepted and 32 rejected models, with 58 removed and 78 projected rows
across 136 records. Coverage included eight late rejection/rollback cases, all
four numeric types, exact/near-unit pivots, stored-256 BigFloat inputs at ambient
32/64/256, rational thresholds, cancellation, unbounded activities and source
preservation.

The full test suite passed **137,455 / 137,455 assertions** in **6m23.2s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
