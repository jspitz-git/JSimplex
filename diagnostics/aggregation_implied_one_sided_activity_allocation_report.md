# One-sided activities in implied-bound checks

Round 164 changes only activity initialization in
`_equality_implies_column_bounds` in `src/presolve_aggregation.jl`. For a positive
pivot, a finite lower pivot bound requires the maximum retained activity, while
a finite upper bound requires the minimum. A negative pivot reverses this mapping.
The function now initializes only the required activities to exact zero; an
unused side starts as `nothing`, so existing guards skip its endpoint conversion,
product and accumulation. The sign is obtained from the exact pivot numerator.

Both-free early return, exact interval arithmetic, fixed-product/shared-sum/
shared-candidate caches, bound decisions, representation gates, staged updates,
rollback and postsolve are unchanged. An unused activity never becomes finite
again, and the final free-bound guards precede any read of that side. Stored
BigFloat precision and ordinary source preservation remain intact.

## Method and results

The baseline includes the preceding 163 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent blocks `pivot*x+3*y=4` and
`6*x+5*y<=100`, with y in `[1,2]`, cost `[0,2]` and objective constant seven.
All 128 pivots are accepted and all equality rows are removed. The second row
has coefficient `5-18/pivot` and upper bound `100-24/pivot`; the objective is
unchanged. Measurement includes the full sparse aggregation pass, with input
construction outside measurement.

The four targets combine pivots +2/-2 with x bounded only below by -8 or only
above by eight. Each avoids 128 unused activities. The `both` control retains
both x bounds `[-8,8]`, and the `free_pivot` control retains neither; both use
pivot +2 and preserve their allocation counts.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| lower_positive | 1,577,496 | 1,509,608 | 4.30% | 42,039 → 39,735 |
| lower_negative | 1,598,584 | 1,487,000 | 6.98% | 42,807 → 39,351 |
| upper_positive | 1,598,888 | 1,487,208 | 6.98% | 42,807 → 39,351 |
| upper_negative | 1,580,200 | 1,511,560 | 4.34% | 42,039 → 39,735 |
| both | 1,697,944 | 1,698,328 | — | 45,879 → 45,879 |
| free_pivot | 1,194,952 | 1,195,768 | — | 29,623 → 29,623 |

Target allocated bytes decrease by **4.30–6.98%**.
Cross-process byte differences on unchanged paths alone establish no benefit.

- `lower_positive` saves **2,304 allocations per call**, or 18 per skipped activity.
- `lower_negative` saves **3,456 allocations per call**, or 27 per skipped activity.
- `upper_positive` saves **3,456 allocations per call**, or 27 per skipped activity.
- `upper_negative` saves **2,304 allocations per call**, or 18 per skipped activity.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 41,264 → 40,432 |
| afiro | sparse | 4,155 → 4,116 | 186,120 → 184,872 |
| afiro | propagation | 2,437 → 2,437 | 92,808 → 92,440 |
| afiro | presolve | 15,641 → 15,626 | 706,264 → 705,256 |
| afiro | dual | 16,456 → 16,441 | 841,800 → 841,304 |
| afiro | primal | 16,362 → 16,347 | 818,744 → 819,464 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,336 → 2,282 | 156,824 → 154,808 |
| adlittle | propagation | 18,182 → 18,182 | 640,840 → 641,928 |
| adlittle | presolve | 81,416 → 81,251 | 3,289,008 → 3,284,128 |
| adlittle | dual | 83,431 → 83,266 | 4,080,224 → 4,074,048 |
| adlittle | primal | 84,229 → 84,064 | 4,356,624 → 4,350,912 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,064 → 461,032 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,088 → 607,216 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,704 → 105,240 |
| kb2 | sparse | 2,257 → 2,207 | 137,512 → 135,256 |
| kb2 | propagation | 12,948 → 12,948 | 454,672 → 454,928 |
| kb2 | presolve | 227,905 → 227,463 | 10,590,752 → 10,576,624 |
| kb2 | dual | 229,107 → 228,665 | 11,045,152 → 11,029,600 |
| kb2 | primal | 229,274 → 228,832 | 11,059,472 → 11,041,920 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,256 → 878,208 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,848 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,164 → 6,081 | 281,984 → 280,080 |
| sc50a | propagation | 6,020 → 6,020 | 222,112 → 222,752 |
| sc50a | presolve | 66,275 → 66,097 | 2,801,416 → 2,796,504 |
| sc50a | dual | 67,347 → 67,169 | 3,148,072 → 3,142,824 |
| sc50a | primal | 67,292 → 67,114 | 3,100,792 → 3,095,288 |
| sc50a | dual_no_presolve | 961 → 961 | 306,112 → 306,272 |
| sc50a | primal_no_presolve | 964 → 964 | 232,184 → 232,184 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 4,667 → 4,646 | 173,368 → 173,176 |
| flugpl | propagation | 3,253 → 3,253 | 123,344 → 123,168 |
| flugpl | presolve | 27,926 → 27,926 | 1,057,336 → 1,058,840 |
| flugpl | dual | 28,597 → 28,597 | 1,167,152 → 1,167,488 |
| flugpl | primal | 28,946 → 28,946 | 1,211,584 → 1,212,160 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save 15 allocations on afiro, 165 on
adlittle, 442 on kb2 and 178 on sc50a; flugpl remains unchanged at those stages.
Standalone sparse aggregation saves 39, 54, 50, 83 and 21 respectively.
The other 33 reference model/stage allocation counts are unchanged; none increase.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-one-sided-activity-allocations-before.toml`](aggregation-implied-one-sided-activity-allocations-before.toml)
and [`aggregation-implied-one-sided-activity-allocations-after.toml`](aggregation-implied-one-sided-activity-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-one-sided-activity-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_one_sided_activity_probe(kind; count=128, T=Float64)
    pivot=kind in (:lower_negative,:upper_negative) ? T(-2) : T(2)
    term=T(3);low=one(T);high=T(2)
    xlo=kind in (:upper_positive,:upper_negative,:free_pivot) ? nothing : T(-8)
    xhi=kind in (:lower_positive,:lower_negative,:free_pivot) ? nothing : T(8)
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

for kind in (:lower_positive,:lower_negative,:upper_positive,:upper_negative,:both,:free_pivot)
    problem, pass = aggregation_implied_one_sided_activity_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **3,082 assertions** and failed only
the four target allocation guards; both controls passed. After the change, all
**3,086 new assertions** passed. Existing allocation budgets were not relaxed.

An independent endpoint oracle covers 1,200 helper models across Float32,
Float64, BigFloat and Rational{BigInt}, signed pivots/RHS, fixed/variable and
unbounded retained endpoints, cancellation and finite/free/one-sided pivot
bounds. The ±1000 witnesses suffice for these small bounded-size fixtures.
The cases detect reversed activity selection or revival of an unbounded side.

BigFloat cases store a true candidate `1+2^-200` and fixed retained endpoint
`2+2^-200` at 256 bits, then compare a single lower or upper bound offset by
0, 1 or 2 times `2^-200` at ambient precision 32/64/256. Large rational candidates
have 300-bit numerators and denominators 5, 7, 15 or 21; a single-bound displacement
of `2^-350` must change the proof. Both unit and nonunit signed pivots are covered.

Full aggregation checks cover matrix/bounds/objective, row removal, primal/basis
restoration, objective equivalence and source preservation after ordinary output
mutation. Both-bound and free-pivot allocation controls reject regressions in
unaffected paths.

The targeted suite passed **142,064/142,064 assertions** in 2m43.9s.

Independent differential review passed **33,182/33,182 assertions** across
1,052 models (1,024 accepted, 28 rejected), including 3,108 helper checks against
the baseline and an independent interval oracle, 558 row removals, 466
projections, 3,156 primal restorations, 4,208 basis restorations and eight rollback
cases. The review covered all four numeric types, asymmetric/unbounded intervals,
large rationals and stored 256-bit BigFloat at ambient 32/64/256; no findings.

The full project suite passed **161,561/161,561 assertions** in 6m55.4s.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
