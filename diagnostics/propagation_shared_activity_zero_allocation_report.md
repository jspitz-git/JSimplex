# Share the propagation zero with cancelled other activity

Round 73 passes the existing lazy exact activity zero to `_other_activity`.
When the finite total equals the removed term, the helper reuses this value
instead of constructing another rational zero. Three-argument calls retain
the previous fallback. Remaining unbounded terms are checked first, and zero
or unbounded removed terms still reuse the total. Unequal finite operands
still subtract normally. All arithmetic replaces values; neither inputs nor
the shared zero are mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 72 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation, so no runtime
speedup is claimed.

The targets contain 128 independent singleton rows with coefficients two,
minus two, or one, initial column bounds `[1, 10]`, and row bounds corresponding
to column bounds `[2, 6]`. Both activity directions cancel, and propagation
tightens every column to `[2, 6]`. The free-column control has unit coefficients
and initially unbounded columns. The unequal-total control contains 128 rows
`[2, 2]` with bounds `[8, 36]` and column bounds `[1, 10]`; no individual bound
can tighten. All objectives are ones.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Cancellation, coefficient 2 | 733,824 | 705,840 | 3.81% | 20,165 → 19,141 |
| Cancellation, coefficient -2 | 732,048 | 703,248 | 3.93% | 20,037 → 19,013 |
| Cancellation, coefficient 1 | 552,848 | 524,720 | 5.09% | 15,301 → 14,277 |
| Free-column control | 414,320 | 414,592 | — | 10,693 → 10,693 |
| Unequal-total control | 1,442,512 | 1,443,696 | — | 38,617 → 38,617 |

Each target removes 1,024 allocations. Both controls retain their allocation
counts; small byte differences reflect cross-process exact-arithmetic variation.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 101,960 → 101,400 | 2,737 → 2,737 | 818,344 → 815,880 |
| adlittle | 742,168 → 741,032 | 20,337 → 20,329 | 3,615,848 → 3,615,256 |
| kb2 | 593,896 → 593,064 | 16,127 → 16,075 | 11,108,000 → 11,106,240 |
| sc50a | 270,984 → 268,776 | 7,280 → 7,196 | 3,048,768 → 3,048,928 |
| flugpl | 162,648 → 161,496 | 4,151 → 4,131 | 1,329,456 → 1,327,056 |

Four direct propagation passes remove allocations; afiro retains its count.
Sc50a removes 84 allocations in its direct pass. Its full-presolve byte total
increases slightly despite 16 fewer allocations.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 953,224 → 953,640 | 931,912 → 930,792 | 32 |
| adlittle | 4,405,736 → 4,403,768 | 4,682,152 → 4,680,728 | 20 |
| kb2 | 11,559,328 → 11,558,208 | 11,574,912 → 11,571,600 | 76 |
| sc50a | 3,395,856 → 3,394,240 | 3,348,368 → 3,346,960 | 16 |
| flugpl | 1,438,712 → 1,438,136 | 1,483,128 → 1,482,552 | 36 |

Full presolve and both whole solves remove allocations on all five fixtures.
Afiro's dual-solve bytes increase slightly despite 32 fewer allocations.
Paths without presolve keep identical allocation counts, with byte differences
from -688 to +176. Counts provide clearer evidence for small fixture differences;
lower byte totals alone do not establish a benefit when counts remain unchanged.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-shared-activity-zero-allocations-before.toml`](propagation-shared-activity-zero-allocations-before.toml)
and [`propagation-shared-activity-zero-allocations-after.toml`](propagation-shared-activity-zero-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-shared-activity-zero-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:positive, :negative, :unit, :free, :unequal)
    count = 128
    coefficient = kind == :negative ? -2.0 : kind in (:unit, :free) ? 1.0 : 2.0
    problem = if kind == :unequal
        LinearProblem(sparse(fill(coefficient, count, 2)), ones(2);
            row_lower=fill(4coefficient, count), row_upper=fill(18coefficient, count),
            column_lower=fill(1.0, 2), column_upper=fill(10.0, 2))
    else
        LinearProblem(sparse(1:count, 1:count, fill(coefficient, count), count, count), ones(count);
            row_lower=fill(min(2coefficient, 6coefficient), count),
            row_upper=fill(max(2coefficient, 6coefficient), count),
            column_lower=fill(kind == :free ? nothing : 1.0, count),
            column_upper=fill(kind == :free ? nothing : 10.0, count))
    end
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

All three target allocation guards failed on the original implementation:
20,210 exceeded 19,700, 20,045 exceeded 19,600, and 15,309 exceeded 14,800.
The other 12 initial assertions passed, including both controls. All 333 new
assertions now pass as part of 2,755 targeted propagation and presolve assertions.
Whole-pass budgets use allocation counts to avoid unstable exact-arithmetic
byte totals.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; positive,
negative, and fractional coefficients; finite cancellation; unequal operands;
zero terms; remaining unbounded terms; compatibility of three-argument helper
calls; input and shared-zero preservation; cancellation between fixed columns;
activation of later rows; changed flags; postsolve; and full/incremental worklists.

Independent review found no issues and separately passed all 333 new assertions.
An additional 2,360 independent assertions passed, including 81 saved-baseline
propagation comparisons, 420 helper cases, and 32 idle-worklist checks. These
cover unbounded precedence, shared-zero identity, rational input/cache
preservation, mixed-precision BigFloat, incremental changes, failure metadata,
postsolve, and basis restoration. Only the baseline activity helper and internal
propagation function were renamed and connected; other helpers remained current.

The full mandatory suite passed all 23,456 assertions in 4m55.4s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
