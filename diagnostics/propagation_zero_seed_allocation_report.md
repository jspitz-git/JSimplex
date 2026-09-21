# Reuse a lazily initialized exact zero across propagation rows

Round 46 creates one exact zero per propagation pass instead of two per visited
nonempty row. Minimum and maximum sums start from that shared `Rational{BigInt}`
value. Subsequent arithmetic replaces values and does not mutate the zero, so
the sums remain independent across directions and rows.

Initialization occurs only at the first active nonempty row. Empty rows and
inactive rows still skip all activity setup; an entirely empty or inactive pass
does not allocate this zero. The value is local to the invocation, with no global
state. Bound caches, contradictions, redundancy, worklists, and postsolve logic
are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 45 allocation rounds. All 32 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The probe has 128 rows `x + y = 0`, both columns fixed to zero, and unit objective
coefficients. Propagation removes every row as redundant. The control uses the
same dimensions and bounds but an empty sparse matrix; propagation retains the
original model, as before this change.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| 128 nonempty rows | 252,544 | 227,408 | 9.95% | 7,782 → 6,890 |
| 128 empty rows | 7,168 | 7,168 | 0% | 152 → 152 |

The nonempty-row probe removes 892 allocations. Both allocated bytes and
allocation counts are unchanged for the empty-row control.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 114,704 → 108,128 | 3,062 → 2,877 | 995,024 → 987,824 |
| adlittle | 755,752 → 743,320 | 20,796 → 20,408 | 3,841,128 → 3,819,448 |
| kb2 | 619,688 → 610,120 | 16,823 → 16,526 | 12,471,032 → 12,451,592 |
| sc50a | 312,304 → 301,472 | 8,346 → 8,007 | 3,946,288 → 3,935,008 |
| flugpl | 175,672 → 171,176 | 4,473 → 4,351 | 1,386,272 → 1,378,688 |

Standalone propagation allocates 1.54–5.73% fewer bytes on these fixtures.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,129,536 → 1,123,504 | 1,108,608 → 1,101,600 | 195 |
| adlittle | 4,630,280 → 4,608,504 | 4,907,176 → 4,884,680 | 734 |
| kb2 | 12,921,976 → 12,906,024 | 12,936,072 → 12,918,984 | 587 |
| sc50a | 4,292,784 → 4,280,640 | 4,245,584 → 4,233,504 | 356 |
| flugpl | 1,495,912 → 1,488,376 | 1,540,376 → 1,532,984 | 219 |

Whole solves with presolve allocate approximately 0.12–0.63% fewer bytes.
Full presolve removes the same number of allocations as each whole solve.
Unchanged paths without presolve have identical allocation counts, with byte
differences between -544 and +64. Exact arithmetic introduces further byte
variation, so not every byte of the reduction can be attributed to this change.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-zero-seed-allocations-before.toml`](propagation-zero-seed-allocations-before.toml)
and [`propagation-zero-seed-allocations-after.toml`](propagation-zero-seed-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-zero-seed-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
count = 128
for A in (sparse(ones(count, 2)), spzeros(count, 2))
    problem = LinearProblem(A, ones(2);
        row_lower=zeros(count), row_upper=zeros(count), column_upper=zeros(2))
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

The allocation guard failed against the original implementation: 7,827
allocations exceeded the 7,200 limit, while the other 59 assertions passed.
All 60 new assertions now pass, as do all 1,472 targeted propagation assertions
together. The direct guard includes 45 instrumentation allocations beyond the
warmed benchmark. Allocation counts avoid unstable exact-arithmetic byte budgets.

The new tests cover positive, zero, and negative activities in successive rows,
redundant-row removal, empty and inactive prefixes before the first visited
nonempty row, untouched inactive columns, accepted tightenings, worklist
preservation, postsolve values, and original inputs. Entirely inactive and
empty passes retain their identity result. Numeric coverage includes Float32,
Float64, BigFloat, and Rational{BigInt}. Existing targeted tests additionally
cover cancellation, unbounded contributions, mixed precision, restored bases,
and failures after prior tightening.

Independent review found no issues and separately passed all 60 new assertions.
Thirty-eight comparisons with the original implementation passed 142 assertions
across all four numeric types, covering empty and inactive prefixes, no work,
successive activity signs, unbounded terms, cancellation, incremental updates,
failures, and mixed BigFloat precision. Twelve inference checks confirmed that
both sums remain `Rational{BigInt}` and return types match the baseline. No new
uninferred calls or mutable-sharing issues were found.

The full mandatory suite passed all 19,692 assertions in 4m52.0s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
