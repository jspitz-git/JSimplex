# Lazy selection storage for dual fixing

Round 35 delays the selection vector in `reduce_dual_fixings` until the first
eligible column. A pass that selects no column returns the original problem
without constructing the vector or scanning it afterward. On the first hit,
the original typed vector is initialized with `nothing` for all columns;
later hits reuse it.

The eligibility conditions and their order are unchanged. A zero-cost column
still prefers a feasible lower-bound move and falls back to its upper bound
when appropriate. The selected value and variable state are passed to the
unchanged basic-presolve implementation, including its exactness checks and
possible rejection of a selected column.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 32 measurements per run recorded zero compilation
time. The baseline includes the preceding 34 allocation rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

Both probes use a 128 × 128 identity matrix, objective coefficients of one,
and column bounds `[0,1]`. In the blocked probe, row bounds `[0,1]` prevent all
downward moves. In the selected control, rows have only upper bounds of one,
allowing every column to be fixed to zero.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| All candidates blocked | 2,392 | 144 | 93.98% | 4 → 1 |
| All candidates selected | 225,736 | 225,512 | — | 6,064 → 6,064 |

The selected control still needs the vector. Its 224-byte difference is not
attributed to this optimization; allocation counts are identical.

| Model | Dual-fixing pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 752 → 144 | 3 → 1 | 1,131,128 → 1,128,888 |
| adlittle | 39,040 → 39,040 | 119 → 119 | 4,734,088 → 4,730,552 |
| kb2 | 912 → 144 | 3 → 1 | 13,125,808 → 13,125,360 |
| sc50a | 1,072 → 144 | 3 → 1 | 4,120,128 → 4,119,088 |
| flugpl | 10,464 → 10,464 | 115 → 115 | 1,493,000 → 1,492,232 |

The standalone passes on afiro, kb2, and sc50a select no columns and save
80.85%, 84.21%, and 86.57%, respectively. Adlittle and flugpl still allocate
their selection vectors. Later no-selection passes within full presolve can
avoid storage on all five models.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,266,312 → 1,265,112 | 1,245,432 → 1,243,336 | 4 |
| adlittle | 5,523,320 → 5,520,840 | 5,801,032 → 5,797,080 | 2 |
| kb2 | 13,580,640 → 13,577,312 | 13,595,952 → 13,590,880 | 4 |
| sc50a | 4,467,760 → 4,464,384 | 4,420,752 → 4,417,216 | 4 |
| flugpl | 1,602,176 → 1,601,424 | 1,647,328 → 1,646,240 | 2 |

Full presolve removes the same number of allocations as each whole solve.
Cross-process byte variability prevents attributing the entire byte difference
to this change: unchanged paths without presolve vary from -480 to 0 bytes
with identical allocation counts, and exact arithmetic in presolve introduces
further variation. The isolated blocked-candidate measurements give the
clearest evidence.

All ten model snapshots (five fixtures × dual-fixing/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dual-selections-allocations-before.toml`](dual-selections-allocations-before.toml)
and [`dual-selections-allocations-after.toml`](dual-selections-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dual_fixings --output=dual-selections-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:blocked, :selected)
    count = 128
    A = sparse(1:count, 1:count, ones(count), count, count)
    problem = LinearProblem(A, ones(count);
        row_lower=kind == :blocked ? zeros(count) : fill(nothing, count),
        row_upper=ones(count), column_lower=zeros(count), column_upper=ones(count))
    println(measure_allocations(_ -> JSimplex.reduce_dual_fixings(problem); samples=3))
end
```

## Regression coverage

The new 512-byte budget failed against the original body at 2,392 bytes and
now passes. All 166 new assertions pass, covering identity returns, skipped
columns before the first selection, both objective senses, zero-cost lower
preference and upper fallback, nonzero objective contributions, negative
coefficients, selected values and states, retained rows and columns, names,
postsolve primal values, restored bases, input preservation, empty matrix
dimensions, and absent finite column bounds. Numeric coverage includes
Float32, Float64, BigFloat, and Rational{BigInt}.

Independent review found no issue and passed all 166 new assertions. Its 688
differential assertions across 144 models covered six numeric types (also
Float16 and Rational{Int}) and both objective senses. Complete result and failure
fields, inputs, identity behavior, primal reconstruction, and basis restoration
matched the renamed baseline. Edge cases included stored zeros, infeasible
empty rows, and selected candidates subsequently rejected for inexact objective
or row-bound updates.

The complete mandatory suite passed **18,005/18,005** tests, including the 166
new assertions. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
