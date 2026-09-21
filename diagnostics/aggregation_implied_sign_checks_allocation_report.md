# Exact sign checks in implied-bound activities

Round 167 changes only sign decisions in `_equality_implies_column_bounds` in
`src/presolve_aggregation.jl`. Each retained coefficient's sign is determined
once from its exact numerator and reused for both endpoint selections. The
already-computed exact pivot sign is reused for lower/upper activity selection.
This removes four rational-to-integer comparisons for a one-retained-term row.
Canonical finite rationals have positive denominators, so the selected endpoints
are identical, including for tiny coefficients and signed unit pivots.

A warmed local sign probe on ±3//2 measured four allocations (112 bytes) for
`x>0` and zero for `numerator(x)>0`. The full-pass measurements below show the
resulting effect. Exact coefficient conversion, arithmetic, free/unbounded guards,
all sharing caches, bound decisions, representation gates, staged updates,
rollback and postsolve remain unchanged. No floating-point approximation or
stored-precision reduction is introduced.

## Method and results

The baseline includes the preceding 166 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent blocks `pivot*x+term*y=4` and
`6*x+5*y<=100`, with y in `[1,2]`, cost `[0,2]` and objective constant seven.
All 128 pivots are accepted and all equality rows are removed. The second row's
coefficient is `5-6*term/pivot`, its upper bound is `100-24/pivot`, and the objective
is unchanged. Measurement includes the full sparse aggregation pass; input
construction is outside measurement.

Targets use x in `[-8,8]` and all four sign combinations of pivot ±2 and term
±3. Each block avoids two pivot and two retained-coefficient rational comparisons,
saving 16 allocations. The `free_positive` and `free_negative` controls have
both x bounds free, term three and pivot +2/-2. Their existing early return
avoids these comparisons already, so allocation counts remain unchanged.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive | 1,680,952 | 1,624,328 | 3.37% | 45,367 → 43,319 |
| negative | 1,683,048 | 1,626,360 | 3.37% | 45,367 → 43,319 |
| negative_term | 1,682,968 | 1,626,440 | 3.36% | 45,367 → 43,319 |
| negative_both | 1,682,936 | 1,626,264 | 3.37% | 45,367 → 43,319 |
| free_positive | 1,196,376 | 1,196,440 | — | 29,623 → 29,623 |
| free_negative | 1,195,912 | 1,196,568 | — | 29,623 → 29,623 |

Target allocated bytes decrease by **3.36–3.37%**.
Cross-process byte differences on unchanged paths alone establish no benefit.

- `positive` saves **2,048 allocations per call**, or 16 per block.
- `negative` saves **2,048 allocations per call**, or 16 per block.
- `negative_term` saves **2,048 allocations per call**, or 16 per block.
- `negative_both` saves **2,048 allocations per call**, or 16 per block.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,736 → 40,960 |
| afiro | sparse | 4,116 → 3,820 | 185,464 → 176,616 |
| afiro | propagation | 2,437 → 2,437 | 92,968 → 92,744 |
| afiro | presolve | 15,618 → 15,434 | 704,904 → 700,456 |
| afiro | dual | 16,433 → 16,249 | 840,776 → 836,296 |
| afiro | primal | 16,339 → 16,155 | 818,728 → 813,912 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,792 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,282 → 1,970 | 154,920 → 142,792 |
| adlittle | propagation | 18,182 → 18,182 | 640,728 → 641,528 |
| adlittle | presolve | 81,243 → 80,787 | 3,282,704 → 3,272,656 |
| adlittle | dual | 83,258 → 82,802 | 4,072,480 → 4,062,816 |
| adlittle | primal | 84,056 → 83,600 | 4,349,312 → 4,339,824 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,080 → 461,032 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,312 → 607,376 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,256 → 105,192 |
| kb2 | sparse | 2,207 → 1,999 | 135,304 → 127,640 |
| kb2 | propagation | 12,948 → 12,948 | 453,824 → 454,592 |
| kb2 | presolve | 227,425 → 227,041 | 10,574,488 → 10,564,120 |
| kb2 | dual | 228,627 → 228,243 | 11,026,888 → 11,017,672 |
| kb2 | primal | 228,794 → 228,410 | 11,038,808 → 11,030,344 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,176 → 877,952 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,880 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,081 → 5,729 | 279,424 → 270,240 |
| sc50a | propagation | 6,020 → 6,020 | 221,776 → 222,672 |
| sc50a | presolve | 66,097 → 65,321 | 2,795,032 → 2,774,776 |
| sc50a | dual | 67,169 → 66,393 | 3,140,024 → 3,120,760 |
| sc50a | primal | 67,114 → 66,338 | 3,093,048 → 3,074,344 |
| sc50a | dual_no_presolve | 961 → 961 | 306,208 → 306,176 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 4,428 → 4,068 | 164,040 → 153,864 |
| flugpl | propagation | 3,253 → 3,253 | 123,216 → 123,200 |
| flugpl | presolve | 27,176 → 26,096 | 1,029,176 → 1,000,184 |
| flugpl | dual | 27,847 → 26,767 | 1,138,784 → 1,111,248 |
| flugpl | primal | 28,196 → 27,116 | 1,183,648 → 1,155,952 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save 184 allocations on afiro, 456 on
adlittle, 384 on kb2, 776 on sc50a and 1,080 on flugpl. Standalone sparse
aggregation saves 296, 312, 208, 352 and 360 respectively. The other 30 reference
model/stage allocation counts are unchanged; none increase.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-sign-checks-allocations-before.toml`](aggregation-implied-sign-checks-allocations-before.toml)
and [`aggregation-implied-sign-checks-allocations-after.toml`](aggregation-implied-sign-checks-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-sign-checks-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_sign_checks_probe(kind; count=128, T=Float64)
    pivot=kind in (:negative,:negative_both,:free_negative) ? T(-2) : T(2)
    term=kind in (:negative_term,:negative_both) ? T(-3) : T(3)
    low=one(T);high=T(2);rhs=T(4)
    free=kind in (:free_positive,:free_negative)
    xlo=free ? nothing : T(-8);xhi=free ? nothing : T(8)
    rows=collect(1:2:2count);other=rows.+1
    A=sparse(vcat(rows,rows,other,other),vcat(rows,other,rows,other),
        vcat(fill(pivot,count),fill(term,count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,repeat(T[0,2],count);objective_constant=T(7),
        row_lower=[isodd(i) ? rhs : nothing for i in 1:2count],
        row_upper=[isodd(i) ? rhs : T(100) for i in 1:2count],
        column_lower=[isodd(i) ? xlo : low for i in 1:2count],
        column_upper=[isodd(i) ? xhi : high for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:positive,:negative,:negative_term,:negative_both,:free_positive,:free_negative)
    problem, pass = aggregation_implied_sign_checks_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,602 assertions** and failed only
the four target allocation guards; both controls passed. After the change, all
**2,606 new assertions** passed. Existing allocation budgets were not relaxed.

An independent four-vertex endpoint oracle covers 1,024 helper models across
Float32, Float64, BigFloat and Rational{BigInt}, signed unit/nonunit pivots,
zero/nonzero RHS, positive/negative retained coefficients and finite/free/
one-sided pivot bounds. Retained intervals include zeros, variable bounds,
cancellation and unbounded endpoints. The ±1000 witnesses suffice for these
small bounded-size fixtures. Source preservation is checked for every model.

A further 72 BigFloat cases store pivots ±2^-200, retained coefficients ±2^-210
and endpoints `1+2^-200` and `1+2*2^-200` at 256 bits. The tested pivot bound is
displaced by -1, 0 or +1 times 2^-220 from an independently enumerated endpoint;
its decision is checked under ambient precision 32/64/256. All four sign
combinations and both bound directions are covered.

Full aggregation checks cover matrix/bounds/objective, row removal, primal/basis
restoration, objective equivalence and source preservation after ordinary output
mutation. The two free-pivot controls reject regressions in unaffected paths.

The targeted suite passed **150,578/150,578 assertions** in 2m47.7s.

Independent differential review passed **5,768/5,768 assertions** across
180 models (136 accepted, 44 rejected), including 600 helper checks against the
baseline and an independent interval oracle, 102 row removals, 34 projections,
540 primal restorations, 720 basis restorations and eight rollback cases.
Coverage includes all four scalar types, signed unit/nonunit coefficients and
pivots, tiny stored BigFloat coefficients across ambient precisions, and
300-bit nondyadic rationals. Both baseline helper and aggregation caller were
independently renamed. Source preservation passed; no findings.

The full project suite passed **170,075/170,075 assertions** in 7m02.6s.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
