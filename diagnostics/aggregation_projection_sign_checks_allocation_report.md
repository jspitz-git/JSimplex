# Exact sign selection for projected equality bounds

Round 169 changes only the sign selection used by bound projection in
`aggregate_sparse_equalities` in `src/presolve_aggregation.jl`. The exact pivot's
numerator is tested once and the resulting Boolean selects the source endpoint
for each projected bound. This replaces the two rational-to-integer `pivot>0`
comparisons. Canonical finite rationals have positive denominators, so the same
endpoints are selected for positive and negative pivots.

The implied-bound helper, fixed-bound projection reuse, free-bound handling,
exact arithmetic, representation gates, staged updates, rollback, row removal
and postsolve are unchanged. The nonallocating sign check has no observable
effect when bounds are already implied and projection is skipped. No approximate
sign test or reduction of stored BigFloat precision is introduced.

## Method and results

The baseline includes the preceding 168 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent four-column blocks:
`pivot*x+3*y+5*z+7*w=4` and `6*x+5*y+7*z+9*w<=100`, with z and w fixed to one,
costs `[0,2,3,4]` and objective constant seven. All 128 pivots are accepted.
The second row's coefficients become `[5-18/pivot,7-30/pivot,9-42/pivot]`, its
upper bound becomes `100-24/pivot`, and the objective remains unchanged.
Measurement includes the full sparse aggregation pass; construction is outside it.

Targets require projection: `positive`/`negative` use pivot +2/-2, x in `[-8,8]`
and y fully free; `lower_only` uses pivot two, x bounded below by -8 and y in
`[1,+∞)`; `upper_only` uses pivot two, x bounded above by eight and y in `(-∞,2]`.
Equality rows remain, projected to `3*y+5*z+7*w` in `[-12,20]`, `(-∞,20]` or
`[-12,+∞)`, respectively. Each block avoids two allocating sign comparisons,
saving eight allocations, including when one selected source bound is free.

Both controls use pivot two and y in `[1,2]`. The `finite` control has x in
`[-8,8]`; the `free_pivot` control has both x bounds free. Bounds are implied in
both controls, so their equality rows are removed without projection and their
allocation counts remain unchanged.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive | 2,982,984 | 2,956,536 | 0.89% | 72,923 → 71,899 |
| negative | 2,985,880 | 2,958,840 | 0.91% | 72,923 → 71,899 |
| lower_only | 2,779,736 | 2,753,736 | 0.94% | 67,291 → 66,267 |
| upper_only | 2,780,280 | 2,753,464 | 0.96% | 67,291 → 66,267 |
| free_pivot | 2,422,640 | 2,424,528 | — | 58,579 → 58,579 |
| finite | 3,180,512 | 3,181,440 | — | 82,771 → 82,771 |

Target allocated bytes decrease by **0.89–0.96%**.
Cross-process byte differences on unchanged paths alone establish no benefit.

- `positive` saves **1,024 allocations per call**, or 8 per block.
- `negative` saves **1,024 allocations per call**, or 8 per block.
- `lower_only` saves **1,024 allocations per call**, or 8 per block.
- `upper_only` saves **1,024 allocations per call**, or 8 per block.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,928 → 40,928 |
| afiro | sparse | 3,760 → 3,736 | 174,160 → 173,392 |
| afiro | propagation | 2,437 → 2,437 | 92,328 → 92,552 |
| afiro | presolve | 15,434 → 15,410 | 699,464 → 699,624 |
| afiro | dual | 16,249 → 16,225 | 834,584 → 834,200 |
| afiro | primal | 16,155 → 16,131 | 813,000 → 812,184 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 1,706 → 1,642 | 133,064 → 130,648 |
| adlittle | propagation | 18,182 → 18,182 | 640,808 → 640,584 |
| adlittle | presolve | 80,535 → 80,447 | 3,262,664 → 3,260,856 |
| adlittle | dual | 82,550 → 82,462 | 4,053,608 → 4,052,808 |
| adlittle | primal | 83,348 → 83,260 | 4,329,656 → 4,329,880 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,816 → 461,336 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,776 → 607,440 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,016 → 105,272 |
| kb2 | sparse | 1,999 → 1,999 | 127,480 → 127,736 |
| kb2 | propagation | 12,948 → 12,948 | 453,552 → 453,760 |
| kb2 | presolve | 227,041 → 227,017 | 10,562,936 → 10,561,736 |
| kb2 | dual | 228,243 → 228,219 | 11,016,152 → 11,016,008 |
| kb2 | primal | 228,410 → 228,386 | 11,030,168 → 11,028,776 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,256 → 878,032 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,848 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 5,585 → 5,489 | 265,104 → 262,064 |
| sc50a | propagation | 6,020 → 6,020 | 221,488 → 221,184 |
| sc50a | presolve | 65,117 → 64,941 | 2,767,632 → 2,761,936 |
| sc50a | dual | 66,189 → 66,013 | 3,113,248 → 3,108,512 |
| sc50a | primal | 66,134 → 65,958 | 3,065,856 → 3,061,296 |
| sc50a | dual_no_presolve | 961 → 961 | 306,240 → 306,240 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 4,068 → 3,956 | 153,272 → 149,432 |
| flugpl | propagation | 3,253 → 3,253 | 123,024 → 122,960 |
| flugpl | presolve | 26,096 → 25,764 | 999,016 → 990,600 |
| flugpl | dual | 26,767 → 26,435 | 1,109,152 → 1,100,144 |
| flugpl | primal | 27,116 → 26,784 | 1,153,344 → 1,144,864 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,728 → 91,680 |

Full presolve and each solve with presolve save 24 allocations on afiro, 88 on
adlittle, 24 on kb2, 176 on sc50a and 332 on flugpl. Standalone sparse aggregation
saves 24, 64, zero, 96 and 112 respectively. The other 31 reference model/stage
allocation counts are unchanged; none increase.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-projection-sign-checks-allocations-before.toml`](aggregation-projection-sign-checks-allocations-before.toml)
and [`aggregation-projection-sign-checks-allocations-after.toml`](aggregation-projection-sign-checks-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-projection-sign-checks-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_projection_sign_checks_probe(kind; count=128, T=Float64)
    pivot=kind==:negative ? T(-2) : T(2)
    xlo=kind in (:upper_only,:free_pivot) ? nothing : T(-8)
    xhi=kind in (:lower_only,:free_pivot) ? nothing : T(8)
    ylo=kind in (:positive,:negative,:upper_only) ? nothing : one(T)
    yhi=kind in (:positive,:negative,:lower_only) ? nothing : T(2)
    w=one(T)
    rows=collect(1:2:2count);other=rows.+1;cols=collect(1:4:4count)
    A=sparse(vcat(rows,rows,rows,rows,other,other,other,other),
        vcat(cols,cols.+1,cols.+2,cols.+3,cols,cols.+1,cols.+2,cols.+3),
        vcat(fill(pivot,count),fill(T(3),count),fill(T(5),count),fill(T(7),count),
             fill(T(6),count),fill(T(5),count),fill(T(7),count),fill(T(9),count)),2count,4count)
    problem=LinearProblem(A,repeat(T[0,2,3,4],count);objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=repeat([xlo,ylo,one(T),w],count),
        column_upper=repeat([xhi,yhi,one(T),w],count))
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:positive,:negative,:lower_only,:upper_only,:free_pivot,:finite)
    problem, pass = aggregation_projection_sign_checks_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **3,114 assertions** and failed only
the four target allocation guards; both controls passed. After the change, all
**3,118 new assertions** passed. Existing allocation budgets were not relaxed.

Independent interval-image enumeration covers 320 full-pass models across
Float32, Float64, BigFloat and Rational{BigInt}, pivots ±2 and ±1/2, retained
coefficients ±3, zero/nonzero RHS, finite/fixed/free/one-sided pivot bounds.
Small dyadic fixtures make the separate Float64 interval-image calculation exact.
Tests compare projected matrix/bounds/objective, removed-row flags, primal/basis
restoration and source preservation.

A further 48 BigFloat cases store pivots ±2^-200 or ±1 and bounds involving
`1+2^-200` at 256 bits. Both/fixed/lower-only/upper-only bounds are tested under
ambient precision 32/64/256. The first two precisions must reject aggregation
when projected bounds are not exactly representable; 256-bit projection must
succeed with the independently enumerated bounds. The retained column has
original degree one, preventing an alternative pivot from hiding a rejection.

The six full-pass block probes additionally check projected/removed rows,
retained column bounds, objective equivalence, primal/basis restoration and
source preservation after ordinary output mutation. The controls guard against
allocation regressions when no projection is needed.

The targeted suite passed **156,110/156,110 assertions** in 2m50.7s.

Independent differential review passed **4,544/4,544 assertions** across
144 models (124 accepted, 20 rejected), including 116 projected rows, eight
removed rows, 432 primal restorations, 576 basis restorations and eight late
rejection/rollback cases. Coverage includes signed unit/nonunit pivots, fixed
and one-sided bounds, large rationals and stored-256-bit BigFloat representation
gates. Baseline comparison and an independent affine-image oracle preserved
all results; source preservation passed and the review found no issues.

The full project suite passed **175,607/175,607 assertions** in 7m06.8s.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
