# Skip conversion of weaker propagation candidates

Round 74 extends the existing exact-equality guard before `_represent_exact`.
A lower candidate at or below the cached finite lower bound, or an upper
candidate at or above the cached finite upper bound, cannot tighten the model.
These candidates now skip conversion to the working numeric type and the
conversion's exactness check. Contradiction checks still run first. Candidates
that improve a bound, including initially unbounded columns, retain the existing
representability checks and cache/worklist updates. Stored inputs are not mutated.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 73 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

The three targets contain 128 identical rows `[c, c]`, with coefficients `c`
equal to two, minus two, or one. Columns have bounds `[1, 10]`, and row bounds
are the sorted values `4c` and `18c`. Individual candidates are weaker than the
existing column bounds, so propagation retains the model unchanged.
The equal-bound control uses 128 rows `[1, 1]` with equality bound 10 and column
bounds `[0, 10]`. The tightening control contains 128 independent singleton rows
with coefficient two, row bounds `[4, 12]`, and initial column bounds `[1, 10]`;
propagation tightens all columns to `[2, 6]`. All objectives are ones.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Weaker, coefficient 2 | 1,442,608 | 1,109,104 | 23.12% | 38,617 → 30,937 |
| Weaker, coefficient -2 | 1,435,856 | 1,102,976 | 23.18% | 38,361 → 30,681 |
| Weaker, coefficient 1 | 1,079,344 | 746,768 | 30.81% | 28,889 → 21,209 |
| Equal-bound control | 528,672 | 528,480 | — | 15,443 → 15,443 |
| Tightening control | 707,696 | 707,648 | — | 19,141 → 19,141 |

Each target removes 7,680 allocations. Both controls retain their allocation
counts; their small byte differences reflect cross-process exact-arithmetic
variation, so no benefit is claimed for those cases.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 101,576 → 99,504 | 2,737 → 2,692 | 817,976 → 802,416 |
| adlittle | 742,040 → 686,464 | 20,329 → 19,298 | 3,614,984 → 3,471,072 |
| kb2 | 592,584 → 529,288 | 16,075 → 14,843 | 11,106,816 → 10,901,944 |
| sc50a | 268,952 → 250,312 | 7,196 → 6,843 | 3,049,840 → 3,042,552 |
| flugpl | 162,664 → 141,416 | 4,131 → 3,742 | 1,328,528 → 1,291,088 |

All five direct propagation passes benefit. Kb2 removes 1,232 allocations in
the direct pass; flugpl's direct allocated-byte total falls by about 13.1%.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 953,656 → 937,344 | 931,512 → 915,904 | 305 |
| adlittle | 4,405,176 → 4,261,856 | 4,681,336 → 4,539,072 | 2,631 |
| kb2 | 11,558,832 → 11,354,856 | 11,573,056 → 11,367,592 | 4,051 |
| sc50a | 3,395,168 → 3,388,680 | 3,348,048 → 3,341,272 | 115 |
| flugpl | 1,438,168 → 1,400,968 | 1,483,048 → 1,445,272 | 679 |

Full presolve and both whole solves remove allocations and allocated bytes on
all five fixtures. Paths without presolve keep identical allocation counts,
with byte differences from -208 to +80. No improvement is claimed for those
unchanged paths.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-weaker-candidates-allocations-before.toml`](propagation-weaker-candidates-allocations-before.toml)
and [`propagation-weaker-candidates-allocations-after.toml`](propagation-weaker-candidates-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-weaker-candidates-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function propagation_weaker_candidates_probe(kind; count=128)
    coefficient = kind == :negative ? -2.0 : kind == :unit ? 1.0 : 2.0
    if kind == :tightening
        return LinearProblem(sparse(1:count, 1:count, fill(coefficient, count), count, count), ones(count);
            row_lower=fill(4.0, count), row_upper=fill(12.0, count),
            column_lower=fill(1.0, count), column_upper=fill(10.0, count))
    elseif kind == :equal
        return LinearProblem(sparse(ones(count, 2)), ones(2);
            row_lower=fill(10.0, count), row_upper=fill(10.0, count),
            column_lower=zeros(2), column_upper=fill(10.0, 2))
    end
    return LinearProblem(sparse(fill(coefficient, count, 2)), ones(2);
        row_lower=fill(min(4coefficient, 18coefficient), count),
        row_upper=fill(max(4coefficient, 18coefficient), count),
        column_lower=fill(1.0, 2), column_upper=fill(10.0, 2))
end
for kind in (:positive, :negative, :unit, :equal, :tightening)
    problem = propagation_weaker_candidates_probe(kind)
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

All three target allocation guards failed on the original implementation:
38,662 exceeded 37,000, 38,369 exceeded 36,800, and 28,897 exceeded 27,000.
The other 172 assertions passed, including both controls. All 175 new assertions
now pass as part of 2,930 targeted propagation and presolve assertions.
Whole-pass budgets use allocation counts to avoid unstable exact-arithmetic
byte totals.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; positive,
negative, unit, and fractional coefficients; weaker, equal, and improving
candidates; preservation of bounds and pre-existing changed flags; postsolve;
and full/incremental propagation using the latest bounds from earlier rows.
Existing regression tests retain coverage of unbounded columns, contradictions,
representability, and stored BigFloat precision.

Independent review found no issues and separately passed all 175 new assertions.
An additional 15,281 independent assertions passed, including 1,397 saved-baseline
propagation comparisons, 32 idle-worklist calls, and 420 helper comparisons.
Coverage includes signed zero, unrepresentable weaker/improving bounds, partially
unbounded bounds, contradictions, mixed-precision BigFloat, and 600 deterministic
random LPs with full/partial worklists. Only the baseline activity helper and
internal propagation function were renamed and connected; other helpers remained
current.

The full mandatory suite passed all 23,631 assertions in 5m01.4s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
