# Avoid unit-factor multiplication in sparse matrix updates

Round 95 extends the matrix-update calculation in sparse equality aggregation.
Zero multipliers retain the existing shortcut. For nonzero multipliers, the
equality term is converted exactly once; a unit factor reuses the other factor
and a negative unit factor negates it exactly. Two nonunit factors retain
exact multiplication, and the product is subtracted from the current value.

The current coefficient still comes from `matrix_updates` before the shortcut,
and every result retains the exact representability check and normal staging.
All comparisons and negations operate on exact rational values, preserving
BigFloat distinctions under lower ambient precision. Objective updates, bound
shifts, candidate selection, and restoration are unchanged. Reused rational
values are not mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 94 allocation rounds. All 41 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each probe has 128 equalities `2*x[i] + t*y = 5`, zero-cost `x[i]` bounded by
`[1,3]`, free `y` with cost two, and objective constant seven. The extra row
`2*m*sum(x) + 2*y <= 2000` gives each pivot column degree two and produces
substitution multiplier `m`. After all eliminations, the last row has
coefficient `2 - 128*m*t` and upper bound `2000 - 640*m`.

Two targets use `m=±1,t=3`; two use `m=2,t=±1`. The nonunit control uses
`m=2,t=3`. The zero-multiplier control retains explicitly stored pivot-column
zeros and uses `t=3`; its previous zero-update shortcut remains unchanged.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Multiplier 1, term 3 | 1,429,536 | 1,386,176 | 3.03% | 38,231 → 37,079 |
| Multiplier -1, term 3 | 1,438,832 | 1,401,472 | 2.60% | 38,487 → 37,591 |
| Multiplier 2, term 1 | 1,475,080 | 1,431,160 | 2.98% | 39,380 → 38,228 |
| Multiplier 2, term -1 | 1,474,896 | 1,438,128 | 2.49% | 39,383 → 38,487 |
| Nonunit-factor control | 1,475,120 | 1,474,336 | — | 39,383 → 39,383 |
| Zero-multiplier control | 1,109,368 | 1,108,392 | — | 29,142 → 29,142 |

Positive-unit targets remove 1,152 allocations (nine per update); negative-unit
targets remove 896 (seven per update). Both controls retain their allocation
counts; byte differences on unchanged paths alone establish no benefit.

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 44,928 → 44,928 | 843 → 843 | 239,448 → 227,872 | 5,517 → 5,241 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 178,336 → 175,664 | 2,861 → 2,843 |
| kb2 | 111,968 → 111,760 | 2,060 → 2,060 | 166,432 → 162,160 | 2,958 → 2,903 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 332,192 → 313,536 | 7,434 → 7,011 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 216,552 → 214,344 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 748,192 → 737,520 | 883,056 → 873,616 | 861,824 → 852,192 | 199 |
| adlittle | 3,355,616 → 3,351,600 | 4,145,632 → 4,141,824 | 4,422,912 → 4,418,608 | 18 |
| kb2 | 10,683,352 → 10,679,656 | 11,136,520 → 11,132,808 | 11,149,672 → 11,146,088 | 14 |
| sc50a | 2,896,504 → 2,872,680 | 3,242,456 → 3,219,608 | 3,195,256 → 3,171,592 | 539 |
| flugpl | 1,204,624 → 1,203,088 | 1,314,520 → 1,312,776 | 1,359,064 → 1,357,336 | 0 |

Full presolve and both whole solves remove 199 allocations for afiro, 18 for
adlittle, 14 for kb2, and 539 for sc50a. Flugpl retains its count. Singleton
aggregation retains its count on all five fixtures.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-unit-matrix-update-allocations-before.toml`](aggregation-unit-matrix-update-allocations-before.toml)
and [`aggregation-unit-matrix-update-allocations-after.toml`](aggregation-unit-matrix-update-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-unit-matrix-update-singleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-unit-matrix-update-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_unit_matrix_update_probe(kind; count=128)
    multiplier = kind == :multiplier_positive ? 1.0 : kind == :multiplier_negative ? -1.0 : kind == :zero ? 0.0 : 2.0
    term = kind == :term_positive ? 1.0 : kind == :term_negative ? -1.0 : 3.0
    rows = vcat(collect(1:count),fill(count+1,count),collect(1:count),count+1)
    columns = vcat(collect(1:count),collect(1:count),fill(count+1,count+1))
    values = vcat(fill(2.0,count),fill(2multiplier,count),fill(term,count),2.0)
    A = sparse(rows,columns,values,count+1,count+1)
    problem = LinearProblem(A,vcat(zeros(count),2.0);objective_constant=7.0,
        row_lower=vcat(fill(5.0,count),nothing),row_upper=vcat(fill(5.0,count),2000.0),
        column_lower=vcat(fill(1.0,count),nothing),column_upper=vcat(fill(3.0,count),nothing))
    return problem,JSimplex.aggregate_sparse_equalities
end
for kind in (:multiplier_positive, :multiplier_negative, :term_positive,
             :term_negative, :nonunit, :zero)
    problem, pass = aggregation_unit_matrix_update_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 1,370 assertions and failed the
four target allocation guards. The multiplier probes allocated 38,276
and 38,495 objects, exceeding 37,600 and 37,850; the term probes allocated
39,388 and 39,391, each exceeding 38,750. Both controls passed. All 1,374 new
assertions now pass as part of 13,505 targeted aggregation and presolve
assertions. Existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; both unit
factor positions and signs; zero/nonzero old coefficients; implied/projected
pivot bounds; exact matrix entries, shifted bounds, objectives, restoration,
and unchanged source storage/bounds. Sequential substitutions preserve prior
committed matrix updates.

Stored 256-bit factors ±2^-200 under ambient precision 32/64 produce accepted
exact tiny matrix changes. Factors of ±(1 ± 2^-200), alongside signed units or
a nonunit factor two, remain unrepresentable and reject the only eligible
pivot. A zero right-hand side isolates these checks from bound shifting.
These cases guard against negation before exact conversion or approximate
unit comparisons. The zero-multiplier allocation control prevents moving the
term conversion outside the existing zero shortcut.

An independent read-only review found no issues. It reran all 1,374 focused
assertions and passed 1,264 additional baseline comparisons across 72 models
and 288 basis cases. It covered both factor positions/signs, projected/implied
bounds, sequential updates, reduced-precision BigFloat rejection and accepted
tiny products, partial matrix staging rejection followed by acceptance of a
disjoint candidate, exact objectives, postsolve, and input immutability.

The complete `test/runtests.jl` suite passed 38,901/38,901 assertions in
5m11.3s (exit code zero), including all existing allocation guards.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
