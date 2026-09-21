# Reuse the scale for unit source terms in exact elimination

Round 58 avoids multiplying a row-elimination scale by a unit source coefficient
in `_subtract_scaled!`. The product is already the scale. The existing shortcut
for a unit scale remains first, and all other products retain their multiplication.
This applies to elimination of both row coefficients and their proof coefficients.

Existing cancellation, deletion of zero results, missing target entries,
normalization, interval calculations, work limits, contradictions, and postsolve
behavior are unchanged. Neither the source dictionary nor the scale is mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 57 allocation rounds. All 33 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

Each probe has 128 proportional rows, free columns, and a zero objective. The
first row is `1 ≤ x + 2y - z ≤ 6`. Remaining rows multiply it by two, negative
two, or one, with bounds reordered when the sign changes. All three reductions
retain the first row.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Scale 2 | 859,664 | 774,288 | 9.93% | 22,073 → 19,787 |
| Scale -2 | 859,696 | 774,416 | 9.92% | 22,073 → 19,787 |
| Scale 1 | 598,848 | 599,888 | — | 15,215 → 15,215 |

Both nonunit probes remove 2,286 allocations. The unit-scale control retains
its allocation count; its small byte difference does not establish a regression.

| Model | Dependency pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 246,240 → 228,560 | 5,510 → 5,051 | 960,032 → 915,008 |
| adlittle | 795,944 → 729,208 | 18,768 → 16,986 | 3,788,856 → 3,639,416 |
| kb2 | 4,098,440 → 3,751,944 | 96,161 → 87,503 | 12,123,912 → 11,476,232 |
| sc50a | 1,943,696 → 1,775,104 | 47,417 → 42,926 | 3,819,656 → 3,634,120 |
| flugpl | 213,840 → 204,544 | 4,582 → 4,312 | 1,356,672 → 1,342,128 |

All five direct dependency passes allocate less: 4.35–8.67% fewer bytes in these
runs, with consistently lower allocation counts.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,096,112 → 1,051,472 | 1,075,376 → 1,030,192 | 1,197 |
| adlittle | 4,577,624 → 4,428,296 | 4,854,248 → 4,705,288 | 3,960 |
| kb2 | 12,573,880 → 11,930,696 | 12,588,744 → 11,945,000 | 15,885 |
| sc50a | 4,164,984 → 3,979,016 | 4,117,752 → 3,932,440 | 4,959 |
| flugpl | 1,465,880 → 1,450,744 | 1,510,520 → 1,495,432 | 414 |

Whole solves allocate 1.00–5.12% fewer bytes. Full presolve removes the same
number of allocations as each whole solve. Exact-arithmetic byte totals
fluctuate across processes, so counts provide clearer evidence for small
differences. Unchanged paths without presolve vary from -80 to +176 bytes
with identical allocation counts.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-unit-terms-allocations-before.toml`](dependent-unit-terms-allocations-before.toml)
and [`dependent-unit-terms-allocations-after.toml`](dependent-unit-terms-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-unit-terms-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for scale in (1.0, 2.0, -2.0)
    count = 128
    multipliers = [1.0; fill(scale, count - 1)]
    problem = LinearProblem(sparse(multipliers * [1.0 2.0 -1.0]), zeros(3);
        row_lower=min.(multipliers, 6multipliers), row_upper=max.(multipliers, 6multipliers),
        column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_dependent_rows(problem); samples=3))
end
```

## Regression coverage

Both nonunit allocation guards failed against the original implementation:
22,118 and 22,081 allocations exceeded the 20,500 limit. The other 133
assertions, including the unit-scale control, passed. All 135 new assertions
now pass, as do all 1,339 targeted dependency and presolve assertions together.
Allocation-count budgets avoid unstable exact-arithmetic byte totals.

Direct helper tests use literal expected dictionaries for positive, negative,
fractional, unit, and zero scales, with unit/nonunit/zero source terms, existing
and absent target entries, exact cancellation, and preservation of the source
and scale. Full reduction tests cover Float32, Float64, BigFloat, and
Rational{BigInt}, dependent-row removal, contradictions, postsolve values, and
input preservation.

Independent review found no issues and separately passed all 135 new assertions.
Thirty-two saved-baseline comparisons passed 184 additional assertions:
twelve direct helper cases, sixteen cross-type reduction cases, and four
mixed-precision BigFloat cases. These verify helper edge cases, contradictions,
intervals, postsolve, and input preservation, including the source and scale.

The full mandatory suite passed all 21,105 assertions in 4m54.0s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
