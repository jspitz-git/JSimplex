# Shared nonzero shifts of equal row bounds

Round 170 changes only the row-bound shift block in `aggregate_sparse_equalities`
in `src/presolve_aggregation.jl`. When the shift is nonzero and the original
lower/upper bounds are exactly equal, the upper bound reuses the lower bound's
`_shift_bound_exact` result. This avoids repeating conversion, subtraction and
exact representation checks. If the lower shift fails with `nothing`, that
failure is reused and the existing rejection guard still rejects the candidate.

The equality flag is captured before either local bound is overwritten. The
existing any-finite-bound guard excludes fully unbounded pairs. Unequal bounds
retain independent shifts. Zero shifts also retain both original objects: the
helper's identity path preserves signed-zero differences and distinct stored
BigFloat precisions, even when the bounds compare numerically equal.

Representation gates, private accumulated row bounds, staged matrix/objective
updates, rollback, row removal and postsolve are unchanged. Reused exact values
are not mutated; ordinary output-container changes preserve the source model.

## Method and results

The baseline includes the preceding 169 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent blocks `pivot*x+3*y=rhs` and
`6*x+5*y` in a specified row interval. Both columns are free, costs are `[0,2]`,
and the objective constant is seven. All 128 pivots are accepted and the first
equality rows are removed. The retained coefficient is `5-18/pivot` and each
finite row bound is shifted by `6*rhs/pivot`. Measurement includes the full
sparse aggregation pass, with construction outside measurement.

Four targets use RHS four and equal bounds on the second row:

- `positive`: pivot two, bounds 20, shift 12, resulting bounds eight.
- `negative`: pivot -2, bounds 16, shift -12, resulting bounds 28.
- `cancelled`: pivot two, bounds 12, yielding exact zero.
- `zero_bound`: pivot two, bounds zero, yielding -12.

Each target reuses 128 upper-bound results. The `unequal` control uses pivot
two, RHS four and bounds `[-20,20]`; both shifts must still be computed. The
`zero_shift` control uses pivot two, RHS zero and equal bounds 20; both original
bound representations must be retained. Both controls preserve allocation counts.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive | 1,367,160 | 1,195,240 | 12.57% | 34,231 → 29,623 |
| negative | 1,368,984 | 1,196,888 | 12.57% | 34,231 → 29,623 |
| cancelled | 1,292,104 | 1,158,440 | 10.34% | 32,183 → 28,599 |
| zero_bound | 1,203,608 | 1,113,672 | 7.47% | 29,367 → 27,191 |
| unequal | 1,369,016 | 1,370,136 | — | 34,231 → 34,231 |
| zero_shift | 968,920 | 969,880 | — | 23,479 → 23,479 |

Target allocated bytes decrease by **7.47–12.57%**.
Cross-process byte differences on unchanged paths alone establish no benefit.

- `positive` saves **4,608 allocations per call**, or 36 per reused bound.
- `negative` saves **4,608 allocations per call**, or 36 per reused bound.
- `cancelled` saves **3,584 allocations per call**, or 28 per reused bound.
- `zero_bound` saves **2,176 allocations per call**, or 17 per reused bound.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,448 → 40,800 |
| afiro | sparse | 3,736 → 3,736 | 173,648 → 174,400 |
| afiro | propagation | 2,437 → 2,437 | 92,472 → 92,904 |
| afiro | presolve | 15,410 → 15,410 | 699,624 → 699,048 |
| afiro | dual | 16,225 → 16,225 | 834,984 → 834,552 |
| afiro | primal | 16,131 → 16,131 | 813,304 → 812,600 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 1,642 → 1,572 | 130,824 → 127,752 |
| adlittle | propagation | 18,182 → 18,182 | 641,288 → 641,080 |
| adlittle | presolve | 80,447 → 80,377 | 3,261,368 → 3,258,984 |
| adlittle | dual | 82,462 → 82,392 | 4,052,712 → 4,048,232 |
| adlittle | primal | 83,260 → 83,190 | 4,329,688 → 4,324,568 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,368 → 461,640 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,456 → 607,232 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,160 → 105,176 |
| kb2 | sparse | 1,999 → 1,999 | 127,624 → 127,624 |
| kb2 | propagation | 12,948 → 12,948 | 454,576 → 454,080 |
| kb2 | presolve | 227,017 → 227,017 | 10,563,192 → 10,561,464 |
| kb2 | dual | 228,219 → 228,219 | 11,017,352 → 11,014,920 |
| kb2 | primal | 228,386 → 228,386 | 11,031,096 → 11,028,584 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,448 → 877,936 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,896 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 5,489 → 5,489 | 262,976 → 262,720 |
| sc50a | propagation | 6,020 → 6,020 | 222,496 → 221,648 |
| sc50a | presolve | 64,941 → 64,941 | 2,763,632 → 2,762,432 |
| sc50a | dual | 66,013 → 66,013 | 3,108,400 → 3,108,480 |
| sc50a | primal | 65,958 → 65,958 | 3,061,072 → 3,060,960 |
| sc50a | dual_no_presolve | 961 → 961 | 306,176 → 306,160 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 3,956 → 3,956 | 150,232 → 150,776 |
| flugpl | propagation | 3,253 → 3,253 | 123,424 → 123,632 |
| flugpl | presolve | 25,764 → 25,764 | 991,048 → 990,360 |
| flugpl | dual | 26,435 → 26,435 | 1,101,584 → 1,100,384 |
| flugpl | primal | 26,784 → 26,784 | 1,146,128 → 1,144,688 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Standalone sparse aggregation, full presolve and each solve with presolve save
70 allocations on adlittle. The other 46 reference model/stage allocation
counts are unchanged; none increase.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-shared-shifted-bounds-allocations-before.toml`](aggregation-shared-shifted-bounds-allocations-before.toml)
and [`aggregation-shared-shifted-bounds-allocations-after.toml`](aggregation-shared-shifted-bounds-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-shared-shifted-bounds-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_shared_shifted_bounds_probe(kind; count=128, T=Float64)
    pivot=kind==:negative ? T(-2) : T(2)
    rhs=kind==:zero_shift ? zero(T) : T(4)
    upper=kind==:negative ? T(16) : kind==:cancelled ? T(12) : kind==:zero_bound ? zero(T) : T(20)
    lower=kind==:unequal ? T(-20) : upper
    rows=collect(1:2:2count);other=rows.+1
    A=sparse(vcat(rows,rows,other,other),vcat(rows,other,rows,other),
        vcat(fill(pivot,count),fill(T(3),count),fill(T(6),count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,repeat(T[0,2],count);objective_constant=T(7),
        row_lower=[isodd(i) ? rhs : lower for i in 1:2count],
        row_upper=[isodd(i) ? rhs : upper for i in 1:2count],
        column_lower=fill(nothing,2count),column_upper=fill(nothing,2count))
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:positive,:negative,:cancelled,:zero_bound,:unequal,:zero_shift)
    problem, pass = aggregation_shared_shifted_bounds_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **3,181 assertions** and failed only
the four target allocation guards; both controls passed. After the change, all
**3,185 new assertions** passed. Existing allocation budgets were not relaxed.

Independent exact interval translation covers 336 full-pass models across
Float32, Float64, BigFloat and Rational{BigInt}, signed unit/nonunit pivots,
zero/signed RHS and equal/unequal/one-sided/free row bounds. Tests compare
matrix, shifted bounds, objective, row removal, primal/basis restoration and source.

Zero-shift tests preserve Float32/Float64 -0.0 versus +0.0, and equal BigFloat
bounds stored separately at 128/256 bits under ambient precision 32/64/256.
Eighteen nonzero-shift BigFloat cases check equal inexact bounds, unequal
neighbors separated by 2^-200, and equal exactly representable bounds. Stored
256-bit values must be rejected at ambient 32/64 when required; exact values
and 256-bit results must succeed. Two Float32/Float64 overflow fixtures must
reject without source changes. Their retained column has original degree one,
so no alternative pivot can conceal rejection.

Eight additional models accumulate two accepted shifts into the same private
equality bounds, covering free/bounded pivots and all four numeric types.
The six block probes check matrix/bounds/objective, primal/basis restoration,
objective equivalence and source preservation after ordinary output mutation.
Unequal-bound and zero-shift controls guard unaffected allocation paths.

The targeted suite passed **159,295/159,295 assertions** in 2m51.4s.

Independent differential review passed **3,584/3,584 assertions** across
150 models (140 accepted, 10 rejected), with 164 aggregation records, 140 row
removals, 24 projections, 450 primal restorations, 600 basis restorations and
12 rollback cases. Coverage includes all four numeric types, finite/unbounded
intervals, signed/zero/cancelled shifts, mixed stored BigFloat precision, repeated
private shifts and ordinary container replacement. Baseline outcomes and source
preservation matched; no findings.

The full project suite passed **178,792/178,792 assertions** in 7m06.2s.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
