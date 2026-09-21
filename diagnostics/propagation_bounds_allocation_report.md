# Lazy working bounds in propagation

Round 24 delays lower and upper column-bound copies in `_propagate_row_bounds`.
Each side initially references the input and is copied immediately before its
first accepted tightening. Later updates reuse the private copy. Exact-bound
caches are updated in the same places as before, so later rows see accumulated
bounds. The active worklist and changed-column mask retain their behavior.

Result construction still owns independent bounds, and `BoundPropagationStep`
retains the original bounds for restoration. Rejected candidates and failures
cannot modify the source model.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 32 measurements per run recorded zero compilation
time. The baseline includes the preceding 23 rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

The no-tightening probe has 4,096 free variables and one row, `0 ≤ x₁+x₂ ≤ 1`.
Neither individual bound can be tightened. It fell from **200,536 to 69,320 bytes
(65.43%)**, and from 108 to 102 allocations. A two-variable probe with initial
bounds `[0,10]` and row bounds `3 ≤ x₁+x₂ ≤ 5` only tightens upper bounds: it fell
from 16,064 to 15,968 bytes and from 431 to 429 allocations.

| Model | Propagation before | After | Allocations before → after | Full presolve before | After |
| --- | ---: | ---: | ---: | ---: | ---: |
| afiro | 199,888 | 198,832 | 5,092 → 5,090 | 1,174,664 | 1,172,840 |
| adlittle | 1,148,664 | 1,147,384 | 30,630 → 30,628 | 4,870,920 | 4,866,216 |
| kb2 | 938,184 | 937,688 | 24,783 → 24,781 | 13,164,464 | 13,165,280 |
| sc50a | 501,776 | 500,896 | 12,941 → 12,939 | 4,302,464 | 4,301,136 |
| flugpl | 229,064 | 228,792 | 5,787 → 5,787 | 1,505,312 | 1,504,816 |

Four direct fixture passes avoid one bound-vector copy. Flugpl still requires
both copies; its small byte difference is not attributed to this change.
Every whole solve with presolve enabled made six fewer allocations. Their byte
totals decreased by 0.004–0.088%, but full-presolve-only totals include an 816-byte
increase for kb2. These small whole-stage differences do not establish a uniform
byte reduction. The synthetic probe and allocation counts show the removed copies
more clearly. Unchanged whole-solve paths without presolve varied by -256 to
+48 bytes with identical allocation counts.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-bounds-allocations-before.toml`](propagation-bounds-allocations-before.toml)
and [`propagation-bounds-allocations-after.toml`](propagation-bounds-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-bounds-audit.toml
```

For the no-tightening probe, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
problem = LinearProblem(sparse([1, 1], [1, 2], [1.0, 1.0], 1, 4096), zeros(4096);
    column_lower=fill(nothing, 4096), row_lower=[0.0], row_upper=[1.0])
println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
```

## Regression coverage

The budget failed before the change at 200,536 bytes against a 100,000-byte limit
and now passes at 69,320 bytes. The 86 new checks cover identity returns without
tightening, lower-first and upper-first incremental updates, activation of a
later row, exact-cache consistency, changed-column masks, unchanged caller
worklists, original bounds stored for postsolve, independent result bounds, and
failure after an accepted tightening. Numeric coverage includes Float32,
Float64, BigFloat, and Rational{BigInt}.

Independent review found no issue. Its 270 differential cases across six numeric
types, including 18 failures and empty/full/partial worklists, matched baseline
results, metadata, and changed-column flags. Source bounds and caller worklists
remained unchanged.

The complete mandatory suite passed **16,477/16,477** tests, including the 86 new
checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
