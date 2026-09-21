# Skip zero-term arithmetic in row activities

Round 40 avoids adding exact zero terms to minimum and maximum row-activity
sums. `_other_activity` also returns the existing total when removing a zero
term. Its unbounded-count check still runs first, so a finite zero never masks
another unbounded contribution. Removing nonzero terms retains the subtraction.

These operations use exact `Rational{BigInt}` values, and downstream arithmetic
does not mutate them. Nonzero cancellation, candidate formation, exactness and
contradiction checks, cache updates, worklists, and postsolve logic are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 32 measurements per run recorded zero compilation
time. The baseline includes the preceding 39 allocation rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

The zero-term probe has 128 rows `2 ≤ xᵢ ≤ 6`, initial column bounds `[0,10]`,
and objective coefficients of one. Its control starts at `[1,10]`, making both
activity terms nonzero. Both passes tighten every column to `[2,6]` and retain
all rows.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Zero minimum terms | 795,264 | 712,144 | 10.45% | 21,441 → 19,393 |
| Nonzero terms | 811,456 | 810,464 | — | 22,081 → 22,081 |

The zero-term probe removes 2,048 allocations. The control keeps identical
allocation counts; its 992-byte difference is not attributed to this change.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 184,864 → 154,448 | 4,760 → 4,029 | 1,111,704 → 1,058,456 |
| adlittle | 1,080,504 → 900,552 | 28,928 → 24,409 | 4,569,432 → 4,206,264 |
| kb2 | 902,456 → 770,440 | 23,882 → 20,510 | 13,058,528 → 12,783,584 |
| sc50a | 469,680 → 406,320 | 12,187 → 10,592 | 4,093,520 → 4,034,288 |
| flugpl | 211,192 → 197,064 | 5,375 → 5,017 | 1,459,032 → 1,434,424 |

The standalone propagation passes allocate 6.69–16.65% fewer bytes.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,248,472 → 1,193,672 | 1,226,872 → 1,171,752 | 1,358 |
| adlittle | 5,359,448 → 4,995,672 | 5,636,472 → 5,272,488 | 9,235 |
| kb2 | 13,511,648 → 13,237,728 | 13,525,984 → 13,252,224 | 7,044 |
| sc50a | 4,440,480 → 4,378,880 | 4,393,408 → 4,331,520 | 1,470 |
| flugpl | 1,569,056 → 1,543,776 | 1,613,392 → 1,588,448 | 603 |

Whole solves with presolve allocate approximately 1.39–6.79% fewer bytes.
Full presolve removes the same number of allocations as each whole solve.
Small cross-process byte variation remains: unchanged paths without presolve
vary from -448 to +304 bytes with identical allocation counts. Exact arithmetic
in presolve adds further variation, so not every byte of the difference is
attributed to the removed additions and subtractions.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-zero-activity-allocations-before.toml`](propagation-zero-activity-allocations-before.toml)
and [`propagation-zero-activity-allocations-after.toml`](propagation-zero-activity-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-zero-activity-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for lower in (0.0, 1.0)
    count = 128
    A = sparse(1:count, 1:count, ones(count), count, count)
    problem = LinearProblem(A, ones(count); row_lower=fill(2.0, count),
        row_upper=fill(6.0, count), column_lower=fill(lower, count), column_upper=fill(10.0, count))
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

Both new guards failed against the original bodies: `_other_activity(7//3,0,0)`
allocated 336 bytes against a 128-byte limit, and the propagation probe recorded
21,486 allocations against a 20,500 limit. Both now pass. Direct test
instrumentation records 45 more allocations than the warmed whole-pass
benchmark; allocation counts avoid exact-arithmetic byte variability.

All 105 new assertions pass. They cover exact zero removal, positive/negative
totals, nonzero cancellation, one versus multiple unbounded contributions,
negative column bounds and coefficients, redundant equality removal, zero
finite terms alongside a free variable, changed-column masks, postsolve values,
and input preservation. Numeric coverage includes Float32, Float64, BigFloat,
and Rational{BigInt}.

Together with existing unit-division, unit-product, and lazy-bound propagation
tests, all 497 targeted assertions pass, including precision rejection,
incremental chains, restored bases, and failure after a prior tightening.

Independent review found no actionable issues. A separate run passed all 105
new assertions. Another 38 comparisons against the original implementation
passed 430 assertions across all four numeric types, including incremental
propagation, failures, unchanged inputs, restored primals and bases, and
256-bit BigFloat inputs under 64- and 128-bit working precision. Four nonzero
controls passed 16 assertions with unchanged allocation counts on repeat runs.

The full mandatory suite passed all 18,717 assertions in 4m57.4s. Both saved
report artifacts match their measured source files byte for byte; each contains
32 measurements with three samples and zero compilation time, including 20
`OPTIMAL` solve records. `git diff --check` passed.

The two previously documented JET development-suite failures remain outside
this round's scope; the full optional development suite was not rerun.
