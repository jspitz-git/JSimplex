# Zero RHS in implied-bound differences

Round 165 changes only the lower/upper difference calculation in
`_equality_implies_column_bounds` in `src/presolve_aggregation.jl`. When the RHS
is exactly zero and the selected activity is nonzero, `0-activity` is computed
by exact rational negation. This avoids numerator subtraction and rational
normalization for integer activities, or general rational subtraction for
fractional activities.

The existing zero-activity path and exact-cancellation guards retain precedence.
Nonzero RHS values, including tiny stored BigFloat values, keep the existing
subtraction paths. Candidate division, separate bound comparisons, one-sided
activity selection, shared candidates, representation gates, staged updates,
rollback and postsolve are unchanged. No approximate zero check is introduced;
shared exact activity values are not mutated.

## Method and results

The baseline includes the preceding 164 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent blocks `pivot*x+term*y=rhs` and
`6*x+5*y<=100`, with x in `[-8,8]`, cost `[0,2]` and objective constant seven.
All 128 pivots are accepted and all equality rows are removed. The second row
has coefficient `5-6*term/pivot` and upper bound `100-6*rhs/pivot`; the objective
is unchanged. Measurement includes the full sparse aggregation pass, with input
construction outside measurement.

The four targets use RHS zero, y in `[1,3]`, pivot +2/-2 and term three or one
half. Their distinct minimum/maximum activities require two separate candidate
calculations per block, so there are 256 optimized differences per call.
The `nonzero_rhs` control uses RHS four, pivot two and term three; the
`zero_activity` control uses RHS zero with y fixed to zero. Both preserve their
allocation counts.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive | 1,487,672 | 1,444,248 | 2.92% | 40,503 → 39,223 |
| negative | 1,489,640 | 1,446,232 | 2.91% | 40,503 → 39,223 |
| fraction_positive | 1,571,672 | 1,501,576 | 4.46% | 42,295 → 40,503 |
| fraction_negative | 1,572,056 | 1,501,448 | 4.49% | 42,295 → 40,503 |
| nonzero_rhs | 1,715,240 | 1,717,016 | — | 46,647 → 46,647 |
| zero_activity | 1,207,160 | 1,208,872 | — | 31,543 → 31,543 |

Target allocated bytes decrease by **2.91–4.49%**.
Cross-process byte differences on unchanged paths alone establish no benefit.

- `positive` saves **1,280 allocations per call**, or 5 per optimized difference.
- `negative` saves **1,280 allocations per call**, or 5 per optimized difference.
- `fraction_positive` saves **1,792 allocations per call**, or 7 per optimized difference.
- `fraction_negative` saves **1,792 allocations per call**, or 7 per optimized difference.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 41,440 → 40,928 |
| afiro | sparse | 4,116 → 4,116 | 184,904 → 185,432 |
| afiro | propagation | 2,437 → 2,437 | 92,568 → 92,664 |
| afiro | presolve | 15,626 → 15,626 | 705,064 → 706,120 |
| afiro | dual | 16,441 → 16,441 | 840,616 → 841,272 |
| afiro | primal | 16,347 → 16,347 | 818,520 → 819,320 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,282 → 2,282 | 154,568 → 154,952 |
| adlittle | propagation | 18,182 → 18,182 | 640,536 → 641,800 |
| adlittle | presolve | 81,251 → 81,251 | 3,282,832 → 3,285,056 |
| adlittle | dual | 83,266 → 83,266 | 4,072,896 → 4,073,296 |
| adlittle | primal | 84,064 → 84,064 | 4,349,344 → 4,349,920 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,144 → 461,720 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,664 → 607,536 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,336 → 105,352 |
| kb2 | sparse | 2,207 → 2,207 | 135,400 → 135,416 |
| kb2 | propagation | 12,948 → 12,948 | 453,744 → 454,896 |
| kb2 | presolve | 227,463 → 227,441 | 10,576,032 → 10,574,664 |
| kb2 | dual | 228,665 → 228,643 | 11,026,432 → 11,027,592 |
| kb2 | primal | 228,832 → 228,810 | 11,042,176 → 11,042,008 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,080 → 878,016 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,081 → 6,081 | 278,960 → 280,160 |
| sc50a | propagation | 6,020 → 6,020 | 221,200 → 222,800 |
| sc50a | presolve | 66,097 → 66,097 | 2,795,592 → 2,796,200 |
| sc50a | dual | 67,169 → 67,169 | 3,141,720 → 3,141,848 |
| sc50a | primal | 67,114 → 67,114 | 3,094,232 → 3,094,424 |
| sc50a | dual_no_presolve | 961 → 961 | 306,128 → 306,656 |
| sc50a | primal_no_presolve | 964 → 964 | 232,184 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 4,646 → 4,484 | 172,072 → 166,456 |
| flugpl | propagation | 3,253 → 3,253 | 123,056 → 123,328 |
| flugpl | presolve | 27,926 → 27,356 | 1,057,464 → 1,036,328 |
| flugpl | dual | 28,597 → 28,027 | 1,166,608 → 1,145,584 |
| flugpl | primal | 28,946 → 28,376 | 1,211,136 → 1,189,840 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,728 |

Full presolve and each solve with presolve save 22 allocations on kb2 and 570
on flugpl. Standalone sparse aggregation saves 162 on flugpl. The other 43
reference model/stage allocation counts are unchanged; none increase.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-zero-rhs-allocations-before.toml`](aggregation-implied-zero-rhs-allocations-before.toml)
and [`aggregation-implied-zero-rhs-allocations-after.toml`](aggregation-implied-zero-rhs-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-zero-rhs-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_zero_rhs_probe(kind; count=128, T=Float64)
    pivot=kind in (:negative,:fraction_negative) ? T(-2) : T(2)
    term=kind in (:fraction_positive,:fraction_negative) ? T(1)/2 : T(3)
    low=kind==:zero_activity ? zero(T) : one(T)
    high=kind==:zero_activity ? zero(T) : T(3)
    rhs=kind==:nonzero_rhs ? T(4) : zero(T)
    xlo=T(-8);xhi=T(8)
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

for kind in (:positive,:negative,:fraction_positive,:fraction_negative,:nonzero_rhs,:zero_activity)
    problem, pass = aggregation_implied_zero_rhs_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **3,514 assertions** and failed only
the four target allocation guards; both controls passed. After the change, all
**3,518 new assertions** passed. Existing allocation budgets were not relaxed.

An independent endpoint oracle covers 1,200 helper models across Float32,
Float64, BigFloat and Rational{BigInt}, signed pivots/RHS, fixed/variable and
unbounded retained endpoints, cancellation and finite/free/one-sided pivot
bounds. The ±1000 witnesses suffice for these small bounded-size fixtures.

BigFloat cases store retained endpoints `2+2^-200` and `2+2*2^-200` at 256 bits,
with RHS exactly zero or ±`2^-200`. A single lower/upper pivot bound is displaced
by -1, 0 or +1 times `2^-200` from the independently derived exact endpoint,
then checked at ambient precision 32/64/256. This distinguishes tiny nonzero RHS
values from zero and catches a reversed endpoint. Signed unit/nonunit pivots
are covered. Large rational retained values have 300-bit numerators and
denominators 5, 7, 15 or 21; a bound displacement of `2^-350` must change the proof.

Full aggregation checks cover matrix/bounds/objective, row removal, primal/basis
restoration, objective equivalence and source preservation after ordinary output
mutation. Nonzero-RHS and zero-activity controls reject allocation regressions in
unaffected paths.

The targeted suite passed **145,582/145,582 assertions** in 2m47.4s.

Independent differential review passed **70,494/70,494 assertions** across
2,260 models (2,120 accepted, 140 rejected), including 6,420 helper checks
against the baseline and an independent interval oracle, 1,294 row removals,
826 projections, 6,780 primal restorations, 9,040 basis restorations and eight
rollback cases. The review included stored-256-bit BigFloat zero/±2^-200 RHS
at ambient 32/64/256, huge rationals, source preservation and canonical output.
Both the baseline helper and aggregation caller were renamed independently;
no findings.

The full project suite passed **165,079/165,079 assertions** in 7m00.3s.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
