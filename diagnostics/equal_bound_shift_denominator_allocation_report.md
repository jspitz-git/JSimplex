# Equal denominators in exact bound shifts

Round 171 changes only `_shift_bound_exact` in `src/presolve.jl`, a shared helper
used by basic presolve, free-doubleton substitution and sparse equality
aggregation. When the exact bound and nonzero shift have the same denominator,
it subtracts their numerators and constructs a canonical `Rational{BigInt}`
using that denominator. The constructor still reduces the result; this avoids
the general rational subtraction path's unnecessary denominator arithmetic.

Existing zero-shift, unbounded, zero-bound and exact-cancellation paths are
unchanged. Unequal denominators retain general subtraction. The final
`_represent_exact` gate still rejects overflow or inexact target values.
Zero shifts preserve the original bound, including signed zero and stored
BigFloat precision. Source values are not mutated; rejection, private updates
and postsolve behavior remain unchanged.

## Method and results

The baseline includes the preceding 170 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent blocks `pivot*x+3*y=rhs` and
`factor*x+5*y` in a specified row interval. Both columns are free, costs are
`[0,2]`, and the objective constant is seven. All 128 pivots are accepted and
the first equality rows are removed. Each finite retained row bound shifts
by `factor*rhs/pivot`. Construction is outside measurement; the measured call
runs the complete sparse aggregation pass.

- `positive` and `negative`: pivot ±2, RHS four, factor six and bounds
  `[-20,20]`. Both shifts have denominator one, matching the bounds.
- `fraction_positive` and `fraction_negative`: pivot ±2, RHS one, factor
  three and bounds `[-2.5,2.5]`. Both shift and bounds have denominator two.
- `unequal`: pivot two, RHS one, factor three and bounds `[-2,2]`.
  Shift and bound denominators differ, exercising general subtraction.
- `zero_shift`: pivot two, RHS zero, factor six and bounds `[-20,20]`.
  The helper returns the original bounds.

Each target performs 256 matching-denominator shifts. Both controls preserve
allocation counts.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive | 1,368,280 | 1,340,488 | 2.03% | 34,231 → 33,719 |
| negative | 1,369,928 | 1,342,584 | 2.00% | 34,231 → 33,719 |
| fraction_positive | 1,335,816 | 1,312,808 | 1.72% | 33,079 → 32,823 |
| fraction_negative | 1,335,624 | 1,312,728 | 1.71% | 33,079 → 32,823 |
| unequal | 1,340,088 | 1,340,152 | — | 33,335 → 33,335 |
| zero_shift | 969,064 | 969,256 | — | 23,479 → 23,479 |

Target allocated bytes decrease by **1.71–2.03%**.
Cross-process byte differences on unchanged paths alone establish no benefit.

- `positive` saves **512 allocations per call**, or 2 per bound shift.
- `negative` saves **512 allocations per call**, or 2 per bound shift.
- `fraction_positive` saves **256 allocations per call**, or 1 per bound shift.
- `fraction_negative` saves **256 allocations per call**, or 1 per bound shift.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,640 → 41,072 |
| afiro | sparse | 3,736 → 3,736 | 173,904 → 173,728 |
| afiro | propagation | 2,437 → 2,437 | 92,296 → 92,680 |
| afiro | presolve | 15,410 → 15,410 | 699,800 → 699,208 |
| afiro | dual | 16,225 → 16,225 | 835,688 → 835,272 |
| afiro | primal | 16,131 → 16,131 | 813,608 → 813,288 |
| afiro | dual_no_presolve | 555 → 555 | 89,936 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,776 → 121,776 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 1,572 → 1,572 | 127,272 → 128,456 |
| adlittle | propagation | 18,182 → 18,182 | 641,496 → 641,448 |
| adlittle | presolve | 80,377 → 80,377 | 3,259,048 → 3,258,296 |
| adlittle | dual | 82,392 → 82,392 | 4,050,344 → 4,047,768 |
| adlittle | primal | 83,190 → 83,190 | 4,326,968 → 4,324,232 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,320 → 461,432 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,728 → 607,408 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 104,920 → 106,008 |
| kb2 | sparse | 1,999 → 1,999 | 127,400 → 128,504 |
| kb2 | propagation | 12,948 → 12,948 | 454,736 → 454,400 |
| kb2 | presolve | 227,017 → 227,017 | 10,561,944 → 10,562,888 |
| kb2 | dual | 228,219 → 228,219 | 11,016,680 → 11,015,736 |
| kb2 | primal | 228,386 → 228,386 | 11,030,504 → 11,029,704 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,144 → 878,176 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 5,489 → 5,489 | 263,600 → 263,008 |
| sc50a | propagation | 6,020 → 6,020 | 222,960 → 221,888 |
| sc50a | presolve | 64,941 → 64,941 | 2,762,672 → 2,762,672 |
| sc50a | dual | 66,013 → 66,013 | 3,108,912 → 3,108,448 |
| sc50a | primal | 65,958 → 65,958 | 3,061,616 → 3,061,568 |
| sc50a | dual_no_presolve | 961 → 961 | 306,112 → 306,480 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 3,956 → 3,956 | 150,424 → 150,776 |
| flugpl | propagation | 3,253 → 3,253 | 123,536 → 122,752 |
| flugpl | presolve | 25,764 → 25,760 | 991,160 → 990,968 |
| flugpl | dual | 26,435 → 26,431 | 1,101,888 → 1,100,528 |
| flugpl | primal | 26,784 → 26,780 | 1,146,272 → 1,145,120 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save four allocations on flugpl.
The other 47 reference model/stage allocation counts are unchanged; none increase.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`equal-bound-shift-denominator-allocations-before.toml`](equal-bound-shift-denominator-allocations-before.toml)
and [`equal-bound-shift-denominator-allocations-after.toml`](equal-bound-shift-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=equal-bound-shift-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function equal_bound_shift_denominator_probe(kind; count=128, T=Float64)
    pivot=kind in (:negative,:fraction_negative) ? T(-2) : T(2)
    fractional=kind in (:fraction_positive,:fraction_negative,:unequal)
    rhs=kind==:zero_shift ? zero(T) : fractional ? one(T) : T(4)
    factor=fractional ? T(3) : T(6)
    upper=kind in (:fraction_positive,:fraction_negative) ? T(5)/2 : kind==:unequal ? T(2) : T(20)
    rows=collect(1:2:2count);other=rows.+1
    A=sparse(vcat(rows,rows,other,other),vcat(rows,other,rows,other),
        vcat(fill(pivot,count),fill(T(3),count),fill(factor,count),fill(T(5),count)),2count,2count)
    problem=LinearProblem(A,repeat(T[0,2],count);objective_constant=T(7),
        row_lower=[isodd(i) ? rhs : -upper for i in 1:2count],
        row_upper=[isodd(i) ? rhs : upper for i in 1:2count],
        column_lower=fill(nothing,2count),column_upper=fill(nothing,2count))
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:positive,:negative,:fraction_positive,:fraction_negative,:unequal,:zero_shift)
    problem, pass = equal_bound_shift_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **1,418 assertions** and failed only
the four target allocation guards; both controls passed. The file contains
**1,422 new assertions**, all passing after the change. Existing allocation
budgets were not relaxed.

Independent exact subtraction covers 396 finite-bound cases across Float32,
Float64, BigFloat and Rational{BigInt}, with signed, zero, equal-denominator
and unequal-denominator inputs. Forty-four unbounded cases preserve identity.
Forty-eight large rational cases include 300-bit numerators and denominators
5, 7, 15 and 21; results must remain canonical, including reducible differences.

Thirty BigFloat cases use bounds stored at 256 bits under ambient precision
32/64/256. Exact cancellation and representable results must succeed, while
inexact results must fail; zero shifts preserve the stored representation.
Float32/Float64 overflow and inexact-rounding cases must reject without source
changes; additional zero-shift cases preserve signed zero.

Twenty-four full-pass models cover the six probes and four numeric types,
checking matrix/bounds/objective, row removal, primal/basis restoration,
objective equivalence and source preservation after ordinary output mutation.

The targeted suite passed **160,717/160,717 assertions** in 2m53.1s.

Independent differential review passed **5,434/5,434 assertions**: 256 helper
cases and 158 aggregation models (148 accepted, 10 rejected), including 12
rollback cases, 474 primal and 632 basis restoration comparisons. Exact
matrix, bounds, objective, metadata and source preservation matched the saved
baseline. Coverage includes canonical large rationals, signed zero, overflow
and stored 256-bit BigFloat under ambient precisions 32/64/256. No findings.

The full project suite passed **180,214/180,214 assertions** in 7m08.0s.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
