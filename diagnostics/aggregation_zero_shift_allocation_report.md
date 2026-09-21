# Reuse exact zero factors as sparse aggregation shifts

Round 92 changes the shift product in sparse equality aggregation. A zero
exact right-hand side is used directly as the shift. Otherwise a zero exact
multiplier is used directly; two nonzero factors retain their exact product.
Both zero checks follow the existing exact conversions.

The bound-shift helper already returns its input bound unchanged for a zero
shift. This change avoids constructing that zero by multiplication while
preserving the helper's behavior, including stored BigFloat precision.
Multiplier calculation, matrix updates, objective updates, representability
checks, candidate selection, staging, and restoration remain unchanged.
Reusing a rational value does not mutate its source.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 91 allocation rounds. All 41 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each target probe has 128 equalities `c*x[i] + y = 0`, with pivot `c=1` or
`c=-1`, zero-cost `x[i]` bounded by `[1,3]`, and a free shared `y` with cost
two. An extra row `d*sum(x) + 2*y <= 1000`, with `d=2` or `d=-2`, gives each
pivot column degree two. Every substitution has a zero right-hand side and
therefore a zero bound shift. After all eliminations, the last row has
coefficient `2 - 128*d/c` and retains upper bound 1000. The objective constant
starts and ends at seven.

The nonzero-shift control uses the same sparse probe with `c=1,d=2` and right-
hand side five. The singleton control uses `c=1`, right-hand side zero, and
omits the extra row, exercising a pass unaffected by this change.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Pivot 1, other coefficient 2 | 1,128,568 | 1,088,712 | 3.53% | 30,036 → 29,140 |
| Pivot 1, other coefficient -2 | 1,129,984 | 1,090,512 | 3.49% | 30,039 → 29,143 |
| Pivot -1, other coefficient 2 | 1,151,808 | 1,112,128 | 3.45% | 30,807 → 29,911 |
| Pivot -1, other coefficient -2 | 1,151,880 | 1,112,056 | 3.46% | 30,804 → 29,908 |
| Nonzero-shift control | 1,389,640 | 1,389,160 | — | 37,070 → 37,070 |
| Singleton-pass control | 679,992 | 679,704 | — | 17,152 → 17,152 |

Each target removes 896 allocations (seven per substitution). Both controls
retain their allocation counts; byte differences on unchanged paths alone
establish no benefit.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 44,688 → 44,832 | 843 → 843 | 243,584 → 240,416 | 5,587 → 5,524 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 177,664 → 177,936 | 2,861 → 2,861 |
| kb2 | 112,240 → 112,496 | 2,060 → 2,060 | 169,232 → 166,256 | 3,028 → 2,958 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 342,128 → 332,208 | 7,651 → 7,434 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 216,568 → 216,344 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 750,704 → 747,872 | 886,032 → 882,880 | 864,096 → 861,024 | 49 |
| adlittle | 3,357,632 → 3,356,688 | 4,147,136 → 4,145,232 | 4,424,704 → 4,421,824 | 0 |
| kb2 | 10,688,024 → 10,683,864 | 11,143,400 → 11,136,344 | 11,156,872 → 11,148,584 | 56 |
| sc50a | 2,914,744 → 2,897,432 | 3,261,128 → 3,243,928 | 3,213,768 → 3,196,936 | 378 |
| flugpl | 1,205,520 → 1,205,728 | 1,315,560 → 1,315,128 | 1,360,008 → 1,359,544 | 0 |

Full presolve and both whole solves remove 49 allocations for afiro, 56 for
kb2, and 378 for sc50a. Adlittle and flugpl retain their counts. Singleton
aggregation retains its allocation count on all five fixtures.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-zero-shift-allocations-before.toml`](aggregation-zero-shift-allocations-before.toml)
and [`aggregation-zero-shift-allocations-after.toml`](aggregation-zero-shift-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-zero-shift-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-zero-shift-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_zero_shift_probe(kind; count=128)
    coefficient = kind in (:negative_positive,:negative_negative) ? -1.0 : 1.0
    other_coefficient = kind in (:positive_negative,:negative_negative) ? -2.0 : 2.0
    A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
    rhs = kind == :nonzero ? 5.0 : 0.0
    row_lower = Union{Nothing,Float64}[rhs for _ in 1:count]
    row_upper = fill(rhs,count)
    if kind != :singleton
        A = vcat(A,sparse(reshape(vcat(fill(other_coefficient,count),2.0),1,count+1)))
        push!(row_lower,nothing); push!(row_upper,1000.0)
    end
    problem = LinearProblem(A,vcat(zeros(count),2.0);objective_constant=7.0,
        row_lower,row_upper,column_lower=vcat(fill(1.0,count),nothing),
        column_upper=vcat(fill(3.0,count),nothing))
    pass = kind == :singleton ? JSimplex.aggregate_singleton_equalities : JSimplex.aggregate_sparse_equalities
    return problem,pass
end
for kind in (:positive_positive, :positive_negative, :negative_positive,
             :negative_negative, :nonzero, :singleton)
    problem, pass = aggregation_zero_shift_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 994 assertions and failed the
four target allocation guards. Positive-pivot probes allocated 30,081 and
30,047 objects, exceeding 29,500; negative-pivot probes allocated 30,815 and
30,812, exceeding 30,250. Both controls passed. All 998 new
assertions now pass as part of 9,895 targeted aggregation and presolve
assertions. Existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; both unit
pivot signs; signed and explicitly stored zero off-pivot coefficients; lower,
upper, two-sided, and unbounded other rows. Zero right-hand sides preserve
bounds while matrix substitution proceeds. Tests check matrix entries,
objectives, primal restoration, and unchanged source matrices/bounds.

Stored 256-bit BigFloat bounds 7 ± 2^-200 under ambient precision 32/64 are
retained exactly with their stored precision when either the right-hand side
or the multiplier is zero. Nonzero factors ±2^-200 produce accepted exact
tiny shifts. The smallest nonzero Float32/Float64 right-hand sides with
multiplier ±1/2 produce unrepresentable shifts and must still reject the only
eligible pivot. These cases guard against approximate zero checks and
floating-point underflow changing a shift into zero.

An independent read-only review found no issues. It reran all 998 focused
assertions and passed 1,620 additional baseline comparisons across 92 models
and 368 basis cases. It verified stored CSC zeros, projected bounds, sequential
mixed shifts, preserved BigFloat precision, tiny nonzero shifts, underflow
rejection, and staged rejection before a subsequent accepted candidate.
Complete results and source/primal/basis immutability matched the baseline.

The complete `test/runtests.jl` suite passed 35,291/35,291 assertions in
5m09.4s (exit code zero), including all existing allocation guards.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
