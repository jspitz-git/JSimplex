# Zero endpoints in implied-bound activity checks

Round 152 changes only `_equality_implies_column_bounds` in
`src/presolve_aggregation.jl`. This helper decides whether an equality and the
other variables' bounds already imply the eliminated variable's bounds. For a
finite zero endpoint, the partial minimum or maximum activity is reused instead
of converting zero to an exact rational, multiplying it by a coefficient, and
adding the zero product.

The unbounded-activity and unbounded-endpoint guards run first, so a later zero
cannot revive an unbounded activity. The coefficient sign still determines which
endpoint contributes to each extreme. Signed zero is handled exactly; tiny
nonzero endpoints retain full arithmetic and stored BigFloat precision. Final
implied-bound comparisons, projection, row-removal decisions, objective/matrix
updates, representation gates, staging, rollback and postsolve are unchanged.
Only private exact activity values are reused, and no input operands are mutated.

## Method and results

The baseline includes the preceding 151 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent two-row, two-column blocks:
`2*x+term*y=4` and `6*x+5*y<=100`. The pivot x has bounds `[1,3]`, its cost is
zero, y's cost is two, and the objective constant is seven. All pivots are
accepted. The second row's coefficient becomes `5-3*term` and its upper bound
88. Costs and constant remain unchanged. Measurement includes the full sparse
aggregation pass, not just the helper.

Fixed-zero targets fix y to zero and use term 3 or -3. Both activity endpoints
are skipped, and the equality implies x=2, allowing its row to be removed.
The lower-zero target uses term three and y in `[0,2]`; the upper-zero target
uses y in `[-2,0]`. One activity endpoint is skipped. These intervals do not imply
both x bounds, so the equality row remains projected with coefficient three
and bounds `[-2,2]`.

The nonzero-endpoint control uses y in `[1/2,1]` and retains general arithmetic
for both extremes and the projected equality row. The free-pivot control gives
x no finite bounds and fixes y to zero; the helper's existing early return
removes the equality row without computing activities. Input construction is
outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Fixed zero, positive term | 1,843,080 | 1,609,608 | 12.67% | 48,567 → 42,423 |
| Fixed zero, negative term | 1,845,416 | 1,611,288 | 12.69% | 48,567 → 42,423 |
| Zero lower endpoint | 2,280,848 | 2,164,192 | 5.11% | 60,229 → 57,157 |
| Zero upper endpoint | 2,280,752 | 2,164,384 | 5.10% | 60,229 → 57,157 |
| Nonzero-endpoint control | 2,333,664 | 2,334,288 | — | 62,533 → 62,533 |
| Free-pivot control | 1,196,472 | 1,195,912 | — | 29,623 → 29,623 |

Allocated bytes decrease by **5.10–12.69%** across the four targets.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

- `fixed_positive` saves **6,144 allocations per call**, or 24 per skipped zero endpoint.
- `fixed_negative` saves **6,144 allocations per call**, or 24 per skipped zero endpoint.
- `lower_zero` saves **3,072 allocations per call**, or 24 per skipped zero endpoint.
- `upper_zero` saves **3,072 allocations per call**, or 24 per skipped zero endpoint.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 41,376 → 40,752 |
| afiro | sparse | 4,891 → 4,243 | 214,368 → 190,000 |
| afiro | propagation | 2,437 → 2,437 | 92,440 → 92,440 |
| afiro | presolve | 16,121 → 15,713 | 723,640 → 708,920 |
| afiro | dual | 16,936 → 16,528 | 859,672 → 843,768 |
| afiro | primal | 16,842 → 16,434 | 837,544 → 822,680 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,747 → 2,339 | 173,736 → 157,032 |
| adlittle | propagation | 18,182 → 18,182 | 640,744 → 641,304 |
| adlittle | presolve | 82,433 → 81,609 | 3,328,088 → 3,294,248 |
| adlittle | dual | 84,448 → 83,624 | 4,116,632 → 4,085,144 |
| adlittle | primal | 85,246 → 84,422 | 4,393,496 → 4,361,448 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,432 → 461,944 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,424 → 607,776 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,592 → 105,848 |
| kb2 | sparse | 2,836 → 2,380 | 161,392 → 143,280 |
| kb2 | propagation | 12,948 → 12,948 | 454,064 → 454,512 |
| kb2 | presolve | 229,049 → 228,185 | 10,634,584 → 10,600,888 |
| kb2 | dual | 230,251 → 229,387 | 11,088,040 → 11,056,072 |
| kb2 | primal | 230,418 → 229,554 | 11,102,520 → 11,069,320 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,256 → 878,176 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,234 | 298,928 → 285,056 |
| sc50a | propagation | 6,020 → 6,020 | 221,648 → 222,320 |
| sc50a | presolve | 67,457 → 66,497 | 2,846,424 → 2,809,048 |
| sc50a | dual | 68,529 → 67,569 | 3,192,600 → 3,154,536 |
| sc50a | primal | 68,474 → 67,514 | 3,145,256 → 3,107,032 |
| sc50a | dual_no_presolve | 961 → 961 | 306,416 → 306,208 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,306 | 209,944 → 199,384 |
| flugpl | propagation | 3,253 → 3,253 | 122,096 → 123,680 |
| flugpl | presolve | 30,791 → 30,154 | 1,169,376 → 1,145,920 |
| flugpl | dual | 31,462 → 30,825 | 1,279,688 → 1,254,760 |
| flugpl | primal | 31,811 → 31,174 | 1,324,168 → 1,299,448 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save **408 allocations on afiro**,
**824 on adlittle**, **864 on kb2**, **960 on sc50a**, and **637 on flugpl**.
The standalone sparse pass saves 648, 408, 456, 384, and 292 allocations,
respectively. The other 30 reference measurements retain their allocation counts,
including both solves without presolve and the standalone singleton pass.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-zero-bounds-allocations-before.toml`](aggregation-implied-zero-bounds-allocations-before.toml)
and [`aggregation-implied-zero-bounds-allocations-after.toml`](aggregation-implied-zero-bounds-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-zero-bounds-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_zero_bounds_probe(kind; count=128, T=Float64)
    term=kind==:fixed_negative ? T(-3) : T(3)
    low=kind==:upper_zero ? T(-2) : kind==:nonzero_bounds ? T(1)/2 : zero(T)
    high=kind==:lower_zero ? T(2) : kind==:nonzero_bounds ? one(T) : zero(T)
    odd=collect(1:2:2count);even=odd.+1
    A=sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(T(2),count),fill(term,count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,[isodd(i) ? zero(T) : T(2) for i in 1:2count];objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? (kind==:free_pivot ? nothing : one(T)) : low for i in 1:2count],
        column_upper=[isodd(i) ? (kind==:free_pivot ? nothing : T(3)) : high for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:fixed_positive,:fixed_negative,:lower_zero,:upper_zero,:nonzero_bounds,:free_pivot)
    problem, pass = aggregation_implied_zero_bounds_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **3,802 assertions** and failed only
the four target allocation guards: 48,612 and 48,575 against 48,067, and two
cases of 60,237 against 59,729. Both control budgets passed. There are
**3,806 new assertions**; existing budgets were not relaxed.

Direct helper tests compare against independent endpoint enumeration on 1,600
small models across Float32, Float64, BigFloat, and Rational{BigInt}. Bounds
include fixed zero, one/two-sided unbounded intervals, finite nonzero intervals,
and zero before or after an unbounded term. Coefficient/pivot signs and free,
one-sided, two-sided and fixed pivot bounds vary. Infinite endpoints use
+/-1000 witnesses only in these bounded-size fixtures; all finite coefficients
and pivot bounds make those witnesses sufficient to establish violations.

BigFloat tests store endpoints at 256-bit precision and evaluate at ambient
32/64/256. Endpoints of magnitude `2^-200` still prevent an implied-bound proof,
whereas exact zero permits row removal. Full aggregation tests verify the
corresponding projected/removed-row decisions, matrix, bounds, objective,
primal/basis restoration and source preservation. Signed-zero cases preserve
input signs and behave like positive zero.

The targeted presolve/allocation suite passed **107,806 / 107,806 assertions**
in 2m08.2s, including every new allocation guard.

Independent read-only review found no issues. AST-renamed copies of the saved
helper and sparse aggregation function passed **4,306 assertions across 144
differential models**, including 452 helper comparisons with baseline and an
independent exact interval oracle, 432 primal and 576 basis comparisons. There
were 140 accepted models and four rejections, with 65 removed and 91 projected
rows. Coverage included eight rejection/rollback cases, all numeric types,
stored-256-bit BigFloat at ambient 32/64/256, decision-changing tiny endpoints,
unbounded/zero term ordering, and source preservation. Review also confirmed
the validity of the new focused tests' bounded-size +/-1000 witnesses.

The full test suite passed **127,303 / 127,303 assertions** in **6m10.6s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
