# Skip division by one when forming propagated bounds

Round 39 avoids rational division by one in the two positive-coefficient
candidate-bound expressions in `_propagate_row_bounds`. Each expression first
subtracts the other variables' activity from the row bound. For coefficient
one, that exact difference is already the candidate; other positive
coefficients still divide it. The negative-coefficient branch is unchanged.

Contradiction checks, conversion through `_represent_exact`, bound updates,
exact-cache replacement, worklist expansion, and postsolve behavior retain
their original order and logic.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 32 measurements per run recorded zero compilation
time. The baseline includes the preceding 38 allocation rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

The unit probe has 128 rows `2 ≤ xᵢ ≤ 6`, initial column bounds `[0,10]`, and
objective coefficients of one. The nonunit control scales the matrix and row
bounds by two. Both passes tighten every column to `[2,6]` and retain all rows.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Unit coefficients | 882,016 | 795,248 | 9.84% | 23,745 → 21,441 |
| Nonunit coefficients | 974,128 | 975,088 | — | 26,049 → 26,049 |

The unit probe removes 2,304 allocations. The nonunit control keeps identical
allocation counts; its 960-byte difference is not attributed to this change.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 188,032 → 184,624 | 4,842 → 4,760 | 1,117,784 → 1,111,448 |
| adlittle | 1,109,720 → 1,079,400 | 29,716 → 28,928 | 4,630,232 → 4,567,464 |
| kb2 | 914,152 → 901,656 | 24,193 → 23,882 | 13,086,912 → 13,059,760 |
| sc50a | 482,576 → 469,376 | 12,521 → 12,187 | 4,100,848 → 4,091,568 |
| flugpl | 220,200 → 211,912 | 5,591 → 5,375 | 1,471,640 → 1,458,104 |

The standalone propagation passes allocate 1.37–3.76% fewer bytes.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,253,432 → 1,247,512 | 1,232,136 → 1,226,024 | 167 |
| adlittle | 5,420,072 → 5,356,760 | 5,696,488 → 5,633,944 | 1,620 |
| kb2 | 13,538,096 → 13,510,704 | 13,552,096 → 13,524,608 | 724 |
| sc50a | 4,445,984 → 4,437,696 | 4,398,368 → 4,390,848 | 149 |
| flugpl | 1,580,944 → 1,567,536 | 1,625,424 → 1,611,968 | 351 |

Whole solves with presolve allocate approximately 0.17–1.17% fewer bytes.
Full presolve removes the same number of allocations as each whole solve.
Small cross-process byte variation remains: unchanged paths without presolve
vary from -496 to +48 bytes with identical allocation counts. Exact arithmetic
in presolve adds further variation, so not every byte of the difference is
attributed to the removed divisions.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-unit-division-allocations-before.toml`](propagation-unit-division-allocations-before.toml)
and [`propagation-unit-division-allocations-after.toml`](propagation-unit-division-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-unit-division-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for pivot in (1.0, 2.0)
    count = 128
    A = sparse(1:count, 1:count, fill(pivot, count), count, count)
    problem = LinearProblem(A, ones(count); row_lower=fill(2pivot, count),
        row_upper=fill(6pivot, count), column_lower=zeros(count), column_upper=fill(10.0, count))
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

The 22,000-allocation guard failed against the original body at 23,790 and now
passes. Direct test instrumentation records 45 more allocations than the warmed
benchmark. The guard uses allocation count to avoid exact-arithmetic byte
variability.

All 180 new assertions pass. They cover both resulting column bounds, unit,
negative, and nonunit coefficients, changed-column masks, input preservation,
primal and basis restoration, nonrepresentable nonunit bounds, signed-zero
normalization, and a stored 256-bit BigFloat bound rejected at a 64-bit working
precision. Numeric coverage includes Float32, Float64, BigFloat, and
Rational{BigInt}.

Together with existing unit-product and lazy-bound propagation tests, all 392
targeted assertions pass, including incremental chains, unbounded activities,
and failure after a prior tightening.

Independent review found no issue and passed all 180 new assertions. Its 196
differential assertions across 34 cases and four numeric types matched the
renamed baseline, including exactness rejection, signed zero, reduced BigFloat
working precision, incremental activation, failure after tightening, unchanged
inputs, postsolve output, and empty worklists.

Eight allocation checks passed using five repeated measurements per coefficient.
Nonunit counts remained 26,049 for coefficient 2, 25,921 for -1, and 26,049 for
1/2; the unit count fell from 23,745 to 21,441. An exploratory strict byte check
was unsuitable because repeated runs varied in allocated bytes for both versions
while nonunit counts stayed identical. Extreme exponent stress was excluded.

The complete mandatory suite passed **18,612/18,612** tests, including the 180
new assertions. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
