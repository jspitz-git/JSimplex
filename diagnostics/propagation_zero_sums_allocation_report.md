# Reuse activity terms when the running sum is zero

Round 44 retains a nonzero exact activity term directly when its minimum or
maximum running sum is zero. This avoids constructing a new `Rational{BigInt}`
for `0 + term`, both at the start of a row and after exact cancellation.
Nonzero running sums retain the original addition. The existing handling of
zero terms and unbounded contributions is unchanged.

These exact values are not mutated by downstream arithmetic, and cache updates
replace entries. Retaining a term therefore preserves later activity removal,
candidate formation, contradictions, worklists, and postsolve behavior.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 43 allocation rounds. All 32 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The probe has 128 rows `0 ≤ x + y ≤ 20`, both columns bounded by `[1,10]`, and
unit objective coefficients. Its minimum and maximum activities each start
with a nonzero term. The control fixes both columns to zero, so the existing
zero-term guards already skip every addition. Both passes remove all rows as
redundant and preserve the column bounds.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Nonzero activity terms | 438,304 | 349,584 | 20.24% | 12,786 → 10,482 |
| All-zero activity terms | 263,920 | 262,816 | — | 8,166 → 8,166 |

The nonzero-term probe removes 2,304 allocations. The control retains
identical allocation counts; its 1,104-byte decrease is allocator variation.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 115,280 → 113,952 | 3,112 → 3,094 | 1,005,920 → 997,360 |
| adlittle | 773,848 → 758,696 | 21,261 → 20,928 | 3,912,504 → 3,874,760 |
| kb2 | 665,048 → 640,952 | 18,010 → 17,434 | 12,560,152 → 12,513,608 |
| sc50a | 331,760 → 317,424 | 8,854 → 8,521 | 3,958,208 → 3,948,176 |
| flugpl | 194,664 → 180,312 | 4,911 → 4,605 | 1,424,352 → 1,399,392 |

Standalone propagation allocates 1.15–7.37% fewer bytes on these fixtures.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,140,672 → 1,131,984 | 1,119,648 → 1,110,832 | 162 |
| adlittle | 4,703,992 → 4,663,976 | 4,980,344 → 4,941,112 | 981 |
| kb2 | 13,013,592 → 12,965,384 | 13,026,648 → 12,979,480 | 1,152 |
| sc50a | 4,303,488 → 4,294,096 | 4,256,272 → 4,246,704 | 153 |
| flugpl | 1,533,816 → 1,509,112 | 1,578,328 → 1,553,528 | 594 |

Whole solves with presolve allocate approximately 0.22–1.61% fewer bytes.
Full presolve removes the same number of allocations as each whole solve.
Unchanged paths without presolve have identical allocation counts, with byte
differences between -336 and +352. Exact arithmetic introduces further byte
variation, so not every byte of the reduction can be attributed to this change.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-zero-sums-allocations-before.toml`](propagation-zero-sums-allocations-before.toml)
and [`propagation-zero-sums-allocations-after.toml`](propagation-zero-sums-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-zero-sums-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for (low, high) in ((1.0, 10.0), (0.0, 0.0))
    count = 128
    problem = LinearProblem(sparse(ones(count, 2)), ones(2);
        row_lower=zeros(count), row_upper=fill(20.0, count),
        column_lower=fill(low, 2), column_upper=fill(high, 2))
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

The allocation guard failed against the original implementation: 12,831
allocations exceeded the 11,200 limit, while the other 106 assertions passed.
All 107 new assertions now pass, as do all 1,248 targeted propagation assertions
together. The direct guard includes 45 instrumentation allocations beyond the
warmed benchmark. Allocation counts avoid unstable exact-arithmetic byte budgets.

The new tests cover leading zero terms, positive and negative terms, exact
cancellation followed by another nonzero term, redundant-row removal, accepted
tightenings, changed-column flags, postsolve values, input preservation, and
finite sums alongside unbounded contributions. Numeric coverage includes
Float32, Float64, BigFloat, and Rational{BigInt}. Existing targeted tests also
cover signed zero, mixed precision, incremental caches, restored bases,
contradictions, and failures after prior tightening.

Independent review found no issues and separately passed all 107 new assertions.
Forty comparisons with the original implementation passed 152 assertions across
all four numeric types, covering cancellation and restarted sums, nonzero sums,
unbounded endpoints, incremental updates, failures, original inputs, and
postsolve. Two additional assertions checked mixed BigFloat precision.

The full mandatory suite passed all 19,468 assertions in 4m48.3s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
