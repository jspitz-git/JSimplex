# Zero partial sums in implied-bound activity checks

Round 153 changes only `_equality_implies_column_bounds` in
`src/presolve_aggregation.jl`. For a finite nonzero endpoint, the exact product
now directly replaces a zero partial activity instead of being added to zero.
Nonzero partial sums retain general addition. Each minimum and maximum activity
uses its own current value, including after cancellation of earlier terms.

The preceding unbounded-activity, unbounded-endpoint and zero-endpoint guards
retain their order and behavior. An unbounded activity cannot become finite
again. Products still use exact stored input values, including BigFloat values
stored at higher precision than the current context. Final implied-bound
comparisons, projection, row-removal decisions, objective/matrix updates,
representation gates, staging, rollback and postsolve remain unchanged.
Only private exact activity values are reused, and no inputs are mutated.

## Method and results

The baseline includes the preceding 152 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent two-row, two-column blocks:
`2*x+term*y=4` and `6*x+5*y<=100`. Variable x has bounds `[1,3]`, its cost is
zero, y's cost is two, and the objective constant is seven. All pivots are
accepted. The second row's coefficient becomes `5-3*term`, its upper bound
becomes 88, and costs and constant remain unchanged. Measurement includes the
full sparse aggregation pass.

Positive and negative targets use term 3 or -3 with y in `[1/2,1]`. Both finite
activity sums begin at zero and can directly reuse their first nonzero product.
The lower-zero target uses term three and y in `[0,2]`; the upper-zero target
uses y in `[-2,0]`. The existing zero-endpoint branch skips one activity, while
the other uses the new zero-sum branch. None of these intervals implies both
bounds of x, so the equality row remains projected with its original retained
term and row bounds `[-2,2]`.

The zero-endpoint control fixes y to zero, retaining the previous zero-endpoint
shortcuts and removing the equality row. The free-pivot control gives x no
finite bounds, retaining the helper's early return; y remains in `[1/2,1]`.
Both controls accept all pivots. Input construction is outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive term, two finite endpoints | 2,331,696 | 2,244,112 | 3.76% | 62,533 → 60,229 |
| Negative term, two finite endpoints | 2,335,264 | 2,247,184 | 3.77% | 62,533 → 60,229 |
| Zero lower endpoint | 2,165,264 | 2,120,160 | 2.08% | 57,157 → 56,005 |
| Zero upper endpoint | 2,165,264 | 2,120,096 | 2.09% | 57,157 → 56,005 |
| Zero-endpoint control | 1,612,296 | 1,611,224 | — | 42,423 → 42,423 |
| Free-pivot control | 1,196,648 | 1,196,168 | — | 29,623 → 29,623 |

Allocated bytes decrease by **2.08–3.77%** across the four targets.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

- `positive` saves **2,304 allocations per call**, or 9 per zero-sum update.
- `negative` saves **2,304 allocations per call**, or 9 per zero-sum update.
- `lower_zero` saves **1,152 allocations per call**, or 9 per zero-sum update.
- `upper_zero` saves **1,152 allocations per call**, or 9 per zero-sum update.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,992 → 40,688 |
| afiro | sparse | 4,243 → 4,243 | 190,960 → 188,992 |
| afiro | propagation | 2,437 → 2,437 | 93,352 → 91,592 |
| afiro | presolve | 15,713 → 15,713 | 710,168 → 708,200 |
| afiro | dual | 16,528 → 16,528 | 845,448 → 843,336 |
| afiro | primal | 16,434 → 16,434 | 823,672 → 821,832 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,776 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,339 → 2,339 | 156,376 → 156,392 |
| adlittle | propagation | 18,182 → 18,182 | 642,744 → 640,488 |
| adlittle | presolve | 81,609 → 81,555 | 3,297,320 → 3,293,144 |
| adlittle | dual | 83,624 → 83,570 | 4,088,056 → 4,083,160 |
| adlittle | primal | 84,422 → 84,368 | 4,365,272 → 4,359,720 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,208 → 461,224 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,328 → 607,344 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,080 → 105,112 |
| kb2 | sparse | 2,380 → 2,371 | 142,640 → 142,256 |
| kb2 | propagation | 12,948 → 12,948 | 455,488 → 453,584 |
| kb2 | presolve | 228,185 → 228,131 | 10,603,592 → 10,600,056 |
| kb2 | dual | 229,387 → 229,333 | 11,055,064 → 11,052,824 |
| kb2 | primal | 229,554 → 229,500 | 11,069,432 → 11,065,336 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,968 → 878,208 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,864 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,234 → 6,234 | 285,568 → 284,080 |
| sc50a | propagation | 6,020 → 6,020 | 223,216 → 221,232 |
| sc50a | presolve | 66,497 → 66,497 | 2,812,056 → 2,809,688 |
| sc50a | dual | 67,569 → 67,569 | 3,156,872 → 3,154,936 |
| sc50a | primal | 67,514 → 67,514 | 3,109,816 → 3,107,784 |
| sc50a | dual_no_presolve | 961 → 961 | 306,144 → 306,304 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,306 → 5,063 | 200,520 → 188,984 |
| flugpl | propagation | 3,253 → 3,253 | 124,128 → 122,288 |
| flugpl | presolve | 30,154 → 29,344 | 1,146,832 → 1,114,096 |
| flugpl | dual | 30,825 → 30,015 | 1,256,216 → 1,223,688 |
| flugpl | primal | 31,174 → 30,364 | 1,301,016 → 1,268,264 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save **54 allocations on adlittle**,
**54 on kb2**, and **810 on flugpl**. The standalone sparse pass saves nine on
kb2 and 243 on flugpl. The other 39 reference measurements retain their
allocation counts, including all solves without presolve.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-zero-sums-allocations-before.toml`](aggregation-implied-zero-sums-allocations-before.toml)
and [`aggregation-implied-zero-sums-allocations-after.toml`](aggregation-implied-zero-sums-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-zero-sums-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_zero_sums_probe(kind; count=128, T=Float64)
    term=kind==:negative ? T(-3) : T(3)
    low=kind in (:lower_zero,:zero_bounds) ? zero(T) : kind==:upper_zero ? T(-2) : T(1)/2
    high=kind in (:upper_zero,:zero_bounds) ? zero(T) : kind==:lower_zero ? T(2) : one(T)
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

for kind in (:positive,:negative,:lower_zero,:upper_zero,:zero_bounds,:free_pivot)
    problem, pass = aggregation_implied_zero_sums_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,770 assertions** and failed only
the four target allocation guards: 62,578 and 62,541 against 62,033, and two
cases of 57,165 against 56,657. Both control budgets passed. There are
**2,774 new assertions**; existing budgets were not relaxed.

An independent endpoint oracle covers 1,152 small helper models across Float32,
Float64, BigFloat and Rational{BigInt}. Signed integer/fractional prefixes cancel
before a later contribution; other cases leave only one activity extreme at
zero. Finite/free/one-sided pivot bounds and endpoint signs vary. The oracle's
small dyadic values are exactly representable. Separate tests place unbounded
terms before and after cancelling prefixes to verify they remain unbounded.

BigFloat tests store cancelling coefficients `±(3+2^-200)` at 256 bits and run
at ambient 32/64/256. The subsequent endpoint `±2^-200` still changes the implied
bound decision, whereas zero permits the proof. Full aggregation checks cover
matrix/bounds/objective, projected/removed rows, primal/basis restoration,
objective equivalence and source preservation after ordinary output mutation.

The targeted presolve/allocation suite passed **110,580 / 110,580 assertions**
in 2m10.6s, including every new allocation guard.

Independent read-only review found no issues. AST-renamed copies of the saved
helper and sparse aggregation function passed **5,407 assertions across 152
differential models**, including 604 helper comparisons with baseline and an
independent exact interval oracle, 456 primal and 608 basis comparisons. There
were 148 accepted models and four rejections, with 80 removed and 84 projected
rows across 164 records. Coverage included eight rollback cases, 48 stored-256
BigFloat cases at ambient 32/64/256, zero re-entry, unequal activity extremes,
unbounded ordering, all numeric types, and source preservation. Review also
confirmed that the focused endpoint oracle's small dyadic calculations are exact.

The full test suite passed **130,077 / 130,077 assertions** in **6m25.7s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
