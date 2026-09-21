# Shared fixed-endpoint products in implied-bound checks

Round 161 changes only endpoint-product handling in
`_equality_implies_column_bounds` in `src/presolve_aggregation.jl`. Each retained
term starts with no cached minimum product. The minimum activity records its
finite nonzero endpoint product only when the maximum activity is still finite
and its selected bound exactly equals the maximum's selected bound. The maximum can then reuse that recorded product.
This avoids a second exact endpoint conversion and product computation.
Recording only for equal endpoints avoids materializing an unused rational
object on variable-bound paths.

The maximum's unbounded-activity, unbounded-endpoint and zero-endpoint guards
still run before reuse. An already unbounded minimum computes no product, so
the maximum falls back to its own calculation. Resetting the optional product
for every term prevents reuse of an earlier term. Unequal bounds retain the
previous computation, including exact stored BigFloat values at lower ambient
precision. Activity sums, final bound comparisons, projection, row-removal
decisions, representation gates, staged updates, rollback and postsolve remain
unchanged. Only private exact values are shared; inputs are not mutated.

## Method and results

The baseline includes the preceding 160 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent blocks `2*x+term*y=4` and
`6*x+5*y<=100`. The cost of x is zero, y's cost is two, and the objective constant
is seven. All 128 pivots are accepted and all equality rows are removed. The
second row's retained coefficient becomes `5-3*term` and its upper bound becomes
88. Measurement includes the full sparse aggregation pass, with input
construction outside measurement.

Targets use term 3, -3, 1 or -1, x in `[-8,8]` and y fixed to two. Each target
executes 128 reused maximum products. The nonunit targets avoid both exact
conversion and general multiplication; unit targets avoid exact conversion and,
for the negative unit, negation.

The variable-bound control uses term three, x in `[-8,8]` and y in `[1,2]`;
its different endpoints retain separate products. The free-pivot control uses
term three, free x and y fixed to two; the helper returns early. Both controls
accept all pivots and remove the equality rows.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive | 1,719,672 | 1,634,760 | 4.94% | 46,263 → 43,703 |
| negative | 1,722,216 | 1,637,288 | 4.93% | 46,263 → 43,703 |
| unit_positive | 1,591,944 | 1,550,136 | 2.63% | 42,807 → 41,399 |
| unit_negative | 1,613,688 | 1,564,584 | 3.04% | 43,575 → 41,911 |
| variable | 1,697,304 | 1,698,152 | — | 45,879 → 45,879 |
| free_pivot | 1,195,624 | 1,196,264 | — | 29,623 → 29,623 |

Target allocated bytes decrease by **2.63–4.94%**.
Both controls retain allocation counts. Cross-process byte differences on
unchanged paths alone establish no benefit.

- `positive` saves **2,560 allocations per call**, or 20 per reused product.
- `negative` saves **2,560 allocations per call**, or 20 per reused product.
- `unit_positive` saves **1,408 allocations per call**, or 11 per reused product.
- `unit_negative` saves **1,664 allocations per call**, or 13 per reused product.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 41,344 → 40,752 |
| afiro | sparse | 4,167 → 4,167 | 187,480 → 187,032 |
| afiro | propagation | 2,437 → 2,437 | 93,032 → 92,840 |
| afiro | presolve | 15,653 → 15,653 | 707,160 → 707,640 |
| afiro | dual | 16,468 → 16,468 | 842,104 → 843,112 |
| afiro | primal | 16,374 → 16,374 | 819,928 → 820,312 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,936 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,339 → 2,339 | 156,744 → 156,536 |
| adlittle | propagation | 18,182 → 18,182 | 641,240 → 642,216 |
| adlittle | presolve | 81,426 → 81,426 | 3,288,384 → 3,290,032 |
| adlittle | dual | 83,441 → 83,441 | 4,078,592 → 4,080,576 |
| adlittle | primal | 84,239 → 84,239 | 4,355,152 → 4,357,184 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,048 → 461,192 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,360 → 606,960 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,576 → 105,352 |
| kb2 | sparse | 2,259 → 2,259 | 137,496 → 137,240 |
| kb2 | propagation | 12,948 → 12,948 | 453,584 → 455,248 |
| kb2 | presolve | 227,907 → 227,907 | 10,590,688 → 10,591,184 |
| kb2 | dual | 229,109 → 229,109 | 11,043,264 → 11,044,448 |
| kb2 | primal | 229,276 → 229,276 | 11,057,344 → 11,057,936 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,936 → 878,224 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,864 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,174 → 6,174 | 281,968 → 283,088 |
| sc50a | propagation | 6,020 → 6,020 | 221,712 → 223,200 |
| sc50a | presolve | 66,302 → 66,302 | 2,801,928 → 2,802,984 |
| sc50a | dual | 67,374 → 67,374 | 3,149,032 → 3,149,592 |
| sc50a | primal | 67,319 → 67,319 | 3,101,448 → 3,101,976 |
| sc50a | dual_no_presolve | 961 → 961 | 306,144 → 306,128 |
| sc50a | primal_no_presolve | 964 → 964 | 232,184 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 4,667 → 4,667 | 173,240 → 174,328 |
| flugpl | propagation | 3,253 → 3,253 | 123,424 → 123,840 |
| flugpl | presolve | 28,046 → 27,926 | 1,062,488 → 1,059,176 |
| flugpl | dual | 28,717 → 28,597 | 1,171,920 → 1,168,944 |
| flugpl | primal | 29,066 → 28,946 | 1,215,904 → 1,213,456 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save 120 allocations on flugpl.
The other 47 reference-stage measurements retain their allocation counts.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-fixed-products-allocations-before.toml`](aggregation-implied-fixed-products-allocations-before.toml)
and [`aggregation-implied-fixed-products-allocations-after.toml`](aggregation-implied-fixed-products-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-fixed-products-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_fixed_products_probe(kind; count=128, T=Float64)
    term=kind==:negative ? T(-3) : kind==:unit_positive ? one(T) : kind==:unit_negative ? -one(T) : T(3)
    low=kind==:variable ? one(T) : T(2);high=T(2)
    xlo=kind==:free_pivot ? nothing : T(-8)
    xhi=kind==:free_pivot ? nothing : T(8)
    rows=collect(1:2:2count);other=rows.+1
    A=sparse(vcat(rows,rows,other,other),vcat(rows,other,rows,other),
        vcat(fill(T(2),count),fill(term,count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,repeat(T[0,2],count);objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? xlo : low for i in 1:2count],
        column_upper=[isodd(i) ? xhi : high for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:positive,:negative,:unit_positive,:unit_negative,:variable,:free_pivot)
    problem, pass = aggregation_implied_fixed_products_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,994 assertions** and failed only
the four target allocation guards. Both controls passed. There are **3,000 new
assertions**; existing allocation budgets were not relaxed.

An independent endpoint oracle covers 1,200 helper models across Float32,
Float64, BigFloat and Rational{BigInt}, signed pivots/RHS, fixed and variable
endpoints, cancellation and finite/free/one-sided bounds. The ±1000 witnesses
suffice for these small bounded-size fixtures. BigFloat cases store a lower
bound of 2+2^-200 at 256 bits, with an equal upper bound or a neighbor another
2^-200 away, and run at ambient 32/64/256. A separate sequence seeds product six,
then makes the minimum unbounded, then needs a distinct fixed product nine;
this guards against stale reuse and skipped maximum computation. Large rational
endpoint tests use 300-bit numerators and denominators 5, 7, 15 and 21.

An additional two-assertion regression guards against recording an unused
product after the maximum activity becomes unbounded. Before the final guard,
128 helper calls made 16,000 allocations versus the baseline 15,872, failing
the 15,936 limit. The variable-bound probe also has a tightened new control
budget to catch materialization of a product that cannot be reused.

Full aggregation checks cover matrix/bounds/objective, projected/removed rows,
primal/basis restoration, objective equivalence and source preservation after
ordinary output mutation.

The targeted presolve/allocation suite passed **132,848 / 132,848 assertions**
in **2m23.9s**, including the final conditional-cache allocation guards.

Independent read-only review found no issues in the final conditional cache.
AST-renamed baseline helper and sparse aggregation functions passed **4,926
assertions across 152 differential models**, including 476 helper comparisons
against baseline and an independent exact interval oracle, 456 primal and 608
basis restoration comparisons. There were 116 accepted and 36 rejected models,
with 92 removed and 24 projected rows. Coverage included eight rollback cases,
all four numeric types, MIN/MAX senses, signed pivots/products, unbounded cache
resets and fallback, stored-256 BigFloat neighbors at ambient 32/64/256, 300-bit
rational endpoints, and source preservation. The refined conditional recording
and final finite-maximum guard were verified by fresh differential runs.

The full test suite passed **152,345 / 152,345 assertions** in **6m43.1s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
