# Skip division by one when normalizing parallel rows

Round 30 avoids exact rational division by one in `_parallel_signature` and
`_normalized_interval`. Unit-pivot signatures convert the stored coefficients
directly; unit-pivot intervals return the converted endpoints. Other pivots
retain their previous arithmetic, including swapping endpoints for negative
pivots. Support grouping, interval comparisons, row selection, and postsolve
maps remain unchanged.

The unit-interval branch occurs before the original endpoint assignments. This
keeps those locals out of the additional return path and avoids extra boxed
`Rational{BigInt}` values on the nonunit path in the measured Julia version.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 32 measurements per run recorded zero compilation
time. The baseline includes the preceding 29 rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

The unit-pivot probe has 128 identical rows `0 ≤ x + 2y - z ≤ 6`, free variables,
and a zero objective. Parallel-row reduction retains the first row. A control
scales every row and its upper bound by two.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Unit pivots | 635,056 | 407,440 | 35.84% | 18,362 → 12,346 |
| Nonunit pivots | 637,056 | 636,336 | — | 18,362 → 18,362 |

The nonunit control retains identical allocation counts; its small byte change
is not attributed to the optimization.

| Model | Parallel pass before | After | Allocations before → after | Full presolve before | After |
| --- | ---: | ---: | ---: | ---: | ---: |
| afiro | 8,336 | 8,336 | 127 → 127 | 1,143,048 | 1,139,320 |
| adlittle | 83,984 | 81,728 | 1,796 → 1,751 | 4,764,696 | 4,756,776 |
| kb2 | 213,216 | 204,240 | 5,517 → 5,301 | 13,161,632 | 13,142,736 |
| sc50a | 29,592 | 28,584 | 570 → 543 | 4,141,200 | 4,134,912 |
| flugpl | 6,016 | 6,016 | 91 → 91 | 1,501,832 | 1,500,904 |

The three affected direct fixture passes reduce allocated bytes by 2.69–4.21%.
Full presolve and both whole-solve algorithms remove 85 allocations on afiro,
180 on adlittle, 432 on kb2, and 135 on sc50a. These whole solves allocate
0.12–0.39% fewer bytes. Flugpl keeps identical counts, so its small byte changes
do not establish a benefit. Earlier presolve passes change the rows available
for grouping, explaining why direct-pass and complete-presolve counts differ.
Unchanged paths without presolve vary from -32 to +496 bytes with identical
allocation counts.

All ten model snapshots (five fixtures × parallel/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`parallel-unit-pivot-allocations-before.toml`](parallel-unit-pivot-allocations-before.toml)
and [`parallel-unit-pivot-allocations-after.toml`](parallel-unit-pivot-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_parallel_rows --output=parallel-unit-pivot-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for pivot in (1.0, 2.0)
    count = 128
    A = sparse(repeat(reshape([pivot, 2pivot, -pivot], 1, 3), count, 1))
    problem = LinearProblem(A, zeros(3); row_lower=zeros(count),
        row_upper=fill(6pivot, count), column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_parallel_rows(problem); samples=3))
end
```

## Regression coverage

All three final allocation budgets failed against the original helper bodies:
50,600 bytes against a 35,000-byte signature limit, 1,616 against a 1,000-byte
interval limit, and 624,688 against a 500,000-byte full-pass limit. All now pass.
These direct-call tests use a different call context from the warmed benchmark
and therefore have different byte totals.

The 159 new assertions cover the three budgets, signatures with pivots of 1,
-1, 2, and 1/2, bounded/unbounded interval endpoints, successively tighter rows,
overlapping intervals that must both remain, different signatures on the same
support, late contradictions, row names, postsolve maps and reconstruction, and
deep-copied input preservation. Numeric coverage includes Float32, Float64,
BigFloat, and Rational{BigInt}.

Independent review found no remaining issue in the final diff. Its 360
differential cases across six numeric types, including 95 failures, matched
baseline model/map/postsolve data and preserved inputs. Stored 512-bit BigFloat
values under a 64-bit ambient precision also matched in its semantic check. It
independently passed all 159 new assertions.

The complete mandatory suite passed **17,496/17,496** tests, including the 159 new
checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
