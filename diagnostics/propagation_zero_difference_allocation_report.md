# Skip zero subtraction in propagation candidates

Round 43 avoids subtracting an exact zero activity from a row bound when forming
a candidate column bound. This applies to both coefficient signs and both bound
directions. The row bound is already an exact `Rational{BigInt}`, so it can be
retained as the candidate numerator. Arithmetic does not mutate these values.
Nonzero activities retain the original subtraction; division, exactness checks,
contradiction checks, cache updates, and postsolve behavior are unchanged.

The shortcut also covers exact cancellation of nonzero activity terms. It is
only reached after the existing checks for finite row bounds and finite other
activity; unbounded contributions remain distinct from zero.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 42 allocation rounds. All 32 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The zero-activity probe has 128 independent rows `2 ≤ xᵢ ≤ 6`, initial column
bounds `[0,10]`, and unit objective coefficients. Every candidate has zero
other activity; the pass retains all rows and tightens every column to `[2,6]`.
The control has 128 rows `4 ≤ x + y ≤ 12` with both columns bounded by `[1,10]`.
Its other activities are nonzero, and propagation retains the original model.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Zero other activity | 713,616 | 625,968 | 12.28% | 19,393 → 17,089 |
| Nonzero other activity | 1,191,536 | 1,191,056 | — | 32,085 → 32,085 |

The zero-activity probe removes 2,304 allocations. The control retains
identical allocation counts; its 480-byte decrease is allocator variation.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 124,784 → 114,672 | 3,361 → 3,112 | 1,017,888 → 1,004,496 |
| adlittle | 805,832 → 773,144 | 22,113 → 21,261 | 3,974,248 → 3,914,168 |
| kb2 | 673,016 → 664,632 | 18,210 → 18,010 | 12,583,992 → 12,558,408 |
| sc50a | 351,552 → 331,008 | 9,356 → 8,854 | 3,973,776 → 3,957,232 |
| flugpl | 196,328 → 193,400 | 4,969 → 4,911 | 1,426,896 → 1,422,736 |

Standalone propagation allocates 1.25–8.10% fewer bytes on these fixtures.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,153,424 → 1,140,624 | 1,132,416 → 1,118,896 | 333 |
| adlittle | 4,763,560 → 4,703,608 | 5,040,152 → 4,980,440 | 1,598 |
| kb2 | 13,036,536 → 13,010,648 | 13,050,616 → 13,024,968 | 651 |
| sc50a | 4,320,000 → 4,302,960 | 4,272,864 → 4,255,264 | 430 |
| flugpl | 1,536,216 → 1,532,824 | 1,580,840 → 1,577,208 | 72 |

Whole solves with presolve allocate approximately 0.20–1.26% fewer bytes.
Full presolve removes the same number of allocations as each whole solve.
Unchanged paths without presolve have identical allocation counts, with byte
differences between -336 and +432. Exact arithmetic introduces further byte
variation, so not every byte of the reduction can be attributed to this change.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-zero-difference-allocations-before.toml`](propagation-zero-difference-allocations-before.toml)
and [`propagation-zero-difference-allocations-after.toml`](propagation-zero-difference-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-zero-difference-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
count = 128
zero_other = LinearProblem(sparse(1:count, 1:count, ones(count), count, count), ones(count);
    row_lower=fill(2.0, count), row_upper=fill(6.0, count), column_upper=fill(10.0, count))
nonzero_other = LinearProblem(sparse(ones(count, 2)), ones(2);
    row_lower=fill(4.0, count), row_upper=fill(12.0, count),
    column_lower=ones(2), column_upper=fill(10.0, 2))
for problem in (zero_other, nonzero_other)
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

The allocation guard failed against the original implementation: 19,438
allocations exceeded the 18,000 limit, while the other 248 assertions passed.
All 249 new assertions now pass, as do all 1,141 targeted propagation assertions
together. The direct guard includes 45 instrumentation allocations beyond the
warmed benchmark. Allocation counts avoid unstable exact-arithmetic byte budgets.

The new tests cover both bound directions and coefficients `1`, `-1`, `2`,
`-2`, `1/2`, and `-1/2`. They include zero other activity from cancellation,
change flags, postsolve values, and input preservation across Float32, Float64,
BigFloat, and Rational{BigInt}. Floating zero candidates retain their original
normalization. A stored 256-bit BigFloat candidate is still rejected at 64-bit
working precision while an exactly representable opposite bound is tightened.
Existing targeted tests also cover unbounded activities, nonzero differences,
incremental caches, restored bases, and failures.

Independent review found no issues and separately passed all 249 new assertions.
Forty comparisons with the original implementation passed 152 assertions across
all four numeric types, covering zero, cancelled, and nonzero other activities,
coefficient signs and fractions, incremental updates, unbounded bounds, failures,
signed zero, original inputs, and postsolve. Two additional assertions checked
mixed BigFloat precision.

The full mandatory suite passed all 19,361 assertions in 4m40.9s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
