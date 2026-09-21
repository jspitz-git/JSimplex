# Avoid unit-factor multiplication in sparse aggregation shifts

Round 93 extends the exact shift calculation in sparse equality aggregation.
After the existing zero-factor cases, a multiplier of one reuses the right-hand
side and a multiplier of minus one negates it. If the multiplier is nonunit,
a right-hand side of one reuses the multiplier and minus one negates it.
Two nonzero, nonunit factors retain exact multiplication.

Every comparison and negation operates on already-converted exact rational
values. Near-unit BigFloat values therefore retain their distinctions under
lower ambient precision. Bound shifting, matrix substitution, objectives,
representability checks, candidate selection, staging, and restoration are
unchanged. Reused rational values are not mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 92 allocation rounds. All 41 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each probe has 128 equalities `2*x[i] + y = rhs`, zero-cost `x[i]` bounded by
`[1,3]`, a free shared `y` with cost two, and objective constant seven. An extra
row `2*m*sum(x) + 2*y <= 1000` gives each pivot column degree two and produces
exact substitution multiplier `m`. After all eliminations, the last row has
coefficient `2 - 128*m` and upper bound `1000 - 128*m*rhs`.

Two targets use `m=±1,rhs=5`; two use `m=2,rhs=±1`. The nonunit control uses
`m=2,rhs=5`, and the zero-shift control uses `m=2,rhs=0`. Both controls retain
their previous multiplication or zero-factor paths.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Multiplier 1, RHS 5 | 1,473,256 | 1,430,296 | 2.92% | 39,380 → 38,228 |
| Multiplier -1, RHS 5 | 1,475,312 | 1,438,720 | 2.48% | 39,383 → 38,487 |
| Multiplier 2, RHS 1 | 1,475,272 | 1,431,736 | 2.95% | 39,380 → 38,228 |
| Multiplier 2, RHS -1 | 1,475,192 | 1,438,616 | 2.48% | 39,380 → 38,484 |
| Nonunit-factor control | 1,474,808 | 1,474,776 | — | 39,374 → 39,374 |
| Zero-shift control | 1,177,128 | 1,177,048 | — | 31,444 → 31,444 |

Positive-unit targets remove 1,152 allocations (nine per substitution);
negative-unit targets remove 896 (seven per substitution). Both controls retain
their allocation counts; byte differences on unchanged paths alone establish
no benefit.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 44,864 → 45,024 | 843 → 843 | 240,224 → 238,664 | 5,524 → 5,517 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 177,200 → 177,392 | 2,861 → 2,861 |
| kb2 | 112,272 → 112,160 | 2,060 → 2,060 | 165,712 → 165,712 | 2,958 → 2,958 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 331,824 → 331,008 | 7,434 → 7,434 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 215,992 → 215,784 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 747,664 → 746,528 | 882,848 → 881,872 | 860,624 → 859,616 | 0 |
| adlittle | 3,356,080 → 3,353,312 | 4,146,208 → 4,144,320 | 4,423,264 → 4,420,528 | 0 |
| kb2 | 10,681,976 → 10,680,792 | 11,136,472 → 11,133,032 | 11,150,008 → 11,147,400 | 0 |
| sc50a | 2,898,040 → 2,894,296 | 3,243,656 → 3,240,760 | 3,196,600 → 3,193,864 | 0 |
| flugpl | 1,205,664 → 1,203,520 | 1,314,568 → 1,313,128 | 1,359,576 → 1,357,512 | 0 |

Direct sparse aggregation removes seven allocations for afiro; all other
direct aggregation counts remain unchanged. Full presolve and both whole
solves retain their allocation counts on all five fixtures.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-unit-shift-allocations-before.toml`](aggregation-unit-shift-allocations-before.toml)
and [`aggregation-unit-shift-allocations-after.toml`](aggregation-unit-shift-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-unit-shift-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-unit-shift-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_unit_shift_probe(kind; count=128)
    multiplier = kind == :multiplier_negative ? -1.0 : kind == :multiplier_positive ? 1.0 : 2.0
    rhs = kind == :rhs_positive ? 1.0 : kind == :rhs_negative ? -1.0 : kind == :zero ? 0.0 : 5.0
    A = hcat(sparse(1:count,1:count,fill(2.0,count),count,count),sparse(ones(count,1)))
    A = vcat(A,sparse(reshape(vcat(fill(2multiplier,count),2.0),1,count+1)))
    problem = LinearProblem(A,vcat(zeros(count),2.0);objective_constant=7.0,
        row_lower=vcat(fill(rhs,count),nothing),row_upper=vcat(fill(rhs,count),1000.0),
        column_lower=vcat(fill(1.0,count),nothing),column_upper=vcat(fill(3.0,count),nothing))
    return problem,JSimplex.aggregate_sparse_equalities
end
for kind in (:multiplier_positive, :multiplier_negative, :rhs_positive,
             :rhs_negative, :nonunit, :zero)
    problem, pass = aggregation_unit_shift_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 1,274 assertions and failed the
four target allocation guards. The four probes allocated 39,425, 39,391,
39,388, and 39,388 objects, each exceeding 38,750. Both controls passed. All 1,278 new
assertions now pass as part of 11,173 targeted aggregation and presolve
assertions. Existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; signed unit
multipliers and right-hand sides; lower, upper, two-sided, and unbounded other
rows. Tests check matrix coefficients, exact shifted bounds, unchanged costs
and constant, primal restoration, and unchanged source matrices/bounds.

Stored 256-bit BigFloat factors ±2^-200 under ambient precision 32/64 produce
accepted exact tiny shifts with either unit-factor position and sign. Rejection
cases use factors of ±(1 ± 2^-200) alongside signed units or the nonunit factor
two. All cases retain their unrepresentable exact shifts and reject the only
eligible pivot. These cases guard against
negating before exact conversion and approximate unit comparisons.

An independent read-only review found no issues. It reran all 1,278 focused
assertions and passed 1,256 additional baseline comparisons across 72 models
and 288 basis restorations. Coverage included both unit-factor positions and
signs, projected bounds, sequential shifts, tiny/near-unit BigFloat values at
reduced precision, and staged bound/matrix rejection followed by acceptance.
Full results, exact objectives, and source/primal/basis immutability matched.

The complete `test/runtests.jl` suite passed 36,569/36,569 assertions in
5m10.3s (exit code zero), including all existing allocation guards.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
