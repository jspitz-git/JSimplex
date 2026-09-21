# Negate exact bounds for negative unit activity products

Round 69 replaces multiplication by minus one with exact negation when computing
minimum and maximum activity terms in `_propagate_row_bounds`. The negative-unit
condition is computed once per coefficient. Existing unbounded, unit, and zero
shortcuts retain precedence; other coefficients retain multiplication. Cached
bounds and previous activity terms are never mutated. Candidate divisions,
representability checks, cache updates, incremental worklists, and postsolve
remain unchanged.

A baseline allocation profile of kb2's propagation pass, sampled at rate 0.1,
identified maximum activity-term construction among the leading allocation
sites: 85 sampled allocations and 4,256 sampled bytes at the original line 73.
Exact conversion remained the largest sampled site. The profile motivated this
bounded arithmetic change; sampled totals are not whole-call allocation totals.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 68 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The probes contain 128 identical rows `[c, c]` and two columns with objective
coefficients one. Column bounds are `[1, 10]`, except in the zero-bound target,
which uses `[0, 10]`. Row bounds exactly span the attainable activity, so all
rows are redundant. Targets use `c = -1`; controls use `c = 1`, `c = 2`, and
`c = -2`.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Negative unit, nonzero bounds | 526,752 | 379,744 | 27.91% | 15,094 → 11,510 |
| Negative unit, zero lower bounds | 379,024 | 304,816 | 19.58% | 10,992 → 9,200 |
| Unit coefficients | 336,640 | 335,712 | — | 9,974 → 9,974 |
| Positive nonunit coefficients | 528,112 | 527,088 | — | 15,094 → 15,094 |
| Negative nonunit coefficients | 528,016 | 527,104 | — | 15,094 → 15,094 |

The targets remove 3,584 and 1,792 allocations. All three controls retain their
counts; their small byte differences reflect cross-process exact-arithmetic
allocation variation, so no improvement is claimed for them.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 108,368 → 107,088 | 2,877 → 2,877 | 828,224 → 824,176 |
| adlittle | 744,024 → 742,384 | 20,408 → 20,387 | 3,621,832 → 3,617,224 |
| kb2 | 612,136 → 608,944 | 16,526 → 16,491 | 11,154,080 → 11,142,232 |
| sc50a | 302,848 → 292,048 | 8,007 → 7,769 | 3,062,528 → 3,056,208 |
| flugpl | 171,368 → 169,528 | 4,351 → 4,281 | 1,341,232 → 1,336,304 |

Four direct propagation passes remove allocations; afiro retains its count.
Sc50a has the largest direct-pass reduction, 238 allocations and 3.57% of bytes.
Earlier presolve stages expose a benefiting case on afiro.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 964,144 → 960,880 | 942,640 → 939,200 | 70 |
| adlittle | 4,410,856 → 4,406,856 | 4,687,352 → 4,682,824 | 42 |
| kb2 | 11,607,616 → 11,596,680 | 11,620,400 → 11,610,136 | 217 |
| sc50a | 3,408,512 → 3,401,632 | 3,361,200 → 3,354,560 | 112 |
| flugpl | 1,451,048 → 1,445,528 | 1,495,464 → 1,490,072 | 98 |

Full presolve removes the same number of allocations as each whole solve.
All five fixtures benefit at that level. Unchanged paths without presolve vary
from -96 to +176 bytes with identical allocation counts. Counts provide the
clearer evidence for small fixture differences; lower byte totals alone do not
establish a benefit when counts remain unchanged.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-negative-products-allocations-before.toml`](propagation-negative-products-allocations-before.toml)
and [`propagation-negative-products-allocations-after.toml`](propagation-negative-products-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --sample-rate=0.1 --output=propagation-negative-products-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:negative, :zero, :unit, :positive, :nonunit)
    count = 128
    coefficient = kind == :unit ? 1.0 : kind == :positive ? 2.0 : kind == :nonunit ? -2.0 : -1.0
    low = kind == :zero ? 0.0 : 1.0
    problem = LinearProblem(sparse(fill(coefficient, count, 2)), ones(2);
        row_lower=fill(min(2low*coefficient, 20coefficient), count),
        row_upper=fill(max(2low*coefficient, 20coefficient), count),
        column_lower=fill(low, 2), column_upper=fill(10.0, 2))
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

Both target allocation guards failed against the original implementation:
15,139 allocations exceeded the 13,000 limit, and 11,000 exceeded 9,900. The
other 140 assertions, including all three controls, passed. All 142 new assertions
now pass as part of 1,900 targeted propagation and presolve assertions.
Allocation-count budgets avoid unstable exact-arithmetic byte totals.

Tests cover Float32, Float64, BigFloat, and Rational{BigInt}, nonzero/zero/free
bounds, incremental cache replacement, incident-row activation, changed-column
tracking, positive and negative nonunit controls, contradictions, redundant-row
removal, postsolve, basis restoration, and input preservation.

Independent review found no issues and separately passed all 142 new assertions.
Saved-baseline comparisons passed 748 additional assertions across 32 four-type
scenarios and four mixed-precision BigFloat scenarios, each with full and
incremental worklists. Checks include changed flags, contradictions, redundant
rows, input preservation, postsolve, and basis restoration. Only the baseline
internal propagation function was renamed; unchanged helpers remained current.

The full mandatory suite passed all 22,601 assertions in 4m57.3s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
