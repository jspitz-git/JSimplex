# Reuse zero for exactly cancelled candidate differences

Round 79 avoids general rational subtraction when a finite row endpoint equals
the finite activity of the other columns. The candidate numerator reuses the
existing activity zero. This applies to both lower and upper candidates for
positive and negative coefficients. The existing zero-other-activity shortcut
still runs first, and unequal operands subtract normally.

Equality compares exact rationals, preserving tiny nonzero differences even
when their stored BigFloat operands would round equal at ambient precision.
The shared zero is initialized before use and is not mutated. Bound flags,
unbounded activity checks, division shortcuts, representability checks, cache
updates, worklists, and postsolve retain their previous behavior.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 78 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

The three targets contain 128 rows `c*x[i] + 3*y = 3`, with each `x[i]` initially
free and the shared column `y` fixed at one. Coefficients `c` are two, minus two,
or one. In both activity directions, the numerator is `3 - 3`, and all `x[i]`
are fixed at zero. The unequal-operands control uses coefficient two and row
endpoint five, fixing each `x[i]` at one. The zero-other-activity control fixes
`y` at zero and uses coefficient two and row endpoint four, fixing each `x[i]`
at two. All objectives are ones.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Cancellation, coefficient 2 | 560,296 | 471,784 | 15.80% | 14,551 → 12,247 |
| Cancellation, coefficient -2 | 557,384 | 469,480 | 15.77% | 14,423 → 12,119 |
| Cancellation, coefficient 1 | 561,752 | 473,208 | 15.76% | 14,551 → 12,247 |
| Unequal-operands control | 668,024 | 667,336 | — | 17,623 → 17,623 |
| Zero-other-activity control | 532,928 | 532,272 | — | 14,036 → 14,036 |

Each target removes 2,304 allocations. Both controls retain their allocation
counts. Small byte differences on unchanged paths reflect cross-process
exact-arithmetic variation; no benefit is claimed for those cases.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 91,496 → 91,176 | 2,437 → 2,437 | 794,352 → 793,088 |
| adlittle | 675,544 → 674,504 | 18,971 → 18,971 | 3,453,808 → 3,451,760 |
| kb2 | 513,816 → 511,976 | 14,312 → 14,312 | 10,873,048 → 10,870,328 |
| sc50a | 234,984 → 233,224 | 6,312 → 6,312 | 3,030,712 → 3,027,640 |
| flugpl | 135,712 → 134,816 | 3,556 → 3,556 | 1,281,568 → 1,278,416 |

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 931,296 → 929,776 | 908,576 → 907,616 | 0 |
| adlittle | 4,243,200 → 4,240,368 | 4,520,080 → 4,517,136 | 0 |
| kb2 | 11,325,784 → 11,324,424 | 11,340,856 → 11,337,784 | 0 |
| sc50a | 3,376,328 → 3,373,128 | 3,328,728 → 3,325,528 | 0 |
| flugpl | 1,391,160 → 1,388,408 | 1,436,072 → 1,432,872 | 0 |

All five fixtures retain their allocation counts in direct propagation, full
presolve, and both whole solves. Their lower byte totals alone do not establish
an improvement. This round demonstrates savings on the targeted cancellation
models, not an allocation-count reduction on these fixtures. Paths without
presolve also retain their counts, with byte differences from -128 to +496.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-cancelled-candidates-allocations-before.toml`](propagation-cancelled-candidates-allocations-before.toml)
and [`propagation-cancelled-candidates-allocations-after.toml`](propagation-cancelled-candidates-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-cancelled-candidates-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function propagation_cancelled_candidates_probe(kind; count=128)
    coefficient = kind == :negative ? -2.0 : kind == :unit ? 1.0 : 2.0
    fixed = kind == :zero_other ? 0.0 : 1.0
    endpoint = kind == :unequal ? 5.0 : kind == :zero_other ? 4.0 : 3.0
    A = sparse(vcat(collect(1:count), collect(1:count)),
        vcat(collect(1:count), fill(count+1, count)),
        vcat(fill(coefficient, count), fill(3.0, count)), count, count+1)
    return LinearProblem(A, ones(count+1);
        row_lower=fill(endpoint, count), row_upper=fill(endpoint, count),
        column_lower=vcat(fill(nothing, count), fixed),
        column_upper=vcat(fill(nothing, count), fixed))
end
for kind in (:positive, :negative, :unit, :unequal, :zero_other)
    problem = propagation_cancelled_candidates_probe(kind)
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

All three target allocation guards failed on the original implementation:
14,596 exceeded 13,200, 14,431 exceeded 13,100, and 14,559 exceeded 13,200.
The other 404 assertions passed, including both controls. All 407 new assertions
now pass as part of 4,718 targeted propagation and presolve assertions.
Whole-pass budgets use allocation counts to avoid unstable exact-arithmetic
byte totals. Existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; positive,
negative, unit, and fractional coefficients; both and one-sided row bounds;
source-bound preservation; changed flags; postsolve; and full/incremental
activation of later rows. Stored 256-bit BigFloat row endpoints `3 ± 2^-100`
produce the correct signed nonzero residual after subtraction and division,
even though the endpoints round to three under ambient precision 32/64.

Independent review found no issues and separately passed all 407 new assertions.
Its 9,368 additional saved-baseline assertions passed across four numeric types
and all four candidate branches, covering zero/unequal activities, unbounded
precedence, contradictions, incremental caches, input/shared-zero preservation,
primal restoration, and basis restoration. Mixed-precision checks preserved
exact equality and nonzero residuals of `±2^-180` under 32/64-bit ambient precision.

The full mandatory suite passed all 25,419 assertions in 5m06.3s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
