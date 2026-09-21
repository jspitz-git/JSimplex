# Shared nonzero shifts of equal bounds in basic presolve

Round 172 changes only the row-bound shift block in `_presolve_basic` in
`src/presolve.jl`. When the shift is nonzero and the original lower/upper bounds
are exactly equal, the upper bound reuses the lower bound's `_shift_bound_exact`
result. This avoids repeating conversion, subtraction and exact representation
checks while removing fixed variables. If the lower shift fails with `nothing`,
that failure is reused and the existing guard rejects the elimination.

The equality flag is captured before either local bound is overwritten. The
existing any-finite-bound guard excludes fully unbounded pairs. Unequal bounds
retain independent shifts. Zero shifts retain both original objects: the
helper's identity path preserves signed-zero differences and distinct stored
BigFloat precisions even when the bounds compare numerically equal.

Exact representation checks, precomputed selections, accumulated private row
bounds, staged changes and rejection cleanup are unchanged. The shared result
is not mutated; ordinary output-container changes preserve the source model.

## Method and results

The baseline includes the preceding 171 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 rows `6*x+5*y` with specified row bounds. Variable
`x` is fixed, `y` is free, costs are `[0,2]`, and the objective constant is
seven. Basic presolve removes `x`, retains all rows and their coefficient five,
and shifts each finite row bound by `6*x`. Construction is outside measurement;
the measured call runs the complete basic presolve pass.

- `positive`: fixed value two, equal bounds 20, resulting bounds eight.
- `negative`: fixed value -2, equal bounds 16, resulting bounds 28.
- `cancelled`: fixed value two, equal bounds 12, resulting exact zero.
- `zero_bound`: fixed value two, equal bounds zero, resulting bounds -12.
- `unequal`: fixed value two and bounds `[-20,20]`, retaining independent shifts.
- `zero_shift`: fixed value zero and equal bounds 20, preserving both originals.

Each target reuses 128 upper-bound results. Both controls preserve allocation counts.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive | 446,688 | 287,696 | 35.59% | 11,476 → 7,124 |
| negative | 448,112 | 288,912 | 35.53% | 11,476 → 7,124 |
| cancelled | 398,336 | 263,664 | 33.81% | 9,940 → 6,356 |
| zero_bound | 309,424 | 218,944 | 29.24% | 7,124 → 4,948 |
| unequal | 448,144 | 449,264 | — | 11,476 → 11,476 |
| zero_shift | 28,648 | 28,648 | — | 81 → 81 |

Target allocated bytes decrease by **29.24–35.59%**.
Cross-process byte differences on unchanged paths alone establish no benefit.

- `positive` saves **4,352 allocations per call**, or 34 per reused bound.
- `negative` saves **4,352 allocations per call**, or 34 per reused bound.
- `cancelled` saves **3,584 allocations per call**, or 28 per reused bound.
- `zero_bound` saves **2,176 allocations per call**, or 17 per reused bound.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 41,888 → 41,568 |
| afiro | sparse | 3,736 → 3,736 | 173,648 → 173,920 |
| afiro | propagation | 2,437 → 2,437 | 93,528 → 93,416 |
| afiro | presolve | 15,410 → 15,410 | 698,968 → 699,480 |
| afiro | dual | 16,225 → 16,225 | 834,728 → 835,384 |
| afiro | primal | 16,131 → 16,131 | 812,888 → 813,384 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 1,572 → 1,572 | 127,768 → 128,024 |
| adlittle | propagation | 18,182 → 18,182 | 641,288 → 642,024 |
| adlittle | presolve | 80,377 → 80,377 | 3,257,992 → 3,258,648 |
| adlittle | dual | 82,392 → 82,392 | 4,046,584 → 4,046,856 |
| adlittle | primal | 83,190 → 83,190 | 4,322,904 → 4,323,560 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,864 → 461,656 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,360 → 607,328 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,272 → 105,448 |
| kb2 | sparse | 1,999 → 1,999 | 127,752 → 127,928 |
| kb2 | propagation | 12,948 → 12,948 | 454,176 → 454,720 |
| kb2 | presolve | 227,017 → 227,017 | 10,561,176 → 10,561,128 |
| kb2 | dual | 228,219 → 228,219 | 11,014,568 → 11,015,128 |
| kb2 | primal | 228,386 → 228,386 | 11,028,296 → 11,029,896 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,968 → 878,000 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,928 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 5,489 → 5,489 | 262,960 → 262,832 |
| sc50a | propagation | 6,020 → 6,020 | 222,800 → 222,896 |
| sc50a | presolve | 64,941 → 64,941 | 2,762,368 → 2,763,456 |
| sc50a | dual | 66,013 → 66,013 | 3,108,400 → 3,108,848 |
| sc50a | primal | 65,958 → 65,958 | 3,060,800 → 3,061,664 |
| sc50a | dual_no_presolve | 961 → 961 | 306,592 → 306,528 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 3,956 → 3,956 | 149,672 → 150,088 |
| flugpl | propagation | 3,253 → 3,253 | 123,664 → 123,872 |
| flugpl | presolve | 25,760 → 25,726 | 990,840 → 990,456 |
| flugpl | dual | 26,431 → 26,397 | 1,100,960 → 1,099,840 |
| flugpl | primal | 26,780 → 26,746 | 1,145,408 → 1,144,192 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save 34 allocations on flugpl.
The other 47 reference model/stage allocation counts are unchanged; none increase.
The flugpl benefit appears during the repeated presolve pipeline; standalone
basic presolve on its original input has no allocation-count change.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`basic-shared-shifted-bounds-allocations-before.toml`](basic-shared-shifted-bounds-allocations-before.toml)
and [`basic-shared-shifted-bounds-allocations-after.toml`](basic-shared-shifted-bounds-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=basic-shared-shifted-bounds-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function basic_shared_shifted_bounds_probe(kind; count=128, T=Float64)
    value=kind==:negative ? T(-2) : kind==:zero_shift ? zero(T) : T(2)
    upper=kind==:negative ? T(16) : kind==:cancelled ? T(12) : kind==:zero_bound ? zero(T) : T(20)
    lower=kind==:unequal ? T(-20) : upper
    problem=LinearProblem(sparse(hcat(fill(T(6),count),fill(T(5),count))),T[0,2];objective_constant=T(7),
        row_lower=fill(lower,count),row_upper=fill(upper,count),
        column_lower=[value,nothing],column_upper=[value,nothing])
    return problem,JSimplex._presolve_basic
end

for kind in (:positive,:negative,:cancelled,:zero_bound,:unequal,:zero_shift)
    problem, pass = basic_shared_shifted_bounds_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **3,509 assertions** and failed only
the four target allocation guards; both controls passed. The file contains
**3,513 new assertions**, all passing after the change. Existing allocation
budgets were not relaxed.

Independent exact interval translation covers 336 full-pass models across
Float32, Float64, BigFloat and Rational{BigInt}, signed/zero fixed values,
signed coefficients, equal/unequal/one-sided/free row bounds, and both ordinary
and precomputed elimination selections. Tests compare matrix, shifted bounds,
objective, elimination maps, primal/basis restoration, source and selections.

Zero-shift tests preserve Float32/Float64 -0.0 versus +0.0 and equal BigFloat
bounds stored separately at 128/256 bits under ambient precision 32/64/256.
Eighteen nonzero-shift BigFloat cases check equal inexact bounds, unequal
neighbors separated by 2^-200 and equal exactly representable bounds. Stored
256-bit values must be rejected at ambient 32/64 when required; exact values
and 256-bit results must succeed. Two Float32/Float64 overflow models must
reject without source changes.

Eight additional models accumulate two accepted shifts into the same private
equality bounds, with ordinary/precomputed selections and all four numeric
types. Twenty-four block-probe models check matrix/bounds/objective, primal/basis
restoration, objective equivalence and source preservation after ordinary output
mutation. Unequal-bound and zero-shift controls guard unchanged allocation paths.

The targeted suite passed **164,230/164,230 assertions** in 2m55.0s.

Independent differential review passed **3,183/3,183 assertions** across 136
models: 120 accepted reductions, 12 unchanged models and four PresolveFailure
outcomes. Coverage includes 68 cached-selection cases, 396 primal restorations,
528 basis restorations and eight staged rollbacks. Exact model, elimination map,
metadata, source preservation and stored BigFloat precision/sign snapshots
matched the AST-loaded saved baseline. No findings.

The full project suite passed **183,727/183,727 assertions** in 7m11.4s.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
