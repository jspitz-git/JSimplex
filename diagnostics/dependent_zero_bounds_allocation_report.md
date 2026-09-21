# Skip zero source bounds in dependent-row intervals

Round 50 skips exact conversion, multiplication, and addition when a finite
source endpoint contributes zero to `_implied_interval`. The existing checks
for unbounded endpoints run first: a zero contribution cannot turn an unbounded
sum into a finite one. Coefficient signs still select the same source bounds;
zero coefficients and the current row remain excluded as before. No exact
values are mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 49 allocation rounds. All 32 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

Each probe has 128 identical rows with coefficients `[1, 2, -1]`, free columns,
and a zero objective. The target has row bounds `[0, 6]`; the control has bounds
`[1, 6]`. Dependency reduction retains the first row in both cases.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Zero lower bound | 771,744 | 654,368 | 15.21% | 19,532 → 16,484 |
| Nonzero endpoints | 799,536 | 798,448 | — | 20,675 → 20,675 |

The target removes 3,048 allocations. The control retains its allocation count;
its small byte difference does not establish a benefit.

| Model | Dependency pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 258,560 → 257,104 | 5,854 → 5,804 | 986,752 → 974,160 |
| adlittle | 810,376 → 809,672 | 19,175 → 19,175 | 3,814,920 → 3,815,384 |
| kb2 | 4,140,408 → 4,124,248 | 97,229 → 96,869 | 12,428,072 → 12,210,904 |
| sc50a | 1,970,608 → 1,965,920 | 48,069 → 48,044 | 3,931,088 → 3,887,808 |
| flugpl | 219,248 → 218,864 | 4,731 → 4,731 | 1,378,320 → 1,377,328 |

Direct dependency-pass savings on the three affected fixtures are 0.24–0.56%.
Earlier presolve passes expose additional zero endpoints, so the complete
presolve pipeline benefits more.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,123,056 → 1,109,936 | 1,101,872 → 1,088,864 | 292 |
| adlittle | 4,604,984 → 4,604,696 | 4,881,352 → 4,881,480 | 0 |
| kb2 | 12,881,880 → 12,665,128 | 12,895,848 → 12,679,288 | 5,483 |
| sc50a | 4,277,056 → 4,233,232 | 4,229,952 → 4,186,032 | 1,080 |
| flugpl | 1,488,248 → 1,486,728 | 1,533,064 → 1,531,176 | 0 |

The affected whole solves allocate 1.02–1.68% fewer bytes. Full presolve removes
the same number of allocations as each whole solve. Adlittle and flugpl retain
identical counts throughout; their byte differences do not establish a benefit.
Unchanged paths without presolve vary from -272 to +16 bytes with identical
allocation counts. Exact-arithmetic byte totals fluctuate across processes.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-zero-bounds-allocations-before.toml`](dependent-zero-bounds-allocations-before.toml)
and [`dependent-zero-bounds-allocations-after.toml`](dependent-zero-bounds-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-zero-bounds-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for low in (0.0, 1.0)
    count = 128
    problem = LinearProblem(sparse(repeat([1.0 2.0 -1.0], count, 1)), zeros(3);
        row_lower=fill(low, count), row_upper=fill(6.0, count),
        column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_dependent_rows(problem); samples=3))
end
```

## Regression coverage

Both allocation guards failed against the original implementation: 19,577 and
19,540 allocations exceeded the 18,000 limit for zero lower and upper bounds,
respectively. The other 110 assertions passed. All 112 new assertions now pass,
as do all 345 targeted dependency and presolve assertions together.
Allocation-count budgets avoid unstable exact-arithmetic byte totals.

The tests distinguish finite zero from unbounded endpoints, cover both signs
of proof coefficients, ignored current rows and zero weights, dependent-row
removal, contradictions, postsolve values, and input preservation across
Float32, Float64, BigFloat, and Rational{BigInt}.

Independent review found no issues and separately passed all 112 new assertions.
Thirty-two comparisons with the original implementation passed 103 additional
assertions across all four numeric types, including cancellation, mixed stored
96/192-bit BigFloat endpoints under 64-bit working precision, complete results,
and input preservation.

The full mandatory suite passed all 20,111 assertions in 4m49.6s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
