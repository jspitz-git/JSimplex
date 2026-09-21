# Normalize negative unit dependency pivots by negation

Round 63 replaces exact rational division by a pivot of minus one with negation
in `reduce_dependent_rows`. The shortcut applies to both row coefficients and
dependency-proof coefficients. The existing reuse of one for coefficients equal
to the pivot takes precedence. Unit pivots still skip normalization; other
pivots retain ordinary division. The negative-unit condition is computed once
per normalization. All arithmetic replaces dictionary values without mutating
shared rational components.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 62 allocation rounds. All 34 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The probes contain 128 independent rows and 129 free columns. Row `i` has pivot
`s` in column `i` and trailing coefficient `v` in column `i+1`, with upper bound
three and a zero objective. Pivot minus one exercises the shortcut, including
an equal-coefficient case that already avoids coefficient division and therefore
isolates the proof normalization. Pivots one and minus two serve as controls.
Every model is retained unchanged.

| Probe `(s, v)` | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Negative unit `(-1, 3)` | 366,352 | 291,696 | 20.38% | 6,810 → 5,018 |
| Equal coefficients `(-1, -1)` | 322,784 | 284,768 | 11.78% | 5,658 → 4,762 |
| Unit pivot `(1, 3)` | 276,944 | 275,952 | — | 4,506 → 4,506 |
| Nonunit pivot `(-2, 3)` | 366,368 | 365,568 | — | 6,810 → 6,810 |

The targets remove 1,792 and 896 allocations. Both controls retain their counts;
their small byte differences reflect cross-process exact-arithmetic allocation
variation, so no improvement is claimed for those cases.

| Model | Dependency pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 205,792 → 198,048 | 4,440 → 4,272 | 856,480 → 831,392 |
| adlittle | 721,432 → 718,904 | 16,804 → 16,762 | 3,626,664 → 3,623,832 |
| kb2 | 3,478,984 → 3,463,920 | 80,354 → 80,025 | 11,180,792 → 11,166,520 |
| sc50a | 1,422,728 → 1,328,712 | 33,292 → 31,066 | 3,087,864 → 3,061,568 |
| flugpl | 199,360 → 183,264 | 4,158 → 3,830 | 1,341,632 → 1,339,968 |

All five direct dependency passes allocate less. The largest direct-pass byte
reductions are 6.61% on sc50a and 8.07% on flugpl. The full presolve pipeline
does not encounter the same pivots as a standalone pass, so those savings do
not transfer uniformly to whole solves.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 991,248 → 966,384 | 969,472 → 944,688 | 602 |
| adlittle | 4,415,656 → 4,412,792 | 4,692,520 → 4,689,432 | 0 |
| kb2 | 11,634,072 → 11,619,752 | 11,647,032 → 11,633,896 | 336 |
| sc50a | 3,434,232 → 3,406,560 | 3,387,128 → 3,359,488 | 629 |
| flugpl | 1,451,208 → 1,449,832 | 1,495,608 → 1,494,344 | 0 |

Full presolve removes the same number of allocations as each whole solve.
Three fixtures benefit at this level; adlittle and flugpl retain their counts.
Afiro's whole-solve byte reduction is 2.51–2.56%. Unchanged paths without
presolve vary from -16 to +64 bytes with identical allocation counts. Counts
provide the clearer evidence for small fixture differences; lower byte totals
alone do not establish a benefit when counts remain unchanged.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-negative-pivot-allocations-before.toml`](dependent-negative-pivot-allocations-before.toml)
and [`dependent-negative-pivot-allocations-after.toml`](dependent-negative-pivot-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-negative-pivot-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for (pivot, trailing) in ((-1.0, 3.0), (-1.0, -1.0), (1.0, 3.0), (-2.0, 3.0))
    count = 128
    A = sparse([collect(1:count); collect(1:count)],
        [collect(1:count); collect(2:count+1)],
        [fill(pivot, count); fill(trailing, count)], count, count+1)
    problem = LinearProblem(A, zeros(count+1); row_upper=fill(3.0, count),
        column_lower=fill(nothing, count+1))
    println(measure_allocations(_ -> JSimplex.reduce_dependent_rows(problem); samples=3))
end
```

## Regression coverage

Both target allocation guards failed against the original implementation:
6,855 allocations exceeded the 5,600 limit, and 5,666 exceeded the 5,100 limit.
The other 166 assertions, including both controls, passed. All 168 new assertions
now pass as part of 2,058 targeted dependency assertions. Allocation-count
budgets avoid unstable exact-arithmetic byte totals.

Tests cover Float32, Float64, BigFloat, and Rational{BigInt}, negative unit pivots
present initially and appearing after elimination, fractional and signed proof
contributions, equal and opposite coefficients, row removal, contradictions,
postsolve, input preservation, and orientation of unequal interval endpoints.

Independent review found no issues and separately passed all 168 new assertions.
Thirty-two saved-baseline differential cases passed 120 additional assertions
across Float32, Float64, Rational{BigInt}, and mixed-precision BigFloat. Complete
results, input preservation, identity behavior, and postsolve matched, including
original and elimination-created negative unit pivots, mixed-sign and fractional
proofs, contradictions, and interval orientation.

The full mandatory suite passed all 21,831 assertions in 4m53.1s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
