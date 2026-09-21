# Shared nonzero shifts of equal bounds in doubleton substitution

Round 173 changes only the row-bound shift block in `substitute_free_doubleton`
in `src/presolve_substitution.jl`. When the shift is nonzero and the original
lower/upper bounds are exactly equal, the upper bound reuses the lower bound's
`_shift_bound_exact` result. This avoids repeating conversion, subtraction and
exact representation checks. If the lower shift fails with `nothing`, that
failure is reused and the existing guard rejects the candidate substitution.

The equality flag is captured before either local bound is overwritten. The
existing any-finite-bound guard excludes fully unbounded pairs. Unequal bounds
retain independent shifts. Zero shifts retain both original objects: the
helper's identity path preserves signed-zero differences and distinct stored
BigFloat precisions even when the bounds compare numerically equal.

Exact representation gates, private matrix/bound copies, candidate selection,
rollback, row/column removal and postsolve remain unchanged. Reused exact values
are not mutated; ordinary output-container changes preserve the source model.

## Method and results

The baseline includes the preceding 172 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains one equality `pivot*x+3*y=rhs` followed by 128 rows
`6*x+5*y` with specified row bounds. Variable `x` is free, `y` has bounds
`[-10,10]`, costs are `[0,2]`, and the objective constant is seven. Substitution
removes `x` and the first equality, retains the other rows with coefficient
`5-18/pivot`, and shifts their bounds by `6*rhs/pivot`. Construction is outside
measurement; the measured call runs the complete free-doubleton substitution.

- `positive`: pivot two, RHS four, equal bounds 20, resulting bounds eight.
- `negative`: pivot -2, RHS four, equal bounds 16, resulting bounds 28.
- `cancelled`: pivot two, RHS four, equal bounds 12, resulting exact zero.
- `zero_bound`: pivot two, RHS four, equal bounds zero, resulting bounds -12.
- `unequal`: pivot two, RHS four and bounds `[-20,20]`, retaining independent shifts.
- `zero_shift`: pivot two, RHS zero and equal bounds 20, preserving both originals.

Each target reuses 128 upper-bound results. Both controls preserve allocation counts.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive | 660,312 | 496,984 | 24.73% | 17,114 → 12,762 |
| negative | 661,208 | 497,944 | 24.69% | 17,114 → 12,762 |
| cancelled | 611,320 | 472,904 | 22.64% | 15,578 → 11,994 |
| zero_bound | 522,920 | 428,984 | 17.96% | 12,762 → 10,586 |
| unequal | 661,592 | 657,672 | — | 17,114 → 17,114 |
| zero_shift | 296,552 | 293,976 | — | 7,243 → 7,243 |

Target allocated bytes decrease by **17.96–24.73%**.
Cross-process byte differences on unchanged paths alone establish no benefit.

- `positive` saves **4,352 allocations per call**, or 34 per reused bound.
- `negative` saves **4,352 allocations per call**, or 34 per reused bound.
- `cancelled` saves **3,584 allocations per call**, or 28 per reused bound.
- `zero_bound` saves **2,176 allocations per call**, or 17 per reused bound.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,384 → 40,720 |
| afiro | sparse | 3,736 → 3,736 | 175,664 → 173,216 |
| afiro | propagation | 2,437 → 2,437 | 93,688 → 91,992 |
| afiro | presolve | 15,410 → 15,410 | 702,024 → 698,760 |
| afiro | dual | 16,225 → 16,225 | 837,688 → 834,136 |
| afiro | primal | 16,131 → 16,131 | 815,112 → 812,264 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 1,572 → 1,572 | 127,128 → 127,624 |
| adlittle | propagation | 18,182 → 18,182 | 643,832 → 641,032 |
| adlittle | presolve | 80,377 → 80,377 | 3,261,640 → 3,257,368 |
| adlittle | dual | 82,392 → 82,392 | 4,052,376 → 4,046,600 |
| adlittle | primal | 83,190 → 83,190 | 4,329,672 → 4,323,176 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,384 → 461,336 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,520 → 607,744 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,080 → 105,368 |
| kb2 | sparse | 1,999 → 1,999 | 127,560 → 127,832 |
| kb2 | propagation | 12,948 → 12,948 | 457,056 → 454,288 |
| kb2 | presolve | 227,017 → 227,017 | 10,565,128 → 10,562,024 |
| kb2 | dual | 228,219 → 228,219 | 11,019,032 → 11,013,960 |
| kb2 | primal | 228,386 → 228,386 | 11,033,544 → 11,027,912 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,968 → 877,920 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,944 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 5,489 → 5,489 | 264,624 → 262,608 |
| sc50a | propagation | 6,020 → 6,020 | 224,672 → 221,872 |
| sc50a | presolve | 64,941 → 64,941 | 2,764,736 → 2,761,856 |
| sc50a | dual | 66,013 → 66,013 | 3,109,488 → 3,108,208 |
| sc50a | primal | 65,958 → 65,958 | 3,062,272 → 3,060,816 |
| sc50a | dual_no_presolve | 961 → 961 | 306,128 → 306,288 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,232 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 3,956 → 3,956 | 151,544 → 150,360 |
| flugpl | propagation | 3,253 → 3,253 | 124,576 → 123,200 |
| flugpl | presolve | 25,726 → 25,726 | 992,136 → 988,792 |
| flugpl | dual | 26,397 → 26,397 | 1,102,624 → 1,099,248 |
| flugpl | primal | 26,746 → 26,746 | 1,146,848 → 1,143,472 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All 50 reference model/stage allocation counts are unchanged. The measured
benefit is confined to the targeted equal-bound substitution probes.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`doubleton-shared-shifted-bounds-allocations-before.toml`](doubleton-shared-shifted-bounds-allocations-before.toml)
and [`doubleton-shared-shifted-bounds-allocations-after.toml`](doubleton-shared-shifted-bounds-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-shared-shifted-bounds-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_shared_shifted_bounds_probe(kind; count=128, T=Float64)
    pivot=kind==:negative ? T(-2) : T(2)
    rhs=kind==:zero_shift ? zero(T) : T(4)
    upper=kind==:negative ? T(16) : kind==:cancelled ? T(12) : kind==:zero_bound ? zero(T) : T(20)
    lower=kind==:unequal ? T(-20) : upper
    A=sparse(hcat(vcat(pivot,fill(T(6),count)),vcat(T(3),fill(T(5),count))))
    problem=LinearProblem(A,T[0,2];objective_constant=T(7),
        row_lower=vcat(rhs,fill(lower,count)),row_upper=vcat(rhs,fill(upper,count)),
        column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end

for kind in (:positive,:negative,:cancelled,:zero_bound,:unequal,:zero_shift)
    problem, pass = doubleton_shared_shifted_bounds_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **3,145 assertions** and failed only
the four target allocation guards; both controls passed. The file contains
**3,149 new assertions**, all passing after the change. Existing allocation
budgets were not relaxed.

Independent exact interval translation covers 336 full-pass models across
Float32, Float64, BigFloat and Rational{BigInt}, signed unit/nonunit pivots,
zero/signed RHS and equal/unequal/one-sided/free row bounds. Tests compare
matrix, shifted bounds, objective, selected substitution, primal/basis restoration
and source preservation. The retained variable is bounded so another pivot
cannot conceal a rejection.

Zero-shift tests preserve Float32/Float64 -0.0 versus +0.0 and equal BigFloat
bounds stored separately at 128/256 bits under ambient precision 32/64/256.
Eighteen nonzero-shift BigFloat cases check equal inexact bounds, unequal
neighbors separated by 2^-200 and equal exactly representable bounds. Stored
256-bit values must be rejected at ambient 32/64 when required; exact values
and 256-bit results must succeed. Two Float32/Float64 overflow models must
reject without source changes. Affected rows in these rejection fixtures contain
only the eliminated column, preventing a later equality from hiding rejection.

Four additional Float32/Float64 models reject the first candidate after a
successful private equal-bound shift, then accept a later independent candidate.
They verify that neither staged matrix entries nor bounds leak into the result,
including failure of the upper bound after a representable lower-bound shift.
Twenty-four probe models check matrix/bounds/objective, primal/basis restoration,
objective equivalence and source preservation after ordinary output mutation.
Unequal-bound and zero-shift controls guard unchanged allocation paths.

The targeted suite passed **167,379/167,379 assertions** in 2m58.9s.

Independent differential review passed **4,277/4,277 assertions** across 152
models: 140 accepted substitutions and 12 unchanged/rejected cases. Coverage
includes 456 primal restorations, 608 basis restorations and eight staged
rollbacks, with exact matrix, bounds, objective, metadata, substitution step,
source and ordinary output-container mutation comparisons. All matched the
AST-loaded saved baseline, including stored BigFloat precision. No findings.

The full project suite passed **186,876/186,876 assertions** in 7m12.1s.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
