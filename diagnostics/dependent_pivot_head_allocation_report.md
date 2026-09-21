# Reuse exact one for normalized dependency pivots

Round 57 avoids dividing a nonunit pivot coefficient by itself in
`reduce_dependent_rows`. Its normalized value is the exact unit value already
available as the initial proof seed. Selection uses the pivot's dictionary key,
not iteration position or column one. All other row coefficients and every
proof coefficient retain their existing division by the cached original scale.

The unit-pivot fast path, pivot selection, elimination, interval calculations,
work limits, contradictions, and postsolve behavior remain unchanged. No exact
values are mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 56 allocation rounds. All 33 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

Each probe has 128 independent rows, 129 free columns, a zero objective, and
upper row bounds of three. Row `i` has equal nonzero coefficients in columns
`i` and `i + 1`. The coefficients are two, negative two, or one. Every row is
retained and the model remains unchanged.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Pivot 2 | 410,736 | 367,872 | 10.44% | 7,962 → 6,810 |
| Pivot -2 | 410,704 | 367,808 | 10.44% | 7,962 → 6,810 |
| Pivot 1 | 276,880 | 277,232 | — | 4,506 → 4,506 |

Both nonunit probes remove 1,152 allocations. The unit control retains its
allocation count; its small byte difference does not establish a regression.

| Model | Dependency pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 254,384 → 247,216 | 5,708 → 5,510 | 969,952 → 961,808 |
| adlittle | 807,560 → 797,384 | 19,011 → 18,768 | 3,806,216 → 3,786,008 |
| kb2 | 4,112,008 → 4,100,056 | 96,494 → 96,161 | 12,145,320 → 12,120,472 |
| sc50a | 1,961,328 → 1,944,720 | 47,831 → 47,417 | 3,841,656 → 3,818,008 |
| flugpl | 219,024 → 215,712 | 4,681 → 4,582 | 1,373,824 → 1,355,856 |

All five direct dependency passes allocate less: 0.29–2.82% fewer bytes in these
runs, with consistently lower allocation counts.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,105,296 → 1,095,920 | 1,083,664 → 1,074,656 | 234 |
| adlittle | 4,594,376 → 4,577,064 | 4,871,816 → 4,853,912 | 468 |
| kb2 | 12,596,024 → 12,574,024 | 12,610,712 → 12,588,328 | 594 |
| sc50a | 4,187,512 → 4,163,352 | 4,139,528 → 4,115,784 | 576 |
| flugpl | 1,483,960 → 1,466,072 | 1,528,552 → 1,510,424 | 450 |

Whole solves allocate 0.17–1.21% fewer bytes. Full presolve removes the same
number of allocations as each whole solve. Exact-arithmetic byte totals
fluctuate across processes, so counts provide clearer evidence for small
differences. Unchanged paths without presolve vary from -64 to +528 bytes
with identical allocation counts.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-pivot-head-allocations-before.toml`](dependent-pivot-head-allocations-before.toml)
and [`dependent-pivot-head-allocations-after.toml`](dependent-pivot-head-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-pivot-head-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for pivot in (1.0, 2.0, -2.0)
    count = 128
    A = sparse([collect(1:count); collect(1:count)],
        [collect(1:count); collect(2:count+1)], fill(pivot, 2count), count, count + 1)
    problem = LinearProblem(A, zeros(count + 1); row_upper=fill(3.0, count),
        column_lower=fill(nothing, count + 1))
    println(measure_allocations(_ -> JSimplex.reduce_dependent_rows(problem); samples=3))
end
```

## Regression coverage

Both nonunit allocation guards failed against the original implementation:
8,007 and 7,970 allocations exceeded the 7,300 limit. The other 148 assertions,
including the unit-pivot control, passed. All 150 new assertions now pass,
as do all 1,204 targeted dependency and presolve assertions together.
Allocation-count budgets avoid unstable exact-arithmetic byte totals.

The tests cover positive, negative, and fractional pivots across Float32,
Float64, BigFloat, and Rational{BigInt}. Cases include nonunit pivots arising
after elimination, pivots outside the first column, single-term rows,
dependent-row removal, contradictions, postsolve values, and input preservation.

Independent review found no issues and separately passed all 150 new assertions.
Thirty-two saved-baseline comparisons passed 120 additional assertions across
all four numeric types, covering signed/fractional pivots, nonfirst-column and
after-elimination pivots, cancellation, single-term rows, retained/dependent/
infeasible cases, one-sided bounds, postsolve, identity, and input preservation.
Seven further assertions verified stored 256-bit BigFloat inputs under 64-bit
working precision, including preserved output coefficient and bound precision.

The full mandatory suite passed all 20,970 assertions in 4m51.9s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
