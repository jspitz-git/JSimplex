# Shared candidates in implied-bound checks

Round 163 changes only final candidate handling in
`_equality_implies_column_bounds` in `src/presolve_aggregation.jl`. A candidate
computed by the ordinary lower-bound branch is recorded only when the upper
bound is finite and both selected exact activity values are identical (`===`).
The zero-activity, positive-unit-pivot case skips caching: its candidate is
already the RHS, and caching would materialize an extra rational object.
The upper-bound branch can reuse this candidate after its existing free-bound,
unbounded-activity and exact-cancellation guards.

Both stored bounds are still converted exactly and compared independently.
A skipped lower computation records nothing; distinct activity values and a
free upper bound retain their previous paths without an unused cached value.
The exact difference and division formulas are unchanged. Stored BigFloat
precision, projection, row-removal decisions, representation gates, staged
updates, rollback and postsolve are preserved. Shared exact values are never mutated.

## Method and results

The baseline includes the preceding 162 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent blocks `pivot*x+3*y=4` and
`6*x+5*y<=100`. The cost of x is zero, y's cost is two, and the objective constant
is seven. All 128 pivots are accepted and all equality rows are removed. The
second row's coefficient becomes `5-18/pivot` and its upper bound becomes
`100-24/pivot`. Measurement includes the full sparse aggregation pass, with
input construction outside measurement.

Targets use pivots 2, -2, 1 or -1, x in `[-8,8]` and y fixed to two. The shared
activity is six, so both inferred bounds are `-2/pivot`. Each target executes
128 reused upper-bound candidates, avoiding a second difference and quotient.

The variable-bound control uses pivot two, x in `[-8,8]` and y in `[1,2]`;
its different activities require separate candidate calculations. The upper-free
control uses pivot two, x bounded below by -8 with no upper bound, and y fixed
to two. Its lower candidate must not be recorded for a nonexistent upper
comparison. Both controls accept all pivots and remove the equality rows.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive | 1,634,840 | 1,587,304 | 2.91% | 43,703 → 42,295 |
| negative | 1,636,488 | 1,589,064 | 2.90% | 43,703 → 42,295 |
| unit_positive | 1,569,032 | 1,543,912 | 1.60% | 41,783 → 41,015 |
| unit_negative | 1,590,568 | 1,558,280 | 2.03% | 42,551 → 41,527 |
| variable | 1,697,688 | 1,698,152 | — | 45,879 → 45,879 |
| upper_free | 1,538,248 | 1,539,080 | — | 40,631 → 40,631 |

Target allocated bytes decrease by **1.60–2.91%**.
Both controls retain allocation counts. Cross-process byte differences on
unchanged paths alone establish no benefit.

- `positive` saves **1,408 allocations per call**, or 11 per reused candidate.
- `negative` saves **1,408 allocations per call**, or 11 per reused candidate.
- `unit_positive` saves **768 allocations per call**, or 6 per reused candidate.
- `unit_negative` saves **1,024 allocations per call**, or 8 per reused candidate.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,752 → 41,248 |
| afiro | sparse | 4,155 → 4,155 | 186,520 → 186,056 |
| afiro | propagation | 2,437 → 2,437 | 92,872 → 92,616 |
| afiro | presolve | 15,641 → 15,641 | 707,000 → 706,328 |
| afiro | dual | 16,456 → 16,456 | 841,624 → 840,712 |
| afiro | primal | 16,362 → 16,362 | 819,880 → 819,400 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,336 → 2,336 | 156,472 → 156,728 |
| adlittle | propagation | 18,182 → 18,182 | 641,528 → 640,904 |
| adlittle | presolve | 81,416 → 81,416 | 3,289,616 → 3,287,744 |
| adlittle | dual | 83,431 → 83,431 | 4,078,992 → 4,078,048 |
| adlittle | primal | 84,229 → 84,229 | 4,355,984 → 4,354,768 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,272 → 461,448 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,456 → 607,728 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,064 → 105,368 |
| kb2 | sparse | 2,257 → 2,257 | 136,904 → 137,192 |
| kb2 | propagation | 12,948 → 12,948 | 454,352 → 453,856 |
| kb2 | presolve | 227,905 → 227,905 | 10,591,040 → 10,590,480 |
| kb2 | dual | 229,107 → 229,107 | 11,044,016 → 11,043,792 |
| kb2 | primal | 229,274 → 229,274 | 11,058,176 → 11,057,680 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,208 → 878,176 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,164 → 6,164 | 281,824 → 281,216 |
| sc50a | propagation | 6,020 → 6,020 | 222,032 → 221,072 |
| sc50a | presolve | 66,275 → 66,275 | 2,802,488 → 2,800,088 |
| sc50a | dual | 67,347 → 67,347 | 3,148,424 → 3,145,720 |
| sc50a | primal | 67,292 → 67,292 | 3,101,176 → 3,098,408 |
| sc50a | dual_no_presolve | 961 → 961 | 306,160 → 306,176 |
| sc50a | primal_no_presolve | 964 → 964 | 232,184 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 4,667 → 4,667 | 172,984 → 172,328 |
| flugpl | propagation | 3,253 → 3,253 | 123,536 → 122,656 |
| flugpl | presolve | 27,926 → 27,926 | 1,058,744 → 1,057,304 |
| flugpl | dual | 28,597 → 28,597 | 1,168,240 → 1,166,880 |
| flugpl | primal | 28,946 → 28,946 | 1,212,656 → 1,211,280 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All 50 reference model/stage allocation counts remain unchanged. This round
shows a benefit on the targeted probes only; byte differences on the five
reference models do not establish an allocation improvement.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-shared-candidates-allocations-before.toml`](aggregation-implied-shared-candidates-allocations-before.toml)
and [`aggregation-implied-shared-candidates-allocations-after.toml`](aggregation-implied-shared-candidates-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-shared-candidates-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_shared_candidates_probe(kind; count=128, T=Float64)
    pivot=kind==:negative ? T(-2) : kind==:unit_positive ? one(T) : kind==:unit_negative ? -one(T) : T(2)
    term=T(3);low=kind==:variable ? one(T) : T(2);high=T(2)
    xlo=T(-8);xhi=kind==:upper_free ? nothing : T(8)
    rows=collect(1:2:2count);other=rows.+1
    A=sparse(vcat(rows,rows,other,other),vcat(rows,other,rows,other),
        vcat(fill(pivot,count),fill(term,count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,repeat(T[0,2],count);objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? xlo : low for i in 1:2count],
        column_upper=[isodd(i) ? xhi : high for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:positive,:negative,:unit_positive,:unit_negative,:variable,:upper_free)
    problem, pass = aggregation_implied_shared_candidates_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **3,082 assertions** and failed only
the four target allocation guards. Both controls passed. There are **3,088 new
assertions**; existing allocation budgets were not relaxed.

An independent endpoint oracle covers 1,200 helper models across Float32,
Float64, BigFloat and Rational{BigInt}, signed pivots/RHS, fixed/variable endpoints,
cancellation and finite/free/one-sided bounds. The ±1000 witnesses suffice for
these small bounded-size fixtures. BigFloat cases store a true candidate
1+2^-200 and fixed retained endpoint 2+2^-200 at 256 bits, then compare lower or
upper bounds offset by 0, 1 or 2 times 2^-200 at ambient precision 32/64/256.
Large rational candidates have 300-bit numerators and denominators 5, 7, 15 or
21; a bound displacement of 2^-350 must still change the proof. Both unit and
nonunit signed pivots are covered. The variable and upper-free allocation
controls use tight budgets to reject unused candidate materialization.

A further two-assertion regression covers cancelling fixed activities
`3*1-3*1=0`, RHS four and pivot +1. Profiling found 118 allocations before
this round and 119 with unconditional candidate caching. The new 128-call
guard failed on that intermediate implementation (15,277 allocations versus
a 15,168 limit), then passed after excluding the unchanged-RHS case. Final direct profiling
confirms the original 118 allocations; negative-unit and signed nonunit pivots
retain their savings on this cancellation fixture.

Full aggregation checks cover matrix/bounds/objective, projected/removed rows,
primal/basis restoration, objective equivalence and source preservation after
ordinary output mutation.

The targeted suite passed **138,978/138,978 assertions** in 2m43.6s.

Independent differential review of the final source passed **4,746/4,746
assertions across 156 models**: 128 accepted, 28 rejected, 420 helper checks
against the baseline and an independent interval oracle, 102 row removals,
26 projections, 468 primal restorations, 624 basis restorations and eight
rollback cases. The final cache guard and added regression were reviewed
without findings.

The full project suite passed **158,475/158,475 assertions** in 6m54.0s.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
