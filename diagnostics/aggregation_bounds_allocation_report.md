# Lazy working row bounds in equality aggregation

Round 36 delays the paired row-bound copies in `aggregate_singleton_equalities`
and `aggregate_sparse_equalities`. Both passes initially read the input arrays.
The singleton pass copies them immediately before committing its first chosen
candidate. The sparse pass copies them after all candidate staging succeeds,
before committing changes. Later accepted candidates reuse the private arrays,
so accumulated shifts remain visible to subsequent staging.

Passes without accepted candidates avoid both copies. Candidate arithmetic,
exactness checks, preference for exact over rounded singleton objective updates,
row/column selection, and postsolve logic are unchanged. Result construction
continues to provide independent bound arrays.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 37 measurements per run recorded zero compilation
time: two synthetic probes and five fixtures with three presolve stages and
four whole-solve configurations. The baseline includes the preceding 35 rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

The probes use 128 inequalities `0 ≤ x₂ᵢ₋₁ + x₂ᵢ ≤ 1`, nonnegative columns,
and objective coefficients of one. Both passes return the original model.

| Probe pass | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Singleton equality aggregation | 19,440 | 15,200 | 21.81% | 281 → 275 |
| Sparse equality aggregation | 19,872 | 15,632 | 21.34% | 291 → 285 |

| Model | Singleton pass before → after | Sparse pass before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 46,096 → 46,256 | 273,904 → 273,392 | 1,133,912 → 1,129,944 |
| adlittle | 67,640 → 67,640 | 193,872 → 193,200 | 4,736,984 → 4,730,568 |
| kb2 | 149,288 → 148,472 | 198,552 → 197,976 | 13,131,296 → 13,122,960 |
| sc50a | 14,464 → 12,608 | 404,248 → 402,568 | 4,124,176 → 4,113,328 |
| flugpl | 5,120 → 4,384 | 236,376 → 234,120 | 1,496,904 → 1,490,056 |

The standalone singleton pass on sc50a saves 12.83% and drops from 302 to 298
allocations. On flugpl it saves 14.38% and drops from 104 to 100; sparse
aggregation there drops from 6,252 to 6,248. All other standalone passes retain
their allocation counts because accepted candidates still require the copies.
Their small byte differences are not attributed to this change.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,269,992 → 1,265,368 | 1,247,944 → 1,243,656 | 12 |
| adlittle | 5,527,048 → 5,520,536 | 5,803,432 → 5,797,192 | 8 |
| kb2 | 13,581,968 → 13,575,344 | 13,595,504 → 13,588,768 | 12 |
| sc50a | 4,471,040 → 4,460,128 | 4,423,936 → 4,412,560 | 16 |
| flugpl | 1,606,944 → 1,600,528 | 1,651,552 → 1,645,120 | 24 |

Full presolve removes the same number of allocations as each whole solve.
Cross-process byte variability prevents attributing the entire byte difference
to this change: unchanged paths without presolve vary from -416 to +96 bytes
with identical allocation counts, and exact arithmetic in presolve introduces
further variation. The synthetic probes give the clearest byte measurements.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-bounds-allocations-before.toml`](aggregation-bounds-allocations-before.toml)
and [`aggregation-bounds-allocations-after.toml`](aggregation-bounds-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=aggregation-bounds-audit.toml
```

Use `--profile=aggregate_sparse_equalities` for an allocation profile of the
second pass. For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
count = 128
A = sparse(repeat(collect(1:count), inner=2), collect(1:2count),
           ones(2count), count, 2count)
problem = LinearProblem(A, ones(2count); row_lower=zeros(count), row_upper=ones(count))
for pass in (JSimplex.aggregate_singleton_equalities, JSimplex.aggregate_sparse_equalities)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Both 17,000-byte budgets failed against the original bodies at 19,440 and
19,872 bytes, respectively, and now pass. The 180 new assertions cover identity
returns, repeated accepted singleton rows, repeated sparse substitutions
shifting a shared row, retained projected bounds versus removed equality rows,
objective updates, postsolve values, independent result bounds, and unchanged
input matrices, costs, and bounds even after mutating result bounds. Numeric
coverage includes Float32, Float64, BigFloat, and Rational{BigInt}.

Together with the existing sparse scratch and free-pivot proof tests, all 515
targeted assertions pass; these include staged cost, coefficient, and bound
rejections before a later accepted candidate.

Independent review found no issue and passed all 180 new assertions. Its 532
differential assertions across 57 cases and four numeric types matched the
renamed pre-round functions. Coverage included rejected candidates before and
after acceptance, repeated bound writes, free and bounded pivots, no accepted
candidates, exact/rounded objective preference, input independence, and
postsolve primal and basis equivalence.

The complete mandatory suite passed **18,185/18,185** tests, including the 180
new assertions. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
