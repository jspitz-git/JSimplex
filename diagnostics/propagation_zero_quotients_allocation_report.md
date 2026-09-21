# Reuse zero candidate numerators during propagation

Round 71 skips division or negation when a candidate-bound numerator is exactly
zero in `_propagate_row_bounds`. All four lower/upper and positive/negative
coefficient branches reuse that exact zero. Positive unit coefficients retain
their existing shortcut; nonzero numerators retain the previous normalization.
The check operates on the exact rational difference, including cancellation
between nonzero values. Activity arithmetic, representability checks, cache
updates, worklists, and postsolve remain unchanged. Arithmetic never mutates
the shared numerator or source bounds.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 70 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The probes contain 128 independent singleton rows `c*x = b`, initially free
columns, and objective coefficients one. Targets use `b = 0` with coefficients
two, minus two, and minus one. Controls use coefficient one with zero right-hand
side, and coefficient two with right-hand side six. Propagation fixes each
column to `b/c`; model construction is outside measurement.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Zero numerator, coefficient 2 | 454,192 | 374,128 | 17.63% | 10,949 → 9,157 |
| Zero numerator, coefficient -2 | 451,088 | 371,840 | 17.57% | 10,821 → 9,029 |
| Zero numerator, coefficient -1 | 387,632 | 371,872 | 4.07% | 9,541 → 9,029 |
| Unit coefficient control | 376,928 | 376,000 | — | 9,157 → 9,157 |
| Nonzero numerator control | 503,696 | 502,064 | — | 12,997 → 12,997 |

The targets remove 1,792, 1,792, and 512 allocations. Both controls retain their
counts; their small byte differences reflect cross-process exact-arithmetic
allocation variation, so no improvement is claimed for them.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 104,480 → 101,272 | 2,781 → 2,737 | 821,864 → 818,024 |
| adlittle | 742,984 → 740,664 | 20,352 → 20,345 | 3,616,968 → 3,612,632 |
| kb2 | 601,624 → 596,568 | 16,258 → 16,190 | 11,117,328 → 11,107,328 |
| sc50a | 279,688 → 274,824 | 7,468 → 7,370 | 3,052,808 → 3,047,040 |
| flugpl | 166,936 → 164,104 | 4,211 → 4,176 | 1,333,760 → 1,329,392 |

All five direct propagation passes remove allocations, from seven on adlittle
to 98 on sc50a. Afiro has the largest direct-pass byte reduction, 3.07%.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 957,912 → 955,256 | 936,312 → 933,336 | 32 |
| adlittle | 4,406,088 → 4,403,592 | 4,682,920 → 4,679,944 | 28 |
| kb2 | 11,569,008 → 11,564,112 | 11,581,952 → 11,577,888 | 132 |
| sc50a | 3,397,016 → 3,392,224 | 3,349,848 → 3,344,592 | 84 |
| flugpl | 1,444,488 → 1,438,968 | 1,488,760 → 1,483,608 | 63 |

Full presolve removes the same number of allocations as each whole solve.
All five fixtures benefit at that level. Unchanged paths without presolve vary
from -48 to +416 bytes with identical allocation counts. Counts provide the
clearer evidence for small fixture differences; lower byte totals alone do not
establish a benefit when counts remain unchanged.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-zero-quotients-allocations-before.toml`](propagation-zero-quotients-allocations-before.toml)
and [`propagation-zero-quotients-allocations-after.toml`](propagation-zero-quotients-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-zero-quotients-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:positive, :negative, :negative_unit, :unit, :nonzero)
    count = 128
    coefficient = kind == :unit ? 1.0 : kind == :negative_unit ? -1.0 : kind == :negative ? -2.0 : 2.0
    endpoint = kind == :nonzero ? 6.0 : 0.0
    problem = LinearProblem(sparse(1:count, 1:count, fill(coefficient, count), count, count), ones(count);
        row_lower=fill(endpoint, count), row_upper=fill(endpoint, count),
        column_lower=fill(nothing, count), column_upper=fill(nothing, count))
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

All three target allocation guards failed against the original implementation:
10,994 exceeded 9,800, 10,829 exceeded 9,700, and 9,549 exceeded 9,400. The other
189 assertions, including both controls, passed. All 192 new assertions now pass
as part of 2,251 targeted propagation and presolve assertions. Allocation-count
budgets avoid unstable exact-arithmetic byte totals.

Tests cover Float32, Float64, BigFloat, and Rational{BigInt}, zero numerators
formed by cancellation, signed and fractional coefficients, both candidate
directions, changed flags, canonical candidate zero signs, free activity,
postsolve, and input preservation. A 2^-100 exact difference between stored
256-bit BigFloat values produces nonzero 2^-101 bounds under 64-bit working
precision rather than being treated as zero.

Independent review found no issues and separately passed all 192 new assertions.
Saved-baseline comparisons passed 1,054 additional assertions across 32 four-type
scenarios and eight BigFloat scenarios: 80 baseline comparisons and 32 empty-
worklist checks. Coverage includes cancellation, signed/fractional/unit
coefficients, free bounds, changed flags, contradictions, identity, input
preservation, postsolve, and basis restoration. Only the baseline internal
propagation function was renamed; unchanged helpers remained current.

The full mandatory suite passed all 22,952 assertions in 4m55.5s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
