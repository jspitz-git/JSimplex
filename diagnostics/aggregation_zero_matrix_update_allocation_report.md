# Preserve matrix coefficients directly for zero substitution multipliers

Round 94 changes one matrix-update expression in sparse equality aggregation.
A zero exact multiplier reuses `old_value`, avoiding conversion of the equality
term, multiplication by zero, and subtraction of zero. Nonzero multipliers
retain the original arithmetic.

The current coefficient is still fetched from `matrix_updates` before taking
the shortcut, so prior committed substitutions remain visible. The reused
value still passes the exact representability check and is staged normally.
This preserves rejection under reduced BigFloat precision and prevents partial
updates from rejected candidates. Objective updates, bound shifts, candidate
selection, and restoration are unchanged; reused rationals are not mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 93 allocation rounds. All 41 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each target has 128 equalities `c*x[i] + y = 5`, with pivot `c=2` or `c=-2`,
zero-cost `x[i]` bounded by `[1,3]`, free `y` with cost two, and objective
constant seven. The extra row contains an explicitly stored zero in every
pivot column and a `y` coefficient of two or zero, with upper bound 1000.
Stored zeros give each pivot column degree two, but its substitution multiplier
in the extra row is zero. The last row's coefficient and bound remain unchanged.
The four targets cover both pivot signs and zero/nonzero old coefficients.

The nonzero-multiplier control replaces those stored pivot-column zeros with
two and uses positive pivots. The singleton control omits the extra row,
exercising a pass unaffected by this change. The targets deliberately retain
stored zeros; matrices without these entries do not trigger this shortcut.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Pivot 2, old coefficient 2 | 1,237,464 | 1,107,448 | 10.51% | 32,726 → 29,142 |
| Pivot -2, old coefficient 2 | 1,239,480 | 1,109,128 | 10.52% | 32,726 → 29,142 |
| Pivot 2, old coefficient 0 | 1,227,720 | 1,099,320 | 10.46% | 32,207 → 28,751 |
| Pivot -2, old coefficient 0 | 1,227,528 | 1,099,496 | 10.43% | 32,207 → 28,751 |
| Nonzero-multiplier control | 1,432,424 | 1,431,480 | — | 38,228 → 38,228 |
| Singleton-pass control | 806,248 | 804,648 | — | 20,480 → 20,480 |

Targets with old coefficient two remove 3,584 allocations (28 per update);
targets with old coefficient zero remove 3,456 (27 per update). Both controls
retain their allocation counts; byte differences on unchanged paths alone
establish no benefit.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 44,224 → 45,088 | 843 → 843 | 240,280 → 239,880 | 5,517 → 5,517 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 177,776 → 177,760 | 2,861 → 2,861 |
| kb2 | 111,616 → 112,368 | 2,060 → 2,060 | 166,160 → 165,872 | 2,958 → 2,958 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 332,656 → 332,304 | 7,434 → 7,434 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 216,776 → 216,488 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 749,072 → 746,816 | 883,456 → 883,136 | 861,872 → 860,816 | 0 |
| adlittle | 3,357,696 → 3,353,872 | 4,148,064 → 4,144,224 | 4,425,008 → 4,421,152 | 0 |
| kb2 | 10,685,064 → 10,681,064 | 11,138,104 → 11,134,328 | 11,150,904 → 11,149,576 | 0 |
| sc50a | 2,898,440 → 2,896,088 | 3,244,600 → 3,241,992 | 3,197,128 → 3,194,648 | 0 |
| flugpl | 1,207,216 → 1,205,200 | 1,317,336 → 1,314,552 | 1,361,816 → 1,359,224 | 0 |

All five fixtures retain their allocation counts for both aggregation passes,
full presolve, and both whole solves. The measured benefit is confined to the
probes retaining explicit zeros in the pivot columns.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-zero-matrix-update-allocations-before.toml`](aggregation-zero-matrix-update-allocations-before.toml)
and [`aggregation-zero-matrix-update-allocations-after.toml`](aggregation-zero-matrix-update-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-zero-matrix-update-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-zero-matrix-update-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_zero_matrix_update_probe(kind; count=128)
    pivot = kind in (:negative_present,:negative_absent) ? -2.0 : 2.0
    stored = kind == :nonzero ? 2.0 : 0.0
    old_coefficient = kind in (:positive_absent,:negative_absent) ? 0.0 : 2.0
    rows = vcat(collect(1:count),fill(count+1,count),collect(1:count),count+1)
    columns = vcat(collect(1:count),collect(1:count),fill(count+1,count+1))
    values = vcat(fill(pivot,count),fill(stored,count),ones(count),old_coefficient)
    A = sparse(rows,columns,values,count+1,count+1)
    lower = vcat(fill(5.0,count),nothing)
    upper = vcat(fill(5.0,count),1000.0)
    if kind == :singleton
        A = A[1:count,:]; lower = lower[1:count]; upper = upper[1:count]
    end
    problem = LinearProblem(A,vcat(zeros(count),2.0);objective_constant=7.0,
        row_lower=lower,row_upper=upper,column_lower=vcat(fill(1.0,count),nothing),
        column_upper=vcat(fill(3.0,count),nothing))
    pass = kind == :singleton ? JSimplex.aggregate_singleton_equalities : JSimplex.aggregate_sparse_equalities
    return problem,pass
end
for kind in (:positive_present, :negative_present, :positive_absent,
             :negative_absent, :nonzero, :singleton)
    problem, pass = aggregation_zero_matrix_update_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 954 assertions and failed the
four target allocation guards. Nonzero-old-coefficient probes allocated
32,771 and 32,734 objects, exceeding 31,500; zero-old-coefficient probes
allocated 32,215 each, exceeding 31,000. Both controls passed. All 958 new
assertions now pass as part of 12,131 targeted aggregation and presolve
assertions. Existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; pivots ±2;
signed/fractional equality terms; zero/nonzero old coefficients; implied and
projected pivot bounds; matrix entries, costs, constants, row bounds, primal
restoration, and unchanged source storage/bounds. Sequential substitutions mix
zero/nonzero multipliers in both orders and retain the current matrix value.

Stored 256-bit old coefficients 3 ± 2^-200 under ambient precision 32/64 remain
unrepresentable and must still reject aggregation. Tiny nonzero multipliers
produce accepted exact coefficient changes. The smallest nonzero Float32/64
stored coefficients divided by pivots ±2 produce unrepresentable matrix
changes with a zero right-hand side, isolating matrix rejection from bound
shifting. These cases guard against skipping representability checks or
mistaking a tiny nonzero multiplier for zero.

An independent read-only review found no issues. It reran all 958 focused
assertions and passed 1,472 additional baseline comparisons across 88 models
and 352 basis restorations. It covered stored CSC zeros, implied/projected
bounds, sequential zero/nonzero updates in both orders, precision rejection
of unchanged BigFloat entries, tiny nonzero updates, underflow rejection,
and source/primal/basis immutability.

The complete `test/runtests.jl` suite passed 37,527/37,527 assertions in
5m10.2s (exit code zero), including all existing allocation guards.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
