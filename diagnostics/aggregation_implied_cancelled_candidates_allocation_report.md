# Cancelled candidates in implied-bound checks

Round 157 changes only the two final bound comparisons in
`_equality_implies_column_bounds` in `src/presolve_aggregation.jl`. When the
exact RHS equals the relevant activity extreme, the inferred bound is zero.
The lower-bound check compares the numerator of the exact stored bound with zero
using `<=`; the upper-bound check uses `>=`. Canonical rational denominators are
positive, so only the numerator determines the sign. This avoids constructing
a zero difference and dividing it by the nonzero pivot, and also avoids the
allocating rational-to-integer comparison.

Free bounds and unbounded activities are still handled before this shortcut.
The pivot sign still selects the correct activity extreme. All other cases
retain the previous subtraction and division paths. Stored bounds are still
converted exactly before comparison. Exact rational equality distinguishes tiny
residuals and preserves stored BigFloat precision. Projection, row-removal
decisions, representation gates, staged updates, rollback and postsolve are
unchanged. Inputs are not mutated.

## Method and results

The baseline includes the preceding 156 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent blocks `pivot*x+3*y=3` and
`6*x+5*y<=100`. The cost of x is zero, y's cost is two, and the objective constant
is seven. All 128 pivots are accepted. The second row's coefficient becomes
`5-18/pivot` and its upper bound becomes `100-18/pivot`. Measurement includes
the full sparse aggregation pass, with input construction outside measurement.

Positive/negative targets use pivots ±2, x in `[-1,1]`, and y fixed to one.
Both activity extremes equal the RHS, so the equality is removed. Each call
has 256 cancelled candidates. The lower-cancellation target uses pivot two,
x in `[0,1]` and y in `[0,1]`; the upper-cancellation target instead uses
x in `[-1,0]` and y in `[1,2]`. These each have 128 cancelled candidates and
retain the equality projected with coefficient three and row bounds `[1,3]`
or `[3,5]`, respectively.

The noncancellation control uses pivot two, x in `[-1,1]` and y in `[1/2,3/4]`;
neither activity equals the RHS, and the equality is removed. The free-pivot
control uses pivot two, free x and y fixed to one; the helper returns early and
the equality is removed. Both controls accept all pivots.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive | 1,692,168 | 1,528,056 | 9.70% | 44,983 → 40,887 |
| negative | 1,694,616 | 1,530,088 | 9.71% | 44,983 → 40,887 |
| lower_cancel | 1,919,056 | 1,837,104 | 4.27% | 50,245 → 48,197 |
| upper_cancel | 2,059,024 | 1,977,296 | 3.97% | 54,341 → 52,293 |
| noncancel | 1,827,432 | 1,827,752 | — | 49,335 → 49,335 |
| free_pivot | 1,195,064 | 1,195,448 | — | 29,623 → 29,623 |

Target allocated bytes decrease by **3.97–9.71%**.
Both controls retain allocation counts. Cross-process byte differences on
unchanged paths alone establish no benefit.

- `positive` saves **4,096 allocations per call**, or 16 per cancelled candidate.
- `negative` saves **4,096 allocations per call**, or 16 per cancelled candidate.
- `lower_cancel` saves **2,048 allocations per call**, or 16 per cancelled candidate.
- `upper_cancel` saves **2,048 allocations per call**, or 16 per cancelled candidate.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 41,088 → 40,992 |
| afiro | sparse | 4,171 → 4,167 | 186,184 → 186,552 |
| afiro | propagation | 2,437 → 2,437 | 91,880 → 92,552 |
| afiro | presolve | 15,657 → 15,653 | 706,344 → 706,264 |
| afiro | dual | 16,472 → 16,468 | 842,136 → 841,208 |
| afiro | primal | 16,378 → 16,374 | 819,512 → 819,864 |
| afiro | dual_no_presolve | 555 → 555 | 89,936 → 89,936 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,339 → 2,339 | 156,264 → 156,888 |
| adlittle | propagation | 18,182 → 18,182 | 641,000 → 641,416 |
| adlittle | presolve | 81,429 → 81,429 | 3,290,488 → 3,289,896 |
| adlittle | dual | 83,444 → 83,444 | 4,080,600 → 4,077,688 |
| adlittle | primal | 84,242 → 84,242 | 4,356,920 → 4,354,968 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,544 → 461,480 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,440 → 607,232 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,048 → 105,480 |
| kb2 | sparse | 2,284 → 2,259 | 138,088 → 137,416 |
| kb2 | propagation | 12,948 → 12,948 | 454,272 → 454,272 |
| kb2 | presolve | 227,965 → 227,915 | 10,594,808 → 10,589,464 |
| kb2 | dual | 229,167 → 229,117 | 11,044,584 → 11,044,760 |
| kb2 | primal | 229,334 → 229,284 | 11,059,224 → 11,059,160 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,032 → 878,144 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,880 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,180 → 6,174 | 282,360 → 282,464 |
| sc50a | propagation | 6,020 → 6,020 | 222,288 → 222,368 |
| sc50a | presolve | 66,361 → 66,302 | 2,805,440 → 2,801,160 |
| sc50a | dual | 67,433 → 67,374 | 3,150,560 → 3,146,840 |
| sc50a | primal | 67,378 → 67,319 | 3,103,152 → 3,099,864 |
| sc50a | dual_no_presolve | 961 → 961 | 306,112 → 306,144 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 4,699 → 4,697 | 174,712 → 175,040 |
| flugpl | propagation | 3,253 → 3,253 | 122,656 → 122,752 |
| flugpl | presolve | 28,138 → 28,138 | 1,067,136 → 1,067,120 |
| flugpl | dual | 28,809 → 28,809 | 1,176,184 → 1,176,808 |
| flugpl | primal | 29,158 → 29,158 | 1,220,920 → 1,221,416 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save four allocations on afiro,
50 on kb2 and 59 on sc50a. Standalone sparse aggregation saves four on afiro,
25 on kb2, six on sc50a and two on flugpl. The remaining 37 reference measurements
retain their allocation counts.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-cancelled-candidates-allocations-before.toml`](aggregation-implied-cancelled-candidates-allocations-before.toml)
and [`aggregation-implied-cancelled-candidates-allocations-after.toml`](aggregation-implied-cancelled-candidates-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-cancelled-candidates-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_cancelled_candidates_probe(kind; count=128, T=Float64)
    pivot=kind==:negative ? T(-2) : T(2)
    low=kind==:lower_cancel ? zero(T) : kind==:noncancel ? T(1)/2 : one(T)
    high=kind==:upper_cancel ? T(2) : kind==:noncancel ? T(3)/4 : one(T)
    xlo=kind==:free_pivot ? nothing : kind==:lower_cancel ? zero(T) : -one(T)
    xhi=kind==:free_pivot ? nothing : kind==:upper_cancel ? zero(T) : one(T)
    odd=collect(1:2:2count);even=odd.+1
    A=sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(pivot,count),fill(T(3),count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,[isodd(i) ? zero(T) : T(2) for i in 1:2count];objective_constant=T(7),
        row_lower=[isodd(i) ? T(3) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(3) : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? xlo : low for i in 1:2count],
        column_upper=[isodd(i) ? xhi : high for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:positive,:negative,:lower_cancel,:upper_cancel,:noncancel,:free_pivot)
    problem, pass = aggregation_implied_cancelled_candidates_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **3,154 assertions** and failed only
the four target allocation guards. Both controls passed. There are **3,158 new
assertions**; existing allocation budgets were not relaxed.

An independent endpoint oracle covers 1,200 helper models across Float32,
Float64, BigFloat and Rational{BigInt}, signed nonunit pivots, signed/zero RHS,
cancelled/noncancelled candidates and finite/free/one-sided bounds. The ±1000
witnesses suffice for these small bounded-size fixtures. BigFloat cases store
RHS or activity residuals of ±2^-200 at 256 bits and run at ambient 32/64/256,
with both signs of unit and nonunit pivots. Exact zero candidates are also
compared with tiny negative, zero and positive bounds for every numeric type.
Large rational cases distinguish cancellation from a residual of 2^-350 with
300-bit numerators and denominators 5, 7, 15 and 21.

Full aggregation checks cover matrix/bounds/objective, projected/removed rows,
primal/basis restoration, objective equivalence and source preservation after
ordinary output mutation.

The targeted presolve/allocation suite passed **121,116 / 121,116 assertions**
in **2m17.0s**, including every new allocation guard on the final revision.

Independent read-only review found no issues in the final numerator comparison.
AST-renamed baseline helper and sparse aggregation functions passed **4,718
assertions across 152 differential models**, including 412 helper comparisons
against baseline and an independent exact interval oracle, 456 primal and 608
basis restoration comparisons. There were 108 accepted and 44 rejected models,
with 76 removed and 32 projected equality rows. Coverage included eight
rejection/rollback cases, all four numeric types, signed unit/nonunit pivots,
cancellation versus residuals, tiny signed bounds, unbounded activities, large
non-dyadic rationals, stored-256 BigFloat at ambient 32/64/256 and source
preservation.

The full test suite passed **140,613 / 140,613 assertions** in **6m22.2s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
