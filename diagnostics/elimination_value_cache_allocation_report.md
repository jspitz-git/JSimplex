# Reuse exact eliminated values in basic presolve

Round 28 converts each selected elimination value to `Rational{BigInt}` once in
`_presolve_basic`. The objective contribution and all incident row shifts reuse
that exact value. Previously each stored coefficient triggered another identical
conversion. The value remains local to its selected column; original values and
states are still stored for postsolve.

Candidate selection, representability checks, rejected-candidate rollback, and
the order of accepted updates remain unchanged. Explicit selections used by
other presolve passes use the same path.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 32 measurements per run recorded zero compilation
time. The baseline includes the preceding 27 rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

The probes have 256 rows `1 ≤ x + yᵢ ≤ 3`, with `0 ≤ yᵢ ≤ 2`, objective
`2x + sum(yᵢ)`, and `x` fixed to either 0.5 or zero. Both eliminate only `x` in
the measured basic pass.

| Fixed value | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| 0.5 | 1,077,528 | 983,560 | 8.72% | 27,036 → 23,964 |
| 0 | 354,712 | 278,296 | 21.54% | 7,286 → 4,982 |

The 256 avoided conversions remove 3,072 allocations for 0.5 and 2,304 for zero.
All five standalone basic passes on the original fixtures retain identical bytes
and allocation counts. Their original models do not exercise repeated value
conversion along an eliminated column. Later passes can make additional
eliminations possible.

| Model | Full presolve before | After | Allocations before → after |
| --- | ---: | ---: | ---: |
| afiro | 1,143,688 | 1,141,160 | 26,838 → 26,838 |
| adlittle | 4,767,320 | 4,761,288 | 118,050 → 117,987 |
| kb2 | 13,160,672 | 13,158,224 | 292,209 → 292,209 |
| sc50a | 4,141,840 | 4,139,728 | 102,013 → 102,013 |
| flugpl | 1,503,248 | 1,499,240 | 39,158 → 39,089 |

Both whole-solve algorithms with presolve remove 63 allocations on adlittle and
69 on flugpl, with unchanged counts on the other three models. The corresponding
adlittle byte totals are 5,556,840 → 5,551,496 (dual) and 5,833,720 → 5,828,696
(primal); flugpl totals are 1,612,888 → 1,610,016 and 1,657,272 → 1,654,640.
Those reductions are approximately 0.09–0.18% and include measurement variation.
No whole-solver benefit is inferred from unchanged allocation counts elsewhere.
Unchanged paths without presolve varied by -720 to +128 bytes, also with identical
counts. The synthetic probes show the removed conversions more clearly.

All ten model snapshots (five fixtures × basic/full presolve) matched exactly:
CSC arrays, objective and constant, sense, bounds, domains, names, and original
column count. All 20 whole-solve combinations remained `OPTIMAL`, with identical
status, objective, complete primal vector, and iteration count (`isequal`).

Machine-readable results:
[`elimination-value-cache-allocations-before.toml`](elimination-value-cache-allocations-before.toml)
and [`elimination-value-cache-allocations-after.toml`](elimination-value-cache-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=elimination-value-cache-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for value in (0.5, 0.0)
    count = 256
    A = hcat(sparse(ones(count, 1)),
        sparse(1:count, 1:count, ones(count), count, count))
    problem = LinearProblem(A, [2.0; ones(count)];
        row_lower=ones(count), row_upper=fill(3.0, count),
        column_lower=[value; zeros(count)], column_upper=[value; fill(2.0, count)])
    println(measure_allocations(_ -> JSimplex._presolve_basic(problem); samples=3))
end
```

## Regression coverage

The direct-call allocation budgets failed before the change at 1,064,712 bytes
against a 1,020,000-byte limit and 345,256 bytes against a 320,000-byte limit.
Both now pass. Their call context differs from the warmed benchmark harness, so
their byte counts are not the table's benchmark results.

The 121 new checks cover the two budgets, per-column reuse with distinct positive
and negative values, automatic and explicit selections, objective constants,
shifted row bounds, removed states, postsolve reconstruction, and deep-copied
input preservation. Numeric coverage includes Float32, Float64, BigFloat, and
Rational{BigInt}. A separate case retains a 256-bit BigFloat input while the pass
runs with a 64-bit default precision. Together with 79 existing checks for lazy
row bounds and rejected eliminations, all 200 targeted assertions pass.

Independent review found no issue. Its 432 differential cases across six numeric
types matched baseline model fields, CSC storage, postsolve values, and all 11
failure results. Deep-copied inputs remained unchanged. Cases included automatic
and explicit selections, negative values, signed zero, and inexact reductions.
It independently passed all 121 new assertions.

The complete mandatory suite passed **17,111/17,111** tests, including the 121 new
checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
