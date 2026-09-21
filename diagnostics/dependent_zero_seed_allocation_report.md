# Share the initial exact zero in dependent-row intervals

Round 53 initializes the upper sum in `_implied_interval` from the lower sum's
existing exact zero. Previously both endpoints constructed their own
`Rational{BigInt}` zero. Subsequent operations rebind the sums or use nonmutating
arithmetic, so neither endpoint changes the shared initial value. Each call
still constructs its own initial zero; there is no global mutable state.

All endpoint selection, unbounded and zero-source guards, unit-weight shortcuts,
zero-sum shortcuts, contradictions, and postsolve behavior remain unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 52 allocation rounds. All 33 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The unit probe has 128 identical rows `1 ≤ x + 2y - z ≤ 6`, free columns, and a
zero objective. The nonunit probe scales all but the first row, including bounds,
by two. The zero-endpoint probe uses 128 identical rows `x + 2y - z = 0`.
All three reductions retain the first row.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Unit weight | 624,000 | 609,280 | 2.36% | 16,103 → 15,595 |
| Nonunit weight | 885,168 | 870,512 | 1.66% | 22,961 → 22,453 |
| Zero endpoints | 505,664 | 491,120 | 2.88% | 12,039 → 11,531 |

Each probe removes 508 allocations, four for each of its 127 dependent-row
interval calculations.

| Model | Dependency pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 256,272 → 256,480 | 5,793 → 5,789 | 973,280 → 971,936 |
| adlittle | 809,912 → 809,656 | 19,175 → 19,175 | 3,815,416 → 3,813,464 |
| kb2 | 4,125,000 → 4,120,680 | 96,854 → 96,838 | 12,198,984 → 12,194,440 |
| sc50a | 1,967,008 → 1,965,920 | 48,034 → 48,030 | 3,887,088 → 3,880,832 |
| flugpl | 219,216 → 219,200 | 4,731 → 4,731 | 1,378,272 → 1,377,232 |

Direct dependency-pass allocation counts drop on afiro, kb2, and sc50a. The
small byte differences include cross-process exact-arithmetic variation:
afiro uses slightly more bytes despite its lower count.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,108,800 → 1,107,936 | 1,088,032 → 1,087,312 | 12 |
| adlittle | 4,604,264 → 4,603,640 | 4,881,560 → 4,880,104 | 0 |
| kb2 | 12,653,976 → 12,647,672 | 12,667,032 → 12,660,760 | 76 |
| sc50a | 4,233,488 → 4,226,960 | 4,185,760 → 4,179,808 | 144 |
| flugpl | 1,487,288 → 1,486,296 | 1,531,896 → 1,531,080 | 0 |

Full presolve removes the same number of allocations as each whole solve.
Adlittle and flugpl retain identical counts throughout; their byte differences
do not establish a benefit. Unchanged paths without presolve vary from -16 to
+432 bytes with identical allocation counts. Counts provide clearer evidence
than the small fixture byte differences.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-zero-seed-allocations-before.toml`](dependent-zero-seed-allocations-before.toml)
and [`dependent-zero-seed-allocations-after.toml`](dependent-zero-seed-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-zero-seed-audit.toml
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

The allocation guard failed against the original implementation: 12,084
allocations exceeded the 11,900 limit, while the other 117 assertions passed.
All 118 new assertions now pass, as do all 709 targeted dependency and presolve
assertions together. Direct instrumentation includes 45 allocations beyond the
warmed benchmark. Allocation-count budgets avoid unstable exact-arithmetic
byte totals.

The tests cover empty, current-row-only, zero-coefficient, finite-zero, positive,
negative, and one- or two-sided unbounded combinations across Float32, Float64,
BigFloat, and Rational{BigInt}. They check input preservation and that subsequent
calls do not overwrite previously returned endpoints. Existing targeted tests
also cover cancellation, continued accumulation, dependent-row removal,
contradictions, and postsolve values.

Independent review found no issues and separately passed all 118 new assertions.
Thirty-two comparisons with the saved original implementation passed 136
additional assertions: 24 interval cases and eight complete reductions across
all four numeric types. These cover empty and skipped combinations, signed
unit/nonunit terms, cancellation, unbounded endpoints, BigFloat precision
changes, contradictions, postsolve, and input preservation. The review also
confirmed that endpoint updates rebind values using nonmutating arithmetic and
current callers only compare returned endpoints.

The full mandatory suite passed all 20,475 assertions in 4m55.9s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
