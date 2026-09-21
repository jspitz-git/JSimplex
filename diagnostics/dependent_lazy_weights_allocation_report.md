# Defer unused weight negation in dependent-row intervals

Round 54 delays constructing the negated proof weight in `_implied_interval`
until a finite, nonzero source endpoint contributes to a finite running sum.
The source endpoint is selected directly from the original weight's sign.
Zero proof weights are skipped before negation. If both endpoints need the
weight, they reuse the same negated value; the upper endpoint initializes it
when the lower endpoint did not need it.

Unbounded and zero-source handling, unit-weight and zero-sum shortcuts,
contradictions, and postsolve behavior remain unchanged. No exact values are
mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 53 allocation rounds. All 33 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The target has 128 identical rows `x + 2y - z = 0`, free columns, and a zero
objective. The unit-weight control uses bounds `[1, 6]`. The nonunit control
also uses those bounds, then scales all but the first row, including bounds,
by two. All three reductions retain the first row.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Zero endpoints | 491,248 | 483,912 | 1.49% | 11,531 → 11,277 |
| Unit weight | 609,808 | 609,392 | — | 15,595 → 15,595 |
| Nonunit weight | 870,784 | 870,272 | — | 22,453 → 22,453 |

The target removes 254 allocations. Both controls retain identical counts;
their small byte differences do not establish a benefit.

| Model | Dependency pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 257,472 → 256,064 | 5,789 → 5,785 | 973,488 → 972,160 |
| adlittle | 810,232 → 810,536 | 19,175 → 19,175 | 3,816,744 → 3,815,016 |
| kb2 | 4,122,904 → 4,114,104 | 96,838 → 96,619 | 12,198,056 → 12,148,424 |
| sc50a | 1,967,136 → 1,963,216 | 48,030 → 47,978 | 3,883,216 → 3,851,704 |
| flugpl | 220,048 → 219,328 | 4,731 → 4,731 | 1,378,480 → 1,377,264 |

Direct dependency-pass counts drop on afiro, kb2, and sc50a. Earlier presolve
passes expose more opportunities, so the complete pipeline benefits more.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,109,616 → 1,108,432 | 1,087,568 → 1,086,768 | 16 |
| adlittle | 4,605,624 → 4,604,552 | 4,882,856 → 4,881,160 | 0 |
| kb2 | 12,649,528 → 12,605,800 | 12,663,288 → 12,619,528 | 1,140 |
| sc50a | 4,229,760 → 4,196,456 | 4,182,368 → 4,149,000 | 1,116 |
| flugpl | 1,488,152 → 1,487,736 | 1,532,856 → 1,532,088 | 0 |

Whole solves allocate about 0.35% fewer bytes on kb2 and 0.79–0.80% fewer on
sc50a. Afiro's smaller measured reduction is 0.07–0.11%. Full presolve removes
the same number of allocations as each whole solve. Adlittle and flugpl retain
identical counts throughout; their byte differences do not establish a benefit.
Unchanged paths without presolve vary from -624 to +304 bytes with identical
allocation counts. Exact-arithmetic byte totals fluctuate across processes.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-lazy-weights-allocations-before.toml`](dependent-lazy-weights-allocations-before.toml)
and [`dependent-lazy-weights-allocations-after.toml`](dependent-lazy-weights-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-lazy-weights-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:unit, :nonunit, :zero)
    count = 128
    multipliers = kind != :nonunit ? ones(count) : [1.0; fill(2.0, count - 1)]
    problem = LinearProblem(sparse(multipliers * [1.0 2.0 -1.0]), zeros(3);
        row_lower=kind == :zero ? zeros(count) : multipliers,
        row_upper=kind == :zero ? zeros(count) : 6multipliers,
        column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_dependent_rows(problem); samples=3))
end
```

## Regression coverage

The zero-endpoint allocation guard failed against the original implementation:
11,576 allocations exceeded the 11,400 limit, while the other 101 assertions
passed. These include allocation guards for both nonzero-endpoint controls.
All 102 new assertions now pass, as do all 811 targeted dependency and presolve
assertions together. Allocation-count budgets avoid unstable exact-arithmetic
byte totals.

The tests exercise weight creation for the lower endpoint, the upper endpoint,
both, and neither. They cover positive and negative weights, unit and nonunit
weights, zero and unbounded bounds, ignored current rows and zero proof weights,
and input preservation across Float32, Float64, BigFloat, and Rational{BigInt}.
Existing targeted tests also cover cancellation, dependent-row removal,
contradictions, and postsolve values.

Independent review found no issues and separately passed all 102 new assertions.
Thirty-two bounded comparisons with the saved original implementation passed
192 additional assertions across all four numeric types. These cover fractional
weights, signs, all contribution paths, skipped proofs, stored 192/320-bit
BigFloat endpoints under 64-bit working precision, complete reductions,
infeasibility, postsolve, and input preservation.

The full mandatory suite passed all 20,577 assertions in 4m53.7s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
