# Shared initial zero in implied-bound activities

Round 166 changes only the initial maximum activity in
`_equality_implies_column_bounds` in `src/presolve_aggregation.jl`. If both
activities are required, the maximum reuses the minimum's exact zero instead
of constructing a second rational zero. If only the maximum is required, it
still receives its own zero. An unused maximum remains `nothing`.

The both-free early return, sign-based activity selection and all arithmetic
remain unchanged. Initially shared values are never mutated. Existing guards
allow the two activities to diverge after variable bounds or to become
unbounded independently. Fixed-product/shared-sum caches still require matching
operands. If all retained products remain zero, the shared identity also lets
the existing candidate cache avoid repeating a nonunit quotient. Its positive
unit-pivot/unchanged-RHS exclusion remains in place.

Exact bound decisions, representation gates, staged updates, rollback and
postsolve are preserved, including the existing shallow ownership of exact
rational components under ordinary nonmutating arithmetic.

## Method and results

The baseline includes the preceding 165 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent blocks `pivot*x+3*y=4` and
`6*x+5*y<=100`, with cost `[0,2]` and objective constant seven. All 128 pivots
are accepted and all equality rows are removed. The second row's coefficient
is `5-18/pivot`, its upper bound is `100-24/pivot`, and the objective is unchanged.
Measurement includes the full sparse aggregation pass; input construction is
outside measurement.

Targets use both x bounds `[-8,8]`: `positive`/`negative` fix y to two and use
pivot +2/-2; `variable` uses pivot two and y in `[1,2]`; `zero_activity` uses
pivot two with y fixed to zero. Each shares 128 initial zeros. The all-zero
case also enables 128 shared candidates through the existing cache.

The `lower_only` and `upper_only` controls use pivot two and y in `[1,2]`,
keeping only x's lower bound -8 or upper bound eight, respectively. They retain
the previous initialization path and allocation counts.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive | 1,585,672 | 1,571,848 | 0.87% | 42,295 → 41,783 |
| negative | 1,588,408 | 1,574,328 | 0.89% | 42,295 → 41,783 |
| zero_activity | 1,479,192 | 1,446,696 | 2.20% | 38,967 → 37,943 |
| variable | 1,697,384 | 1,683,496 | 0.82% | 45,879 → 45,367 |
| lower_only | 1,511,528 | 1,511,624 | — | 39,735 → 39,735 |
| upper_only | 1,487,544 | 1,487,448 | — | 39,351 → 39,351 |

Target allocated bytes decrease by **0.82–2.20%**.
Cross-process byte differences on unchanged paths alone establish no benefit.

- `positive` saves **512 allocations per call**, or 4 per block.
- `negative` saves **512 allocations per call**, or 4 per block.
- `zero_activity` saves **1,024 allocations per call**, or 8 per block.
- `variable` saves **512 allocations per call**, or 4 per block.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,960 → 41,056 |
| afiro | sparse | 4,116 → 4,116 | 185,400 → 184,920 |
| afiro | propagation | 2,437 → 2,437 | 92,904 → 92,232 |
| afiro | presolve | 15,626 → 15,618 | 706,168 → 705,544 |
| afiro | dual | 16,441 → 16,433 | 841,560 → 841,048 |
| afiro | primal | 16,347 → 16,339 | 819,016 → 818,520 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,282 → 2,282 | 154,584 → 154,824 |
| adlittle | propagation | 18,182 → 18,182 | 641,176 → 641,448 |
| adlittle | presolve | 81,251 → 81,243 | 3,283,136 → 3,282,560 |
| adlittle | dual | 83,266 → 83,258 | 4,073,568 → 4,072,528 |
| adlittle | primal | 84,064 → 84,056 | 4,350,352 → 4,349,712 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,032 → 461,368 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,200 → 607,392 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,432 → 105,384 |
| kb2 | sparse | 2,207 → 2,207 | 135,464 → 135,448 |
| kb2 | propagation | 12,948 → 12,948 | 454,704 → 453,536 |
| kb2 | presolve | 227,441 → 227,425 | 10,575,896 → 10,574,088 |
| kb2 | dual | 228,643 → 228,627 | 11,029,528 → 11,027,256 |
| kb2 | primal | 228,810 → 228,794 | 11,042,488 → 11,041,320 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,080 → 878,000 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,081 → 6,081 | 280,256 → 278,992 |
| sc50a | propagation | 6,020 → 6,020 | 222,880 → 221,296 |
| sc50a | presolve | 66,097 → 66,097 | 2,796,856 → 2,795,736 |
| sc50a | dual | 67,169 → 67,169 | 3,142,392 → 3,140,776 |
| sc50a | primal | 67,114 → 67,114 | 3,095,096 → 3,093,544 |
| sc50a | dual_no_presolve | 961 → 961 | 306,432 → 306,112 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,232 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 4,484 → 4,428 | 166,584 → 164,184 |
| flugpl | propagation | 3,253 → 3,253 | 123,984 → 123,008 |
| flugpl | presolve | 27,356 → 27,176 | 1,036,488 → 1,030,712 |
| flugpl | dual | 28,027 → 27,847 | 1,145,664 → 1,139,568 |
| flugpl | primal | 28,376 → 28,196 | 1,190,576 → 1,184,096 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save eight allocations on afiro and
adlittle, 16 on kb2 and 180 on flugpl. Standalone sparse aggregation saves 56 on
flugpl. The other 37 reference model/stage allocation counts are unchanged;
none increase.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-shared-zero-seed-allocations-before.toml`](aggregation-implied-shared-zero-seed-allocations-before.toml)
and [`aggregation-implied-shared-zero-seed-allocations-after.toml`](aggregation-implied-shared-zero-seed-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-shared-zero-seed-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_shared_zero_seed_probe(kind; count=128, T=Float64)
    pivot=kind==:negative ? T(-2) : T(2)
    term=T(3)
    low=kind==:zero_activity ? zero(T) : kind in (:variable,:lower_only,:upper_only) ? one(T) : T(2)
    high=kind==:zero_activity ? zero(T) : T(2)
    rhs=T(4)
    xlo=kind==:upper_only ? nothing : T(-8)
    xhi=kind==:lower_only ? nothing : T(8)
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

for kind in (:positive,:negative,:zero_activity,:variable,:lower_only,:upper_only)
    problem, pass = aggregation_implied_shared_zero_seed_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,386 assertions** and failed only
the four target allocation guards; both controls passed. After the change, all
**2,390 new assertions** passed. Existing allocation budgets were not relaxed.

An independent four-vertex endpoint oracle covers 1,024 helper models across
Float32, Float64, BigFloat and Rational{BigInt}, signed unit/nonunit pivots,
zero/nonzero RHS and finite/free/one-sided pivot bounds. Retained intervals cover
all-zero activities, zero prefixes followed by variable terms, cancellation,
diverging activities, unbounded prefixes followed by fixed terms, and a final
fully unbounded retained variable. The ±1000 witnesses suffice for these small
bounded-size fixtures. Source preservation is checked for every model.

Full aggregation checks cover matrix/bounds/objective, row removal, primal/basis
restoration, objective equivalence and source preservation after ordinary output
mutation. Both one-sided allocation controls reject regressions in unaffected
paths. Existing stored-precision BigFloat, large-rational and unchanged-RHS cache
regressions run with the wider targeted and full suites.

The targeted suite passed **147,972/147,972 assertions** in 2m47.3s.

Independent differential review passed **5,184/5,184 assertions** across
156 models (128 accepted, 28 rejected), including 552 helper checks against the
baseline and an independent interval oracle, 94 row removals, 34 projections,
468 primal restorations, 624 basis restorations and eight rollback cases.
Coverage includes all four numeric types and 36 stored-256-bit BigFloat cases
at ambient 32/64/256. Both baseline helper and caller were independently renamed.
Source preservation and downstream identity-dependent caches passed; no findings.

The full project suite passed **167,469/167,469 assertions** in 7m03.3s.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
