# Reuse terms when dependent-row interval sums are zero

Round 52 avoids adding a contribution to an exact zero running sum in
`_implied_interval`. Each endpoint now uses an explicit guarded block: retain
unboundedness, skip finite zero source bounds, calculate the contribution, then
reuse it if the sum is zero. This applies both to the initial sum and a sum that
has returned to zero through cancellation. Unit-weight multiplication shortcuts
remain intact. Nonzero sums keep the original addition; no exact values are
mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 51 allocation rounds. All 33 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The unit probe has 128 identical rows `1 ≤ x + 2y - z ≤ 6`, free columns, and a
zero objective. The nonunit probe scales all but the first row, including bounds,
by two. The zero-endpoint control uses 128 identical rows `x + 2y - z = 0`.
All three reductions retain the first row.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Unit weight | 709,600 | 623,952 | 12.07% | 18,389 → 16,103 |
| Nonunit weight | 970,240 | 884,624 | 8.82% | 25,247 → 22,961 |
| Zero endpoints | 512,704 | 505,072 | 1.49% | 12,293 → 12,039 |

Both nonzero-endpoint probes remove 2,286 allocations. The explicit guarded
blocks also remove 254 allocations from the zero-endpoint control, although
that path already skipped source arithmetic before this round.

| Model | Dependency pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 255,504 → 256,176 | 5,804 → 5,793 | 973,152 → 972,160 |
| adlittle | 808,792 → 809,960 | 19,175 → 19,175 | 3,815,448 → 3,813,384 |
| kb2 | 4,123,384 → 4,121,016 | 96,869 → 96,854 | 12,214,280 → 12,196,920 |
| sc50a | 1,964,560 → 1,964,992 | 48,044 → 48,034 | 3,887,808 → 3,885,200 |
| flugpl | 217,888 → 218,816 | 4,731 → 4,731 | 1,377,344 → 1,377,216 |

Direct dependency-pass allocation counts drop on afiro, kb2, and sc50a. The
small byte differences include cross-process exact-arithmetic variation:
afiro and sc50a use slightly more bytes despite their lower counts.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,109,600 → 1,107,440 | 1,088,048 → 1,086,640 | 39 |
| adlittle | 4,603,880 → 4,604,488 | 4,881,032 → 4,881,096 | 0 |
| kb2 | 12,666,008 → 12,650,056 | 12,678,952 → 12,664,152 | 388 |
| sc50a | 4,233,792 → 4,230,848 | 4,186,496 → 4,183,712 | 45 |
| flugpl | 1,486,216 → 1,487,464 | 1,530,712 → 1,531,624 | 0 |

The affected whole solves allocate 0.07–0.19% fewer bytes in these runs. Full
presolve removes the same number of allocations as each whole solve. Adlittle
and flugpl retain identical counts throughout; their byte differences do not
establish a benefit or regression. Unchanged paths without presolve vary from
-160 to +400 bytes with identical allocation counts. Counts provide clearer
evidence than the small fixture byte differences.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-zero-sums-allocations-before.toml`](dependent-zero-sums-allocations-before.toml)
and [`dependent-zero-sums-allocations-after.toml`](dependent-zero-sums-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-zero-sums-audit.toml
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

Both allocation guards failed against the original implementation: 18,434 and
25,255 allocations exceeded the 17,500 and 24,000 limits, respectively. The
other 118 assertions passed. All 120 new assertions now pass, as do all 591
targeted dependency and presolve assertions together. Allocation-count budgets
avoid unstable exact-arithmetic byte totals.

The tests cover cancellation to zero, subsequent positive and negative terms,
unit and nonunit weights, unbounded endpoints that remain unbounded despite
cancellation, zero coefficients and ignored current rows, dependent-row removal,
contradictions, postsolve values, and input preservation across Float32, Float64,
BigFloat, and Rational{BigInt}.

Independent review found no issues and separately passed all 120 new assertions.
Thirty-two interval comparisons and twelve full reduction comparisons with the
original implementation passed 136 additional assertions across all four
numeric types. These include cancellation followed by accumulation in the
actual dictionary iteration order, fractional weights, stored BigFloat endpoints
at 192/256/320-bit precision under 64-bit working precision, complete results,
contradictions, postsolve, and input preservation.

The review also independently confirmed two fewer allocations per contributing
row in all-zero intervals: before/after counts were 23/21, 35/31, and 107/91 for
one, two, and eight source rows, respectively, with identical outputs.

The full mandatory suite passed all 20,357 assertions in 4m55.7s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
