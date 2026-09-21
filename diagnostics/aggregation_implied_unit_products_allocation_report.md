# Signed-unit products in implied-bound activity checks

Round 154 changes only the two finite nonzero endpoint products in
`_equality_implies_column_bounds` in `src/presolve_aggregation.jl`. An exact
coefficient of one reuses the exact endpoint; minus one negates it. Otherwise,
an exact endpoint of one reuses the coefficient; minus one negates it. General
multiplication handles all remaining products. Comparisons use exact rationals,
so stored BigFloat values near signed units are not mistaken for units when the
ambient precision is lower.

Unbounded-activity, unbounded-endpoint and zero-endpoint guards retain their
order. Zero partial sums still reuse the product; other sums retain general
addition. Final implied-bound comparisons, projection, row-removal decisions,
representation gates, staged updates, rollback and postsolve are unchanged.
Only private exact activity values are reused; inputs are not mutated.

## Method and results

The baseline includes the preceding 153 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent blocks `2*x+term*y=4` and
`6*x+5*y<=100`. The cost of x is zero, y's cost is two, and the objective constant
is seven. All 128 pivots are accepted. The second row's retained coefficient
becomes `5-3*term` and its upper bound becomes 88. Measurement includes the full
sparse aggregation pass; input construction is outside measurement.

Coefficient targets use term ±1, x in `[1,3]` and y in `[2,3]`. The equality
remains projected with its retained term and bounds `[-2,2]`. Endpoint targets
use term three, x in `[-4,4]` and y fixed to ±1. Both bounds of x follow from
the equality, which is removed. Each target executes 256 signed-unit products.

The nonunit control uses term three, x in `[1,3]` and y in `[1/2,3/2]`; its
equality remains projected. The zero-endpoint control fixes y to zero and
retains x in `[1,3]`; the previous zero-endpoint guards apply, and the equality
is removed. Both controls accept all pivots.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Coefficient +1 | 2,183,456 | 2,097,296 | 3.95% | 58,309 → 56,005 |
| Coefficient -1 | 2,193,488 | 2,121,360 | 3.29% | 58,565 → 56,773 |
| Endpoint +1 | 1,828,600 | 1,742,152 | 4.73% | 49,335 → 47,031 |
| Endpoint -1 | 1,828,552 | 1,756,408 | 3.95% | 49,335 → 47,543 |
| Nonunit control | 2,248,192 | 2,248,400 | — | 60,229 → 60,229 |
| Zero-endpoint control | 1,611,288 | 1,611,688 | — | 42,423 → 42,423 |

The positive-unit targets each save **2,304 allocations**, or nine per product.
The negative-unit targets each save **1,792 allocations**, or seven per product.
Allocated bytes decrease by **3.29–4.73%**. Both controls retain their allocation
counts. Small cross-process byte differences on unchanged paths establish no benefit.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,672 → 41,072 |
| afiro | sparse | 4,243 → 4,243 | 190,160 → 189,920 |
| afiro | propagation | 2,437 → 2,437 | 92,872 → 92,776 |
| afiro | presolve | 15,713 → 15,713 | 708,568 → 708,856 |
| afiro | dual | 16,528 → 16,528 | 844,616 → 844,776 |
| afiro | primal | 16,434 → 16,434 | 822,472 → 823,048 |
| afiro | dual_no_presolve | 555 → 555 | 89,936 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,776 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,339 → 2,339 | 156,408 → 156,984 |
| adlittle | propagation | 18,182 → 18,182 | 641,672 → 641,816 |
| adlittle | presolve | 81,555 → 81,483 | 3,295,032 → 3,292,024 |
| adlittle | dual | 83,570 → 83,498 | 4,084,296 → 4,080,440 |
| adlittle | primal | 84,368 → 84,296 | 4,360,968 → 4,356,904 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,384 → 461,240 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,328 → 607,440 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 104,760 → 105,656 |
| kb2 | sparse | 2,371 → 2,364 | 141,904 → 142,424 |
| kb2 | propagation | 12,948 → 12,948 | 454,944 → 454,352 |
| kb2 | presolve | 228,131 → 228,104 | 10,600,200 → 10,597,816 |
| kb2 | dual | 229,333 → 229,306 | 11,054,264 → 11,050,184 |
| kb2 | primal | 229,500 → 229,473 | 11,067,320 → 11,064,536 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,240 → 878,160 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,234 → 6,234 | 285,168 → 284,656 |
| sc50a | propagation | 6,020 → 6,020 | 222,864 → 221,856 |
| sc50a | presolve | 66,497 → 66,497 | 2,809,800 → 2,809,144 |
| sc50a | dual | 67,569 → 67,569 | 3,156,136 → 3,154,984 |
| sc50a | primal | 67,514 → 67,514 | 3,108,808 → 3,107,752 |
| sc50a | dual_no_presolve | 961 → 961 | 306,320 → 306,416 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,184 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,063 → 4,849 | 190,472 → 181,104 |
| flugpl | propagation | 3,253 → 3,253 | 123,568 → 123,440 |
| flugpl | presolve | 29,344 → 28,618 | 1,115,040 → 1,085,952 |
| flugpl | dual | 30,015 → 29,289 | 1,224,168 → 1,195,112 |
| flugpl | primal | 30,364 → 29,638 | 1,268,920 → 1,239,960 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save 72 allocations on adlittle,
27 on kb2 and 726 on flugpl. Standalone sparse aggregation saves seven on kb2
and 214 on flugpl. The remaining 39 reference measurements retain their counts.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-unit-products-allocations-before.toml`](aggregation-implied-unit-products-allocations-before.toml)
and [`aggregation-implied-unit-products-allocations-after.toml`](aggregation-implied-unit-products-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-unit-products-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_unit_products_probe(kind; count=128, T=Float64)
    term=kind==:coefficient_positive ? one(T) : kind==:coefficient_negative ? -one(T) : T(3)
    low=kind==:bound_positive ? one(T) : kind==:bound_negative ? -one(T) : kind==:zero_bounds ? zero(T) : kind==:nonunit ? T(1)/2 : T(2)
    high=kind in (:bound_positive,:bound_negative,:zero_bounds) ? low : kind==:nonunit ? T(3)/2 : T(3)
    wide=kind in (:bound_positive,:bound_negative)
    odd=collect(1:2:2count);even=odd.+1
    A=sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(T(2),count),fill(term,count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,[isodd(i) ? zero(T) : T(2) for i in 1:2count];objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? (wide ? T(-4) : one(T)) : low for i in 1:2count],
        column_upper=[isodd(i) ? (wide ? T(4) : T(3)) : high for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:coefficient_positive,:coefficient_negative,:bound_positive,:bound_negative,:nonunit,:zero_bounds)
    problem, pass = aggregation_implied_unit_products_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **1,490 assertions** and failed only
the four target allocation guards. Both controls passed. There are **1,494 new
assertions**; existing allocation budgets were not relaxed.

An independent endpoint oracle covers 480 helper models across Float32,
Float64, BigFloat and Rational{BigInt}, with signed pivots, coefficient/endpoint
units, mixed signs, nonunit and zero controls, and finite/free/one-sided bounds.
The ±1000 witnesses suffice for these small bounded-size fixtures. BigFloat
cases store ±1 and their neighbors ±(1+2^-200) at 256 bits, then run at ambient
32/64/256; the neighbors still change the bound decision. Large rational cases
use 300-bit numerators and denominators 5, 7, 15 and 21 to check exact thresholds.

Full aggregation checks cover matrix/bounds/objective, projected/removed rows,
primal/basis restoration, objective equivalence and source preservation after
ordinary output mutation.

The targeted presolve/allocation suite passed **112,074 / 112,074 assertions**
in 2m10.4s, including every new allocation guard.

Independent read-only review found no issues. AST-renamed baseline helper and
sparse aggregation functions passed **4,361 assertions across 144 differential
models**, including 460 helper comparisons against baseline and an independent
exact interval oracle, 432 primal and 576 basis restorations. There were 134
accepted models and ten unchanged models, with 68 removed and 82 projected rows
across 150 records. Coverage included eight rollback cases, all four numeric
types, stored-256 BigFloat inputs at ambient 32/64/256, both signed-unit factor
positions, near units, nonunit/zero controls and source preservation.

The full test suite passed **131,571 / 131,571 assertions** in **6m12.9s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
