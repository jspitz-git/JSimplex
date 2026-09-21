# Share the initial proof coefficient in dependent-row reduction

Round 55 reuses one exact unit coefficient for the initial proof dictionaries
in `reduce_dependent_rows`. The value is constructed lazily for the first
nonempty coefficient row. Empty rows need no seed. Every row still receives a
separate dictionary: normalization replaces its entries, and elimination uses
nonmutating arithmetic before replacing or deleting entries. Neither operation
mutates the shared rational value.

All pivot selection, work limits, interval calculations, contradictions, and
postsolve behavior remain unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 54 allocation rounds. All 34 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The unit probe has 128 identical rows `1 ≤ x + 2y - z ≤ 6`, free columns, and a
zero objective. The nonunit probe scales all but the first row, including bounds,
by two. The zero-endpoint probe has identical rows `x + 2y - z = 0`. These three
reductions retain the first row. The empty control has 128 zero rows and zero
row bounds; its model remains unchanged.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Unit weight | 609,584 | 599,184 | 1.71% | 15,595 → 15,215 |
| Nonunit weight | 870,720 | 860,512 | 1.17% | 22,453 → 22,073 |
| Zero endpoints | 484,136 | 473,976 | 2.10% | 11,277 → 10,897 |
| Empty rows | 80,400 | 80,400 | 0% | 649 → 649 |

Each nonempty probe removes 380 allocations. The empty control preserves both
its byte total and allocation count.

A separate same-process comparison with the saved baseline checked tiny
zero-endpoint models using the same warmup and sampling protocol. With one
nonempty row the change costs one allocation (64 → 65; 3,464 → 3,496 bytes).
With two rows it already saves two allocations (189 → 187; 8,744 → 8,696 bytes).
Thus this optimization has a small cost for a single nonempty row. The cases
can be reproduced by setting `count` to one or two for the zero-endpoint probe
below. An explicit typed dictionary constructor gave identical allocation
counts to the chosen implementation in a separate constructor check.

| Model | Dependency pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 257,648 → 254,432 | 5,785 → 5,708 | 974,080 → 969,616 |
| adlittle | 812,440 → 805,896 | 19,175 → 19,011 | 3,815,672 → 3,804,760 |
| kb2 | 4,115,000 → 4,109,336 | 96,619 → 96,494 | 12,153,224 → 12,145,864 |
| sc50a | 1,965,488 → 1,961,472 | 47,978 → 47,835 | 3,850,664 → 3,840,056 |
| flugpl | 220,656 → 217,552 | 4,731 → 4,681 | 1,378,016 → 1,373,216 |

All five direct dependency passes allocate less: 0.14–1.41% fewer bytes in these
runs, with consistently lower allocation counts.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,109,392 → 1,104,688 | 1,088,096 → 1,083,056 | 121 |
| adlittle | 4,604,168 → 4,594,344 | 4,881,880 → 4,871,096 | 310 |
| kb2 | 12,603,320 → 12,595,144 | 12,618,232 → 12,609,000 | 247 |
| sc50a | 4,196,152 → 4,184,920 | 4,149,128 → 4,137,816 | 378 |
| flugpl | 1,487,752 → 1,482,792 | 1,532,344 → 1,527,304 | 138 |

Whole solves allocate 0.06–0.46% fewer bytes. Full presolve removes the same
number of allocations as each whole solve. Exact-arithmetic byte totals
fluctuate across processes, so counts provide clearer evidence for small
differences. Unchanged paths without presolve vary from -144 to +256 bytes
with identical allocation counts.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-proof-seed-allocations-before.toml`](dependent-proof-seed-allocations-before.toml)
and [`dependent-proof-seed-allocations-after.toml`](dependent-proof-seed-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-proof-seed-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:unit, :nonunit, :zero, :empty)
    count = 128
    multipliers = kind != :nonunit ? ones(count) : [1.0; fill(2.0, count - 1)]
    zero_bounds = kind in (:zero, :empty)
    problem = LinearProblem(kind == :empty ? spzeros(count, 3) :
        sparse(multipliers * [1.0 2.0 -1.0]), zeros(3);
        row_lower=zero_bounds ? zeros(count) : multipliers,
        row_upper=zero_bounds ? zeros(count) : 6multipliers,
        column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_dependent_rows(problem); samples=3))
end
```

## Regression coverage

The allocation guard failed against the original implementation: 11,322
allocations exceeded the 11,000 limit, while the other 130 assertions passed.
All 131 new assertions now pass, as do all 942 targeted dependency and presolve
assertions together. Allocation-count budgets avoid unstable exact-arithmetic
byte totals.

The tests cover positive, negative, and fractional nonunit pivot normalization,
subsequent proof elimination, repeated invocations, contradictions, postsolve,
and input preservation across Float32, Float64, BigFloat, and Rational{BigInt}.
They also check zero-row models, all-empty rows, and empty rows interspersed
with nonempty rows.

Independent review found no issues and separately passed all 131 new assertions.
Thirty-two saved-baseline cases across the four numeric types passed 1,627
additional assertions; six mixed stored/ambient BigFloat precision cases passed
354 more. The review verified independent/dependent/infeasible cases, signed
and fractional pivots, empty/interspersed/stored-zero rows, postsolve, and input
preservation. It confirmed that normalization and elimination replace entries
without mutating the shared exact seed.

The full mandatory suite passed all 20,708 assertions in 4m57.6s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
