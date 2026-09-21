# Cache a negated scale for missing unit terms

Round 61 reuses the negative elimination scale for missing target entries whose
source coefficient is one in `_subtract_scaled!`. The helper creates this value
only on first use and shares it for later matching entries in the same call.
Zero results remain absent. Existing entries and the negative-unit shortcuts
retain their previous behavior; the source and scale are never mutated.

The cache starts with the existing scale and a separate Boolean initialization
flag. This keeps its type concrete while deferring negation. A nullable rational
cache added allocations in a diagnostic comparison: the wide target
probe used 2,926 allocations and the duplicate-row control regressed from
10,897 to 11,024. The concrete cache reduces the target to 2,797 and preserves
the duplicate control at 10,897. An additional nonunit control remains at 4,203
allocations, compared with 4,204 for the nullable cache. Allocation limits were
not relaxed to accommodate the initial regression.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 60 allocation rounds. All 33 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The probes have two independent rows and 130 free columns, a zero objective,
and upper row bounds of three. The first row has coefficient one in column one
and 128 coefficients `v` in columns two through 129. The second has coefficient
`s` in column one and one in column 130. Eliminating column one introduces 128
previously absent coefficients. The target uses `(s, v) = (2, 1)`; controls use
`(2, 2)` and `(-1, 1)`. Every model is retained unchanged.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Missing unit terms | 125,512 | 120,128 | 4.29% | 3,051 → 2,797 |
| Nonunit source terms | 171,320 | 173,432 | — | 4,203 → 4,203 |
| Negative-unit scale | 73,472 | 74,320 | — | 1,623 → 1,623 |

The target removes 254 allocations. Both controls retain their counts; their
byte differences reflect cross-process exact-arithmetic allocation variation.

| Model | Dependency pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 209,792 → 210,928 | 4,565 → 4,557 | 878,352 → 877,296 |
| adlittle | 725,432 → 726,184 | 16,932 → 16,903 | 3,635,048 → 3,633,160 |
| kb2 | 3,502,512 → 3,494,584 | 80,974 → 80,732 | 11,224,648 → 11,210,296 |
| sc50a | 1,418,016 → 1,418,952 | 33,322 → 33,292 | 3,086,608 → 3,088,120 |
| flugpl | 197,872 → 198,688 | 4,158 → 4,158 | 1,340,224 → 1,340,720 |

Four direct passes remove allocations; flugpl is unchanged. Small byte increases
on afiro, adlittle, and sc50a coexist with their lower allocation counts.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,015,008 → 1,013,408 | 993,088 → 991,904 | 88 |
| adlittle | 4,424,024 → 4,422,040 | 4,700,840 → 4,699,064 | 62 |
| kb2 | 11,675,720 → 11,662,776 | 11,690,520 → 11,676,968 | 484 |
| sc50a | 3,432,400 → 3,433,192 | 3,385,008 → 3,385,992 | 6 |
| flugpl | 1,449,976 → 1,450,744 | 1,494,488 → 1,495,544 | 0 |

Full presolve removes the same number of allocations as each whole solve.
Fixture benefits are small compared with exact-arithmetic byte variation;
sc50a's totals increase despite six fewer allocations. Flugpl keeps identical
counts and establishes no benefit. Unchanged paths without presolve vary from
-368 to +304 bytes with identical allocation counts. Counts provide the clearer
evidence for these small fixture changes.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-negated-scale-allocations-before.toml`](dependent-negated-scale-allocations-before.toml)
and [`dependent-negated-scale-allocations-after.toml`](dependent-negated-scale-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-negated-scale-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for (scale, value) in ((2.0, 1.0), (2.0, 2.0), (-1.0, 1.0))
    count = 128
    A = sparse([ones(Int, count+1); 2; 2], [collect(1:count+1); 1; count+2],
        [1.0; fill(value, count); scale; 1.0], 2, count+2)
    problem = LinearProblem(A, zeros(count+2); row_upper=fill(3.0, 2),
        column_lower=fill(nothing, count+2))
    println(measure_allocations(_ -> JSimplex.reduce_dependent_rows(problem); samples=3))
end
```

## Regression coverage

The target allocation guard failed against the original implementation:
3,096 allocations exceeded the 2,900 limit. The other 139 assertions, including
both controls, passed. All 140 new assertions now pass, as do all 1,745 targeted
dependency and presolve assertions together. Allocation-count budgets avoid
unstable exact-arithmetic byte totals.

Tests cover multiple missing unit terms, mixed source values, existing entries
and cancellation, zero/fractional/negative scales, repeated invocations, and
preservation of previously returned values, source, and scale. Full reductions
cover Float32, Float64, BigFloat, and Rational{BigInt}, dependent-row removal,
contradictions, postsolve, and input preservation.

Independent review found no issues and separately passed all 140 new assertions.
Thirty-two saved-baseline scenarios passed 189 additional assertions: sixteen
direct helper cases and sixteen reductions across the four numeric types.
Coverage includes cache-sharing arithmetic, fallback behavior, negative-unit
precedence, repeated calls, failures, postsolve, and input preservation. Mixed
BigFloat coefficients stored at 80/384 bits and bounds at 96/320 bits matched
the baseline under 64-bit working precision. Subsequent arithmetic left sibling
entries sharing the cached rational components unchanged.

The full mandatory suite passed all 21,511 assertions in 4m54.5s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
