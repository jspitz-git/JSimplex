# Reuse exact bounds for unit-coefficient activity products

Round 38 skips multiplication by one when computing minimum and maximum row
activity terms in `_propagate_row_bounds`. A unit coefficient reuses the exact
bound value already in the cache. Unbounded terms remain `nothing`, while
negative and other nonunit coefficients retain the original multiplication.

Accepted tightenings replace cache entries, and subsequent exact arithmetic is
nonmutating. Thus activity terms retain their original values for the current
row while later rows see the updated cache. Row sums, candidate divisions,
representability checks, incremental worklists, and postsolve logic are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 32 measurements per run recorded zero compilation
time. The baseline includes the preceding 37 allocation rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

The unit probe has 128 identical rows `0 ≤ x + y ≤ 20`, column bounds `[0,10]`,
and objective coefficients of one. The nonunit control multiplies both matrix
coefficients and row bounds by two. Both passes remove all redundant rows.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Unit coefficients | 614,784 | 431,632 | 29.79% | 17,132 → 12,524 |
| Nonunit coefficients | 615,904 | 614,944 | — | 17,132 → 17,132 |

The unit probe removes 4,608 allocations. The nonunit control keeps identical
allocation counts; its 960-byte difference is not attributed to this change.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 199,168 → 187,568 | 5,090 → 4,842 | 1,129,656 → 1,117,528 |
| adlittle | 1,148,200 → 1,107,912 | 30,628 → 29,716 | 4,731,864 → 4,627,128 |
| kb2 | 938,536 → 912,648 | 24,781 → 24,193 | 13,123,936 → 13,083,904 |
| sc50a | 500,336 → 481,536 | 12,939 → 12,521 | 4,118,064 → 4,097,152 |
| flugpl | 228,504 → 218,776 | 5,787 → 5,591 | 1,491,512 → 1,469,928 |

The standalone propagation passes allocate 2.76–5.82% fewer bytes.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,265,304 → 1,252,328 | 1,243,976 → 1,230,408 | 258 |
| adlittle | 5,521,400 → 5,416,760 | 5,797,816 → 5,693,672 | 2,542 |
| kb2 | 13,577,296 → 13,536,784 | 13,590,816 → 13,550,960 | 966 |
| sc50a | 4,462,272 → 4,442,944 | 4,414,720 → 4,395,568 | 410 |
| flugpl | 1,601,536 → 1,579,360 | 1,645,824 → 1,623,920 | 486 |

Whole solves with presolve allocate approximately 0.29–1.90% fewer bytes.
Full presolve removes the same number of allocations as each whole solve.
Small cross-process byte variation remains: unchanged paths without presolve
vary from -160 to +208 bytes with identical allocation counts. Exact arithmetic
in presolve adds further variation, so not every byte of the difference is
attributed to the removed multiplications.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-unit-products-allocations-before.toml`](propagation-unit-products-allocations-before.toml)
and [`propagation-unit-products-allocations-after.toml`](propagation-unit-products-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-unit-products-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for pivot in (1.0, 2.0)
    count = 128
    problem = LinearProblem(sparse(fill(pivot, count, 2)), ones(2);
        row_lower=zeros(count), row_upper=fill(20pivot, count),
        column_lower=zeros(2), column_upper=fill(10.0, 2))
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

The new 16,000-allocation limit failed against the original body at 17,177 and
now passes. Direct test instrumentation records 45 more allocations than the
warmed benchmark. The guard uses allocation count to avoid exact-arithmetic
byte variability.

All 126 new assertions pass. They cover redundant-row removal, a chain of
incrementally activated rows sharing cached bounds, negative and nonunit terms
mixed with unit terms, changed-column and original-worklist behavior, postsolve
primal and basis restoration, unchanged input bounds and coefficients, fully
unbounded activities, and finite tightening with one free variable. Numeric
coverage includes Float32, Float64, BigFloat, and Rational{BigInt}.

Together with existing lazy propagation-bound tests, all 212 targeted assertions
pass, including failure after an earlier tightening.

Independent review found no issue and passed all 126 new assertions. Its
12,252 differential assertions against renamed baseline functions covered
1,536 propagation calls, including 12 failures. Checks included repeated
tightening, worklist activation, unbounded bounds, stored zeros, negative and
nonunit coefficients, exactness rejection, failure metadata, postsolve values
and bases, and input preservation. Numeric coverage included Float32, Float64,
Rational{BigInt}, BigFloat at 32/128/256 bits, and mixed input/working precisions.
Twelve nonunit allocation checks for coefficients -2, 2, and 3 retained baseline
counts without a boxing regression. Extreme exponent limits were excluded.

The complete mandatory suite passed **18,432/18,432** tests, including the 126
new assertions. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
