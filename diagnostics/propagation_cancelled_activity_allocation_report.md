# Construct zero directly for cancelled other activity

Round 72 avoids general rational subtraction in `_other_activity` when the
finite activity total equals the removed term. It constructs an exact zero
directly. The remaining-unbounded check still precedes this shortcut, and
unbounded or zero removed terms retain the existing total-reuse path. Unequal
finite operands still subtract normally. Inputs are never mutated. Candidate
construction, representability checks, cache updates, worklists, and postsolve
retain their previous behavior.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 71 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The three targets contain 128 independent singleton rows with coefficients two,
minus two, or one, initial column bounds `[1, 10]`, and row bounds corresponding
to column bounds `[2, 6]`. The finite activity total equals the removed term in
both directions, and propagation tightens each column to `[2, 6]`.
The free-column control has unit coefficients and initially unbounded columns,
exercising the existing unbounded-term path. The unequal-total control contains
128 rows `[2, 2]` with bounds `[8, 36]` and column bounds `[1, 10]`; no individual
bound can tighten, so its model is retained unchanged. All objectives are ones.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Cancellation, coefficient 2 | 793,616 | 735,328 | 7.34% | 21,445 → 20,165 |
| Cancellation, coefficient -2 | 792,080 | 732,864 | 7.48% | 21,317 → 20,037 |
| Cancellation, coefficient 1 | 613,072 | 554,224 | 9.60% | 16,581 → 15,301 |
| Free-column control | 415,712 | 415,200 | — | 10,693 → 10,693 |
| Unequal-total control | 1,444,944 | 1,444,784 | — | 38,617 → 38,617 |

Each target removes 1,280 allocations. Both controls retain their counts; their
small byte differences reflect cross-process exact-arithmetic allocation
variation, so no improvement is claimed for them.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 102,584 → 102,360 | 2,737 → 2,737 | 820,328 → 818,472 |
| adlittle | 741,816 → 742,120 | 20,345 → 20,337 | 3,616,280 → 3,614,920 |
| kb2 | 597,288 → 594,424 | 16,190 → 16,127 | 11,113,360 → 11,108,624 |
| sc50a | 276,088 → 271,736 | 7,370 → 7,280 | 3,049,824 → 3,049,200 |
| flugpl | 164,808 → 162,344 | 4,176 → 4,151 | 1,330,640 → 1,330,112 |

Four direct propagation passes remove allocations; afiro retains its count.
Sc50a removes 90 allocations in the direct pass. Adlittle's byte total increases
slightly despite eight fewer allocations.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 956,568 → 953,976 | 933,784 → 932,168 | 40 |
| adlittle | 4,405,768 → 4,405,240 | 4,681,208 → 4,681,128 | 20 |
| kb2 | 11,566,112 → 11,561,344 | 11,580,448 → 11,575,968 | 88 |
| sc50a | 3,394,928 → 3,395,696 | 3,347,968 → 3,348,480 | 20 |
| flugpl | 1,440,600 → 1,439,432 | 1,485,480 → 1,484,040 | 45 |

Full presolve removes the same number of allocations as each whole solve.
All five fixtures benefit in allocation counts at that level. Sc50a's whole-solve
byte totals increase despite 20 fewer allocations. Unchanged paths without
presolve vary from -624 to +48 bytes with identical allocation counts. Counts
provide the clearer evidence for small fixture differences; lower byte totals
alone do not establish a benefit when counts remain unchanged.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-cancelled-activity-allocations-before.toml`](propagation-cancelled-activity-allocations-before.toml)
and [`propagation-cancelled-activity-allocations-after.toml`](propagation-cancelled-activity-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-cancelled-activity-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:positive, :negative, :unit, :free, :unequal)
    count = 128
    coefficient = kind == :negative ? -2.0 : kind in (:unit, :free) ? 1.0 : 2.0
    problem = if kind == :unequal
        LinearProblem(sparse(fill(coefficient, count, 2)), ones(2);
            row_lower=fill(4coefficient, count), row_upper=fill(18coefficient, count),
            column_lower=fill(1.0, 2), column_upper=fill(10.0, 2))
    else
        LinearProblem(sparse(1:count, 1:count, fill(coefficient, count), count, count), ones(count);
            row_lower=fill(min(2coefficient, 6coefficient), count),
            row_upper=fill(max(2coefficient, 6coefficient), count),
            column_lower=fill(kind == :free ? nothing : 1.0, count),
            column_upper=fill(kind == :free ? nothing : 10.0, count))
    end
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

All three target allocation guards failed against the original implementation:
21,490 exceeded 20,700, 21,325 exceeded 20,600, and 16,589 exceeded 15,900. The
direct helper used 320 bytes against a 176-byte limit. The other 167 assertions,
including both controls, passed. All 171 new assertions now pass as part of
2,422 targeted propagation and presolve assertions. Whole-pass budgets use
allocation counts to avoid unstable exact-arithmetic byte totals.

Tests cover Float32, Float64, BigFloat, and Rational{BigInt}, positive and
negative exact cancellation, separately allocated equal operands, unequal and
opposite operands, zero terms, unbounded-term precedence, signed/fractional
coefficients, cancellation from multiple nonzero columns, changed flags,
postsolve, and preservation of inputs.

Independent review found no issues and separately passed all 171 new assertions.
Saved-baseline checks passed 1,481 additional assertions across 32 four-type
scenarios, four tiny-residual and four mixed-precision BigFloat cases. Coverage
includes 80 propagation comparisons, 32 empty-worklist identity checks, and
140 direct helper comparisons, plus changed flags, unbounded precedence,
failures, immutability, postsolve, and basis restoration. Only the baseline
activity helper and internal propagation function were renamed and connected;
other helpers remained current.

The full mandatory suite passed all 23,123 assertions in 4m56.0s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
