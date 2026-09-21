# Skip unused activity removal for one-sided rows

Round 45 computes the minimum activity of other columns only when a row has a
finite upper bound, and their maximum activity only when it has a finite lower
bound. These are the only combinations used to form candidate bounds, for both
coefficient signs. An absent row bound now skips the corresponding
`_other_activity` call, including its exact subtraction when applicable.

Full row activities, unbounded counts, contradiction checks, and redundant-row
checks are still computed before candidate formation. Division, exactness checks,
accepted bound updates, worklists, and postsolve behavior remain unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 44 allocation rounds. All 33 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

Each probe has 128 identical rows involving `x + y`, both columns bounded by
`[1,10]`, and unit objective coefficients. The upper-only probe requires
`x + y ≤ 12`; the lower-only probe requires `x + y ≥ 4`. The control has both
row bounds. All three passes retain the original model without tightening.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Upper row bound only | 793,760 | 698,512 | 12.00% | 21,845 → 19,285 |
| Lower row bound only | 795,504 | 700,576 | 11.93% | 21,845 → 19,285 |
| Both row bounds | 1,103,696 | 1,104,544 | — | 29,781 → 29,781 |

Each one-sided probe removes 2,560 allocations. The control retains identical
allocation counts; its 848-byte increase is allocator variation.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 114,576 → 112,288 | 3,094 → 3,062 | 999,136 → 993,760 |
| adlittle | 761,048 → 754,408 | 20,928 → 20,796 | 3,877,160 → 3,840,104 |
| kb2 | 642,792 → 618,552 | 17,434 → 16,823 | 12,517,272 → 12,467,016 |
| sc50a | 318,864 → 310,240 | 8,521 → 8,346 | 3,951,968 → 3,947,072 |
| flugpl | 182,040 → 175,432 | 4,605 → 4,473 | 1,400,784 → 1,384,656 |

Standalone propagation allocates 0.87–3.77% fewer bytes on these fixtures.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,134,400 → 1,129,024 | 1,113,264 → 1,107,616 | 105 |
| adlittle | 4,665,560 → 4,629,416 | 4,942,648 → 4,906,472 | 945 |
| kb2 | 12,969,192 → 12,921,912 | 12,983,512 → 12,935,928 | 1,245 |
| sc50a | 4,298,096 → 4,291,584 | 4,250,864 → 4,244,528 | 95 |
| flugpl | 1,510,424 → 1,494,792 | 1,554,984 → 1,539,128 | 397 |

Whole solves with presolve allocate approximately 0.15–1.03% fewer bytes.
Full presolve removes the same number of allocations as each whole solve.
Unchanged paths without presolve have identical allocation counts, with byte
differences between -208 and +448. Exact arithmetic introduces further byte
variation, so not every byte of the reduction can be attributed to this change.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-one-sided-activity-allocations-before.toml`](propagation-one-sided-activity-allocations-before.toml)
and [`propagation-one-sided-activity-allocations-after.toml`](propagation-one-sided-activity-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-one-sided-activity-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for (low, high) in ((nothing, 12.0), (4.0, nothing), (4.0, 12.0))
    count = 128
    problem = LinearProblem(sparse(ones(count, 2)), ones(2);
        row_lower=fill(low, count), row_upper=fill(high, count),
        column_lower=ones(2), column_upper=fill(10.0, 2))
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

Both allocation guards failed against the original implementation: 21,890 and
21,853 allocations exceeded the 20,500 limit, while the other 162 assertions
passed. All 164 new assertions now pass, as do all 1,412 targeted propagation
assertions together. Direct test instrumentation adds a small overhead beyond
the warmed benchmark. Allocation counts avoid unstable exact-arithmetic byte
budgets.

The new tests cover both one-sided row directions, positive and negative
coefficients, the correct resulting column bound, changed-column flags,
postsolve values, input preservation, and contradictions detected from full
row activities. Numeric coverage includes Float32, Float64, BigFloat, and
Rational{BigInt}. Existing targeted tests also cover unbounded columns, signed
zero, mixed precision, incremental caches, restored bases, and failures after
prior tightening.

Independent review found no issues and separately passed all 164 new assertions.
Thirty-eight comparisons with the original implementation passed 142 assertions
across all four numeric types, covering lower, upper, both, and absent row bounds,
coefficient signs, unbounded columns, incremental caches, contradictions, mixed
BigFloat precision, original inputs, and postsolve.

The full mandatory suite passed all 19,632 assertions in 4m47.4s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
