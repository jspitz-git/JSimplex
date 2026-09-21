# Negate sparse fill products when the current coefficient is zero

Round 96 changes the final subtraction in sparse equality matrix updates.
For a nonzero multiplier, the exact product is computed as before. If the
current exact coefficient is zero, the candidate value is the negated product;
otherwise the existing subtraction remains in place.

The zero check uses the current value fetched from `matrix_updates`, preserving
both prior nonzero updates and cancellation to zero. All arithmetic remains
exact, including negation under reduced ambient BigFloat precision. The
zero-multiplier shortcut, product calculation, representability checks,
staging, bounds, objectives, and restoration are unchanged. Reused values
are not mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 95 allocation rounds. All 41 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each probe has 128 independent pairs of rows: `2*x[i] + t*y[i] = 5` and
`2*m*x[i] + old*y[i] <= 20`. Each `x[i]` has zero cost and bounds `[1,3]`;
all `y[i]` are free with cost two, and the objective constant is seven.
Targets use `old=0`, so the y coefficient in the second row is structurally
absent before aggregation and becomes `-m*t`. The four targets cover `m=±2`
and `t=±3`. Each substitution shifts its second-row upper bound to `20-5*m`.

Independent row pairs keep the current coefficient zero at all 128 update
sites. The nonzero-old control uses `old=2,m=2,t=3`; the zero-multiplier control
uses `old=0,m=0,t=3` and retains explicit zero entries in the pivot columns.
Both controls retain their existing arithmetic paths.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Multiplier 2, term 3 | 1,801,680 | 1,765,632 | 2.00% | 46,149 → 45,253 |
| Multiplier 2, term -3 | 1,804,704 | 1,768,704 | 1.99% | 46,149 → 45,253 |
| Multiplier -2, term 3 | 1,804,944 | 1,768,624 | 2.01% | 46,149 → 45,253 |
| Multiplier -2, term -3 | 1,804,592 | 1,768,576 | 2.00% | 46,149 → 45,253 |
| Nonzero-old-coefficient control | 1,820,176 | 1,819,952 | — | 46,661 → 46,661 |
| Zero-multiplier control | 1,397,000 | 1,396,888 | — | 35,001 → 35,001 |

Each target removes 896 allocations (seven per update). Both controls retain
their allocation counts; byte differences on unchanged paths alone establish
no benefit.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 44,704 → 44,704 | 843 → 843 | 228,528 → 218,256 | 5,241 → 5,003 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 176,160 → 176,976 | 2,843 → 2,843 |
| kb2 | 111,936 → 112,096 | 2,060 → 2,060 | 162,928 → 161,008 | 2,903 → 2,836 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 314,368 → 299,632 | 7,011 → 6,647 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 215,976 → 216,648 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 739,088 → 732,200 | 874,928 → 868,056 | 852,288 → 846,264 | 161 |
| adlittle | 3,354,224 → 3,353,568 | 4,144,512 → 4,143,456 | 4,421,856 → 4,420,064 | 0 |
| kb2 | 10,681,752 → 10,678,936 | 11,136,600 → 11,132,392 | 11,149,384 → 11,145,864 | 50 |
| sc50a | 2,875,848 → 2,853,744 | 3,221,480 → 3,198,416 | 3,174,856 → 3,151,488 | 507 |
| flugpl | 1,204,560 → 1,204,976 | 1,314,216 → 1,314,696 | 1,358,792 → 1,359,400 | 0 |

Full presolve and both whole solves remove 161 allocations for afiro, 50 for
kb2, and 507 for sc50a. Adlittle and flugpl retain their counts. Singleton
aggregation retains its count on all five fixtures.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-zero-old-matrix-allocations-before.toml`](aggregation-zero-old-matrix-allocations-before.toml)
and [`aggregation-zero-old-matrix-allocations-after.toml`](aggregation-zero-old-matrix-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-zero-old-matrix-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-zero-old-matrix-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_zero_old_matrix_probe(kind; count=128)
    multiplier = kind in (:negative_positive,:negative_negative) ? -2.0 : kind == :zero_multiplier ? 0.0 : 2.0
    term = kind in (:positive_negative,:negative_negative) ? -3.0 : 3.0
    old = kind == :nonzero_old ? 2.0 : 0.0
    odd = collect(1:2:2count); even = odd .+ 1
    rows = vcat(odd,odd,even); columns = vcat(odd,even,odd)
    values = vcat(fill(2.0,count),fill(term,count),fill(2multiplier,count))
    if !iszero(old)
        append!(rows,even); append!(columns,even); append!(values,fill(old,count))
    end
    A = sparse(rows,columns,values,2count,2count)
    lower = Union{Nothing,Float64}[isodd(i) ? 5.0 : nothing for i in 1:2count]
    upper = [isodd(i) ? 5.0 : 20.0 for i in 1:2count]
    problem = LinearProblem(A,[isodd(i) ? 0.0 : 2.0 for i in 1:2count];objective_constant=7.0,
        row_lower=lower,row_upper=upper,
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end
for kind in (:positive_positive, :positive_negative, :negative_positive,
             :negative_negative, :nonzero_old, :zero_multiplier)
    problem, pass = aggregation_zero_old_matrix_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 738 assertions and failed the
four target allocation guards. The four targets allocated 46,194,
46,157, 46,157, and 46,157 objects, each exceeding 45,550. Both controls passed. All 742 new
assertions now pass as part of 14,247 targeted aggregation and presolve
assertions. Existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; signed unit,
nonunit, and fractional factors; implied/projected pivot bounds; sparse fill,
shifted bounds, objectives, restoration, and unchanged source storage/bounds.
Sequential updates test both an initially zero coefficient becoming nonzero
and an initially nonzero coefficient cancelling to zero before another update.

Stored 256-bit tiny nonzero old coefficients and unrepresentable products under
ambient precision 32/64 must still reject aggregation. Products involving
±2^-200 produce accepted exact tiny fill entries, preserving their sign and
source precision. Float32/64 cases with half-subnormal fill reject the candidate;
a zero right-hand side isolates matrix representability from bound shifting.
These cases guard against approximate zero checks and inexact negation.

An independent read-only review found no issues. It reran all 742 focused
assertions and passed 2,560 additional baseline comparisons across 144 models
and 576 basis cases. It covered signed unit/nonunit/fractional factors,
projected/implied bounds, sequential initial-zero/cancellation cases, reduced-
precision tiny-old/product rejection, accepted tiny fill, underflow, staged
rejection, and source/primal/basis immutability.

The complete `test/runtests.jl` suite passed 39,643/39,643 assertions in
5m11.1s (exit code zero), including all existing allocation guards.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
