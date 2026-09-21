# Lazy exact defaults in equality aggregation

Round 25 replaces three eager dictionary defaults with lazy `get` callbacks in
`aggregate_singleton_equalities` and `aggregate_sparse_equalities`. When a prior
pivot has already updated an objective or matrix coefficient, the next pivot now
reads that exact value without converting the unused original coefficient to
`Rational{BigInt}`. Missing entries still use the original value. Update staging,
representability checks, commit order, and postsolve records are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 37 measurements per run recorded zero compilation
time. The baseline includes the preceding 24 rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

The synthetic models have 64 equalities `xᵢ + y = 1`, free variables, and objective
`sum(xᵢ) + 2y`. Repeated elimination updates the objective coefficient of `y`.
The sparse-pass probe additionally has `sum(xᵢ) + 2y ≤ 100`, so the same matrix
entry also receives repeated updates.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Singleton equality aggregation | 377,696 | 355,848 | 5.78% | 9,706 → 8,950 |
| Sparse equality aggregation | 744,176 | 699,312 | 6.03% | 19,808 → 18,296 |

| Model | Singleton before | After | Sparse before | After | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: | ---: |
| afiro | 46,304 | 45,856 | 280,144 | 278,896 | 6,496 → 6,424 |
| adlittle | 67,640 | 67,640 | 193,664 | 193,392 | 3,277 → 3,277 |
| kb2 | 148,664 | 148,184 | 199,960 | 199,816 | 3,787 → 3,787 |
| sc50a | 14,464 | 14,464 | 419,224 | 415,784 | 9,475 → 9,340 |
| flugpl | 5,120 | 5,120 | 236,392 | 237,256 | 6,262 → 6,262 |

The direct singleton fixture passes kept identical allocation counts. Sparse
aggregation removes 72 allocations on afiro and 135 on sc50a; the other three
fixtures keep identical counts. Full presolve and both whole-solve algorithms
remove 36 allocations on afiro and 135 on sc50a, with unchanged counts elsewhere.
Whole-solve byte differences with presolve range from a 3,872-byte reduction to a
1,248-byte increase. Unchanged paths without presolve vary from -16 to +336 bytes
with identical counts. These small byte differences do not establish a uniform
whole-solver improvement; the repeated-update probes and allocation counts show
the benefit more clearly.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-defaults-allocations-before.toml`](aggregation-defaults-allocations-before.toml)
and [`aggregation-defaults-allocations-after.toml`](aggregation-defaults-allocations-after.toml).

## Reproduction

The fixture stages can be profiled separately:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=singleton-aggregation-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=sparse-aggregation-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_probe(sparse_pass; count=64)
    rows, columns, values = collect(1:count), collect(1:count), ones(count)
    append!(rows, 1:count)
    append!(columns, fill(count + 1, count))
    append!(values, ones(count))
    lower = Union{Nothing,Float64}[ones(count);]
    upper = ones(count)
    if sparse_pass
        append!(rows, fill(count + 1, count + 1))
        append!(columns, 1:count+1)
        append!(values, [ones(count); 2.0])
        push!(lower, nothing)
        push!(upper, 100.0)
    end
    row_count = sparse_pass ? count + 1 : count
    LinearProblem(sparse(rows, columns, values, row_count, count + 1),
        [ones(count); 2.0]; row_lower=lower, row_upper=upper,
        column_lower=fill(nothing, count + 1))
end
for sparse_pass in (false, true)
    problem = aggregation_probe(sparse_pass)
    pass = sparse_pass ? JSimplex.aggregate_sparse_equalities :
                         JSimplex.aggregate_singleton_equalities
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Both allocation budgets failed before the change: 366,848 bytes against a
360,000-byte singleton limit and 730,496 bytes against a 710,000-byte sparse
limit. Both now pass. These direct-call budgets use a separately constructed
equivalent model; they are not the benchmark measurements in the table above.
The 176 semantic checks cover missing and previously updated dictionary entries,
accumulated objective and matrix values, objective constants, postsolve maps and
restored solutions, and unchanged input matrices/objectives. Numeric coverage
includes Float32, Float64, BigFloat, and Rational{BigInt}.

Independent review found no issue. Its 144 differential cases across six numeric
types and both aggregation passes matched baseline models, CSC arrays, postsolve
maps, and reconstruction records. Inputs remained unchanged.

The complete mandatory suite passed **16,655/16,655** tests, including the 178 new
checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
