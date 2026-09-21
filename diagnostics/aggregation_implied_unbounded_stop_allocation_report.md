# Stop after required implied-bound activities become unbounded

Round 168 adds one early-return guard in `_equality_implies_column_bounds` in
`src/presolve_aggregation.jl`. After updating the minimum and maximum for a
retained term, the function returns false if both activities are `nothing`.
This skips exact coefficient conversion and endpoint selection for the remaining
terms once they cannot affect the result.

A `nothing` activity is either unbounded or unused by the pivot's bound checks.
Both-free pivot bounds already return true before initialization. Otherwise at
least one finite pivot bound requires an activity, and that activity cannot
become finite again once unbounded. Therefore both activities being `nothing`
guarantees the original final result is false. A single unbounded activity with
another finite activity still follows the original path.

The caller continues through its existing bound projection; this early return
does not reject aggregation by itself. Exact arithmetic, representation gates,
staged updates, rollback, row removal/projection and postsolve remain unchanged.

## Method and results

The baseline includes the preceding 167 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent four-column blocks:
`pivot*x+3*y+5*z+7*w=4` and `6*x+5*y+7*z+9*w<=100`, with costs `[0,2,3,4]`
and objective constant seven. z is fixed to one. All 128 pivots are accepted.
The second row's coefficients become `[5-18/pivot,7-30/pivot,9-42/pivot]`, its
upper bound becomes `100-24/pivot`, and the objective remains unchanged.
Measurement includes the full sparse aggregation pass; construction is outside it.

Targets have w fixed to one and make all required activities unbounded at y:
`positive`/`negative` use pivot +2/-2, x in `[-8,8]` and y fully free;
`lower_only` uses pivot two, x bounded below by -8 and y in `[1,+∞)`;
`upper_only` uses pivot two, x bounded above by eight and y in `(-∞,2]`.
Each skips two remaining coefficient conversions per block, saving 24
allocations. Equality rows remain, projected to `3*y+5*z+7*w` in `[-12,20]`,
`(-∞,20]` or `[-12,+∞)`, respectively.

The `late_unbounded` control uses pivot two, x in `[-8,8]`, y in `[1,2]` and w
fully free. Both activities become unbounded only at the final term; no remaining
conversion is skipped and the equality row is projected. The `finite` control
fixes w to one, so the equality implies both x bounds and its row is removed.
Both controls preserve their allocation counts.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive | 3,076,472 | 2,982,424 | 3.06% | 75,995 → 72,923 |
| negative | 3,078,600 | 2,984,952 | 3.04% | 75,995 → 72,923 |
| lower_only | 2,873,112 | 2,780,168 | 3.23% | 70,363 → 67,291 |
| upper_only | 2,873,512 | 2,780,072 | 3.25% | 70,363 → 67,291 |
| late_unbounded | 3,341,544 | 3,341,160 | — | 84,187 → 84,187 |
| finite | 3,180,592 | 3,179,904 | — | 82,771 → 82,771 |

Target allocated bytes decrease by **3.04–3.25%**.
Cross-process byte differences on unchanged paths alone establish no benefit.

- `positive` saves **3,072 allocations per call**, or 24 per block.
- `negative` saves **3,072 allocations per call**, or 24 per block.
- `lower_only` saves **3,072 allocations per call**, or 24 per block.
- `upper_only` saves **3,072 allocations per call**, or 24 per block.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 41,296 → 40,640 |
| afiro | sparse | 3,820 → 3,760 | 177,000 → 173,520 |
| afiro | propagation | 2,437 → 2,437 | 92,760 → 91,672 |
| afiro | presolve | 15,434 → 15,434 | 700,136 → 698,424 |
| afiro | dual | 16,249 → 16,249 | 835,512 → 833,736 |
| afiro | primal | 16,155 → 16,155 | 813,528 → 812,200 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 1,970 → 1,706 | 143,944 → 133,640 |
| adlittle | propagation | 18,182 → 18,182 | 641,688 → 639,384 |
| adlittle | presolve | 80,787 → 80,535 | 3,272,128 → 3,262,088 |
| adlittle | dual | 82,802 → 82,550 | 4,061,952 → 4,052,360 |
| adlittle | primal | 83,600 → 83,348 | 4,337,968 → 4,329,256 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,208 → 461,368 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,248 → 607,440 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,992 → 105,352 |
| kb2 | sparse | 1,999 → 1,999 | 128,472 → 127,848 |
| kb2 | propagation | 12,948 → 12,948 | 453,824 → 452,960 |
| kb2 | presolve | 227,041 → 227,041 | 10,562,888 → 10,560,760 |
| kb2 | dual | 228,243 → 228,243 | 11,016,232 → 11,015,944 |
| kb2 | primal | 228,410 → 228,410 | 11,029,384 → 11,029,784 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,048 → 878,080 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 5,729 → 5,585 | 269,440 → 264,352 |
| sc50a | propagation | 6,020 → 6,020 | 221,184 → 220,480 |
| sc50a | presolve | 65,321 → 65,117 | 2,774,664 → 2,766,912 |
| sc50a | dual | 66,393 → 66,189 | 3,120,264 → 3,111,952 |
| sc50a | primal | 66,338 → 66,134 | 3,073,464 → 3,064,992 |
| sc50a | dual_no_presolve | 961 → 961 | 306,416 → 306,288 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 4,068 → 4,068 | 153,896 → 152,984 |
| flugpl | propagation | 3,253 → 3,253 | 123,008 → 121,952 |
| flugpl | presolve | 26,096 → 26,096 | 999,960 → 998,264 |
| flugpl | dual | 26,767 → 26,767 | 1,109,600 → 1,108,000 |
| flugpl | primal | 27,116 → 27,116 | 1,153,968 → 1,152,528 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save 252 allocations on adlittle and
204 on sc50a. Standalone sparse aggregation saves 60 on afiro, 264 on adlittle
and 144 on sc50a. The other 41 reference model/stage allocation counts are
unchanged; none increase.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-unbounded-stop-allocations-before.toml`](aggregation-implied-unbounded-stop-allocations-before.toml)
and [`aggregation-implied-unbounded-stop-allocations-after.toml`](aggregation-implied-unbounded-stop-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-unbounded-stop-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_unbounded_stop_probe(kind; count=128, T=Float64)
    pivot=kind==:negative ? T(-2) : T(2)
    xlo=kind==:upper_only ? nothing : T(-8)
    xhi=kind==:lower_only ? nothing : T(8)
    ylo=kind in (:positive,:negative,:upper_only) ? nothing : one(T)
    yhi=kind in (:positive,:negative,:lower_only) ? nothing : T(2)
    w=kind==:late_unbounded ? nothing : one(T)
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

for kind in (:positive,:negative,:lower_only,:upper_only,:late_unbounded,:finite)
    problem, pass = aggregation_implied_unbounded_stop_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,410 assertions** and failed only
the four target allocation guards; both controls passed. After the change, all
**2,414 new assertions** passed. Existing allocation budgets were not relaxed.

An independent four-vertex endpoint oracle covers 1,024 helper models across
Float32, Float64, BigFloat and Rational{BigInt}, signed unit/nonunit pivots,
zero/nonzero RHS, positive/negative retained coefficients and finite/free/
one-sided pivot bounds. Retained intervals include zeros, variable bounds,
cancellation and early/late unbounded endpoints. The ±1000 witnesses suffice
for these small bounded-size fixtures. Source preservation is checked for every
model, including cases with only one required activity or neither.

Full aggregation checks cover the projected/removed equality rows, updated
matrix and bounds, retained column bounds, objective, primal/basis restoration,
objective equivalence and source preservation after ordinary output mutation.
Both late-unbounded and finite controls reject allocation regressions in
unaffected paths. Existing stored-precision BigFloat and large-rational tests
run with the wider suites.

The targeted suite passed **152,992/152,992 assertions** in 2m48.8s.

Independent differential review passed **5,862/5,862 assertions** across
172 models (144 accepted, 28 rejected), including 616 helper checks against the
baseline and an independent interval oracle, 54 row removals, 90 projections,
516 primal restorations, 688 basis restorations and eight rollback cases.
Coverage includes early/late/split unbounded endpoints, unused sides, free
pivots, signed unit/nonunit coefficients, stored BigFloat precision changes and
300-bit rationals. Both baseline helper and caller were independently renamed.
Source preservation passed; no findings.

The full project suite passed **172,489/172,489 assertions** in 7m07.7s.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
