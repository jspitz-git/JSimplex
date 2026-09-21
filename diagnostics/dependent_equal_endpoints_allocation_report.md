# Reuse exact contributions for equal dependency endpoints

Round 65 reuses a computed lower contribution for an equal upper endpoint in
`_implied_interval`. This avoids a second exact conversion and, for nonunit
weights, a second multiplication or negation. Reuse requires both equal source
values and a lower contribution computed during the current proof iteration.
The per-iteration `coefficient` sentinel distinguishes that case from a skipped
lower calculation, including an already unbounded lower sum. Otherwise the
upper contribution is computed as before. Zero, infinite, and unequal endpoints
retain their existing paths. Arithmetic never mutates the shared rational term.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 64 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The probes contain 128 proportional rows and three free columns with zero
objective. The first row is `[1, 2, -1]`; subsequent rows are its multiple by
`s`. Equality bounds have right-hand side `3s`, with three in the first row.
Targets use `s = 1`, `s = -1`, and `s = 2`. Controls use `s = 1` with unequal
bounds `[3, 6]` or equality bounds of zero. Only the first row is retained.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Unit weight, equal endpoints | 600,048 | 552,776 | 7.88% | 15,215 → 13,691 |
| Negative unit weight, equal endpoints | 624,232 | 568,488 | 8.93% | 15,977 → 14,199 |
| Nonunit weight, equal endpoints | 739,496 | 648,080 | 12.36% | 18,898 → 16,231 |
| Unequal endpoints | 602,560 | 600,624 | — | 15,215 → 15,215 |
| Zero endpoints | 475,432 | 473,480 | — | 10,897 → 10,897 |

The targets remove 1,524, 1,778, and 2,667 allocations. Both controls retain
their counts; their small byte differences reflect cross-process exact-arithmetic
allocation variation, so no benefit is claimed for those controls.

| Model | Dependency pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 201,088 → 198,192 | 4,272 → 4,272 | 832,704 → 830,496 |
| adlittle | 721,016 → 718,904 | 16,762 → 16,762 | 3,626,600 → 3,625,512 |
| kb2 | 3,469,264 → 3,467,408 | 80,025 → 80,025 | 11,168,656 → 11,164,016 |
| sc50a | 1,332,536 → 1,331,240 | 31,066 → 31,066 | 3,064,592 → 3,061,872 |
| flugpl | 185,120 → 183,568 | 3,830 → 3,830 | 1,343,312 → 1,340,784 |

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 967,696 → 966,320 | 946,720 → 944,544 | 0 |
| adlittle | 4,417,400 → 4,414,376 | 4,693,944 → 4,692,008 | 0 |
| kb2 | 11,619,840 → 11,619,904 | 11,634,192 → 11,632,512 | 0 |
| sc50a | 3,410,624 → 3,407,280 | 3,363,392 → 3,359,648 | 0 |
| flugpl | 1,453,160 → 1,450,952 | 1,497,736 → 1,495,416 | 0 |

All five fixtures retain identical allocation counts in the direct pass, full
presolve, and whole solves. The measurements therefore establish a benefit for
the targeted equality cases, not for these fixtures. Unchanged paths without
presolve vary from -32 to +224 bytes with identical allocation counts. Smaller
byte totals alone do not establish an improvement when counts remain unchanged.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-equal-endpoints-allocations-before.toml`](dependent-equal-endpoints-allocations-before.toml)
and [`dependent-equal-endpoints-allocations-after.toml`](dependent-equal-endpoints-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-equal-endpoints-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:unit, :negative, :nonunit, :unequal, :zero)
    count = 128
    scale = kind == :negative ? -1.0 : kind == :nonunit ? 2.0 : 1.0
    multipliers = [1.0; fill(scale, count-1)]
    other = (kind == :unequal ? 6 : 3) .* multipliers
    problem = LinearProblem(sparse(multipliers * [1.0 2.0 -1.0]), zeros(3);
        row_lower=kind == :zero ? zeros(count) : min.(3multipliers, other),
        row_upper=kind == :zero ? zeros(count) : max.(3multipliers, other),
        column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_dependent_rows(problem); samples=3))
end
```

## Regression coverage

All three target allocation guards failed against the original implementation:
15,260 exceeded the 14,800 limit, 15,985 exceeded 15,500, and 18,906 exceeded
18,000. The other 155 assertions, including both controls, passed. All 158 new
assertions now pass as part of 2,356 targeted dependency assertions.
Allocation-count budgets avoid unstable exact-arithmetic byte totals.

Tests cover Float32, Float64, BigFloat, and Rational{BigInt}, positive and
negative equal endpoints, unit/nonunit/fractional weights, one-sided and fully
unbounded sums, zero and unequal endpoints, ignored current proof entries,
row removal, contradictions, postsolve, and preservation of inputs.

Independent review found no issues and separately passed all 158 new assertions.
Thirty-two saved-baseline scenarios passed 241 additional assertions across the
four numeric types, including complete reductions and contradictions. Explicit
dictionary iteration ordering put an unbounded lower contribution before an
equality row and verified the remaining finite upper sum. Sixteen additional
BigFloat cases passed 113 assertions with endpoints stored at 192/224 bits and
working precision from 32 to 256 bits. Equal and unequal stored endpoints,
baseline agreement, and input preservation were checked without rounding the
comparison snapshots to ambient precision.

The full mandatory suite passed all 22,129 assertions in 4m58.7s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
