# Negate candidate bounds for negative unit propagation coefficients

Round 70 replaces division by minus one with exact negation when normalizing
candidate lower and upper column bounds in `_propagate_row_bounds`. Each branch
checks the current candidate-loop coefficient. Other negative coefficients
retain division, and the positive-coefficient path is unchanged. Activity
products, difference calculation, representability checks, cache updates,
incremental worklists, and postsolve retain their existing behavior. Exact
negation does not mutate stored activity or bound values.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 69 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The probes contain 128 identical rows `[c, c]` and two columns with objective
coefficients one and bounds `[1, 10]`. Row bounds span the interval between `4c`
and `18c`, except the one-sided target, which has no lower row bound. Targets
use `c = -1`; controls use `c = 1`, `c = 2`, and `c = -2`. Rows are not redundant,
but no individual column bound can tighten, so every model is retained unchanged.
This exercises candidate construction without measuring accepted updates.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Negative unit, both row bounds | 1,287,488 | 1,143,216 | 11.21% | 34,777 → 31,193 |
| Negative unit, upper row bound only | 807,984 | 734,512 | 9.09% | 22,233 → 20,441 |
| Unit coefficients | 1,078,816 | 1,077,968 | — | 28,889 → 28,889 |
| Positive nonunit coefficients | 1,443,488 | 1,442,400 | — | 38,617 → 38,617 |
| Negative nonunit coefficients | 1,435,488 | 1,434,336 | — | 38,361 → 38,361 |

The targets remove 3,584 and 1,792 allocations. All three controls retain their
counts; their small byte differences reflect cross-process exact-arithmetic
allocation variation, so no improvement is claimed for them.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 106,960 → 102,352 | 2,877 → 2,781 | 823,936 → 819,064 |
| adlittle | 742,624 → 740,360 | 20,387 → 20,352 | 3,618,296 → 3,614,408 |
| kb2 | 608,448 → 598,792 | 16,491 → 16,258 | 11,143,032 → 11,116,080 |
| sc50a | 291,968 → 278,264 | 7,769 → 7,468 | 3,057,328 → 3,050,664 |
| flugpl | 169,112 → 165,592 | 4,281 → 4,211 | 1,336,080 → 1,332,496 |

All five direct propagation passes remove allocations. Sc50a has the largest
direct-pass reduction, 301 allocations and 4.69% of bytes; afiro uses 4.31%
fewer bytes.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 960,336 → 955,720 | 939,088 → 933,640 | 101 |
| adlittle | 4,407,816 → 4,403,784 | 4,684,440 → 4,680,920 | 54 |
| kb2 | 11,596,152 → 11,568,000 | 11,610,600 → 11,581,744 | 678 |
| sc50a | 3,402,816 → 3,396,728 | 3,356,176 → 3,349,592 | 119 |
| flugpl | 1,446,248 → 1,441,560 | 1,490,536 → 1,486,280 | 98 |

Full presolve removes the same number of allocations as each whole solve.
All five fixtures benefit at that level. Unchanged paths without presolve vary
from -224 to +256 bytes with identical allocation counts. Counts provide the
clearer evidence for small fixture differences; lower byte totals alone do not
establish a benefit when counts remain unchanged.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-negative-division-allocations-before.toml`](propagation-negative-division-allocations-before.toml)
and [`propagation-negative-division-allocations-after.toml`](propagation-negative-division-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-negative-division-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:negative, :upper_only, :unit, :positive, :nonunit)
    count = 128
    coefficient = kind == :unit ? 1.0 : kind == :positive ? 2.0 : kind == :nonunit ? -2.0 : -1.0
    lower = kind == :upper_only ? nothing : min(4coefficient, 18coefficient)
    problem = LinearProblem(sparse(fill(coefficient, count, 2)), ones(2);
        row_lower=fill(lower, count), row_upper=fill(max(4coefficient, 18coefficient), count),
        column_lower=fill(1.0, 2), column_upper=fill(10.0, 2))
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

Both target allocation guards failed against the original implementation:
34,822 allocations exceeded the 33,000 limit, and 22,241 exceeded 21,500. The
other 157 assertions, including all three controls, passed. All 159 new assertions
now pass as part of 2,059 targeted propagation and presolve assertions.
Allocation-count budgets avoid unstable exact-arithmetic byte totals.

Tests cover Float32, Float64, BigFloat, and Rational{BigInt}, positive/negative
candidate endpoints, both bound directions, mixed minus-one/minus-two
coefficients in the same row, changed flags, nonrepresentable candidates,
canonical candidate zero signs, contradictions, postsolve, and input preservation.
A stored 256-bit BigFloat candidate remains rejected under 64-bit working
precision, with no bound changes or precision loss in the source model.

Independent review found no issues and separately passed all 159 new assertions.
Saved-baseline checks passed 826 assertions across 32 four-type scenarios;
four stored-precision BigFloat cases passed another 100 assertions. Coverage
includes 72 full/incremental differential calls, empty-worklist identity,
changed flags, mixed coefficients, failures, representability, input preservation,
postsolve, and basis restoration. Only the baseline internal propagation
function was renamed; unchanged helpers remained current.

The full mandatory suite passed all 22,760 assertions in 4m56.8s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
