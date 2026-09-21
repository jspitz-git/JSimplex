# Avoid converting equal propagation candidates

Round 42 skips `_represent_exact` when a candidate bound already equals the
cached exact bound of the same column. An equal candidate cannot tighten the
stored bound, including when BigFloat working precision differs from input
precision. Existing contradiction checks still run first. Different candidates
retain the original conversion, exactness validation, and strict comparison
against the stored bound.

The cache already contains the finite bounds needed by each visited row and
is updated after every accepted tightening. This change adds no new storage
and preserves worklists, changed-column flags, and postsolve behavior.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 41 allocation rounds. All 32 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The probe has 128 rows `x + y = 10`, both columns bounded by `[0,10]`, and unit
objective coefficients. All four candidate bounds per row equal the existing
column bounds. The control uses `6 ≤ x + y ≤ 14`, producing weaker, different
candidates. Both passes retain the original model without tightening bounds.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Equal candidates | 995,088 | 680,448 | 31.62% | 26,703 → 19,791 |
| Different candidates | 1,015,264 | 1,016,512 | — | 27,471 → 27,471 |

The equal-candidate probe removes 6,912 allocations. The control retains
identical allocation counts; its 1,248-byte increase is allocator variation.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 136,224 → 124,160 | 3,613 → 3,361 | 1,029,800 → 1,015,408 |
| adlittle | 806,184 → 803,624 | 22,137 → 22,113 | 4,022,808 → 3,969,080 |
| kb2 | 686,072 → 671,256 | 18,510 → 18,210 | 12,620,128 → 12,580,360 |
| sc50a | 377,760 → 350,496 | 9,920 → 9,356 | 3,997,408 → 3,970,784 |
| flugpl | 195,752 → 195,560 | 4,969 → 4,969 | 1,432,872 → 1,423,600 |

Four standalone propagation passes allocate 0.32–8.86% fewer bytes. The fifth,
flugpl, has unchanged allocation counts; its 192-byte difference is not
attributed to this change. Full presolve benefits on all five models.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,165,944 → 1,151,008 | 1,145,320 → 1,130,288 | 291 |
| adlittle | 4,812,568 → 4,759,288 | 5,088,888 → 5,036,312 | 1,158 |
| kb2 | 13,070,880 → 13,034,696 | 13,085,088 → 13,048,712 | 771 |
| sc50a | 4,344,000 → 4,316,832 | 4,296,416 → 4,269,504 | 516 |
| flugpl | 1,542,256 → 1,533,912 | 1,586,480 → 1,578,248 | 165 |

Whole solves with presolve allocate approximately 0.28–1.31% fewer bytes.
Full presolve removes the same number of allocations as each whole solve.
Unchanged paths without presolve have identical allocation counts, with byte
differences between -384 and +288. Exact arithmetic introduces further byte
variation, so not every byte of the reduction can be attributed to this change.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-equal-candidates-allocations-before.toml`](propagation-equal-candidates-allocations-before.toml)
and [`propagation-equal-candidates-allocations-after.toml`](propagation-equal-candidates-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-equal-candidates-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for (low, high) in ((10.0, 10.0), (6.0, 14.0))
    count = 128
    problem = LinearProblem(sparse(ones(count, 2)), ones(2);
        row_lower=fill(low, count), row_upper=fill(high, count), column_upper=fill(10.0, 2))
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

The allocation guard failed against the original implementation: 26,748
allocations exceeded the 24,000 limit, while the other 152 assertions passed.
All 153 new assertions now pass, as do all 892 targeted propagation assertions
together. The direct guard includes 45 instrumentation allocations beyond the
warmed benchmark. Allocation counts avoid unstable exact-arithmetic byte budgets.

The new tests cover positive, negative, and nonunit coefficients, unchanged
worklists and existing change flags, postsolve values, original input
preservation, and equality with cache values updated earlier in the pass.
Numeric coverage includes Float32, Float64, BigFloat, and Rational{BigInt}.
Signed zero is retained, and stored 256-bit BigFloat bounds remain unchanged
under 64-bit working precision. Existing targeted tests cover different and
inexact candidates, unbounded activities, restored bases, and failures.

Independent review found no issues and separately passed all 153 new assertions.
Thirty-two comparisons with the original implementation passed 120 assertions
across all four numeric types, covering equal, weaker, and tightening bounds,
unbounded endpoints, signed zero, incremental caches, failures, original inputs,
and postsolve. Two additional assertions verified mixed BigFloat precision.

The full mandatory suite passed all 19,112 assertions in 4m47.1s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
